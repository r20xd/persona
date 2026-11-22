from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    class Role(models.TextChoices):
        STUDENT = "student", "Студент"
        OPERATOR = "operator", "Оператор"

    role = models.CharField(max_length=8, choices=Role.choices, default=Role.STUDENT)

    class Meta(AbstractUser.Meta):
        constraints = [
            models.CheckConstraint(
                condition=models.Q(role__in=["student", "operator"]), name="user_role_valid"
            ),
        ]


class StudentProfile(models.Model):
    user = models.OneToOneField("accounts.User", on_delete=models.PROTECT)
    full_name = models.CharField(max_length=200)
    course = models.PositiveSmallIntegerField()
    group = models.ForeignKey("academics.StudyGroup", on_delete=models.PROTECT)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=models.Q(course__gte=1, course__lte=6), name="student_course_valid"
            ),
        ]

    def clean(self):
        from django.core.exceptions import ValidationError

        if self.user_id and self.user.role != User.Role.STUDENT:
            raise ValidationError({"user": "Профиль доступен только студенту."})


class OperatorScope(models.Model):
    operator = models.ForeignKey("accounts.User", on_delete=models.PROTECT)
    group = models.ForeignKey("academics.StudyGroup", on_delete=models.PROTECT)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["operator", "group"], name="operator_group_unique")
        ]

    def clean(self):
        from django.core.exceptions import ValidationError

        if self.operator_id and self.operator.role != User.Role.OPERATOR:
            raise ValidationError({"operator": "Область доступа доступна только оператору."})


class StudentPersona(models.Model):
    student = models.OneToOneField(StudentProfile, on_delete=models.PROTECT)
    strengths = models.JSONField(default=list, blank=True)
    interests = models.JSONField(default=list, blank=True)
    skills = models.JSONField(default=list, blank=True)
    activities = models.JSONField(default=list, blank=True)
    goal = models.CharField(max_length=160, blank=True)
    progress = models.PositiveSmallIntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=models.Q(progress__gte=0, progress__lte=100),
                name="persona_progress_range",
            )
        ]


class StudentCat(models.Model):
    student = models.OneToOneField(StudentProfile, on_delete=models.PROTECT)
    name = models.CharField(max_length=24, default="Плюш")
    character = models.CharField(max_length=8, default="sleepy")
    accessory = models.CharField(max_length=8, default="none")
    toys = models.JSONField(default=list)
    completed = models.PositiveIntegerField(default=0)
    last_attempt = models.CharField(max_length=100, blank=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=models.Q(character__in=["sleepy", "scholar", "chaos"]),
                name="cat_character_valid",
            ),
            models.CheckConstraint(
                condition=models.Q(accessory__in=["none", "yarn", "ball", "mouse", "fish"]),
                name="cat_accessory_valid",
            ),
        ]


class CatPageRating(models.Model):
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE)
    question = models.CharField(max_length=64)
    rating = models.PositiveSmallIntegerField()
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["student", "question"], name="cat_rating_student_question"
            ),
            models.CheckConstraint(
                condition=models.Q(rating__gte=1, rating__lte=5), name="cat_rating_range"
            ),
        ]
