from datetime import UTC, datetime, timedelta
from unittest.mock import patch

import pytest
from django.http import Http404

from apps.academics.models import Term
from apps.dashboard.selectors import dashboard_context
from apps.grades.selectors import study_context
from tests.test_dashboard_demo import demo  # noqa: F401, F811

pytestmark = pytest.mark.django_db


def test_term_dates_moscow_and_explicit_selection(demo):  # noqa: F811
    user, _ = demo
    term = Term.objects.get(code="fiction-study-demo")
    midnight = datetime.combine(term.starts_on, datetime.min.time(), tzinfo=UTC)
    before = midnight - timedelta(hours=2)
    assert study_context(user, now=before)["term_state"] == "current"
    with patch("apps.dashboard.selectors.timezone.now", return_value=before):
        assert dashboard_context(user)["study"]["term"] == term
    assert (
        study_context(user, str(term.pk), now=midnight - timedelta(days=2))["term_state"]
        == "future"
    )
    assert study_context(user, now=midnight - timedelta(days=2))["term"] == term
    after = datetime.combine(term.ends_on + timedelta(days=2), datetime.min.time(), tzinfo=UTC)
    assert study_context(user, now=after)["term_state"] == "past"
    for invalid in ("invalid", "999999999"):
        with pytest.raises(Http404):
            study_context(user, invalid)


def test_ordering_boundaries_and_links(demo, client):  # noqa: F811
    from django.urls import reverse

    from apps.academics.models import CourseOffering, Enrollment

    user, _ = demo
    base = Term.objects.get(code="fiction-study-demo")
    offering = Enrollment.objects.filter(student=user.studentprofile).first().offering
    anchor = base.starts_on - timedelta(days=100)

    def add(code, start, end, own=True):
        term = Term.objects.create(code=code, title=code, starts_on=start, ends_on=end)
        if own:
            course = CourseOffering.objects.create(
                subject=offering.subject,
                group=offering.group,
                term=term,
                control_type=offering.control_type,
            )
            Enrollment.objects.create(student=user.studentprofile, offering=course)
        return term

    past = add("past", anchor - timedelta(days=20), anchor - timedelta(days=1))
    past_tie = add("past-tie", past.starts_on, past.ends_on)
    future = add("future", anchor + timedelta(days=2), anchor + timedelta(days=20))
    add("future-tie", future.starts_on, future.ends_on)
    later = add("later", anchor + timedelta(days=30), anchor + timedelta(days=40))
    now = datetime.combine(anchor, datetime.min.time(), tzinfo=UTC)
    assert study_context(user, now=now)["term"] == past_tie
    future_only = datetime.combine(
        past.starts_on - timedelta(days=1), datetime.min.time(), tzinfo=UTC
    )
    assert study_context(user, now=future_only)["term"] == past
    current = add("current", anchor, anchor + timedelta(days=1))
    current_tie = add("current-tie", current.starts_on, current.ends_on)
    assert study_context(user, now=now)["term"] == current_tie
    assert study_context(user, now=now + timedelta(days=1))["term"] == current_tie
    overlap = add("overlap", anchor - timedelta(days=1), anchor + timedelta(days=1))
    assert study_context(user, now=now)["term"] != overlap
    with patch("apps.grades.selectors.timezone.now", return_value=now):
        client.force_login(user)
        for term, text in [
            (later, "Будущий семестр начнётся"),
            (past, "Прошедший семестр завершился"),
        ]:
            for page, target in [("grades", "session"), ("session", "grades")]:
                response = client.get(reverse(page), {"term": term.pk})
                assert response.status_code == 200
                assert text in response.content.decode()
                assert f"{reverse(target)}?term={term.pk}" in response.content.decode()
        home = client.get(reverse("home"))
        assert home.context["study"]["term"] == current_tie
    client.force_login(user)
    foreign = add("foreign", anchor, anchor, own=False)
    for page in ("grades", "session"):
        assert client.get(reverse(page), {"term": foreign.pk}).status_code == 404
