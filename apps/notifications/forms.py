from django import forms

from .selectors import announcement_groups


class AnnouncementForm(forms.Form):
    group = forms.ModelChoiceField(
        label="Группа",
        queryset=None,
        empty_label="Выберите группу",
        error_messages={"invalid_choice": "Выберите закреплённую за вами группу."},
    )
    title = forms.CharField(label="Заголовок", max_length=200)
    body = forms.CharField(
        label="Текст объявления",
        max_length=10000,
        widget=forms.Textarea(attrs={"rows": 7}),
    )
    submission_key = forms.UUIDField(widget=forms.HiddenInput)

    def __init__(self, *args, user, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["group"].queryset = announcement_groups(user)
        self.fields["group"].label_from_instance = lambda group: group.code


class PersonalDeadlineForm(forms.Form):
    title = forms.CharField(
        label="Название задачи",
        max_length=200,
        widget=forms.TextInput(attrs={"placeholder": "Например, подготовить доклад"}),
    )
    due_date = forms.DateField(
        label="Дата дедлайна",
        input_formats=["%Y-%m-%d"],
        widget=forms.DateInput(attrs={"type": "date"}),
        error_messages={
            "required": "Укажите дату дедлайна.",
            "invalid": "Укажите корректную дату.",
        },
    )
