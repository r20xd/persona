from django.http import Http404
from django.utils import timezone

from apps.academics.models import Term
from apps.academics.selectors import own_enrollments
from apps.schedule.selectors import MOSCOW

from .models import Assessment, ExamEvent, GradeResult


def study_context(user, term_id=None, *, now=None):
    now = now if now is not None else timezone.now()
    today = timezone.localdate(now, timezone=MOSCOW)
    enrollments = own_enrollments(user)
    terms = list(
        Term.objects.filter(courseoffering__enrollment__in=enrollments)
        .distinct()
        .order_by("-starts_on", "-pk")
    )
    selected = (
        next((term for term in terms if str(term.pk) == term_id), None)
        if term_id is not None
        else next((term for term in terms if term.starts_on <= today <= term.ends_on), None)
    )
    if term_id is None and selected is None:
        past = [term for term in terms if term.ends_on < today]
        future = [term for term in terms if term.starts_on > today]
        selected = (
            max(past, key=lambda term: (term.ends_on, term.pk))
            if past
            else min(future, key=lambda term: (term.starts_on, term.pk), default=None)
        )
    term_state = None
    if selected:
        if selected.ends_on < today:
            term_state = "past"
        elif selected.starts_on > today:
            term_state = "future"
        else:
            term_state = "current"
    if term_id is not None and selected is None:
        raise Http404
    enrollments = (
        list(enrollments.filter(offering__term=selected).order_by("offering__subject__name", "pk"))
        if selected
        else []
    )
    visible = GradeResult.objects.filter(enrollment__in=enrollments, published_at__lte=now)
    results = {(item.enrollment_id, item.assessment_id): item for item in visible}
    offerings = [item.offering_id for item in enrollments]
    assessments = Assessment.objects.filter(offering_id__in=offerings).order_by("pk")
    definitions = {}
    for assessment in assessments:
        definitions.setdefault(assessment.offering_id, []).append(assessment)
    rows = []
    counts = {"success": 0, "failure": 0, "awaiting": 0}
    for enrollment in enrollments:
        row = {"offering": enrollment.offering, "work": [], "final": None, "state": "awaiting"}
        for assessment in definitions.get(enrollment.offering_id, []):
            result = results.get((enrollment.pk, assessment.pk))
            if assessment.kind == "coursework":
                row["work"].append({"assessment": assessment, "result": result})
            elif result:
                row["final"] = result
                row["state"] = (
                    "failure" if result.outcome in {"failed", "unsatisfactory"} else "success"
                )
        counts[row["state"]] += 1
        rows.append(row)
    events = (
        ExamEvent.objects.filter(offering_id__in=offerings)
        .select_related("offering__subject", "teacher", "room")
        .order_by("starts_at", "pk")
    )
    return {
        "term_state": term_state,
        "terms": terms,
        "term": selected,
        "rows": rows,
        "counts": counts,
        "events": events,
    }
