from typing import Optional, List
import http.client
import os

from .options import UnmockOptions
from .utils import Patchers, parse_url

__all__ = ["initialize", "reset"]

# Backup:
UNMOCK_AUTH = "___u__n_m_o_c_k_a_u_t__h_"
PATCHERS = Patchers()
STORIES = list()

def initialize(unmock_options: Optional[UnmockOptions] = None, story: Optional[List[str]] = None,
               refresh_token: Optional[str] = None):
    """
    Initialize the unmock library for capturing API calls.

    :param unmock_options: An Optional object allowing customization of how unmock works.
    :type unmock_options UnmockOptions
    :param story: An optional list of unmock stories to initialize the state. These represent previous calls to unmock
        and make unmock stateful.
    :type story List[str]
    :param refresh_token: An optional unmock *refresh token* identifying your account.
    :type refresh_token str
    """
    """
    Entry point to mock the standard http client. Both `urllib` and `requests` library use the
    `http.client.HTTPConnection`, so mocking it should support their use aswell.

    We mock the "low level" API (instead of the `request` method, we mock the `putrequest`, `putheader`, `endheaders`
    and `getresponse` methods; the `request` method calls these sequentially).

    HTTPSConnection also uses the regular HTTPConnection methods under the hood -> hurray!
    """
    global PATCHERS, STORIES
    if story is not None:
        STORIES += story
    if unmock_options is None:  # Default then!
        unmock_options = UnmockOptions(token=refresh_token)
    if os.environ.get("ENV") == "production" and not unmock_options.use_in_production:
        return
    token = unmock_options.get_token()  # Get the *access_token*

    def unmock_putrequest(self: http.client.HTTPConnection, method, url, skip_host=False, skip_accept_encoding=False):
        """putrequest mock; called initially after the HTTPConnection object has been created. Contains information
        about the endpoint and method."""
        global STORIES
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


    def unmock_putheader(self: http.client.HTTPConnection, header, *values):
        """putheader mock; called sequentially after the putrequest.
        Here we simply redirect the different headers as either query parameters to be used, to part of the actual
        headers to be used to the unmock request.
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


    def unmock_end_headers(self: http.client.HTTPConnection, message_body=None, *, encode_chunked=False):
        """endheaders mock; signals the end of the HTTP request.
        At this point we should have all the data to make the request to the unmock service.
        """

        if unmock_options._is_host_whitelisted(self.host):  # Host is whitelisted, redirect to original call.
            # Return to avoid nesting
            return original_endheaders(self, message_body, encode_chunked=encode_chunked)

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
        original_endheaders(self.unmock, message_body, encode_chunked=encode_chunked)


    def unmock_get_response(self: http.client.HTTPConnection):
        """getresponse mock; fetches the response from the connection made.
        Here we just need to redirect and use the getresponse from the linked unmock connection, output some messages
        and update the stories.
        """
        global STORIES
        if unmock_options._is_host_whitelisted(self.host):  # Host is whitelisted, redirect to original call.
            return original_getresponse(self)

        elif hasattr(self, "unmock"):
            unmock_data = self.unmock.unmock_data
            res: http.client.HTTPResponse = original_getresponse(self.unmock)  # Get unmocked response
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
        missed."""
        s = original_response_read(self, amt)
        if hasattr(self, "unmock_hash"):  # We can now save the body of the content if it exists
            unmock_options._save_body(self.unmock_hash, s.decode())
        return s

    # Create the patchers and mock away!
    original_putrequest = PATCHERS.patch("http.client.HTTPConnection.putrequest", unmock_putrequest)
    original_putheader = PATCHERS.patch("http.client.HTTPConnection.putheader", unmock_putheader)
    original_endheaders = PATCHERS.patch("http.client.HTTPConnection.endheaders", unmock_end_headers)
    original_getresponse = PATCHERS.patch("http.client.HTTPConnection.getresponse", unmock_get_response)
    if unmock_options.save:
        # Only patch this if we have save=True or save is a list of hashes/stories to save
        original_response_read = PATCHERS.patch("http.client.HTTPResponse.read", unmock_response_read)

    PATCHERS.start()

def reset():
    global PATCHERS, STORIES
    PATCHERS.stop()
    STORIES = list()  # Reset stories
