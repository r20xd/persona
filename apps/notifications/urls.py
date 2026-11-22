from django.urls import path

from . import views

urlpatterns = [
    path("operator/announcements/new/", views.announcement_new, name="announcement-new"),
    path("notifications/", views.feed, name="notifications"),
    path("notifications/read-all/", views.read_all, name="notifications-read-all"),
    path(
        "notifications/<uuid:notification_id>/read/",
        views.read_notification,
        name="notification-read",
    ),
    path("notifications/<uuid:notification_id>/open/", views.open_target, name="notification-open"),
    path(
        "announcements/<int:announcement_id>/read/",
        views.read_announcement,
        name="announcement-read",
    ),
    path("deadlines/", views.deadlines, name="deadlines"),
    path("deadlines/<uuid:deadline_id>/state/", views.deadline_state, name="deadline-state"),
]
