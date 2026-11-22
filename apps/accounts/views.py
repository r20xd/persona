from django.conf import settings
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.middleware.csrf import rotate_token
from django.shortcuts import redirect, render
from django.utils.cache import patch_cache_control
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from apps.core.views import bad_request

from .cat import cat_card, own_cat
from .forms import LoginForm, PersonaForm
from .models import User
from .persona import OPTIONS, card
from .selectors import own_persona, own_profile
from .services import save_persona


def client_ip(request):
    return request.META.get("REMOTE_ADDR")


def lockout(request, response=None, credentials=None):
    response = render(request, "accounts/locked.html", status=429)
    response["Retry-After"] = "900"
    patch_cache_control(response, private=True, no_store=True)
    return response


def role_destination(user):
    if not user.is_active:
        raise PermissionDenied
    if user.role == User.Role.STUDENT:
        return "/"
    if user.role == User.Role.OPERATOR:
        return "/operator/requests/"
    raise PermissionDenied


@method_decorator(never_cache, name="dispatch")
class SignInView(LoginView):
    template_name = "accounts/login.html"
    authentication_form = LoginForm
    redirect_authenticated_user = False

    def get_success_url(self):
        destination = role_destination(self.request.user)
        # Django validates same-host and HTTPS restrictions on the submitted next.
        return self.get_redirect_url() or destination


def render_profile(request):
    try:
        profile = own_profile(request.user)
    except PermissionDenied:
        return render(
            request,
            "accounts/access_error.html",
            {"message": "Профиль недоступен. Обратитесь к организатору демонстрации."},
            status=403,
        )
    return render(
        request,
        "accounts/profile.html",
        {
            "profile": profile,
            "persona": card(own_persona(request.user)),
            "cat": cat_card(own_cat(request.user)),
        },
    )


@never_cache
@login_required
@require_GET
def profile(request):
    return render_profile(request)


@never_cache
@require_POST
def sign_out(request):
    logout(request)
    rotate_token(request)
    return redirect("login")


@never_cache
def csrf_failure(request, reason=""):
    return render(
        request,
        "accounts/access_error.html",
        {"message": "Срок защиты формы истёк. Обновите страницу и повторите действие."},
        status=403,
    )


@never_cache
@login_required
@require_http_methods(["GET", "POST"])
def persona_edit(request):
    profile = own_profile(request.user)
    persona = own_persona(request.user)
    initial = (
        {field: getattr(persona, field) for field in [*OPTIONS, "goal", "progress"]}
        if persona
        else {"progress": 0}
    )
    form = PersonaForm(request.POST if request.method == "POST" else None, initial=initial)
    if request.method == "POST" and form.is_valid():
        save_persona(actor=request.user, **form.cleaned_data)
        return redirect("profile")
    return render(request, "accounts/persona_edit.html", {"profile": profile, "form": form})


def require_student_directory():
    if not settings.ENABLE_STUDENT_DIRECTORY:
        raise Http404


@never_cache
@login_required
@require_GET
def students(request):
    require_student_directory()

    from django.core.paginator import EmptyPage, Paginator

    from .selectors import directory_profiles

    own_profile(request.user)
    query = request.GET.get("q", "")
    page = request.GET.get("page", "1")
    if (
        set(request.GET) - {"q", "page"}
        or any(len(request.GET.getlist(key)) != 1 for key in request.GET)
        or len(query) > 80
        or not page.isascii()
        or not page.isdecimal()
        or len(page) > 8
        or int(page) < 1
    ):
        return bad_request(request)
    paginator = Paginator(directory_profiles(request.user, query.strip()), 20)
    try:
        items = paginator.page(int(page))
    except EmptyPage:
        return bad_request(request)
    return render(request, "accounts/students.html", {"items": items, "query": query})


@never_cache
@login_required
@require_GET
def student_detail(request, profile_id):
    require_student_directory()

    from .selectors import directory_student

    current = own_profile(request.user)
    if request.GET:
        return bad_request(request)
    if profile_id == current.pk:
        return redirect("profile")
    return render(
        request, "accounts/student_detail.html", directory_student(request.user, profile_id)
    )
