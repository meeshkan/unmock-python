import logging
import logging.handlers
import os
import requests
try:
    from unittest import mock
except ImportError:
    import mock
import pytest
from unmock import UnmockOptions, exceptions as unmock_exceptions
from .utils import one_hit_server, get_token, MockResponse

def test_default_logger(tmpdir):
    opts = UnmockOptions()
    logger = opts._logger
    assert logger.getEffectiveLevel() == logging.DEBUG
    assert logger.name == "unmock.reporter"
    opts = UnmockOptions(storage_path=tmpdir)
    handlers = opts._logger.parent.handlers  # Handlers are set for unmock, not unmock.*
    assert handlers
    for handler in handlers:
        if isinstance(handler, logging.handlers.RotatingFileHandler):
            assert handler.baseFilename.startswith(tmpdir)


def test_wildcard_whitelist():
    opts = UnmockOptions(whitelist="*.amazon.com")
    assert isinstance(opts.whitelist, list)
    assert len(opts.whitelist) == 2  # Adds the unmock API as well by default
    assert opts._is_host_whitelisted("http://eu-west-1.console.aws.amazon.com")


def test_whitelist_local():
    event = one_hit_server()
    while not event.is_set():
        pass  # Wait for server to boot
    res = requests.get("http://127.0.0.1:7331")
    assert res.json().get("success") == True


def test_credentials_with_token(tmpdir):
    opts = UnmockOptions(storage_path=tmpdir)
    assert opts.persistence.token is None
    with open(opts.persistence.config_path, 'w') as cnfgfd:
        cnfgfd.writelines(["[unmock]\ntoken={tok}\n".format(tok=get_token())])
    assert opts.get_token() is not None


def test_get_token_errors(tmpdir):
    PSEUDO_TOKEN = "spam"
    def boom(*args, **kwargs):
        raise requests.ConnectionError

    def mocked_post(response):
        def post(*args, **kwargs):
            assert kwargs["json"]["refreshToken"] == PSEUDO_TOKEN
            return response
        return post

    with mock.patch("requests.get") as requests_get_patch:
        requests_get_patch.side_effect = boom
        opts = UnmockOptions(storage_path=tmpdir)  # Should go to the default /y/ case
        with pytest.raises(unmock_exceptions.UnmockServerUnavailableException):
            opts._validate_access_token("foo")

    with mock.patch("requests.post") as requests_post_patch, mock.patch("requests.get") as requests_get_patch:
        requests_post_patch.side_effect = mocked_post(MockResponse({"accessToken": "eggs"}))
        requests_get_patch.side_effect = lambda _, headers: MockResponse({}, status_code=0)
        with pytest.raises(unmock_exceptions.UnmockAuthorizationException,
                           match="Internal authorization error"):  # get_token called on init
            UnmockOptions(refresh_token=PSEUDO_TOKEN, storage_path=tmpdir)

        requests_post_patch.side_effect = mocked_post(MockResponse({}))
        with pytest.raises(unmock_exceptions.UnmockAuthorizationException,
                           match="Incorrect server response: did not get accessToken"):
            UnmockOptions(refresh_token=PSEUDO_TOKEN, storage_path=tmpdir)

        requests_post_patch.side_effect = mocked_post(MockResponse({}, status_code=0))
        with pytest.raises(unmock_exceptions.UnmockAuthorizationException,
                           match="Internal authorization error, receieved"):
            UnmockOptions(refresh_token=PSEUDO_TOKEN, storage_path=tmpdir)
