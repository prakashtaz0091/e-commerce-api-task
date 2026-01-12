from django.test import TestCase, RequestFactory
from django.http import HttpResponse

from api.middlewares import (
    RequestContextMiddleware,
    get_current_request,
    get_client_ip,
)


class RequestContextMiddlewareTest(TestCase):

    def setUp(self):
        self.factory = RequestFactory()

        # Simple view to pass through middleware
        self.get_response = lambda request: HttpResponse("OK")
        self.middleware = RequestContextMiddleware(self.get_response)

    # ---------------------------------
    # Request context available
    # ---------------------------------
    def test_request_is_available_in_context(self):
        captured_request = []

        def dummy_view(request):
            # get_current_request() is valid inside the middleware call
            captured_request.append(get_current_request())
            return HttpResponse("OK")

        middleware = RequestContextMiddleware(dummy_view)
        request = self.factory.get("/some-path/")
        response = middleware(request)

        # Now captured_request[0] contains the current request
        self.assertIsNotNone(captured_request[0])
        self.assertEqual(captured_request[0].path, "/some-path/")
        self.assertEqual(response.status_code, 200)

    # ---------------------------------
    # Request context cleaned up after response
    # ---------------------------------
    def test_request_context_is_removed_after_response(self):
        request = self.factory.get("/some-path/")
        self.middleware(request)

        # After request finishes, context should be cleared
        self.assertIsNone(get_current_request())

    # ---------------------------------
    # IP extraction from HTTP_X_FORWARDED_FOR
    # ---------------------------------
    def test_get_client_ip_from_forwarded_for(self):
        request = self.factory.get(
            "/some-path/", HTTP_X_FORWARDED_FOR="1.2.3.4, 5.6.7.8"
        )
        ip = get_client_ip(request)
        self.assertEqual(ip, "1.2.3.4")

    # ---------------------------------
    # IP extraction from REMOTE_ADDR fallback
    # ---------------------------------
    def test_get_client_ip_from_remote_addr(self):
        request = self.factory.get("/some-path/", REMOTE_ADDR="9.8.7.6")
        ip = get_client_ip(request)
        self.assertEqual(ip, "9.8.7.6")

    # ---------------------------------
    # IP extraction prefers X_FORWARDED_FOR
    # ---------------------------------
    def test_x_forwarded_for_over_remote_addr(self):
        request = self.factory.get(
            "/some-path/", HTTP_X_FORWARDED_FOR="1.1.1.1", REMOTE_ADDR="2.2.2.2"
        )
        ip = get_client_ip(request)
        self.assertEqual(ip, "1.1.1.1")
