import multiprocessing
from six.moves import BaseHTTPServer


def one_hit_server():
  def init_server():
    srv = BaseHTTPServer.HTTPServer(("127.0.0.1", 7331), RequestHandler)
    event.set()
    srv.handle_request()
    srv.server_close()

  class RequestHandler(BaseHTTPServer.BaseHTTPRequestHandler):
    def do_GET(self):
      self.send_response(200)
      self.send_header("Content-type", "text/json")
      self.end_headers()
      self.wfile.write(b'{ "success": true }')
      self.server.path = self.path

  proc = multiprocessing.Process(target=init_server)
  event = multiprocessing.Event()
  event.clear()
  proc.start()
  return event


class MockResponse:
  def __init__(self, response, status_code=200):
    self.response = response
    self.status_code = status_code

  def json(self):
    return self.response
