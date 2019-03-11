from typing import Optional, List
import http.client
from urllib.parse import urlsplit, SplitResult
import socket
from unittest import mock

from .options import UnmockOptions
from .utils import end_reporter

# Backup:
UNMOCK_AUTH = "___u__n_m_o_c_k_a_u_t__h_"

def parse_url(url) -> SplitResult:
    parsed_url = urlsplit(url)
    if parsed_url.scheme == "" or parsed_url.netloc == "":
        return urlsplit("http://{url}".format(url=url))
    return parsed_url

def initialize(unmock_options: UnmockOptions, story: Optional[List[str]] = None, token: Optional[str] = None):
    story = story or list()

    def unmock_putrequest(self: http.client.HTTPConnection, method, url, skip_host=False, skip_accept_encoding=False):
        if unmock_options.is_host_whitelisted(self.host):
            original_putrequest(self, method, url, skip_host, skip_accept_encoding)

        elif not hasattr(self, "unmock"):  # Store unmock related stuff here
            uri = parse_url(url)
            req = http.client.HTTPSConnection(unmock_options.unmock_host, unmock_options.unmock_port)
            req.__setattr__("unmock_headers", { "headers": dict(),
                                                "path": "{path}?{query}".format(path=uri.path, query=uri.query),
                                                "story": story,
                                                "method": method })
            self.__setattr__("unmock", req)


    def unmock_putheader(self: http.client.HTTPConnection, header, *values):
        print(self.host, hasattr(self, "unmock"), header, values)
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
            self.unmock.unmock_headers["headers"][header] = decoded_values

        elif header == UNMOCK_AUTH:
            self.unmock.unmock_headers["Authorization"] = "".join(decoded_values)
            original_putheader(self.unmock, "Authorization", *decoded_values)

        else:
            self.unmock.unmock_headers["headers"][header] = decoded_values
            # TODO? original_putheader(self.unmock, header, *decoded_values)

    def unmock_end_headers(self: http.client.HTTPConnection, message_body=None, *, encode_chunked=False):
        print("End Headers:", message_body, encode_chunked, self.unmock.unmock_headers)

        if unmock_options.is_host_whitelisted(self.host):
            print(self.host, "in whitelisted mocked endheaders")
            original_endheaders(self, message_body, encode_chunked=encode_chunked)
        else:
            print(self.host, "in mocked endheaders")
            # TODO: build body (query parameters)?
            # if message_body is not None:
            #     original_putheader(self.unmock, "body", message_body)
            query = unmock_options.build_path(story=story, host=self.host, method=self.unmock.unmock_headers["method"],
                                              headers=self.unmock.unmock_headers["headers"],
                                              path="{path}".format(path=self.unmock.unmock_headers["path"]))
            original_putrequest(self.unmock, method="GET",
                                url="{fake_path}?{query}".format(fake_path=unmock_options.xy(token), query=query))
            # TODO: call to end_reporter for a nice printout
            original_endheaders(self.unmock, message_body, encode_chunked=encode_chunked)

    def unmock_get_response(self: http.client.HTTPConnection):
        if unmock_options.is_host_whitelisted(self.host):
            return original_getresponse(self)
        elif hasattr(self, "unmock"):
            return original_getresponse(self.unmock)

    putrequest_patcher = mock.patch("http.client.HTTPConnection.putrequest", unmock_putrequest)
    putheader_patcher = mock.patch("http.client.HTTPConnection.putheader", unmock_putheader)
    endheaders_patcher = mock.patch("http.client.HTTPConnection.endheaders", unmock_end_headers)
    getrespnse_patcher = mock.patch("http.client.HTTPConnection.getresponse", unmock_get_response)

    original_putrequest = putrequest_patcher.get_original()[0]
    original_putheader = putheader_patcher.get_original()[0]
    original_endheaders = endheaders_patcher.get_original()[0]
    original_getresponse = getrespnse_patcher.get_original()[0]

    putheader_patcher.start()
    endheaders_patcher.start()
    putrequest_patcher.start()
    getrespnse_patcher.start()

def reset():
    pass