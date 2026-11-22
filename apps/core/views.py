from urllib.parse import urlsplit

from django.contrib.staticfiles.storage import staticfiles_storage
from django.db import DatabaseError, connection
from django.http import HttpResponse, JsonResponse
from django.template.loader import render_to_string
from django.utils.cache import patch_vary_headers
from django.views.decorators.http import require_safe


def _response(status, *, code=200):
    response = JsonResponse({"status": status}, status=code)
    response["Cache-Control"] = "no-store"
    return response


@require_safe
def live(request):
    return _response("ok")


@require_safe
def ready(request):
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
    except DatabaseError:
        return _response("unavailable", code=503)
    return _response("ok")


ERRORS = {
    400: ("bad_request", "Не удалось открыть страницу", "Параметры запроса не поддерживаются."),
    403: ("forbidden", "Страница недоступна", "У вас нет доступа к этой странице."),
    404: ("not_found", "Страница не найдена", "Возможно, страница удалена или ссылка устарела."),
    500: (
        "error",
        "Не удалось загрузить страницу",
        "Попробуйте вернуться в кабинет немного позже.",
    ),
}


def error_response(request, code):
    status, title, explanation = ERRORS[code]
    if request.get_preferred_type(["text/html", "application/json"]) == "application/json":
        response = _response(status, code=code)
    else:
        # No request context: error recovery must not evaluate users, sessions or database queries.
        stylesheet = None
        try:
            candidate = staticfiles_storage.url("css/workspace.css")
            parsed = urlsplit(candidate)
            if not parsed.scheme and not parsed.netloc and candidate.startswith("/"):
                stylesheet = candidate
        except (ValueError, OSError):
            # A missing collectstatic manifest must not turn recovery into another server error.
            pass
        html = render_to_string(
            "core/error.html",
            {"code": code, "title": title, "explanation": explanation, "stylesheet": stylesheet},
        )
        response = HttpResponse(html, status=code)
        response["Cache-Control"] = "no-store"
    patch_vary_headers(response, ["Accept"])
    return response


def bad_request(request, exception=None):
    return error_response(request, 400)


def permission_denied(request, exception):
    return error_response(request, 403)


def not_found(request, exception):
    return error_response(request, 404)


def server_error(request):
    return error_response(request, 500)
