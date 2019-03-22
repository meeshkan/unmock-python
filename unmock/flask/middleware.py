import requests_mock


# WSGI PEP-3333 specification:
# # https://www.python.org/dev/peps/pep-3333/

class UnmockMiddleware(object):
    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        @requests_mock.Mocker()
        def foo(m):
            m.get('http://test.com', text='resp')
            return self.app(environ, start_response)
        return foo()
