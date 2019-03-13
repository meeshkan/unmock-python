import pytest
import tempfile
from pathlib import Path
import shutil
from typing import Dict, Any
from unmock.core.persistence import FSPersistence

@pytest.fixture
def redirect_home_path():
    FSPersistence.HOMEPATH = Path(tempfile.mkdtemp())
    yield None
    shutil.rmtree(FSPersistence.HOMEPATH)


def test_correct_body_no_headers(redirect_home_path):
    prs = FSPersistence("fake_token")
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
