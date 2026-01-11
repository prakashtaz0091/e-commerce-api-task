from asgiref.local import Local

_request_ctx = Local()


def get_current_request():
    return getattr(_request_ctx, "request", None)


def get_client_ip(request):
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        return x_forwarded_for.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


class RequestContextMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        _request_ctx.request = request
        try:
            return self.get_response(request)
        finally:
            if hasattr(_request_ctx, "request"):
                del _request_ctx.request
