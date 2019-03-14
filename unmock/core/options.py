from typing import Union, List, Optional, Dict, Any, cast
from urllib.parse import urlencode
from http.client import HTTPResponse
from http import HTTPStatus
from pathlib import Path
import logging
import json
import requests

from .persistence import FSPersistence, Persistence
from .utils import parse_url
from .exceptions import UnmockAuthorizationException

__all__ = ["UnmockOptions"]

UNMOCK_HOST = "api.unmock.io"
UNMOCK_PORT = 443

class UnmockOptions:
    def __init__(self, save: Union[bool, List[str]] = False, unmock_host: str = UNMOCK_HOST, unmock_port = UNMOCK_PORT,
                 use_in_production: bool = False, path: Optional[Union[str, Path]] = None,
                 logger: Optional[logging.Logger] = None, persistence: Optional[Persistence] = None,
                 ignore=None, signature: Optional[str] = None, token: Optional[str] = None,
                 whitelist: Optional[List[str]] = None):
        if logger is None:
            # TODO - move the logging definition elsewhere? Console output by default?
            logger = logging.getLogger("reporter")
            logger.setLevel(logging.INFO)
            # For now, make sure we only have one stream logger...
            has_stream_handler = False
            for handler in logger.handlers:
                if isinstance(handler, logging.StreamHandler):
                    has_stream_handler = True
                    break
            if not has_stream_handler:
                frmtr = logging.Formatter("[%(asctime)s] %(levelname)s\\%(name)s - %(message)s")
                console_handler = logging.StreamHandler()
                console_handler.setFormatter(frmtr)
                logger.addHandler(console_handler)
        self.logger = logger
        self.save = save

        uri = parse_url(unmock_host)
        self.scheme = uri.scheme
        self.unmock_host = "{url}{path}{query}".format(url=uri.netloc, path=uri.path, query=uri.query)
        self.unmock_port = unmock_port
        self.use_in_production = use_in_production
        self.ignore = ignore if ignore is not None else [{ "headers": r"\w*User-Agent\w*" }]
        if not isinstance(self.ignore, list):
            self.ignore = [self.ignore]
        self.signature = signature
        self.token = token
        self.whitelist = whitelist if whitelist is not None else ["127.0.0.1", "127.0.0.0", "localhost"]
        if not isinstance(self.whitelist, list):
            self.whitelist = list(self.whitelist)
        # Add the unmock host to whitelist:
        self.whitelist.append(unmock_host)
        if persistence is None:
            persistence = FSPersistence(self.token, path=path)
        self.persistence = persistence

    def ignore(self, *args, **kwargs):
        for key in args:
            self.ignore.append(key)
        for key, value in kwargs:
            self.ignore.append({key: value})

    def get_token(self) -> Optional[str]:
        """
        Fetches a new access token from the unmock server or predisposed access token if it is still valid.
        Throws RuntimeError on logical failures with unexpected responses from the Unmock host.
        """
        url = "{scheme}://{host}:{port}".format(scheme=self.scheme, host=self.unmock_host, port=self.unmock_port)
        access_token = self.persistence.load_auth()
        if access_token is not None:  # If we already have an access token, let's see we can still ping with it
            if self._validate_access_token(access_token):  # We can ping, all's good in the world!
                return access_token

        # Otherwise, we need to get a new token
        refresh_token = self.persistence.load_token()
        if refresh_token is None:
            return  # Continue with the public API ('/y/' version)
        response = requests.post("{url}/token/access".format(url=url), json={"refreshToken": refresh_token})
        if response.status_code == HTTPStatus.OK:
            new_access_token = response.json().get("accessToken")
            if new_access_token is None:  # Response was not present..?
                raise UnmockAuthorizationException("Incorrect server response: did not get accessToken")
            if not self._validate_access_token(new_access_token):  # Could still not ping with new access token?!
                raise UnmockAuthorizationException("Internal authorization error")
            self.persistence.save_auth(new_access_token)
            return new_access_token
        raise UnmockAuthorizationException("Internal authorization error, receieved {response} from"
                                           " {url}".format(response=response.status_code, url=self.unmock_host))

    def _validate_access_token(self, access_token: str) -> bool:
        """
        Validates the access token by pinging the unmock_host with the Authorization header
        :param access_token:
        :return: True if token is valid, False otherwise
        """
        url = "{scheme}://{host}:{port}".format(scheme=self.scheme, host=self.unmock_host, port=self.unmock_port)
        response = requests.get("{url}/ping".format(url=url),
                                headers={"Authorization": "Bearer {token}".format(token=access_token)})
        return response.status_code == HTTPStatus.OK


    def _is_host_whitelisted(self, host: str):
        return host in self.whitelist

    @staticmethod
    def _xy(xy):
        return "/x/" if xy else "/y/"

    def _build_query(self, story: Optional[List[str]],  headers: Dict[str, Any], host: Optional[str] = None,
                     method: Optional[str] = None, path: Optional[str] = None):
        """Builds the querypath for unmock requests"""
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

    def _end_reporter(self, res: HTTPResponse, data: Any, host: str, method: str, path: str, story: List[str], xy: str):
        """
        Reports the capture of an API call, possibly storing the headers in the relevant directory for unmock (if
        persistence layer is activated via `save` parameter).
        :param res: The actual response object from Unmock service
        :param data: The data sent to the unmock server (the body sent)
        :param host: The original host the request was directed to
        :param method: The original method for the request
        :param path: The original path requested from the original host (including query parameters)
        :param story: The list of current stories used and stored in Unmock
        :param xy: string representing whether or not this request is public ('/y/') or private ('/x/')
        :return: A new story if we have not encountered this story before.
        """
        unmock_hash = res.getheader("unmock-hash", default=None)
        if unmock_hash is not None and unmock_hash not in story:
            self.logger.info("*****url-called*****")
            data_string = " with data {data}".format(data=data) if data is not None else "."
            self.logger.info("Hi! We see you've called %s %s%s%s", method, host, path, data_string)
            self.logger.info("We've sent you mock data back. You can edit your mock at https://unmock.io%s%s.", xy,
                             unmock_hash)
            if (self.save == True) or (isinstance(self.save, list) and unmock_hash in self.save):
                self.persistence.save_headers(hash=unmock_hash, headers=dict(res.getheaders()))
            return unmock_hash

    def _save_body(self, unmock_hash, body: Optional[str] = None):
        if (self.save == True) or (isinstance(self.save, list) and unmock_hash in self.save):
            self.persistence.save_body(hash=unmock_hash, body=body)