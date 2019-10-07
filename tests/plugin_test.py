"""Named without test_ in the beginning so we can test manually"""
import pytest
import requests
import os

TIMEOUT = 10


def pytest_wo(cond):
  if os.environ.get("USE_UNMOCK"):  # unmock exists, condition should pass
    assert cond
  else:
    # unmock does not exist, condition should fail "silently"
    with pytest.raises(Exception):
      # this is done intentionally so catching build errors is easier
      assert cond


def test_pytest_flag():
  response = requests.get("http://www.example.com/",
                          timeout=TIMEOUT)  # Nothing here anyway
  pytest_wo(response.text == "")


def test_pytest_flag(unmock):
  def replyFn(req):
    return {"status": 303}
  unmock(replyFn=replyFn)

  response = requests.get("http://www.example.com/",
                          timeout=TIMEOUT)  # Nothing here anyway
  pytest_wo(response.status_code == 303)
