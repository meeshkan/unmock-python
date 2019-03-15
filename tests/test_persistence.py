import pytest
import tempfile
import shutil
from unmock.core.persistence import FSPersistence


def test_correct_body_no_headers():
    prs = FSPersistence("fake_token", path=tempfile.mkdtemp())
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
