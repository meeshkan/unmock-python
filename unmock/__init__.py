from .__version__ import __version__  # Conform to PEP-0396

from . import pytest
from .core import UnmockOptions, Request


def on(**kwargs):
  """Shorthand for initialize"""
  initialize(**kwargs)


def init(**kwargs):
  """Shorthand for initialize"""
  initialize(**kwargs)


def initialize(**kwargs):
  """
  Initialize the unmock library for capturing API calls.
  Pass keyword arguments to be used for internal options:

  :param whitelist: An optional list (or string) of URLs to whitelist, so that you may access them without unmock
      intercepting the calls. Defaults to ["127.0.0.1", "127.0.0.0", "localhost"]
  :type string, list of strings
  """
  from . import core  # Imported internally to keep the namespace clear
  unmock_options = UnmockOptions(**kwargs)

  core.http.initialize(unmock_options)


def off():
  """
  Removes Unmock automatic API call capturing, restoring normal behaviour.
  """
  from . import core
  core.http.reset()


def is_mocking():
  """
  Returns whether or not unmock is currently capturing calls
  """
  from . import core
  return len(core.PATCHERS.targets) > 0


class patch:
  """
  Allows the usage of unmock with scope-specific context managers.
  """

  def __init__(self, **kwargs):
    self.kwargs = kwargs

  def __enter__(self):
    return initialize(**self.kwargs)

  def __exit__(self, exc_type, exc_val, exc_tb):
    reset()
