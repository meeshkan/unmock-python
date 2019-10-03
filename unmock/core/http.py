import os
from io import BytesIO
import socket
import email.parser
from .utils import PATCHERS, is_python_version_at_least
from six.moves import http_client
from .options import UnmockOptions
from .request import Request
try:
  from unittest import mock
except ImportError:
  import mock

__all__ = ["initialize", "reset"]

U_KEY = "unmock"


class MockSocket(socket.socket):
  def __init__(self, content):
    self.content = content
    self.io = BytesIO(content.encode(
        'utf-8') if hasattr(content, 'encode') else content)

  def makefile(self, *args, **kw):
    m = mock.Mock()
    m.read.return_value = self.content

    def readinto(b):
      return self.io.readinto(b)
    m.readinto.side_effect = readinto
    return m

  def close(self, *args, **kw):
    pass


def initialize(unmock_options):
  """
  Entry point to mock the standard http client. Both `urllib` and `requests` library use the
  `http.client.HTTPConnection`, so mocking it should support their use aswell.

  We mock the "low level" API (instead of the `request` method, we mock the `putrequest`, `putheader`, `endheaders`
  and `getresponse` methods; the `request` method calls these sequentially).

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
    :param url - the endpoint on conn
    :type url string
    :param skip_host
    :type skip_host bool
    :param skip_accept_encoding
    :type skip_accept_encoding bool
    """
    # Extract host and port, create the request as normal
    host = conn.host
    port = conn.port
    original_putrequest(conn, method, url, skip_host, skip_accept_encoding)
    if not unmock_options._is_host_whitelisted(host):
      # Attach the unmock object to this connection for information aggregation
      req = Request(host, port, url, method)
      setattr(conn, U_KEY, req)

  def unmock_putheader(conn, header, *values):
    """putheader mock; called sequentially after the putrequest.

    :param conn
    :type conn HTTPConnection
    :param header
    :type header string
    :param values
    :type values list, bytes
    """
    original_putheader(conn, header, *values)  # Add header to the connection
    if hasattr(conn, U_KEY):
      req = getattr(conn, U_KEY)
      req.add_header(header, *values)  # And aggregate if needed

  # The encode_chunked parameters was added in Python 3.6
  if is_python_version_at_least("3.6"):
    def unmock_end_headers(conn, message_body=None, encode_chunked=False):
      """endheaders mock; signals the end of the HTTP request.
      NOTE: We drop the bare asterisk for Python2 compatibility.
      See https://stackoverflow.com/questions/2965271/forced-naming-of-parameters-in-python/14298976#14298976

      :param conn
      :type conn HTTPConnection
      :param message_body
      :type message_body string
      :param encode_chunked
      :type encode_chunked bool
      """
      if unmock_options._is_host_whitelisted(conn.host):
        # endheaders causes the socket to connect and sends data, so only call original
        # function if the connection is whitelisted
        original_endheaders(conn, message_body, encode_chunked=encode_chunked)
      elif hasattr(conn, U_KEY):
        internal_unmock_end_headers(conn, message_body)
  else:
    def unmock_end_headers(conn, message_body=None):
      """endheaders mock; signals the end of the HTTP request.
      At this point we should have all the data to make the request to the unmock service.

      :param conn
      :type conn HTTPConnection
      :param message_body
      :type message_body string
      """
      if unmock_options._is_host_whitelisted(conn.host):
        original_endheaders(conn, message_body)
      elif hasattr(conn, U_KEY):
        internal_unmock_end_headers(conn, message_body)

  def internal_unmock_end_headers(conn, message_body=None):
    req = getattr(conn, U_KEY)
    if message_body:  # Add body if needed
      req.add_body(message_body)

    reply = unmock_options.replyTo(req)  # Get the reply for this Request
    content = reply.get("content", "")
    m = MockSocket(content)  # MockSocket for HTTPResponse generation
    res = http_client.HTTPResponse(m, method=req.method, url=req.endpoint)

    res.chunked = False  # Parameters to keep HTTPResponse at bay while reading the response
    res.length = len(content)
    res.version = (1, 1)
    res.status = reply.get("status", 200)
    res.reason = http_client.responses[res.status]

    # Generate the bytes buffer for the msg attribute
    # (mostly copied from httplib)
    _buffer = []
    for k, v in reply.get("headers", dict()).items():
      val = []
      v = v if isinstance(v, list) else [v]
      for vv in v:
        if hasattr(vv, 'encode'):
          val.append(vv.encode('latin-1'))
        elif isinstance(one_value, int):
          val.append(str(vv).encode('ascii'))
      _buffer.append(k.encode('ascii') + b':' + b'\r\n\t'.join(val))
    hstring = b''.join(_buffer).decode('iso-8859-1')
    res.msg = res.headers = email.parser.Parser(
        _class=http_client.HTTPMessage).parsestr(hstring)

    conn.getresponse = lambda: res
    conn.__response = res
    conn.__state = http_client._CS_REQ_SENT

  # Create the patchers and mock away!
  original_putrequest = PATCHERS.patch(
      "six.moves.http_client.HTTPConnection.putrequest", unmock_putrequest)
  original_putheader = PATCHERS.patch(
      "six.moves.http_client.HTTPConnection.putheader", unmock_putheader)
  original_endheaders = PATCHERS.patch(
      "six.moves.http_client.HTTPConnection.endheaders", unmock_end_headers)

  PATCHERS.start()


def reset():
  PATCHERS.clear()
