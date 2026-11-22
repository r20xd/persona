import uuid
from urllib.parse import urlencode
from zoneinfo import ZoneInfo

from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.core.paginator import EmptyPage, Paginator
from django.db.models import F
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from apps.academics.selectors import own_enrollments
from apps.accounts.models import User
from apps.core.views import bad_request

from . import selectors, services
from .forms import AnnouncementForm, PersonalDeadlineForm


def page(queryset, number):
    if not number.isascii() or not number.isdigit() or len(number) > 8 or int(number) < 1:
        raise ValueError
    try:
        return Paginator(queryset, 20).page(int(number))
    except EmptyPage as error:
        raise Http404 from error


@never_cache
@login_required
@require_http_methods(["GET", "POST"])
def announcement_new(request):
    user = selectors.announcement_operator(request.user)
    form = AnnouncementForm(
        request.POST if request.method == "POST" else None,
        user=user,
        initial={"submission_key": uuid.uuid4()},
    )
    if request.method == "POST" and form.is_valid():
        try:
            item = services.publish_announcement(user, **form.cleaned_data)
        except ValidationError as error:
            form.add_error(None, error)
        else:
            return redirect(reverse("notifications") + f"#announcement-{item.pk}")
    return render(
        request,
        "notifications/announcement_form.html",
        {
            "form": form,
            "operator": True,
            "has_groups": form.fields["group"].queryset.exists(),
        },
    )


@never_cache
@login_required
@require_GET
def feed(request):
    user = selectors.actor(request.user)
    personal = selectors.notifications(user)
    news = selectors.announcements(user)
    allowed = {"page", "news_page", "unread", "kind"}
    if set(request.GET) - allowed or any(len(request.GET.getlist(key)) != 1 for key in request.GET):
        return bad_request(request)
    unread = request.GET.get("unread", "")
    kind = request.GET.get("kind", "")
    if unread not in {"", "1"} or kind not in {"", "schedule", "request", "personal"}:
        return bad_request(request)
    unread_count = (
        personal.filter(read_at__isnull=True).count() + news.filter(is_read=False).count()
    )
    if unread:
        personal = personal.filter(read_at__isnull=True)
        news = news.filter(is_read=False)
    if kind:
        personal = personal.filter(kind=kind)
    try:
        items = page(personal, request.GET.get("page", "1"))
        announcements = page(news, request.GET.get("news_page", "1"))
    except ValueError:
        return bad_request(request)
    links = {}
    for name, listing, param in [("personal", items, "page"), ("news", announcements, "news_page")]:
        for direction, available, number in [
            ("prev", listing.has_previous(), listing.number - 1),
            ("next", listing.has_next(), listing.number + 1),
        ]:
            if available:
                query = request.GET.dict()
                query[param] = number
                links[name + "_" + direction] = "?" + urlencode(query)
    return render(
        request,
        "notifications/feed.html",
        {
            "operator": user.role == User.Role.OPERATOR,
            "items": items,
            "announcements": announcements,
            "unread_count": unread_count,
            "selected_kind": kind,
            "unread": unread,
            "links": links,
        },
    )


@never_cache
@login_required
@require_POST
def read_notification(request, notification_id):
    services.mark_notification(request.user, notification_id)
    return redirect("notifications")


@never_cache
@login_required
@require_POST
def read_all(request):
    services.mark_all_read(request.user)
    return redirect("notifications")


@never_cache
@login_required
@require_POST
def read_announcement(request, announcement_id):
    services.mark_announcement(request.user, announcement_id)
    return redirect("notifications")


@never_cache
@login_required
@require_GET
def open_target(request, notification_id):
    item = get_object_or_404(selectors.notifications(request.user), pk=notification_id)
    if item.target_type == "request":
        from apps.requests.selectors import operator_requests, student_requests

        operator = selectors.actor(request.user).role == User.Role.OPERATOR
        visible = operator_requests(request.user) if operator else student_requests(request.user)
        target = get_object_or_404(visible, pk=item.target_id)
        return redirect(
            "operator-request-detail" if operator else "request-detail", request_id=target.pk
        )
    if item.target_type == "personal":
        target = get_object_or_404(selectors.personal_deadlines(request.user), pk=item.target_id)
        return redirect(
            reverse("deadlines") + "?focus=" + str(target.pk) + "#deadline-" + str(target.pk)
        )
    if item.target_type == "schedule":
        from apps.schedule.models import Lesson
        from apps.schedule.selectors import MOSCOW

        target = get_object_or_404(
            Lesson.objects.filter(
                offering_id__in=own_enrollments(request.user)
                .filter(student__group_id=F("offering__group_id"))
                .values("offering_id")
            ),
            pk=item.target_id,
        )
        return redirect(
            reverse("schedule")
            + "?"
            + urlencode(
                {
                    "date": timezone.localdate(target.starts_at, timezone=MOSCOW).isoformat(),
                    "view": "day",
                }
            )
        )
    raise Http404


@never_cache
@login_required
@require_http_methods(["GET", "POST"])
def deadlines(request):
    items = selectors.personal_deadlines(request.user)
    focus = None
    if request.GET.get("focus"):
        try:
            focus = get_object_or_404(items, pk=uuid.UUID(request.GET["focus"]))
        except ValueError as error:
            raise Http404 from error
    form = PersonalDeadlineForm(request.POST if request.method == "POST" else None)
    if request.method == "POST" and form.is_valid():
        services.add_personal_deadline(request.user, **form.cleaned_data)
        return redirect("deadlines")
    if focus:
        items = items.filter(pk=focus.pk)
    try:
        active = page(items.filter(completed_at__isnull=True), request.GET.get("active_page", "1"))
        completed = page(
            items.filter(completed_at__isnull=False), request.GET.get("completed_page", "1")
        )
    except ValueError:
        return bad_request(request)
    links = {}
    for name, listing in [("active", active), ("completed", completed)]:
        for direction, available, number in [
            ("prev", listing.has_previous(), listing.number - 1),
            ("next", listing.has_next(), listing.number + 1),
        ]:
            if available:
                query = request.GET.dict()
                query[name + "_page"] = number
                links[name + "_" + direction] = "?" + urlencode(query)
    return render(
        request,
        "notifications/deadlines.html",
        {
            "form": form,
            "active_deadlines": active,
            "completed_deadlines": completed,
            "today": timezone.localdate(timezone=ZoneInfo("Europe/Moscow")),
            "focus": focus,
            "links": links,
        },
    )


@never_cache
@login_required
@require_POST
def deadline_state(request, deadline_id):
    if request.POST.get("completed") not in {"yes", "no"}:
        selectors.personal_deadlines(request.user)
        return bad_request(request)
    services.set_personal_deadline_state(
        request.user, deadline_id, completed=request.POST["completed"] == "yes"
    )
    return redirect("deadlines")
