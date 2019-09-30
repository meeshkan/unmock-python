import fnmatch
from six.moves.urllib.parse import urlencode
from six.moves import http_client
try:
  from http import HTTPStatus
except ImportError:
  class HTTPStatus:
    OK = 200

from .utils import parse_url

__all__ = ["UnmockOptions"]


class UnmockOptions:
  def __init__(self, use_in_production=False, whitelist=None):
    """
    Creates a new UnmockOptions object, customizing the use of Unmock
    :param use_in_production: Whether or not to use unmock in production, based on `ENV` environment variable.
        Default to False.
    :type use_in_production boolean

    :param whitelist: An optional list (or string) of URLs to whitelist, so that you may access them without unmock
        intercepting the calls. Defaults to ["127.0.0.1", "127.0.0.0", "localhost"]
    :type string, list of strings

    """

    self.use_in_production = use_in_production
    self.whitelist = whitelist if whitelist is not None else [
        "127.0.0.1", "127.0.0.0", "localhost"]
    if not isinstance(self.whitelist, list):
      self.whitelist = [self.whitelist]

  def _is_host_whitelisted(self, host):
    """
    Checks if given host is whitelisted
    :param host: String representing a host
    :type host string
    :return: True if host is whitelisted, False otherwise
    """
    for whitelisted in self.whitelist:
      if fnmatch.fnmatch(
              host, whitelisted):  # Whitelisted can be a wildcard string (e.g. "*.amazon.com/...")
        return True
    return False
