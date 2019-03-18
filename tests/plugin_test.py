"""Named without test_ in the beginning so we can test manually"""

import requests
import os

TIMEOUT = 10

def test_pytest_flag():
    response = requests.get("http://www.example.com/", timeout=TIMEOUT)  # Nothing here anyway
    if os.environ.get("USE_UNMOCK"):
        assert response.json()  # Will throw as response is not json
    else:
        import pytest
        with pytest.raises(Exception):
            assert response.json()