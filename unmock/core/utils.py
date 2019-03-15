import sys
import json

def is_python2():
    return sys.version_info[0] < 3

if is_python2():
    from urlparse import urlsplit, SplitResult
    import mock
else:
    from urllib.parse import urlsplit, SplitResult
    from unittest import mock

__all__ = ["Patchers", "parse_url", "is_python2"]

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
        self.patchers.clear()
        self.targets.clear()

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
