from typing import List, Dict, Any, Union, Iterable
import json
from unittest import mock

def json_stringify(obj: Union[List, Dict[Any, Any], Any]):
    if isinstance(obj, Iterable):
        return ''.join(json.dumps(obj if obj is not None and len(obj) > 0 else ""))
    return json.dumps(obj)

def end_reporter(body, data, headers, host, hostname, logger, method, path, persistence, save, selfcall, story, xy):
    if not selfcall:
        hash = headers["unmock-hash"]
        if hash not in story:
            story.insert(0, hash)
            # logger.log("*****url-called*****")
            # logger.log("Hi! We see you've called ${method} ${hostname || host}${path}${data ? ` with data ${data}.` : `.`}")
            # logger.log("We've sent you mock data back. You can edit your mock at https://unmock.io/${xy ? "x" : "y"}/${hash}.")
            if (isinstance(save, bool) and save == True) or (isinstance(save, list) and hash in save):
                # TODO:
                # persistence.save_headers(hash, headers)
                if body is not None:
                    # TODO
                    # persistence.save_body(hash, body)
                    pass

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
