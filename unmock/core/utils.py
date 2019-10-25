import sys
from six.moves.urllib.parse import urlsplit, SplitResult
try:
  from unittest import mock
except ImportError:
  import mock

from ..__version__ import __version__

__all__ = ["PATCHERS", "parse_url",
           "is_python_version_at_least"]


def is_python_version_at_least(version):
  """
  Checks if the current python version is at least the version specified.
  Recommended way to import is with try-except; this shorthand is made for where we're not importing modules.
  :param version: A string representing desired python version (e.g. "3.6.8")
  :type version string
  :return: boolean value whether the current python version is at least the given version
  """
  return sys.version_info >= tuple(int(v) for v in version.split("."))


class Patchers:
  """Represents a collection of mock.patcher objects to be started/stopped simulatenously."""

  def __init__(self):
    self.patchers = list()
    self.targets = list()  # So we don't mock a mock mocking a mock.

  def patch(self, target, new_destination):
    """Patches `target` with new_destination, and returns the original target for later use.
    If `target` is already mocked, it is ignored."""
    if target in self.targets:
      return
    patcher = mock.patch(target, new_destination)
    self.targets.append(target)
    self.patchers.append(patcher)
    return patcher.get_original()[0]

  def __contains__(self, item):
    return item in self.targets

  def clear(self):
    """Stop any ongoing patches and clears the list of patchers in this instance"""
    if self.patchers:
      self.stop()
    del self.patchers[:]
    del self.targets[:]

  def start(self):
    """Starts all registered patchers"""
    for patcher in self.patchers:
      if getattr(patcher, 'target', None) is None:
        patcher.start()

  def stop(self):
    """Stops all registered patchers"""
    for patcher in self.patchers:
      if getattr(patcher, 'target', None) is not None:
        patcher.stop()


def parse_url(url):
  """
  Parses a url using urlsplit, returning a SplitResult. Adds https:// scheme if netloc is empty.
  Parse a URL into 5 components:
    <scheme>://<netloc>/<path>?<query>#<fragment>
    Return a 5-tuple: (scheme, netloc, path, query, fragment).
  """
  parsed_url = urlsplit(url)
  if parsed_url.scheme == "" or parsed_url.netloc == "":
    # To make `urlsplit` work we need to provide the protocol; this is arbitrary (and can even be "//")
    return urlsplit("https://{url}".format(url=url))
  return parsed_url


PATCHERS = Patchers()
