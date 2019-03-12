from typing import List, Dict, Any, Union, Iterable
import logging
import json
from unittest import mock

def json_stringify(obj: Union[List, Dict[Any, Any], Any]):
    if isinstance(obj, Iterable):
        return ''.join(json.dumps(obj if obj is not None and len(obj) > 0 else ""))
    return json.dumps(obj)

def end_reporter(body: Any, data: str, headers: Dict[str, str], host: str, logger: logging.Logger, method: str,
                 path: str, persistence, save: Union[bool, List[str]], selfcall: bool, story: List[str], xy: str):
    if logger is None:  # Simple printouts by default?
        # TODO - move the logging definition elsewhere
        logger = logging.getLogger("reporter")
        frmtr = logging.Formatter("[%(asctime)s] %(levelname)s\\%(name)s - %(message)s")
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(frmtr)
        logger.setLevel(logging.INFO)
        logger.addHandler(console_handler)
    if not selfcall:
        unmock_hash = headers["unmock-hash"]
        if unmock_hash not in story:
            logger.info("*****url-called*****")
            data_string = " with data {data}".format(data=data) if data is not None else "."
            logger.info("Hi! We see you've called %s %s%s%s", method, host, path, data_string)
            logger.info("We've sent you mock data back. You can edit your mock at https://unmock.io/%s%s.", xy, unmock_hash)
            if (isinstance(save, bool) and save == True) or (isinstance(save, list) and unmock_hash in save):
                # persistence.save_headers(hash, headers)  # TODO
                if body is not None:
                    # persistence.save_body(hash, body)  # TODO
                    pass
            return unmock_hash

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
