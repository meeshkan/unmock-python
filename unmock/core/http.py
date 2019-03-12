from typing import Optional, List
import http.client
from urllib.parse import urlsplit, SplitResult

from .options import UnmockOptions
from .utils import end_reporter, Patchers

# Backup:
UNMOCK_AUTH = "___u__n_m_o_c_k_a_u_t__h_"
PATCHERS = Patchers()

def parse_url(url) -> SplitResult:
    parsed_url = urlsplit(url)
    if parsed_url.scheme == "" or parsed_url.netloc == "":
        return urlsplit("http://{url}".format(url=url))
    return parsed_url

def initialize(unmock_options: UnmockOptions, story: Optional[List[str]] = None, token: Optional[str] = None):
    global PATCHERS
    story = story or list()

    def unmock_putrequest(self: http.client.HTTPConnection, method, url, skip_host=False, skip_accept_encoding=False):
        if unmock_options.is_host_whitelisted(self.host):
            original_putrequest(self, method, url, skip_host, skip_accept_encoding)

        elif not hasattr(self, "unmock"):  # Store unmock related stuff here
            uri = parse_url(url)
            req = http.client.HTTPSConnection(unmock_options.unmock_host, unmock_options.unmock_port)
            req.__setattr__("unmock_data", { "headers_qp": dict(),
                                             "path": "{path}?{query}".format(path=uri.path, query=uri.query),
                                             "story": story,
                                             "headers": dict(),
                                             "method": method })
            self.__setattr__("unmock", req)


    def unmock_putheader(self: http.client.HTTPConnection, header, *values):
        decoded_values = list()
        for v in values:
            try:
                v = v.decode()
                decoded_values.append(v)
            except AttributeError:
                decoded_values.append(v)

        if unmock_options.is_host_whitelisted(self.host):
            original_putheader(self, header, *decoded_values)

        elif header == "Authorization":
            self.unmock.unmock_data["headers_qp"][header] = decoded_values

        elif header == UNMOCK_AUTH:
            self.unmock.unmock_data["headers"]["Authorization"] = decoded_values

        else:
            self.unmock.unmock_data["headers_qp"][header] = decoded_values
            self.unmock.unmock_data["headers"][header] = decoded_values

    def unmock_end_headers(self: http.client.HTTPConnection, message_body=None, *, encode_chunked=False):
        if unmock_options.is_host_whitelisted(self.host):
            original_endheaders(self, message_body, encode_chunked=encode_chunked)
        else:
            method = self.unmock.unmock_data["method"]
            query = unmock_options.build_path(story=story, host=self.host, method=method,
                                              headers=self.unmock.unmock_data["headers_qp"],
                                              path="{path}".format(path=self.unmock.unmock_data["path"]))
            original_putrequest(self.unmock, method=method,
                                url="{fake_path}?{query}".format(fake_path=unmock_options.xy(token), query=query))
            for header, value in self.unmock.unmock_data["headers"].items():
                original_putheader(self.unmock, header, *value)
            original_endheaders(self.unmock, message_body, encode_chunked=encode_chunked)

    def unmock_get_response(self: http.client.HTTPConnection):
        if unmock_options.is_host_whitelisted(self.host):
            return original_getresponse(self)
        elif hasattr(self, "unmock"):
            # TODO: call to end_reporter for a nice printout
            return original_getresponse(self.unmock)

    original_putrequest = PATCHERS.patch("http.client.HTTPConnection.putrequest", unmock_putrequest)
    original_putheader = PATCHERS.patch("http.client.HTTPConnection.putheader", unmock_putheader)
    original_endheaders = PATCHERS.patch("http.client.HTTPConnection.endheaders", unmock_end_headers)
    original_getresponse = PATCHERS.patch("http.client.HTTPConnection.getresponse", unmock_get_response)
    PATCHERS.start()

def reset():
    global PATCHERS
    PATCHERS.stop()
