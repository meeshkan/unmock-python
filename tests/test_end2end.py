import os
import requests
import pytest
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

def test_hubspot(unmock_and_reset):
    url = "https://www.behance.net/v2/projects"
    api = "?api_key=u_n_m_o_c_k_200"
    response = requests.get("{url}{api}".format(url=url, api=api))
    projects = response.json().get("projects")
    assert projects, "Expecting a non-empty list of 'projects' in response"

    response = requests.get("{url}/{id}{api}".format(url=url, id=projects[0]["id"], api=api))
    proj = response.json()
    assert proj.get("id") == projects[0]["id"], "Returned project ID should matc the requested one"

    response = requests.get("{url}/{id}/comments{api}".format(url=url, id=projects[0]["id"], api=api))
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