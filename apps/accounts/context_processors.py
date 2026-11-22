"""Owner-only cosmetic companion projection. GET never creates a cat."""

from django.conf import settings
from django.utils.crypto import salted_hmac

from .cat import cat_card
from .cat_feedback import page_questions
from .models import StudentCat, StudentProfile

READ_ROUTES = {
    "home",
    "assistant",
    "schedule",
    "session",
    "session-legacy",
    "grades",
    "requests",
    "notifications",
    "students",
    "student-detail",
}


def cat_cameo(request):
    route = getattr(getattr(request, "resolver_match", None), "url_name", None)
    user = getattr(request, "user", None)
    if (
        request.method != "GET"
        or route not in READ_ROUTES | {"cat"}
        or not user
        or not user.is_authenticated
        or not user.is_active
        or user.role != "student"
    ):
        return {}
    profile = StudentProfile.objects.select_related("studentcat").filter(user_id=user.pk).first()
    if profile is None:
        return {}
    owner = salted_hmac("accounts.cat-cameo.v1", str(user.pk)).hexdigest()
    preference = {"owner": owner}
    if route == "cat":
        return {"cat_walk_preference": preference}
    try:
        own = profile.studentcat
    except StudentCat.DoesNotExist:
        own = None
    card = cat_card(own)
    return {
        "cat_walk_preference": preference,
        "cat_rating_questions": page_questions(route),
        "cat_cameo": {
            "name": card["name"],
            "character_label": card["character_label"],
            "renderer": card["renderer"],
            "quote": card["quote"],
        },
    }


def student_directory(request):
    return {"student_directory_enabled": settings.ENABLE_STUDENT_DIRECTORY}
