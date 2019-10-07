import fnmatch
from .utils import parse_url

__all__ = ["UnmockOptions"]


class UnmockOptions:
  def __init__(self, replyFn=None, whitelist=None):
    """
    Creates a new UnmockOptions object, customizing the use of Unmock
    :param replyFn: A function that gets called with a Request object, and replies with a dictionary with the following keys:
        content: string/json - the body of the response (default empty string)
        status: int - the status code for the response (default 200)
        headers: dictionary - the headers for the response (default empty dictionary)
    :type replyFn Callable

    :param whitelist: An optional list (or string) of URLs to whitelist, so that you may access them without unmock
        intercepting the calls. Defaults to ["127.0.0.1", "127.0.0.0", "localhost"]
    :type string, list of strings

    """
    self.replyTo = replyFn if replyFn is not None else (lambda _: dict())
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
