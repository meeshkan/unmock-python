from typing import List, Dict, Any, Union
from collections.abc import Iterable
import json
from unittest import mock

__all__ = ["Patchers"]

class Patchers:
    """Represents a collection of mock.patcher objects to be started/stopped simulatenously."""
    def __init__(self):
        self.patchers = list()

    def patch(self, target, new_destination):
        """Patches `target` with new_destination, and returns the original target for later use"""
        patcher = mock.patch(target, new_destination)
        self.register(patcher)
        return patcher.get_original()[0]

    def register(self, *patchers):
        """Adds a list of patcher objects to this instance"""
        self.patchers += patchers

    def clear(self):
        """Stop any ongoing patches and clears the list of patchers in this instance"""
        if self.patchers:
            self.stop()
        self.patchers = list()

    def start(self):
        """Starts all registered patchers"""
        for patcher in self.patchers:
            patcher.start()

    def stop(self):
        """Stops all registered patchers"""
        for patcher in self.patchers:
            patcher.stop()
