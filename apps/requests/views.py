import uuid

from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.core.paginator import EmptyPage, Paginator
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from apps.core.views import bad_request

from .forms import ApplicationForm, CancelForm, RequestMessageForm, TransitionForm
from .models import ServiceRequest
from .selectors import operator_requests, student_requests
from .services import (
    RequestConflict,
    RequestQuota,
    create_request,
    send_request_message,
    transition_request,
)


def valid_query(request, allowed):
    return not set(request.GET) - allowed and all(
        len(request.GET.getlist(key)) == 1 for key in request.GET
    )


def listing(request, operator=False):
    queryset = operator_requests(request.user) if operator else student_requests(request.user)
    if not valid_query(request, {"status", "page"}):
        return bad_request(request)
    status = request.GET.get("status", "")
    if status and status not in ServiceRequest.Status.values:
        return bad_request(request)
    if status:
        queryset = queryset.filter(status=status)
    page = request.GET.get("page", "1")
    if not page.isascii() or not page.isdigit() or len(page) > 8 or int(page) < 1:
        return bad_request(request)
    try:
        items = Paginator(queryset, 20).page(int(page))
    except EmptyPage as error:
        raise Http404 from error
    return render(
        request,
        "requests/list.html",
        {
            "items": items,
            "operator": operator,
            "statuses": ServiceRequest.Status.choices,
            "selected_status": status,
        },
    )


@never_cache
@login_required
@require_GET
def request_list(request):
    return listing(request)


@never_cache
@login_required
@require_GET
def operator_queue(request):
    return listing(request, operator=True)


@never_cache
@login_required
@require_http_methods(["GET", "POST"])
def new_request(request):
    student_requests(request.user)  # role check before rendering or processing a form
    if request.method == "GET":
        form = ApplicationForm(initial={"submission_key": uuid.uuid4()})
    else:
        form = ApplicationForm(request.POST)
        if form.is_valid():
            try:
                application = create_request(actor=request.user, **form.cleaned_data)
            except RequestConflict as error:
                form.add_error(None, str(error))
                return render(request, "requests/new.html", {"form": form}, status=409)
            except RequestQuota:
                form.add_error(
                    None, "Можно отправить до 30 новых заявок в час. Повторите через час."
                )
                response = render(request, "requests/new.html", {"form": form}, status=429)
                response["Retry-After"] = "3600"
                return response
            except ValidationError as error:
                form.add_error(None, error)
            else:
                return redirect("request-detail", request_id=application.pk)
    return render(request, "requests/new.html", {"form": form})


def render_detail(request, application, operator=False, form=None, status=200, message_form=None):
    if not valid_query(request, {"messages_page"}):
        return bad_request(request)
    page = request.GET.get("messages_page", "1")
    if not page.isascii() or not page.isdigit() or len(page) > 8 or int(page) < 1:
        return bad_request(request)
    try:
        conversation_page = Paginator(application.messages.all(), 20).page(int(page))
    except EmptyPage as error:
        raise Http404 from error
    if message_form is None:
        message_form = RequestMessageForm(initial={"submission_key": uuid.uuid4()})
    if form is None:
        if operator:
            form = TransitionForm(initial={"expected_version": application.version})
            choices = {
                "submitted": [("in_progress", "В работу")],
                "in_progress": [("ready", "Готова"), ("rejected", "Отклонить")],
            }
            form.fields["desired_status"].choices = choices.get(application.status, [])
        else:
            form = CancelForm(initial={"expected_version": application.version})
    return render(
        request,
        "requests/detail.html",
        {
            "application": application,
            "message_form": message_form,
            "conversation_page": conversation_page,
            "events": application.events.all(),
            "operator": operator,
            "form": form,
            "detail_url": reverse(
                "operator-request-detail" if operator else "request-detail",
                kwargs={"request_id": application.pk},
            ),
        },
        status=status,
    )


@never_cache
@login_required
@require_GET
def detail(request, request_id, operator=False):
    queryset = operator_requests(request.user) if operator else student_requests(request.user)
    application = get_object_or_404(queryset.select_related("student"), pk=request_id)
    return render_detail(request, application, operator)


@never_cache
@login_required
@require_POST
def change(request, request_id, operator=False):
    queryset = operator_requests(request.user) if operator else student_requests(request.user)
    application = get_object_or_404(queryset.select_related("student"), pk=request_id)
    form = TransitionForm(request.POST) if operator else CancelForm(request.POST)
    if form.is_valid():
        data = form.cleaned_data
        if not operator:
            data["desired_status"] = "cancelled"
        try:
            transition_request(actor=request.user, request_id=request_id, **data)
        except RequestConflict as error:
            form.add_error(None, str(error))
            application.refresh_from_db()
            return render_detail(request, application, operator, form, status=409)
        except ValidationError as error:
            form.add_error(None, error)
        else:
            return redirect(
                "operator-request-detail" if operator else "request-detail", request_id=request_id
            )
    return render_detail(request, application, operator, form)


@never_cache
@login_required
@require_POST
def message_send(request, request_id, operator=False):
    queryset = operator_requests(request.user) if operator else student_requests(request.user)
    application = get_object_or_404(queryset.select_related("student"), pk=request_id)
    form = RequestMessageForm(request.POST)
    status = 200
    if form.is_valid():
        try:
            send_request_message(
                actor=request.user, request_id=request_id, operator=operator, **form.cleaned_data
            )
        except RequestConflict as error:
            form.add_error(None, str(error))
            status = 409
        except ValidationError as error:
            form.add_error(None, error)
        else:
            url = reverse(
                "operator-request-detail" if operator else "request-detail",
                kwargs={"request_id": request_id},
            )
            return redirect(url + "#conversation")
    return render_detail(request, application, operator, status=status, message_form=form)
