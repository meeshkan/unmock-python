from urllib.parse import urlencode
from http.client import HTTPResponse
from http import HTTPStatus
from pathlib import Path
import logging
import json
import requests
import fnmatch

from .logger import setup_logging
from .persistence import FSPersistence, Persistence
from .utils import parse_url
from .exceptions import UnmockAuthorizationException

__all__ = ["UnmockOptions"]

UNMOCK_HOST = "api.unmock.io"
UNMOCK_PORT = 443

class UnmockOptions:
    def __init__(self, save=False, unmock_host=UNMOCK_HOST, unmock_port=UNMOCK_PORT, use_in_production=False,
                 storage_path=None, logger=None, persistence=None, ignore=None, signature=None, token=None,
                 whitelist=None):
        """
        Creates a new UnmockOptions object, customizing the use of Unmock service
        :param save: whether or not to save all mocks (when using boolean value), or a list of specific story IDs to
            save. Deafult to False.
        :type save boolean, list of strings

        :param unmock_host: The URL for unmock host, if it is on prem. Default to api.unmock.io
        :type unmock_host string

        :param unmock_port: The port for unmock host, if it s on prem. Default to 443.
        :type unmock_port int

        :param use_in_production: Whether or not to use unmock in production, based on `ENV` environment variable.
            Default to False.
        :type use_in_production boolean

        :param storage_path: Location where mocks (and credentials, etc) should be stored. Creates a hidden `.unmock`
            directory in that location to store relevant data. Only relevant when saving some of the data.
            Default to None (uses home directory).
        :type storage_path string

        :param logger: A logger file if a user wants to redirect/manage logs in that non-default way. Defaults to a
            console logger, with `info.log` and `debug.log` in a logs directory located in the storage_path.
        :type logger logging.Logger

        :param persistence: A type of persistence layer, can be used to e.g. save mocks automatically to S3 buckets or
            on local disk. Defaults to None and uses file system to store credentials, mocks (if save is defined), etc.
        :type persistence Persistence

        :param ignore: A string, list, dictionary or a combination of them, specifying different parameters to ignore
            when serving mocks. See the documentation for more details.
        :type string, list, dictionary, any

        :param signature: An optional signature allowing a user to have specific mocks for different purposes.
            The signature is used when computing the story hash; see the documentation for more details.
        :type string

        :param token: An optional refresh token, given when you sign up to the unmock service. With a valid token, you
            can have unlimited calls to the unmock service, an online dashboard, private mocks, etc.
        :type string

        :param whitelist: An optional list (or string) of URLs to whitelist, so that you may access them without unmock
            intercepting the calls. Defaults to ["127.0.0.1", "127.0.0.0", "localhost"]
        :type string, list of strings

        """
        if logger is None:
            if storage_path is not None:
                setup_logging(storage_path)
            logger = logging.getLogger("unmock.reporter")
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
            persistence = FSPersistence(self.token, path=storage_path)
        self.persistence = persistence

    def ignore(self, *args, **kwargs):
        for key in args:
            self.ignore.append(key)
        for key, value in kwargs:
            self.ignore.append({key: value})

    def get_token(self):
        """
        Fetches and returns a new access token from the unmock server or predisposed access token if it is still valid.
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

    def _validate_access_token(self):
        """
        Validates the access token by pinging the unmock_host with the Authorization header
        :param access_token:
        :type access_token string
        :return: True if token is valid, False otherwise
        """
        url = "{scheme}://{host}:{port}".format(scheme=self.scheme, host=self.unmock_host, port=self.unmock_port)
        response = requests.get("{url}/ping".format(url=url),
                                headers={"Authorization": "Bearer {token}".format(token=access_token)})
        return response.status_code == HTTPStatus.OK


    def _is_host_whitelisted(self, host):
        """
        Checks if given host is whitelisted
        :param host: String representing a host
        :type host string
        :return: True if host is whitelisted, False otherwise
        """
        for whitelisted in self.whitelist:
            if fnmatch.fnmatch(host, whitelisted):  # Whitelisted can be a wildcard string (e.g. "*.amazon.com/...")
                return True
        return False

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