"""Trusted internal CLI writes only; ORM bulk writes bypass cross-relation validation.

Lock the offering before reading definitions or modifying results, so all service
writes for a course serialize. No student/operator grade-write endpoint exists.
"""

from django.core.exceptions import ValidationError
from django.db import transaction

from apps.academics.models import CourseOffering, Enrollment

from .models import Assessment, ExamEvent, GradeResult


@transaction.atomic
def create_assessment(**fields):
    offering = fields["offering"]
    CourseOffering.objects.select_for_update().get(pk=offering.pk)
    item = Assessment(**fields)
    item.full_clean()
    item.save()
    return item


@transaction.atomic
def record_result(*, assessment, enrollment, **fields):
    if set(fields) - {"points", "outcome", "published_at"}:
        raise ValidationError("Неизвестные поля результата.")
    CourseOffering.objects.select_for_update().get(pk=assessment.offering_id)
    assessment = (
        Assessment.objects.select_for_update().select_related("offering").get(pk=assessment.pk)
    )
    enrollment = (
        Enrollment.objects.select_for_update()
        .select_related("student", "offering")
        .get(pk=enrollment.pk)
    )
    item = (
        GradeResult.objects.select_for_update()
        .filter(assessment=assessment, enrollment=enrollment)
        .first()
    )
    if item is None:
        item = GradeResult(assessment=assessment, enrollment=enrollment)
    for name, value in fields.items():
        setattr(item, name, value)
    item.full_clean()
    item.save()
    return item


@transaction.atomic
def create_exam_event(**fields):
    CourseOffering.objects.select_for_update().get(pk=fields["offering"].pk)
    item = ExamEvent(**fields)
    item.clean()
    item.full_clean()
    item.save()
    return item
