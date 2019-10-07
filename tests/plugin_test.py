"""Named without test_ in the beginning so we can test manually"""
import pytest
import requests
import os

TIMEOUT = 10


def test_pytest_flag():
  response = requests.get("http://www.example.com/",
                          timeout=TIMEOUT)  # Nothing here anyway
  if os.environ.get("USE_UNMOCK"):
    assert response.text == ""  # No service is defined so we get an empty response by default
  else:
    assert response.text != ""


def test_pytest_flag(unmock):
  def replyFn(req):
    return {"status": 303}
  unmock(replyFn=replyFn)

  response = requests.get("http://www.example.com/",
                          timeout=TIMEOUT)  # Nothing here anyway
  if os.environ.get("USE_UNMOCK"):
    assert response.status_code == 303
  else:
    assert response.status_code != 303
