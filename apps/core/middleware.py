"""Minimal structured access events: no URL, parameters, user data or exception text."""

import logging
import time
import uuid

logger = logging.getLogger("deanery.http")


class RequestLogMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request_id = uuid.uuid4().hex
        started = time.monotonic()
        response = self.get_response(request)
        match = getattr(request, "resolver_match", None)
        route = match.url_name if match and match.url_name else "unmatched"
        logger.info(
            "request_id=%s route=%s status=%d duration_ms=%d",
            request_id,
            route,
            response.status_code,
            (time.monotonic() - started) * 1000,
        )
        response["X-Request-ID"] = request_id
        return response
