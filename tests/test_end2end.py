import os
import requests
import pytest

try:
    from unittest import mock
except ImportError:
    import mock

import unmock
from .utils import get_logger

# End-to-end testing

@pytest.fixture
def unmock_and_reset():
    opts = unmock.UnmockOptions(token=os.environ.get("UNMOCK_TOKEN"), logger=get_logger())
    unmock.init(opts)
    yield opts
    unmock.reset()
    return

URL = "https://www.behance.net/v2/projects"
API = "?api_key=u_n_m_o_c_k_200"

def test_hubspot(unmock_and_reset):
    response = requests.get("{url}{api}".format(url=URL, api=API))
    projects = response.json().get("projects")
    assert projects, "Expecting a non-empty list of 'projects' in response"

    response = requests.get("{url}/{id}{api}".format(url=URL, id=projects[0]["id"], api=API))
    proj = response.json()
    assert proj.get("id") == projects[0]["id"], "Returned project ID should matc the requested one"

    response = requests.get("{url}/{id}/comments{api}".format(url=URL, id=projects[0]["id"], api=API))
    comments = response.json().get("comments")
    assert comments, "Expecting a non-empty list of 'comments' in response"
    assert isinstance(comments[0]["comment"], str), "Comments should be strings"


def test_hubapi(unmock_and_reset):
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
                        "testingapis@hubspot.com/?hapikey=demo", json=json_data)
    res_json = res.json()
    assert isinstance(res_json.get("vid"), int)


def test_no_story(unmock_and_reset):
    unmock_and_reset.ignore("story")  # Adds story to ignore list
    unmock_and_reset.save = True
    mocked_save_content = mock.MagicMock()
    unmock_and_reset.persistence.save_headers = mocked_save_content
    unmock_and_reset.persistence.save_body = mocked_save_content
    for _ in range(3):
        response = requests.get("{url}{api}".format(url=URL, api=API))
        projects = response.json().get("projects")
        assert projects
        assert isinstance(projects[0]["id"], int)
    # Expected to be called once for the first header, then hash is identical
    assert mocked_save_content.call_count == 1


