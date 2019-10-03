import json
from six.moves.urllib.parse import parse_qs
from six.moves.http_client import responses
from .utils import parse_url
try:
  from unittest import mock
except ImportError:
  import mock


class Request:
  def __init__(self, host, port, endpoint, method):
    self.host = host
    self.endpoint = endpoint
    self.method = method
    self.port = port

    self.headers = dict()
    self.data = None
    self.qs = dict()

    _, _, _, query, _ = parse_url(endpoint)
    if query:
      self.add_query(query)

  def add_qs(self, key, value):
    self.qs[key] = value

  def add_query(self, query):
    parsed = parse_qs(query)
    for k, v in parsed.items():
      self.qs[k] = v

  def add_header(self, key, value):
    self.headers[key] = value

  def add_headers(self, headers):
    for (k, v) in self.headers:
      self.headers[k] = v

  def add_body(self, data):
    self.data = data


class Response():
  def __init__(self, content="", statuscode=200, headers=None):
    if isinstance(content, str):
      self.content = content
    else:
      self.content = json.dumps(content)
    self.status = statuscode
    self.headers = headers or dict()
    self.n = 0

  def read(self, amt=None):
    c = self.content
    if amt:
      c = self.content[self.n:self.n+amt]
      self.n += amt
    return c

  def mock(self):
    m = mock.MagicMock()
    # Define the return values for some of HTTPResponse attributes and/or methods
    m.read.side_effect = lambda amt: self.read(amt)
    m.status = self.status
    m.reason = responses[self.status]
    m.headers = self.headers
    m.getheaders.return_value = self.headers
    m.getheader.side_effect = lambda name, default: self.headers.get(
        name, default)
    return m
