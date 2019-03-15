import os
import pytest
import unmock
from .utils import get_logger

@pytest.fixture
def unmock_and_reset():
    def init(**kwargs):
        opts = unmock.UnmockOptions(token=os.environ.get("UNMOCK_TOKEN"), logger=get_logger(), **kwargs)
        unmock.init(opts)
        return opts
    yield init
    unmock.reset()
    return
