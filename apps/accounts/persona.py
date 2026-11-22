"""Student-selected vocabulary; no personality inference or external AI."""

from django.core.exceptions import ValidationError

OPTIONS = {
    "strengths": [
        ("speaking", "Выступать"),
        ("analysis", "Анализировать"),
        ("ideas", "Придумывать"),
        ("organizing", "Организовывать"),
    ],
    "interests": [
        ("languages", "Языки"),
        ("diplomacy", "Дипломатия"),
        ("technology", "Технологии"),
        ("creativity", "Творчество"),
        ("economics", "Экономика"),
        ("culture", "Культура"),
        ("science", "Наука"),
        ("ecology", "Экология"),
    ],
    "skills": [
        ("speaking", "Публичные выступления"),
        ("negotiation", "Переговоры"),
        ("research", "Исследования"),
        ("writing", "Письмо"),
        ("data", "Работа с данными"),
        ("teamwork", "Командная работа"),
    ],
    "activities": [
        ("debates", "Дебаты"),
        ("photo", "Фотография"),
        ("volleyball", "Волейбол"),
        ("music", "Музыка"),
        ("reading", "Чтение"),
        ("walking", "Прогулки"),
        ("theatre", "Театр"),
        ("volunteering", "Волонтёрство"),
    ],
}
LABELS = {
    "strengths": "Сильные стороны",
    "interests": "Интересы",
    "skills": "Хочу научиться",
    "activities": "Вне учёбы",
}
PROGRESS = [(n, f"{n}%") for n in (0, 25, 50, 75, 100)]


def validate_values(values):
    result, errors = {}, {}
    for field, choices in OPTIONS.items():
        value = values.get(field, [])
        allowed = dict(choices)
        if (
            not isinstance(value, list)
            or len(value) > 8
            or any(not isinstance(code, str) or code not in allowed for code in value)
        ):
            errors[field] = "Выберите не более 8 вариантов из списка."
        else:
            result[field] = list(dict.fromkeys(value))
    goal, progress = values.get("goal", ""), values.get("progress", 0)
    if not isinstance(goal, str) or len(goal) > 160:
        errors["goal"] = "Цель должна быть не длиннее 160 символов."
    else:
        result["goal"] = goal.strip()
    if type(progress) is not int or progress not in dict(PROGRESS):
        errors["progress"] = "Выберите отметку прогресса из списка."
    else:
        result["progress"] = progress if result.get("goal") else 0
    if errors:
        raise ValidationError(errors)
    return result


def card(persona):
    if persona is None:
        return None
    sections = [
        {
            "label": LABELS[field],
            "tags": [
                dict(choices)[code] for code in getattr(persona, field) if code in dict(choices)
            ],
        }
        for field, choices in OPTIONS.items()
    ]
    phrase_maps = {
        "strengths": {
            "speaking": "Выступаю",
            "analysis": "Анализирую",
            "ideas": "Придумываю",
            "organizing": "Организую",
        },
        "interests": {
            "languages": "Увлекаюсь языками",
            "diplomacy": "Увлекаюсь дипломатией",
            "technology": "Увлекаюсь технологиями",
            "creativity": "Увлекаюсь творчеством",
            "economics": "Увлекаюсь экономикой",
            "culture": "Увлекаюсь культурой",
            "science": "Увлекаюсь наукой",
            "ecology": "Увлекаюсь экологией",
        },
        "skills": {
            "speaking": "Учусь выступать",
            "negotiation": "Учусь вести переговоры",
            "research": "Учусь исследовать",
            "writing": "Учусь писать",
            "data": "Учусь работать с данными",
            "teamwork": "Учусь работать в команде",
        },
    }
    parts = []
    for field, phrases in phrase_maps.items():
        selected = getattr(persona, field)
        if selected and selected[0] in phrases:
            parts.append(phrases[selected[0]])
    return {
        "sections": sections,
        "phrase": " · ".join(parts),
        "goal": persona.goal,
        "progress": persona.progress,
        "has_content": bool(persona.goal or any(item["tags"] for item in sections)),
    }
