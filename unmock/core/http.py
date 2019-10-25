import os
from io import BytesIO, StringIO
import socket
import email.parser
from .utils import PATCHERS, is_python_version_at_least
from six.moves import http_client
from .options import UnmockOptions
from .request import Request
has_urllib3 = True
try:
  import urllib3
except ImportError:
  has_urllib3 = False

__all__ = ["initialize", "reset"]

U_KEY = "unmock"


class Mocket(socket.socket):
  def __init__(self, content):
    self.content = content
    self.io = BytesIO(content.encode(
        'utf-8') if hasattr(content, 'encode') else content)

  def makefile(self, *args, **kw):
    return self.io

  def close(self, *args, **kw):
    pass


def initialize(unmock_options):
  """
  Entry point to mock the standard http client. It is used by `urllib` as well as the
  `http.client.HTTPConnection`, so mocking it should support their use aswell.

  We mock the "low level" API (instead of the `request` method, we mock the `putrequest`, `putheader`, `endheaders`
  and `getresponse` methods; the `request` method calls these sequentially).

  HTTPSConnection also uses the regular HTTPConnection methods under the hood -> hurray!

  :param unmock_options: An UnmockOptions file with user-behaviour customizations
  :type unmock_options UnmockOptions
  """

  def get_response(req):
    """
    Generates a response from the given request based on the replyFn in `unmock_options`
    """
    reply = unmock_options.replyTo(req)  # Get the reply for this Request
    content = reply.get("content", "")
    m = Mocket(content)  # Mocket for HTTPResponse generation
    # method, url were added later on
    res = http_client.HTTPResponse(
        m, method=req.method, url=req.endpoint) if is_python_version_at_least(
        "3.0") else http_client.HTTPResponse(m)

    # Parameters to keep HTTPResponse at bay while reading the response
    res.chunked = False
    res.length = len(content)
    res.version = 11
    res.status = res.code = reply.get("status", 200)
    res.reason = http_client.responses[res.status]
    res.isclosed = lambda: m.io.closed

    # Generate the bytes buffer for the msg attribute (mostly copied from httplib)
    # This is basically an encoded headers dictionary
    _buffer = []
    for k, v in reply.get("headers", dict()).items():
      val = []
      v = v if isinstance(v, list) else [v]
      for vv in v:
        if hasattr(vv, 'encode'):
          val.append(vv.encode('latin-1'))
        elif isinstance(vv, int):
          val.append(str(vv).encode('ascii'))
      _buffer.append(k.encode('ascii') + b':' + b'\r\n\t'.join(val))
    hstring = b''.join(_buffer).decode('iso-8859-1')
    if is_python_version_at_least("3.0"):
      res.msg = res.headers = email.parser.Parser(
          _class=http_client.HTTPMessage).parsestr(hstring)
    else:
      res.msg = http_client.HTTPMessage(StringIO(hstring))

    return res

  def unmock_urlopen(self, method, url, body=None, headers=None, **kw):
    """
    urllib3.urlopen (used in requests library as well). Requires a different patch as it creates its own sockets
    internally.
    """
    conn = self._get_conn()
    host = conn.host
    port = conn.port
    if unmock_options._is_host_whitelisted(host):
      return original_urlopen(method, url, body, headers, **kw)

    req = Request(host, port, url, method)
    req.add_headers(headers or dict())
    req.add_body(body)
    res = get_response(req)

    # In the process of creating the urllib response from HTTPResponse, the data is flushed (?)
    # TODO this could be an internal error - potentially a hack :shrug:
    contentValue = res.fp.getvalue()
    res = self.ResponseCls.from_httplib(res)  # So we reassign it here
    res._fp = BytesIO(contentValue)

    return res

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
    if not unmock_options._is_host_whitelisted(host):
      # Attach the unmock object to this connection for information aggregation
      req = Request(host, port, url, method)
      setattr(conn, U_KEY, req)
    else:
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

    res = get_response(req)

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

  # We probably do not need to patch the requests module, but in case we do, it's here -> requests.packages.urllib3.connectionpool.HTTPConnectionPool.urlopen
  if has_urllib3:
    original_urlopen = PATCHERS.patch(
        "urllib3.connectionpool.HTTPConnectionPool.urlopen", unmock_urlopen)

  PATCHERS.start()


def reset():
  PATCHERS.clear()
