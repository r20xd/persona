from django.urls import path

from . import views

urlpatterns = [
    path("requests/<uuid:request_id>/messages/", views.message_send, name="request-message-send"),
    path(
        "operator/requests/<uuid:request_id>/messages/",
        views.message_send,
        {"operator": True},
        name="operator-request-message-send",
    ),
    path("requests/", views.request_list, name="requests"),
    path("requests/new/", views.new_request, name="request-new"),
    path("requests/<uuid:request_id>/", views.detail, name="request-detail"),
    path("requests/<uuid:request_id>/cancel/", views.change, name="request-cancel"),
    path("operator/requests/", views.operator_queue, name="operator-requests"),
    path(
        "operator/requests/<uuid:request_id>/",
        views.detail,
        {"operator": True},
        name="operator-request-detail",
    ),
    path(
        "operator/requests/<uuid:request_id>/transition/",
        views.change,
        {"operator": True},
        name="operator-request-transition",
    ),
]
