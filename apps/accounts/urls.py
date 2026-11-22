from django.urls import path

from apps.dashboard.views import home

from . import assistant, cat, cat_feedback, views

urlpatterns = [
    path("assistant/", assistant.assistant, name="assistant"),
    path("assistant/clear/", assistant.assistant_clear, name="assistant-clear"),
    path("cat/", cat.cat_home, name="cat"),
    path("cat/rating/", cat_feedback.cat_rating, name="cat-rating"),
    path("cat/start/", cat.cat_start, name="cat-start"),
    path("cat/finish/", cat.cat_finish, name="cat-finish"),
    path("", home, name="home"),
    path("students/", views.students, name="students"),
    path("students/<int:profile_id>/", views.student_detail, name="student-detail"),
    path("profile/persona/", views.persona_edit, name="persona-edit"),
    path("profile/", views.profile, name="profile"),
    path("login/", views.SignInView.as_view(), name="login"),
    path("logout/", views.sign_out, name="logout"),
]
