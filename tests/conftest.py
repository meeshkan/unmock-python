import tempfile
import shutil
import pytest
import unmock
from .utils import get_logger, get_token

@pytest.fixture
def tmpdir():
    tmpd = tempfile.mkdtemp()
    yield tmpd
    shutil.rmtree(tmpd)
    return

@pytest.fixture
def unmock_and_reset():
    def init(**kwargs):
        default_kwargs = {"token": get_token(), "logger": get_logger()}
        default_kwargs.update(kwargs)
        opts = unmock.UnmockOptions(**default_kwargs)
        unmock.init(opts)
        return opts
    yield init
    unmock.reset()
