from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET

from apps.accounts.selectors import own_profile
from apps.core.views import bad_request

from .selectors import study_context


@never_cache
@login_required
@require_GET
def study(request):
    profile = own_profile(request.user)
    if set(request.GET) - {"term"} or any(
        len(request.GET.getlist(key)) != 1 for key in request.GET
    ):
        return bad_request(request)
    context = study_context(request.user, request.GET.get("term"))
    return render(request, "grades/study.html", {**context, "profile": profile})
