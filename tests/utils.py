import os
import logging
import multiprocessing
from six.moves import BaseHTTPServer

LOGGER = None

def get_logger():
    """Returns a logger for test-use (does not write to log files)"""
    global LOGGER
    if LOGGER is None:
        LOGGER = logging.getLogger("tests.unmock")
        LOGGER.setLevel(logging.WARNING)
        frmtr = logging.Formatter("[%(asctime)s] %(levelname)s\\%(name)s:\t%(message)s")
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(frmtr)
        LOGGER.addHandler(console_handler)
    return LOGGER


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


def get_token():
    return os.environ.get("UNMOCK_TOKEN")


class MockResponse:
    def __init__(self, response, status_code=200):
        self.response = response
        self.status_code = status_code
    def json(self):
        return self.response

