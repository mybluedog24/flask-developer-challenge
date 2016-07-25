# coding=utf-8
"""
Exposes a simple HTTP API to search a users Gists via a regular expression.

Github provides the Gist service as a pastebin analog for sharing code and
other develpment artifacts.  See http://gist.github.com for details.  This
module implements a Flask server exposing two endpoints: a simple ping
endpoint to verify the server is up and responding and a search endpoint
providing a search across all public Gists for a given Github account.
"""

import requests
from flask import Flask, jsonify, request
import re


# *The* app object
app = Flask(__name__)


@app.route("/ping")
def ping():
    """Provide a static response to a simple GET request."""
    return "pong"


def gists_for_user(username):
    """Provides the list of gist metadata for a given user.

    This abstracts the /users/:username/gist endpoint from the Github API.
    See https://developer.github.com/v3/gists/#list-a-users-gists for
    more information.

    Args:
        username (string): the user to query gists for

    Returns:
        The dict parsed from the json response from the Github API.  See
        the above URL for details of the expected structure.
    """
    gists_url = 'https://api.github.com/users/{username}/gists'.format(
            username=username)
    response = requests.get(gists_url)
    # TODO: BONUS: What failures could happen?
    # TODO: BONUS: Paging? How does this work for users with tons of gists?

    return response.json()


@app.route("/api/v1/search", methods=['POST'])
def search():
    """Provides matches for a single pattern across a single users gists.

    Pulls down a list of all gists for a given user and then searches
    each gist for a given regular expression.

    Returns:
        A Flask Response object of type application/json.  The result
        object contains the list of matches along with a 'status' key
        indicating any failure conditions.
    """
    post_data = request.get_json()
    # BONUS: Validate the arguments?
    # Validate keys
    if set(["username", "pattern"]) != set(post_data):
        raise TypeError("request must have excatly keys ['username', 'pattern']: ", post_data.keys())
    # Validate data type of username
    if not isinstance(post_data["username"], unicode):
        raise TypeError("username must be unicode type: ", type(post_data["username"]))
    # Validate data type of pattern
    if not isinstance(post_data["pattern"], unicode):
        raise TypeError("pattern must be unicode type: ", type(post_data["pattern"]))
    # BONUS DONE

    username = post_data['username']
    pattern = post_data['pattern']

    result = {}
    gists = gists_for_user(username)
    # BONUS: Handle invalid users?
    if "message" in gists:
        raise ValueError("username %s: %s" % (str(username), str(gists["message"])))
    # BONUS DONE

    result['matches'] = []
    result['status'] = 'success'

    for gist in gists:
        gist_url = gist["url"]
        html_url = gist["html_url"]
        response = requests.get(gist_url)
        status_code = response.status_code

        # 1. Check status code
        if status_code != 200:
            result['status'] = 'failure'
            continue

        # 2. Search pattern without checking truncation
        match = re.search(pattern, response.content)
        if match:
            result_url = html_url.replace(gist["id"], username + "/" + gist["id"])
            result['matches'].append(result_url)
            continue

        # 3. If no match is found, search truncated files
        #    Documentation about truncation: https://developer.github.com/v3/gists/#truncation
        # TODO: Handle Truncation case1: total number exceeds 300 files
        # TODO: Find a better way to handle this case instead of clone the gist
        # My current idea is clone the gist and store it to a folder.
        # And then search the entire folder to find the pattern.
        # After that, delete the temp folder. But this requires more space and
        # low performance. Also I don't like executing external commands..

        # if gist["truncated"]:
        #     git_pull_url = gist["git_pull_url"]
        #     temp_folder = "./temp_folder/"
        #     os.system("git clone %s %s" % (git_pull_url, temp_folder))

        # 4. If no match is found, search truncated files (including files from 3.)
        #    Documentation about truncation: https://developer.github.com/v3/gists/#truncation
        #    Handle Truncation case2: file content exceeds limit (up to one megabyte)
        # TODO: Find a better way to handle this case Instead of download the whole content
        # If the file is very large, it will slow the process.

        gist_url_response = requests.get(gist_url)
        gist_json = gist_url_response.json()
        files = gist_json["files"]
        for key in files:
            if files[key]["truncated"]:
                file_response = requests.get(files[key]["raw_url"])
                match = re.search(pattern, file_response.content)
                if match:
                    result_url = html_url.replace(gist["id"], username + "/" + gist["id"])
                    result['matches'].append(result_url)

    # REQUIRED: Fetch each gist and check for the pattern
    # REQUIRED DONE
    # TODO: BONUS: What about huge gists?
    # TODO: BONUS: Can we cache results in a datastore/db?

    result['username'] = username
    result['pattern'] = pattern

    return jsonify(result)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8000)

