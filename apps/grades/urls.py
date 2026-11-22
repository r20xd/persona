from django.urls import path

from apps.schedule.views import session

from .views import study

urlpatterns = [
    path("grades/", study, name="grades"),
    path("session/", session, name="session-legacy"),
]
