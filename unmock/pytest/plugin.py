"""A pytest plugin for Unmock"""
import pytest
import os
from .. import on, off

u_flag = "USE_UNMOCK"


@pytest.fixture(scope="function")
def unmock():
  """Initializes the unmock service whenever used in any function"""
  def _init(**kwargs):
    off()
    return on(**kwargs)

  def doNothing(**kwargs):
    pass

  if os.environ.get(u_flag):
    on()
    yield _init
    off()
  else:
    yield doNothing


def pytest_addoption(parser):
  parser.addoption(
      "--unmock", dest=u_flag, action="store_true",
      help="Use Unmock (with default settings) to capture and mock 3rd party API calls")


def pytest_configure(config):
  if config.getoption(u_flag):
    on()
    os.environ[u_flag] = "1"


def pytest_unconfigure(config):  # Cleanup
  if config.getoption(u_flag):
    off()
    os.environ.pop(u_flag, "")
