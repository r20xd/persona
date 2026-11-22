from django.urls import path

from .views import schedule, session

urlpatterns = [
    path("", schedule, name="schedule"),
    path("session/", session, name="session"),
]
