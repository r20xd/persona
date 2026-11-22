"""Private, low-stakes cat game. Server owns rewards; browser owns animation."""

import json
import secrets
import time

from django import forms
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.templatetags.static import static
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_http_methods, require_POST

from .models import StudentCat, StudentProfile
from .selectors import own_profile

CHARACTERS = [("sleepy", "Соня"), ("scholar", "Отличник"), ("chaos", "Маленький хаос")]
ACCESSORIES = [
    ("none", "Без игрушки"),
    ("yarn", "Клубок"),
    ("ball", "Мячик"),
    ("mouse", "Игрушечная мышка"),
    ("fish", "Игрушечная рыбка"),
]
ITEMS = [
    {"id": "notebook", "name": "Тетрадка", "symbol": "▤"},
    {"id": "fish", "name": "Рыба", "symbol": "♓"},
    {"id": "calculator", "name": "Калькулятор", "symbol": "▦"},
    {"id": "slipper", "name": "Тапок", "symbol": "♧"},
    {"id": "diploma", "name": "Диплом по мурчанию", "symbol": "▱"},
    {"id": "pen", "name": "Ручка", "symbol": "✎"},
    {"id": "sausage", "name": "Колбаса", "symbol": "〰"},
    {"id": "headphones", "name": "Наушники"},
    {"id": "key", "name": "Ключ от аудитории"},
    {"id": "tea", "name": "Термос"},
    {"id": "alarm", "name": "Будильник"},
    {"id": "yarn", "name": "Клубок"},
]
MOODS = {
    "sleepy": ("Сон на первой паре", "Я не сплю. Я слушаю с закрытыми глазами."),
    "scholar": ("Теория мурчания", "Конспект съел. Материал усвоил."),
    "chaos": ("Прикладной тыгыдык", "Тапок в рюкзаке? Это мой научный руководитель."),
}
MIN_SECONDS = 2


def own_cat(user):
    return StudentCat.objects.filter(student=own_profile(user)).first()


def cat_card(cat):
    character = cat.character if cat else "sleepy"
    counts = {"idle": 6, "blink": 6, "jump": 8, "joy": 8, "stretch": 8, "yawn": 8, "surprise": 6}
    return {
        "sprite_frames": {pose: list(range(count)) for pose, count in counts.items()},
        "renderer": {
            "character": character,
            "source": static(f"images/cat-assistant-style48/{character}.png"),
            "native_grid": True,
            "counts": counts,
            "palette": [
                [0, 0, 0],
                [35, 49, 64],
                [47, 65, 86],
                [86, 124, 141],
                [126, 167, 177],
                [200, 217, 230],
                [250, 245, 235],
                [255, 251, 245],
                [247, 173, 200],
                [223, 139, 176],
                [201, 186, 219],
                [160, 187, 202],
            ],
            "rig": {
                "tail": [3, 27, 17, 18] if character == "chaos" else [34, 28, 11, 18],
                "eyes": [[16, 16, 9, 7], [27, 17, 8, 6]]
                if character == "chaos"
                else (
                    [[14, 15, 8, 8], [25, 15, 8, 8]]
                    if character == "scholar"
                    else [[14, 16, 9, 6], [26, 16, 9, 6]]
                ),
                "mouth": [21, 22, 10, 7] if character == "chaos" else [20, 21, 9, 6],
            },
        },
        "sprite_timing": {
            "idle": 180,
            "blink": 110,
            "jump": 100,
            "joy": 110,
            "stretch": 140,
            "yawn": 150,
            "surprise": 110,
        },
        "name": cat.name if cat else "Плюш",
        "character": cat.character if cat else "sleepy",
        "character_label": dict(CHARACTERS)[cat.character if cat else "sleepy"],
        "toys": list(cat.toys) if cat else [],
        "selected_toys": [
            {"id": code, "name": label}
            for code, label in ACCESSORIES[1:]
            if cat and code in cat.toys
        ],
        "completed": cat.completed if cat else 0,
        "subject": MOODS[cat.character if cat else "sleepy"][0],
        "quote": MOODS[cat.character if cat else "sleepy"][1],
    }


