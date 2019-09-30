import os
from .utils import Patchers, parse_url, is_python_version_at_least
from six.moves import http_client
from . import PATCHERS
from .options import UnmockOptions
from .utils import unmock_user_agent

__all__ = ["initialize", "reset"]


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
  def unmock_putrequest(conn, method, url, skip_host=False,
                        skip_accept_encoding=False):
    """putrequest mock; called initially after the HTTPConnection object has been created. Contains information
    about the endpoint and method.

    :param conn
    :type conn HTTPConnection
    :param method
    :type method string
    :param url
    :type url string
    :param skip_host
    :type skip_host bool
    :param skip_accept_encoding
    :type skip_accept_encoding bool
    """

    original_putrequest(conn, method, url, skip_host, skip_accept_encoding)

  def unmock_putheader(conn, header, *values):
    """putheader mock; called sequentially after the putrequest.

    :param conn
    :type conn HTTPConnection
    :param header
    :type header string
    :param values
    :type values list, bytes
    """

    original_putheader(conn, header, *values)

  # The encode_chunked parameters was added in Python 3.6
  if is_python_version_at_least("3.6"):
    def unmock_end_headers(conn, message_body=None, encode_chunked=False):
      """endheaders mock; signals the end of the HTTP request.
      At this point we should have all the data to make the request to the unmock service.
      NOTE: We drop the bare asterisk for Python2 compatibility.
      See https://stackoverflow.com/questions/2965271/forced-naming-of-parameters-in-python/14298976#14298976

      :param conn
      :type conn HTTPConnection
      :param message_body
      :type message_body string
      :param encode_chunked
      :type encode_chunked bool
      """

      return original_endheaders(
          conn, message_body, encode_chunked=encode_chunked)
  else:
    def unmock_end_headers(conn, message_body=None):
      """endheaders mock; signals the end of the HTTP request.
      At this point we should have all the data to make the request to the unmock service.

      :param conn
      :type conn HTTPConnection
      :param message_body
      :type message_body string
      """
      return original_endheaders(conn, message_body)

  def unmock_get_response(conn):
    """getresponse mock; fetches the response from the connection made.
    Here we just need to redirect and use the getresponse from the linked unmock connection, output some messages
    and update the stories.

    :param conn
    :type conn HTTPConnection
    """
    return original_getresponse(conn)

  def unmock_response_read(res, amt=None):
    """HTTPResponse.read mock;
    :param res
    :type res HTTPResponse
    :param amt
    :type amt int
    """
    return original_response_read(res, amt)

  # Create the patchers and mock away!
  original_putrequest = PATCHERS.patch(
      "six.moves.http_client.HTTPConnection.putrequest", unmock_putrequest)
  original_putheader = PATCHERS.patch(
      "six.moves.http_client.HTTPConnection.putheader", unmock_putheader)
  original_endheaders = PATCHERS.patch(
      "six.moves.http_client.HTTPConnection.endheaders", unmock_end_headers)
  original_getresponse = PATCHERS.patch(
      "six.moves.http_client.HTTPConnection.getresponse", unmock_get_response)
  original_response_read = PATCHERS.patch(
      "six.moves.http_client.HTTPResponse.read", unmock_response_read)

  PATCHERS.start()


def reset():
  PATCHERS.clear()
