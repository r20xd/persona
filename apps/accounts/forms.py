from django import forms
from django.contrib.auth.forms import AuthenticationForm

from .persona import LABELS, OPTIONS, PROGRESS


class LoginForm(AuthenticationForm):
    error_messages = {
        "invalid_login": "Не удалось войти. Проверьте логин и пароль.",
        "inactive": "Не удалось войти. Проверьте логин и пароль.",
    }


class PersonaForm(forms.Form):
    strengths = forms.MultipleChoiceField(
        label=LABELS["strengths"],
        choices=OPTIONS["strengths"],
        required=False,
        widget=forms.CheckboxSelectMultiple,
    )
    interests = forms.MultipleChoiceField(
        label=LABELS["interests"],
        choices=OPTIONS["interests"],
        required=False,
        widget=forms.CheckboxSelectMultiple,
    )
    skills = forms.MultipleChoiceField(
        label=LABELS["skills"],
        choices=OPTIONS["skills"],
        required=False,
        widget=forms.CheckboxSelectMultiple,
    )
    activities = forms.MultipleChoiceField(
        label=LABELS["activities"],
        choices=OPTIONS["activities"],
        required=False,
        widget=forms.CheckboxSelectMultiple,
    )
    goal = forms.CharField(
        label="Одна цель на семестр",
        max_length=160,
        required=False,
        widget=forms.TextInput(attrs={"placeholder": "Например, выступить на дебатах"}),
    )
    progress = forms.TypedChoiceField(label="Мой прогресс", choices=PROGRESS, coerce=int, initial=0)

    def clean(self):
        values = super().clean()
        for field in OPTIONS:
            if len(values.get(field, [])) > 8:
                self.add_error(field, "Выберите не более 8 вариантов.")
        if not values.get("goal"):
            values["progress"] = 0
        return values