class CatForm(forms.Form):
    name = forms.CharField(label="Имя кота", max_length=24, initial="Плюш")
    character = forms.ChoiceField(label="Характер", choices=CHARACTERS)
    toys = forms.MultipleChoiceField(
        label="Игрушки кота",
        required=False,
        choices=ACCESSORIES[1:],
        widget=forms.CheckboxSelectMultiple,
    )

    def __init__(self, *args, completed=0, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["toys"].choices = ACCESSORIES[1 : min(completed, 4) + 1]

    def clean_toys(self):
        selected = set(self.cleaned_data["toys"])
        return [code for code, _ in ACCESSORIES[1:] if code in selected]


def save_cat(actor, values):
    profile = own_profile(actor)
    with transaction.atomic():
        # Lock the existing parent, serializing first creation and later reward/settings writes.
        StudentProfile.objects.select_for_update().get(pk=profile.pk)
        cat, _ = StudentCat.objects.get_or_create(student=profile)
        form = CatForm(values, completed=cat.completed)
        if not form.is_valid():
            raise ValidationError(form.errors)
        for field, value in form.cleaned_data.items():
            setattr(cat, field, value)
        cat.accessory = cat.toys[0] if cat.toys else "none"
        cat.save()
    return cat


@never_cache
@login_required
@require_http_methods(["GET", "POST"])
def cat_home(request):
    cat = own_cat(request.user)
    current = cat_card(cat)
    form = CatForm(
        request.POST if request.method == "POST" else None,
        initial=current,
        completed=current["completed"],
    )
    if request.method == "POST" and form.is_valid():
        try:
            save_cat(request.user, request.POST)
        except ValidationError:
            form.add_error("toys", "Эта игрушка пока закрыта. Обновите страницу.")
        else:
            return redirect("cat")
    return render(
        request,
        "accounts/cat.html",
        {
            "cat": current,
            "form": form,
            "saved": request.method == "GET",
            "accessories": [
                {"id": code, "name": label, "open": index <= current["completed"], "needed": index}
                for index, (code, label) in enumerate(ACCESSORIES)
                if index
            ],
            "cat_items": ITEMS,
        },
    )


@never_cache
@login_required
@require_POST
def cat_start(request):
    profile = own_profile(request.user)
    initial = secrets.SystemRandom().sample([item["id"] for item in ITEMS], 4)
    attempt = {
        "token": secrets.token_urlsafe(32),
        "student": profile.pk,
        "issued": time.time(),
        "initial": initial[:3],
        "replacement": initial[3],
    }
    request.session["cat_attempt"] = attempt
    return JsonResponse(
        {
            "token": attempt["token"],
            "initial": attempt["initial"],
            "replacement": attempt["replacement"],
            "seconds": 20,
        }
    )


@never_cache
@login_required
@require_POST
def cat_finish(request):
    profile = own_profile(request.user)
    try:
        if len(request.body) > 2048:
            raise ValueError
        data = json.loads(request.body)
        if not isinstance(data, dict) or set(data) != {"token", "collected", "swap_from"}:
            raise ValueError
        token = data["token"]
        if not isinstance(token, str) or len(token) > 100:
            raise ValueError
        attempt = request.session.get("cat_attempt", {})
        if (
            attempt.get("student") != profile.pk
            or token != attempt.get("token")
            or not MIN_SECONDS <= time.time() - attempt["issued"] <= 7200
        ):
            raise ValueError
        initial = attempt["initial"]
        collected = data["collected"]
        swapped = data["swap_from"]
        if (
            not isinstance(collected, list)
            or len(collected) != 3
            or any(not isinstance(item, str) for item in collected)
            or collected[0] not in initial
            or swapped not in initial
            or swapped == collected[0]
        ):
            raise ValueError
        expected = (set(initial) - {swapped}) | {attempt["replacement"]}
        if set(collected) != expected:
            raise ValueError
    except (ValueError, TypeError, KeyError):
        return JsonResponse(
            {"error": "Не удалось подтвердить сбор. Начните новый раунд."}, status=400
        )
    with transaction.atomic():
        StudentProfile.objects.select_for_update().get(pk=profile.pk)
        cat, _ = StudentCat.objects.get_or_create(student=profile)
        duplicate = cat.last_attempt == token
        if not duplicate:
            cat.completed += 1
            cat.last_attempt = token
            cat.save(update_fields=["completed", "last_attempt"])
        reward = ACCESSORIES[min(cat.completed, 4)][1]
    # Keep the receipt in session so a lost HTTP response can be retried without a second reward.
    return JsonResponse(
        {
            "completed": cat.completed,
            "reward": reward,
            "all_open": cat.completed >= 4,
            "duplicate": duplicate,
        }
    )
