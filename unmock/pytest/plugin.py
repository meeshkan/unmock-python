"""A pytest plugin for Unmock"""
import pytest
from .. import init, reset, UnmockOptions

@pytest.fixture
def unmock():
    def _init(**kwargs):
        reset()
        return init(**kwargs)
    init()
    yield _init
    reset()
