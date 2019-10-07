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

  def __str__(self):
    return "{} {}{}:{} {} with body {}".format(
        self.method, self.host, self.endpoint, self.port, self.headers, self.
        data)
