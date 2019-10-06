"""A pytest plugin for Unmock"""
import pytest
from .. import init, UnmockOptions


@pytest.fixture(scope="function")
def unmock_local():
    """Initializes the unmock service whenever used in any function"""
    def _init(**kwargs):
        reset()
        return init(**kwargs)
    init()
    yield _init
    reset()


def pytest_addoption(parser):
    parser.addoption("--unmock", dest="USE_UNMOCK", action="store_true",
                     help="Use Unmock (with default settings) to capture and mock 3rd party API calls")


def pytest_configure(config):
    if config.getoption("USE_UNMOCK"):
        init()


def pytest_unconfigure(config):  # Cleanup
    if config.getoption("USE_UNMOCK"):
        reset()
