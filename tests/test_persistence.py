import pytest
import tempfile
import shutil
from unmock.core.persistence import FSPersistence

@pytest.fixture
def prs():
    tempdir = tempfile.mkdtemp()
    yield FSPersistence("fake_token", path=tempdir)
    shutil.rmtree(tempdir)
    return

def test_correct_body_no_headers(prs):

    prs.save_body(hash="abc", body='{'
                    '"data": ['
                        '{'
                            '"result": true,'
                            '"foo": "bar"'
                        '},'
                        '{'
                            '"spam": "eggs",'
                            '"zoit": null'
                        '} ]'
                  '}')
    body = prs.load_body("abc")
    assert len(body["data"]) == 2
    item1 = body["data"][0]  # type: Dict[str, Any]
    item2 = body["data"][1]  # type: Dict[str, Any]
    assert item1["result"] == True
    assert item2["spam"] == "eggs"
    assert item1["foo"] == "bar"
    assert item2["zoit"] is None


def test_chunked_body(prs):
    prs.save_body(hash="foo", body='{'
                    '"data": ['
                        '{'
                            '"result": true,'
                            '"foo": "')
    prs.save_body(hash="foo", body='bar"'
                        '},'
                        '{'
                            '"spam": "eggs",'
                            '"zoit": null'
                        '} ]'
                  '}')
    body = prs.load_body("foo")
    assert len(body["data"]) == 2
    item1 = body["data"][0]  # type: Dict[str, Any]
    item2 = body["data"][1]  # type: Dict[str, Any]
    assert item1["result"] == True
    assert item2["spam"] == "eggs"
    assert item1["foo"] == "bar"
    assert item2["zoit"] is None


def test_chunked_body_incomplete(prs):
    prs.save_body(hash="foo", body='{ "data": [')
    assert prs.load_body("foo") is None


def test_empty_body(prs):
    prs.save_body(hash="bar")
    assert prs.load_body("bar") is None


def test_headers(prs):
    prs.save_headers(hash="spam", headers="eggs")
    assert prs.load_headers(hash="spam") == "eggs"


def test_auth(prs):
    assert prs.load_auth() is None
    prs.save_auth("zoit")
    assert prs.load_auth() == "zoit"


def test_token(prs):
    assert prs.load_token() == "fake_token"
    prs.token = None
    assert prs.load_token() is None
    # Write to config path
    with open(prs.config_path, 'w') as cnfgfd:
        cnfgfd.writelines(["[unmock]\ntoken=nekot\n"])
    assert prs.load_token() == "nekot"
    