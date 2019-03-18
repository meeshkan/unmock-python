"""A pytest plugin for Unmock"""
import pytest
from .. import init, reset, UnmockOptions

@pytest.fixture(scope="module")
def unmock():
    """Initialized ONCE per module, saving time on pinging host etc"""
    def _init(**kwargs):
        reset()
        return init(**kwargs)
    init()
    yield _init
    reset()

@pytest.fixture(scope="function")
def unmock_local():
    """Initializes the unmock service whenever used in any function"""
    def _init(**kwargs):
        reset()
        return init(**kwargs)
    init()
    yield _init
    reset()

