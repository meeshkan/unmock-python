from typing import List, Dict, Any, Union
from collections.abc import Iterable
import json
from unittest import mock

__all__ = ["Patchers"]

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
        print("Mocking", target)
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
