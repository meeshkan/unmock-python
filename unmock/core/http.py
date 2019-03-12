from typing import Optional, List
import http.client
from urllib.parse import urlsplit, SplitResult

from .options import UnmockOptions
from .utils import Patchers

__all__ = ["initialize", "reset"]

# Backup:
UNMOCK_AUTH = "___u__n_m_o_c_k_a_u_t__h_"
PATCHERS = Patchers()
STORIES = list()

def parse_url(url) -> SplitResult:
    parsed_url = urlsplit(url)
    if parsed_url.scheme == "" or parsed_url.netloc == "":
        return urlsplit("http://{url}".format(url=url))
    return parsed_url

def initialize(unmock_options: UnmockOptions, story: Optional[List[str]] = None, token: Optional[str] = None):
    global PATCHERS, STORIES
    if story is not None:
        STORIES += story

    def unmock_putrequest(self: http.client.HTTPConnection, method, url, skip_host=False, skip_accept_encoding=False):
        global STORIES
        if unmock_options._is_host_whitelisted(self.host):
            original_putrequest(self, method, url, skip_host, skip_accept_encoding)

        elif not hasattr(self, "unmock"):  # Store unmock related stuff here
            uri = parse_url(url)
            req = http.client.HTTPSConnection(unmock_options.unmock_host, unmock_options.unmock_port)
            req.__setattr__("unmock_data", { "headers_qp": dict(),
                                             "path": "{path}?{query}".format(path=uri.path, query=uri.query),
                                             "story": STORIES,
                                             "headers": dict(),
                                             "method": method,
                                             "body": None })
            self.__setattr__("unmock", req)


    def unmock_putheader(self: http.client.HTTPConnection, header, *values):
        decoded_values = list()
        for v in values:
            try:
                v = v.decode()
                decoded_values.append(v)
            except AttributeError:
                decoded_values.append(v)

        if unmock_options._is_host_whitelisted(self.host):
            original_putheader(self, header, *decoded_values)

        elif header == "Authorization":
            self.unmock.unmock_data["headers_qp"][header] = decoded_values

        elif header == UNMOCK_AUTH:
            self.unmock.unmock_data["headers"]["Authorization"] = decoded_values

        else:
            self.unmock.unmock_data["headers_qp"][header] = decoded_values
            self.unmock.unmock_data["headers"][header] = decoded_values

    def unmock_end_headers(self: http.client.HTTPConnection, message_body=None, *, encode_chunked=False):
        if unmock_options._is_host_whitelisted(self.host):
            original_endheaders(self, message_body, encode_chunked=encode_chunked)
        else:
            unmock_data = self.unmock.unmock_data
            method = unmock_data["method"]
            query = unmock_options._build_path(story=unmock_data["story"], host=self.host, method=method,
                                               headers=unmock_data["headers_qp"],
                                               path="{path}".format(path=unmock_data["path"]))
            original_putrequest(self.unmock, method=method,
                                url="{fake_path}?{query}".format(fake_path=unmock_options._xy(token), query=query))
            for header, value in unmock_data["headers"].items():
                original_putheader(self.unmock, header, *value)
            self.unmock.unmock_data["body"] = message_body
            original_endheaders(self.unmock, message_body, encode_chunked=encode_chunked)

    def unmock_get_response(self: http.client.HTTPConnection):
        global STORIES
        if unmock_options._is_host_whitelisted(self.host):
            return original_getresponse(self)
        elif hasattr(self, "unmock"):
            unmock_data = self.unmock.unmock_data
            res: http.client.HTTPResponse = original_getresponse(self.unmock)
            new_story = unmock_options._end_reporter(res=res, data=unmock_data["body"], host=self.host,
                                                     method=unmock_data["method"], path=unmock_data["path"],
                                                     story=STORIES, xy=unmock_options._xy(token))
            if new_story is not None:
                STORIES.append(new_story)
            return res

    original_putrequest = PATCHERS.patch("http.client.HTTPConnection.putrequest", unmock_putrequest)
    original_putheader = PATCHERS.patch("http.client.HTTPConnection.putheader", unmock_putheader)
    original_endheaders = PATCHERS.patch("http.client.HTTPConnection.endheaders", unmock_end_headers)
    original_getresponse = PATCHERS.patch("http.client.HTTPConnection.getresponse", unmock_get_response)
    PATCHERS.start()

def reset():
    global PATCHERS
    PATCHERS.stop()
