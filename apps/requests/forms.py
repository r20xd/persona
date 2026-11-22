from django import forms

from .models import ServiceRequest


class ApplicationForm(forms.Form):
    purpose = forms.ChoiceField(label="Назначение справки", choices=ServiceRequest.Purpose.choices)
    comment = forms.CharField(
        label="Пояснение", required=False, max_length=1000, widget=forms.Textarea(attrs={"rows": 4})
    )
    submission_key = forms.UUIDField(widget=forms.HiddenInput)


class CancelForm(forms.Form):
    expected_version = forms.IntegerField(min_value=1, widget=forms.HiddenInput)


class TransitionForm(CancelForm):
    desired_status = forms.ChoiceField(
        label="Новый статус",
        choices=[("in_progress", "В работу"), ("ready", "Готова"), ("rejected", "Отклонить")],
    )
    comment = forms.CharField(
        label="Комментарий для студента",
        required=False,
        max_length=1000,
        widget=forms.Textarea(attrs={"rows": 3}),
    )

    def clean(self):
        data = super().clean()
        if data.get("desired_status") == "rejected" and not data.get("comment"):
            self.add_error("comment", "Укажите причину отказа.")
        return data


class RequestMessageForm(forms.Form):
    body = forms.CharField(
        label="Сообщение",
        max_length=2000,
        help_text="До 2 000 символов.",
        widget=forms.Textarea(attrs={"rows": 4}),
    )
    submission_key = forms.UUIDField(widget=forms.HiddenInput)
