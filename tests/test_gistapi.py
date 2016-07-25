import os
import json
import tempfile

import pytest

import gistapi
import requests


@pytest.fixture
def client(request):
    # db_fd, gistapi.app.config['DATABASE'] = tempfile.mkstemp()
    gistapi.app.config['TESTING'] = True
    client = gistapi.app.test_client()

    # with gistapi.app.app_context():
    #    gistapi.init_db()

    # def teardown():
    #    os.close(db_fd)
    #    os.unlink(flaskr.app.config['DATABASE'])
    # request.addfinalizer(teardown)

    return client


######################################################
# IMPORTANT: "For unauthenticated requests, the rate limit allows you to make up to 60 requests per hour."
# check limit: curl -i https://api.github.com/users/whatever
# more details: https://developer.github.com/v3/#rate-limiting
######################################################

# Skip tests if status=403 Forbidden. It may caused by rate limit exceeded.
forbidden = pytest.mark.skipif(
    requests.get("https://api.github.com/users/whatever").status_code == 403,
    reason="403 Forbidden")


def test_ping(client):
    """Start with a sanity check."""
    rv = client.get('/ping')
    assert b'pong' in rv.data


@forbidden
def test_search(client):
    """Start with a passing test."""
    post_data = {'username': 'justdionysus', 'pattern': 'TerbiumLabsChallenge_[0-9]+'}
    rv = client.post('/api/v1/search',
                     data=json.dumps(post_data),
                     headers={'content-type': 'application/json'})
    result_dict = json.loads(rv.data.decode('utf-8'))
    expected_dict = {'status': 'success',
                     'username': 'justdionysus',
                     'pattern': 'TerbiumLabsChallenge_[0-9]+',
                     'matches': ['https://gist.github.com/justdionysus/6b2972aa971dd605f524']}

    assert result_dict == expected_dict


@forbidden
def test_invalid_arguments_keys(client):
    """Start with a passing test."""
    post_data = {'username2': 'justdionysus', 'pattern2': 'TerbiumLabsChallenge_[0-9]+'}
    with pytest.raises(TypeError):
        rv = client.post('/api/v1/search',
                         data=json.dumps(post_data),
                         headers={'content-type': 'application/json'})
        json.loads(rv.data.decode('utf-8'))


@forbidden
def test_invalid_arguments_username_value(client):
    """Start with a passing test."""
    post_data = {'username': 2, 'pattern': 'TerbiumLabsChallenge_[0-9]+'}
    with pytest.raises(TypeError):
        rv = client.post('/api/v1/search',
                         data=json.dumps(post_data),
                         headers={'content-type': 'application/json'})
        json.loads(rv.data.decode('utf-8'))


@forbidden
def test_invalid_arguments_pattern_value(client):
    """Start with a passing test."""
    post_data = {'username': "justdionysus", 'pattern': 2}
    with pytest.raises(TypeError):
        rv = client.post('/api/v1/search',
                         data=json.dumps(post_data),
                         headers={'content-type': 'application/json'})
        json.loads(rv.data.decode('utf-8'))


@forbidden
def test_search_nonexistent_username(client):
    """Start with a passing test."""
    post_data = {'username': '++--', 'pattern': 'TerbiumLabsChallenge_[0-9]+'}
    with pytest.raises(ValueError) as errorinfo:
        rv = client.post('/api/v1/search',
                         data=json.dumps(post_data),
                         headers={'content-type': 'application/json'})
        json.loads(rv.data.decode('utf-8'))

    assert errorinfo.value.message == "username ++--: Not Found"

####################################
# These two tests are for truncation case1 and case2.
####################################
# def test_truncation_case1_exceeds_300_files(client):
#     """There are 310 files in one gist. Each file has one integer between 1-310.
#     By checking the list from requests.get(), number 90-99 are truncated."""
#     post_data = {'username': 'mybluedog24', 'pattern': '\\b(9\\d)\\b'}
#     rv = client.post('/api/v1/search',
#                      data=json.dumps(post_data),
#                      headers={'content-type': 'application/json'})
#     result_dict = json.loads(rv.data.decode('utf-8'))
#     expected_dict = {'status': 'success',
#                      'username': 'mybluedog24',
#                      'pattern': '\\b(9\\d)\\b',
#                      'matches': ['https://gist.github.com/mybluedog24/9b79db5c345556bf8e9cb6359ec8a0ba']}
#
#     assert result_dict == expected_dict
#
#
# def test_truncation_case2_file_content_exceeds_limit(client):
#     """There are 310 files in one gist. Each file has one integer between 1-310.
#     By checking the list from requests.get(), number 90-99 are truncated."""
#     post_data = {'username': 'mybluedog24', 'pattern': 'LASTLINE'}
#     rv = client.post('/api/v1/search',
#                      data=json.dumps(post_data),
#                      headers={'content-type': 'application/json'})
#     result_dict = json.loads(rv.data.decode('utf-8'))
#     expected_dict = {'status': 'success',
#                      'username': 'mybluedog24',
#                      'pattern': 'LASTLINE',
#                      'matches': ['https://gist.github.com/mybluedog24/d3e49c8e4a8081a2e40125f48de70317']}
#
#     assert result_dict == expected_dict


