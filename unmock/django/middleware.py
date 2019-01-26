import requests_mock

# Full documentation:
# https://docs.djangoproject.com/en/2.1/topics/http/middleware/

class UnmockMiddleware(object):
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Code to be executed for each request before
        # the view (and later middleware) are called.

        with requests_mock.Mocker() as m:
            m.get('http://test.com', text='resp')
            response = self.get_response(request)

        # Code to be executed for each request/response after
        # the view is called.

        return response

    # Methods that are called during request

    def process_request(self, request):
        pass

    def process_view(self, request, view_func, view_args, view_kwargs):
        pass

    # Methods that are called during response

    def process_exception(self, request, exception):
        pass

    def process_template_response(self, request, response):
        pass

    def process_response(self, request, response):
        pass
