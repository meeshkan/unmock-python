import sys
import os
import json
from six.moves.urllib.parse import urlsplit, SplitResult
try:
    from unittest import mock
except ImportError:
    import mock

from ..__version__ import __version__

__all__ = ["Patchers", "parse_url", "is_python_version_at_least", "makedirs", "unmock_user_agent", "UnmockData"]

class UnmockData:
    STORIES = set()

    def __init__(self, method, path, query=None):
        self.headers_qp = dict()  # contains header information that is used in *q*uery *p*arameters
        self.path = path  # stores the endpoint for the request
        if query is not None:
            self.path = "{path}?{query}".format(path=self.path, query=query)
        self.headers = dict()  # actual headers to send to the unmock API
        self.method = method  # actual method to use with the unmock API (matches the method for the original request)
        self.body = None  # Content of data sent as body of request


    @staticmethod
    def stories(serializable=False):
        if serializable:
            return list(UnmockData.STORIES)  # Returned as list to be serializable
        return UnmockData.STORIES

    @staticmethod
    def add_story(unmock_hash):
        if unmock_hash is not None:
            UnmockData.STORIES.add(unmock_hash)

    @staticmethod
    def add_stories(stories):
        UnmockData.STORIES.update(set(stories))

    @staticmethod
    def clear_stories():
        UnmockData.STORIES.clear()

def unmock_user_agent(stringified=True):
    """Returns an unmock user agent header and value"""
    svi = sys.version_info
    ua_obj = {
        "lang": "python",
        "lang_version": "{major}.{minor}.{patch}".format(major=svi.major, minor=svi.minor, patch=svi.micro),
        "unmock_version": __version__
    }
    return "X-Unmock-Client-User-Agent", json.dumps(ua_obj) if stringified else ua_obj

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
            patcher.start()

    def stop(self):
        """Stops all registered patchers"""
        for patcher in self.patchers:
            patcher.stop()

def parse_url(url):
    """Parses a url using urlsplit, returning a SplitResult. Adds https:// scheme if netloc is empty."""
    parsed_url = urlsplit(url)
    if parsed_url.scheme == "" or parsed_url.netloc == "":
        # To make `urlsplit` work we need to provide the protocol; this is arbitrary (and can even be "//")
        return urlsplit("https://{url}".format(url=url))
    return parsed_url

def makedirs(path):
    """Quiet makedirs (similar to Python3 ok_exists=True flag)"""
    try:
        os.makedirs(path)
    except OSError:
        pass
