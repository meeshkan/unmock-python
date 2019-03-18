import requests

try:
    from unittest import mock
except ImportError:
    import mock

from .utils import get_logger, is_text

# Tests that actually send through to the unmock service and make sure it's all formed correctly
TIMEOUT = 10
URL = "https://www.behance.net/v2/projects"
API = "?api_key=u_n_m_o_c_k_200"

def test_no_credentials_no_signature(unmock_and_reset):
    unmock_and_reset(refresh_token=None)
    response = requests.get("http://www.example.com/", timeout=TIMEOUT)  # Nothing here anyway
    assert response.json()


def test_no_credentials_with_signature(unmock_and_reset):
    opts = unmock_and_reset(signature="boom", refresh_token=None)
    assert opts.persistence.token is None
    response = requests.get("{url}{api}".format(url=URL, api=API), timeout=TIMEOUT)
    projects = response.json().get("projects")
    assert projects
    assert isinstance(projects[0]["id"], int)


def test_behance(unmock_and_reset):
    unmock_and_reset()
    response = requests.get("{url}{api}".format(url=URL, api=API), timeout=TIMEOUT)
    projects = response.json().get("projects")
    assert projects, "Expecting a non-empty list of 'projects' in response"

    response = requests.get("{url}/{id}{api}".format(url=URL, id=projects[0]["id"], api=API), timeout=TIMEOUT)
    proj = response.json()
    assert proj.get("id") == projects[0]["id"], "Returned project ID should matc the requested one"

    response = requests.get("{url}/{id}/comments{api}".format(url=URL, id=projects[0]["id"], api=API), timeout=TIMEOUT)
    comments = response.json().get("comments")
    assert comments, "Expecting a non-empty list of 'comments' in response"
    assert is_text(comments[0]["comment"]), "Comments should be text"


def test_hubapi(unmock_and_reset):
    unmock_and_reset()
    json_data = {
        "properties": [
            {
                "property": "firstname",
                "value": "HubSpot"
            },
            {
                "property": "lastname",
                "value": "Test"
            }
        ]
    }
    res = requests.post("https://api.hubapi.com/contacts/v1/contact/createOrUpdate/email/"
                        "testingapis@hubspot.com/?hapikey=demo", json=json_data, timeout=TIMEOUT)
    res_json = res.json()
    assert isinstance(res_json.get("vid"), int)


def test_no_story(unmock_and_reset):
    # Adds story to ignore list
    opts = unmock_and_reset(ignore="story", save=True)
    mocked_save_headers = mock.MagicMock()
    mocked_save_body = mock.MagicMock()
    opts.persistence.save_headers = mocked_save_headers
    opts.persistence.save_body = mocked_save_body
    for _ in range(3):
        response = requests.get("{url}{api}".format(url=URL, api=API), timeout=TIMEOUT)
        projects = response.json().get("projects")
        assert projects
        assert isinstance(projects[0]["id"], int)
    # Expected to be called once for the first header, then hash is identical
    assert mocked_save_headers.call_count == 1
    assert mocked_save_body.call_count == 1


