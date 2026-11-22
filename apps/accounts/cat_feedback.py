"""Page-specific, private feedback collected by the student's cat."""

from django.http import JsonResponse
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_POST

from .models import CatPageRating
from .selectors import own_profile

QUESTION_POOLS = {
    "home": [
        ("home.overview", "Удобно ли видеть главное на одной странице?"),
        ("home.site", "Как тебе кабинет в целом?"),
    ],
    "schedule": [
        ("schedule.reading", "Легко ли разобраться в расписании?"),
        ("schedule.changes", "Хорошо ли заметны изменения занятий?"),
    ],
    "session": [
        ("session.overview", "Понятно ли расписание сессии?"),
        ("session.details", "Удобно ли находить детали экзаменов?"),
    ],
    "grades": [
        ("grades.overview", "Понятно ли, как идут дела с учёбой?"),
        ("grades.reading", "Удобно ли смотреть оценки?"),
    ],
    "requests": [
        ("requests.status", "Понятны ли статусы заявок?"),
        ("requests.order", "Удобно ли заказывать документы?"),
    ],
    "notifications": [
        ("notifications.reading", "Удобно ли читать объявления?"),
        ("notifications.deadlines", "Хорошо ли заметны важные сроки?"),
    ],
    "students": [
        ("students.search", "Удобно ли искать студентов?"),
        ("students.cards", "Нравятся ли карточки студентов?"),
    ],
    "student-detail": [
        ("student-detail.reading", "Удобно ли смотреть карточку студента?"),
        ("student-detail.persona", "Интересно ли узнавать о других студентах?"),
    ],
    "assistant": [
        ("assistant.help", "Полезен ли тебе ИИ-помощник?"),
        ("assistant.use", "Удобно ли общаться с ИИ-помощником?"),
    ],
}
QUESTION_POOLS["session-legacy"] = QUESTION_POOLS["session"]
QUESTION_KEYS = frozenset(key for pool in QUESTION_POOLS.values() for key, _ in pool)


def page_questions(route):
    return [{"key": key, "text": text} for key, text in QUESTION_POOLS.get(route, ())]


@never_cache
@require_POST
def cat_rating(request):
    student = own_profile(request.user)
    question = request.POST.get("question", "")
    value = request.POST.get("rating", "")
    if question not in QUESTION_KEYS or value not in {"1", "2", "3", "4", "5"}:
        return JsonResponse({"error": "Выбери оценку от 1 до 5 для этого вопроса."}, status=400)
    rating = int(value)
    CatPageRating.objects.update_or_create(
        student=student, question=question, defaults={"rating": rating}
    )
    return JsonResponse({"question": question, "rating": rating})
