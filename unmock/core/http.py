from .utils import Patchers, parse_url, is_python2
if is_python2():
    import httplib
else:
    import http.client
import os

from . import PATCHERS, STORIES
from .options import UnmockOptions

__all__ = ["initialize", "reset"]

# Backup:
UNMOCK_AUTH = "___u__n_m_o_c_k_a_u_t__h_"

def initialize(unmock_options):
    """
    Entry point to mock the standard http client. Both `urllib` and `requests` library use the
    `http.client.HTTPConnection`, so mocking it should support their use aswell.

    We mock the "low level" API (instead of the `request` method, we mock the `putrequest`, `putheader`, `endheaders`
    and `getresponse` methods; the `request` method calls these sequentially).
    To save the body of the response, we also mock the HTTPResponse's `read` method.

    HTTPSConnection also uses the regular HTTPConnection methods under the hood -> hurray!

    :param unmock_options: An UnmockOptions file with user-behaviour customizations
    :type unmock_options UnmockOptions
    """
    token = unmock_options.get_token()  # Get the *access_token*

    def unmock_putrequest(self, method, url, skip_host=False, skip_accept_encoding=False):
        """putrequest mock; called initially after the HTTPConnection object has been created. Contains information
        about the endpoint and method.

        :param self
        :type self HTTPConnection
        :param method
        :type method string
        :param url
        :type url string
        :param skip_host
        :type skip_host bool
        :param skip_accept_encoding
        :type skip_accept_encoding bool
        """
        if unmock_options._is_host_whitelisted(self.host):  # Host is whitelisted, redirect to original call.
            original_putrequest(self, method, url, skip_host, skip_accept_encoding)

        elif not hasattr(self, "unmock"):
            # Otherwise, we create our own HTTPSConnection to redirect the call to our service when needed.
            # We add the "unmock" attribute to this object and store information for later use.
            uri = parse_url(url)
            req = http.client.HTTPSConnection(unmock_options.unmock_host, unmock_options.unmock_port)
            """
            By order:
            - headers_qp -> contains header information that is used in *q*uery *p*arameters
            - path -> stores the endpoint for the request
            - story -> stores previous access to the unmock service
            - headers -> actual headers to send to the unmock API
            - method -> actual method to use with the unmock API (always matches the method for the original request)
            """
            req.__setattr__("unmock_data", { "headers_qp": dict(),
                                             "path": "{path}?{query}".format(path=uri.path, query=uri.query),
                                             "story": STORIES,
                                             "headers": dict(),
                                             "method": method })
            if token is not None:  # Add token to official headers
                # Added as a 1-tuple as the actual call to `putheader` (later on) unpacks it
                req.unmock_data["headers"]["Authorization"] = ("Bearer {token}".format(token=token), )
            self.__setattr__("unmock", req)


    def unmock_putheader(self, header, *values):
        """putheader mock; called sequentially after the putrequest.
        Here we simply redirect the different headers as either query parameters to be used, to part of the actual
        headers to be used to the unmock request.

        :param self
        :type self HTTPConnection
        :param header
        :type header string
        :param values
        :type values list, bytes
        """

        if unmock_options._is_host_whitelisted(self.host):  # Host is whitelisted, redirect to original call.
            original_putheader(self, header, *values)

        elif header == "Authorization":  # Authorization is part of the query parameters
            self.unmock.unmock_data["headers_qp"][header] = values

        elif header == UNMOCK_AUTH:  # UNMOCK_AUTH is part of the actual headers
            # TODO: is this ever called...? Where from..?
            self.unmock.unmock_data["headers"]["Authorization"] = values

        else:  # Otherwise, we both use it for query parameters and for the actual headers
            self.unmock.unmock_data["headers_qp"][header] = values
            self.unmock.unmock_data["headers"][header] = values


    def unmock_internal_end_headers(self, message_body):
        """
        Performs the internal operations when dealing with the endheaders request.
        :param self:
        :type self HTTPConnection
        :param message_body:
        :param message_body string
        :return:
        """
        # Otherwise we make the actual call to the unmock service
        unmock_data = self.unmock.unmock_data
        method = unmock_data["method"]

        # Builds the query parameters line
        query = unmock_options._build_query(story=unmock_data["story"], host=self.host, method=method,
                                            headers=unmock_data["headers_qp"],
                                            path="{path}".format(path=unmock_data["path"]))

        # Make the request to the service
        original_putrequest(self.unmock, method=method,
                            url="{fake_path}?{query}".format(fake_path=unmock_options._xy(token), query=query))

        # Add all the actual headers to the request
        for header, value in unmock_data["headers"].items():
            original_putheader(self.unmock, header, *value)

        # Save body and call original endheaders with the body message
        self.unmock.unmock_data["body"] = message_body

    if is_python2():
        def unmock_end_headers(self, message_body=None):
            """endheaders mock; signals the end of the HTTP request.
            At this point we should have all the data to make the request to the unmock service.

            :param self
            :type self HTTPConnection
            :param message_body
            :type message_body string
            """
            if unmock_options._is_host_whitelisted(self.host):  # Host is whitelisted, redirect to original call.
                # Return to avoid nesting
                return original_endheaders(self, message_body)
            unmock_internal_end_headers(self, message_body)
            original_endheaders(self.unmock, message_body)
    else:
        def unmock_end_headers(self, message_body=None, encode_chunked=False):
            """endheaders mock; signals the end of the HTTP request.
            At this point we should have all the data to make the request to the unmock service.
            NOTE: We drop the bare asterisk for Python2 compatibility.
            See https://stackoverflow.com/questions/2965271/forced-naming-of-parameters-in-python/14298976#14298976

            :param self
            :type self HTTPConnection
            :param message_body
            :type message_body string
            :param encode_chunked
            :type encode_chunked bool
            """

            if unmock_options._is_host_whitelisted(self.host):  # Host is whitelisted, redirect to original call.
                # Return to avoid nesting
                return original_endheaders(self, message_body, encode_chunked=encode_chunked)
            unmock_internal_end_headers(self, message_body)
            original_endheaders(self.unmock, message_body, encode_chunked=encode_chunked)


    def unmock_get_response(self):
        """getresponse mock; fetches the response from the connection made.
        Here we just need to redirect and use the getresponse from the linked unmock connection, output some messages
        and update the stories.

        :param self
        :type self HTTPConnection
        """
        if unmock_options._is_host_whitelisted(self.host):  # Host is whitelisted, redirect to original call.
            return original_getresponse(self)

        elif hasattr(self, "unmock"):
            unmock_data = self.unmock.unmock_data
            # Get unmocked response
            res = original_getresponse(self.unmock)  # type: HTTPResponse
            # Report the unmocked response, URL, and updates stories
            new_story = unmock_options._end_reporter(res=res, data=unmock_data["body"], host=self.host,
                                                     method=unmock_data["method"], path=unmock_data["path"],
                                                     story=STORIES, xy=unmock_options._xy(token))
            if new_story is not None:
                STORIES.append(new_story)
                res.__setattr__("unmock_hash", new_story)  # So we know the story the response belongs to
            return res

    def unmock_response_read(self, amt=None):
        """HTTPResponse.read mock; helps save the body of the unmock response locally if it is so desired.
        Since TCP sockets are one-time-transport, we need to catch the read operation and use it then, so nothing is
        missed.

        :param self
        :type self HTTPResponse
        :param amt
        :type amt int
        """
        s = original_response_read(self, amt)
        if hasattr(self, "unmock_hash"):  # We can now save the body of the content if it exists
            unmock_options._save_body(self.unmock_hash, s.decode())
        return s

    # Create the patchers and mock away!
    lib = "httplib" if is_python2() else "http.client"
    original_putrequest = PATCHERS.patch("{lib}.HTTPConnection.putrequest".format(lib=lib), unmock_putrequest)
    original_putheader = PATCHERS.patch("{lib}.HTTPConnection.putheader".format(lib=lib), unmock_putheader)
    original_endheaders = PATCHERS.patch("{lib}.HTTPConnection.endheaders".format(lib=lib), unmock_end_headers)
    original_getresponse = PATCHERS.patch("{lib}.HTTPConnection.getresponse".format(lib=lib), unmock_get_response)
    if unmock_options.save:
        # Only patch this if we have save=True or save is a list of hashes/stories to save
        original_response_read = PATCHERS.patch("{lib}.HTTPResponse.read".format(lib=lib), unmock_response_read)

    PATCHERS.start()

def reset():
    PATCHERS.clear()
    STORIES.clear()
