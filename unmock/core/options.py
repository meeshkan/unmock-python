from typing import Union, List, Optional, Dict, Any
from urllib.parse import urlencode
from http.client import HTTPResponse
import logging
import json

UNMOCK_HOST = "api.unmock.io"
UNMOCK_PORT = 443

class UnmockOptions:
    def __init__(self, save: Union[bool, List[str]] = False, unmock_host: str = UNMOCK_HOST, unmock_port = UNMOCK_PORT,
                 use_in_production: bool = False,
                 logger=None, persistence=None,
                 ignore=None, signature: Optional[str] = None, token: Optional[str] = None,
                 whitelist: Optional[List[str]] = None):
        if logger is None:
            # TODO - move the logging definition elsewhere? Console output by default?
            logger = logging.getLogger("reporter")
            frmtr = logging.Formatter("[%(asctime)s] %(levelname)s\\%(name)s - %(message)s")
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(frmtr)
            logger.setLevel(logging.INFO)
            logger.addHandler(console_handler)
        self.logger = logger
        self.persistence = persistence  # TODO
        self.save = save
        self.unmock_host = unmock_host
        self.unmock_port = unmock_port
        self.use_in_production = use_in_production
        self.ignore = ignore if ignore is not None else { "headers": r"\w*User-Agent\w*" }
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
            "story": json.dumps(story),
            "path": path or "",
            "hostname": host or "",
            "method": method or "",
            "headers": json.dumps(headers)
        }
        if self.ignore is not None:
            qs["ignore"] = json.dumps(self.ignore)
        if self.signature is not None:
            qs["signature"] = self.signature
        return urlencode(qs)

    def end_reporter(self, res: HTTPResponse, data: Any, host: str, method: str, path: str, story: List[str], xy: str):
        headers = res.headers
        unmock_hash = headers["unmock-hash"]
        if unmock_hash not in story:
            body = res.msg
            self.logger.info("*****url-called*****")
            data_string = " with data {data}".format(data=data) if data is not None else "."
            self.logger.info("Hi! We see you've called %s %s%s%s", method, host, path, data_string)
            self.logger.info("We've sent you mock data back. You can edit your mock at https://unmock.io%s%s.", xy,
                             unmock_hash)
            if (self.save == True) or (isinstance(self.save, list) and unmock_hash in self.save):
                # self.persistence.save_headers(hash, headers)  # TODO
                if body is not None:
                    # self.persistence.save_body(hash, body)  # TODO
                    pass
            return unmock_hash
