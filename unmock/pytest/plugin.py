"""A pytest plugin for Unmock"""
import pytest
from .. import init, reset, UnmockOptions

@pytest.fixture
def unmock():
    def _init(**kwargs):
        opts = UnmockOptions(**kwargs)
        reset()
        init(opts)
        return opts
    init()
    yield _init
    reset()
