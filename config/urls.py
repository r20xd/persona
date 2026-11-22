from django.urls import include, path

from apps.core import preview, views

urlpatterns = [
    path("", include("apps.notifications.urls")),
    path("", include("apps.requests.urls")),
    path("", include("apps.grades.urls")),
    path("schedule/", include("apps.schedule.urls")),
    path("", include("apps.accounts.urls")),
    path("preview/", preview.dashboard, name="preview-dashboard"),
    path("preview/login/", preview.login, name="preview-login"),
    path("health/live/", views.live, name="health-live"),
    path("health/ready/", views.ready, name="health-ready"),
]
handler400 = "apps.core.views.bad_request"
handler403 = "apps.core.views.permission_denied"
handler404 = "apps.core.views.not_found"
handler500 = "apps.core.views.server_error"
