"""Fictional visual review only. No queries, authentication or persistence."""

from django.conf import settings
from django.http import Http404
from django.shortcuts import render
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_safe


def _check_enabled():
    if not getattr(settings, "ENABLE_UI_PREVIEW", False):
        raise Http404


@require_safe
@never_cache
def dashboard(request):
    _check_enabled()
    return render(
        request,
        "core/preview/dashboard.html",
        {
            "days": [
                ("Пн", "2"),
                ("Вт", "3"),
                ("Ср", "4"),
                ("Чт", "5"),
                ("Пт", "6"),
                ("Сб", "7"),
                ("Вс", "8"),
            ],
            "lessons": [
                {
                    "time": "09:00",
                    "end": "10:20",
                    "title": "Международная экономика",
                    "kind": "Лекция",
                    "room": "Ауд. 304 · Корпус А",
                    "teacher": "Н. А. Листова",
                    "state": "Завершилось",
                    "past": True,
                },
                {
                    "time": "10:40",
                    "end": "12:00",
                    "title": "Иностранный язык",
                    "kind": "Практика",
                    "room": "Ауд. 218 · Корпус Б",
                    "teacher": "М. О. Берестова",
                    "state": "Следующее занятие",
                    "next": True,
                },
                {
                    "time": "13:00",
                    "end": "14:20",
                    "title": "Теория международных отношений",
                    "kind": "Семинар",
                    "room": "Ауд. 412 · Корпус А",
                    "teacher": "А. С. Ветренев",
                    "state": "Перенос",
                    "changed": True,
                },
            ],
        },
    )


@require_safe
@never_cache
def login(request):
    _check_enabled()
    return render(request, "core/preview/login.html")
