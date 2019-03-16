import os
import logging
import multiprocessing
try:
    import http.server as HTTPServer
except ImportError:
    import BaseHTTPServer as HTTPServer

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


def is_text(text):
    """Checks whether text is string/unicode (Python 2/3 compatibility)"""
    try:
        return isinstance(text, (unicode, str))
    except NameError:
        return isinstance(text, str)


def one_hit_server():
    def init_server():
        srv = HTTPServer.HTTPServer(("127.0.0.1", 7331), RequestHandler)
        event.set()
        srv.handle_request()
        srv.server_close()

    class RequestHandler(HTTPServer.BaseHTTPRequestHandler):
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

