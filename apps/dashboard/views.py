from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect, render
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET

from apps.accounts.models import User
from apps.accounts.views import role_destination

from . import attention
from .selectors import dashboard_context


@never_cache
@login_required
@require_GET
def home(request):
    if request.user.role == User.Role.OPERATOR:
        return redirect(role_destination(request.user))
    try:
        context = dashboard_context(request.user)
        context["attention"] = attention.context(request.user, context["study"])
    except PermissionDenied:
        return render(
            request,
            "accounts/access_error.html",
            {"message": "Профиль недоступен. Обратитесь к организатору демонстрации."},
            status=403,
        )
    return render(request, "dashboard/home.html", context)
