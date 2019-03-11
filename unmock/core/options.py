from typing import Union, List, Optional, Dict, Any
from urllib.parse import urlencode

from .utils import json_stringify

UNMOCK_HOST = "api.unmock.io"
UNMOCK_PORT = 443

class UnmockOptions:
    def __init__(self, save: Union[bool, List[str]] = False, unmock_host: str = UNMOCK_HOST, unmock_port = UNMOCK_PORT,
                 use_in_production: bool = False,
                 logger=None, persistence=None,
                 ignore=None, signature: Optional[str] = None, token: Optional[str] = None,
                 whitelist: Optional[List[str]] = None):
        self.logger = logger  # TODO
        self.persistence = persistence  # TODO
        self.save = save
        self.unmock_host = unmock_host
        self.unmock_port = unmock_port
        self.use_in_production = use_in_production
        self.ignore = ignore if ignore is not None else { "headers": "\w*User-Agent\w*" }
        self.signature = signature
        self.token = token
        self.whitelist = whitelist if whitelist is not None else ["127.0.0.1", "127.0.0.0", "localhost"]
        # Add the unmock host to whitelist:
        self.whitelist.append(unmock_host)

    def is_host_whitelisted(self, host: str):
        return host in self.whitelist

    @staticmethod
    def xy(xy):
        return "/x/" if xy else "/y/"

    def build_path(self, story: Optional[List[str]],  headers: Dict[str, Any], host: Optional[str] = None,
                   method: Optional[str] = None, path: Optional[str] = None):
        qs = {
            "story": json_stringify(story),
            "path": path or "",
            "hostname": host or "",
            "method": method or "",
            "headers": json_stringify(headers)
        }
        if self.ignore is not None:
            qs["ignore"] = json_stringify(self.ignore)
        if self.signature is not None:
            qs["signature"] = self.signature
        return urlencode(qs)
