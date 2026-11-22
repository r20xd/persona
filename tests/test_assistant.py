"""AI01: isolated chat history and a bounded, injectable provider boundary. No paid calls."""

import io
import json
from unittest.mock import Mock, patch
from urllib.error import URLError

import pytest
from django.test import Client, override_settings

from apps.accounts.assistant import (
    MAX_CONTEXT_CHARS,
    MAX_REPLY,
    MAX_RESPONSE_BYTES,
    SESSION_KEY,
    SYSTEM_INSTRUCTION,
    NoRedirect,
    ProviderUnavailable,
    ReplyTooLong,
    complete,
    configured,
)
from tests.test_accounts import identities  # noqa: F401

pytestmark = pytest.mark.django_db
CONNECTED = {
    "AI_API_KEY": "unit-private-provider-key",
    "AI_API_URL": "https://provider.invalid/chat/completions",
    "AI_MODEL": "unit-model",
}


@pytest.fixture(autouse=True)
def disconnected_by_default():
    with override_settings(AI_API_KEY="", AI_API_URL="", AI_MODEL=""):
        yield


def test_disconnected_no_request_or_fake_reply(client, identities):  # noqa: F811
    client.force_login(identities[0][0])
    with patch("apps.accounts.assistant.build_opener") as transport:
        response = client.get("/assistant/")
        assert response.status_code == 200 and "no-store" in response["Cache-Control"]
        assert "ИИ пока не подключён" in response.text
        response = client.post("/assistant/", {"message": "Мой вопрос"})
        assert response.status_code == 200 and "Текст сохранён в поле" in response.text
        assert "Мой вопрос" in response.text
        assert 'class="assistant-message' not in response.text
        assert SESSION_KEY not in client.session
        transport.assert_not_called()


@override_settings(**CONNECTED)
def test_success_real_boundary_context_cap_and_clear(client, identities):  # noqa: F811
    user = identities[0][0]
    client.force_login(user)
    with patch(
        "apps.accounts.assistant.complete", return_value="Ответ тестового провайдера"
    ) as provider:
        for index in range(8):
            response = client.post("/assistant/", {"message": f"Вопрос {index}"})
            assert response.status_code == 302 and response.url == "/assistant/#latest"
            sent = provider.call_args.args[0]
            assert len(sent) <= 11
            assert all(set(item) == {"role", "content"} for item in sent)
            assert not any(user.studentprofile.full_name in item["content"] for item in sent)
    saved = client.session[SESSION_KEY]
    assert saved["owner"] == user.pk and len(saved["messages"]) == 12
    assert saved["messages"][-1]["role"] == "assistant"
    assert all(item["role"] != "system" for item in saved["messages"])
    assert SYSTEM_INSTRUCTION not in str(saved)
    response = client.get("/assistant/")
    assert "Ответ тестового провайдера" in response.text
    assert SYSTEM_INSTRUCTION not in response.text
    assert CONNECTED["AI_API_KEY"] not in response.text and CONNECTED["AI_API_KEY"] not in str(
        saved
    )
    response = client.post("/assistant/clear/")
    assert response.status_code == 302 and SESSION_KEY not in client.session


@override_settings(**CONNECTED)
def test_provider_error_invalid_input_and_escaping(client, identities):  # noqa: F811
    client.force_login(identities[0][0])
    with patch("apps.accounts.assistant.complete", side_effect=ProviderUnavailable) as provider:
        response = client.post("/assistant/", {"message": "Сохранить этот текст"})
        assert response.status_code == 200 and "Сохранить этот текст" in response.text
        assert "сейчас не отвечает" in response.text and SESSION_KEY not in client.session
        provider.reset_mock()
        for text in ("", " ", "x" * 2001):
            response = client.post("/assistant/", {"message": text})
            assert response.status_code == 200 and response.context["form"].errors
        provider.assert_not_called()
    with patch("apps.accounts.assistant.complete", return_value="<script>evil</script>"):
        client.post("/assistant/", {"message": "<b>Вопрос</b>"})
    response = client.get("/assistant/")
    assert "&lt;script&gt;" in response.text and "&lt;b&gt;" in response.text
    assert "<script>evil</script>" not in response.text
    before = client.session[SESSION_KEY]
    with patch("apps.accounts.assistant.complete", side_effect=ProviderUnavailable):
        client.post("/assistant/", {"message": "Повтор"})
    assert client.session[SESSION_KEY] == before
    with patch("apps.accounts.assistant.complete", side_effect=ReplyTooLong):
        response = client.post("/assistant/", {"message": "Сохранить длинный вопрос"})
    assert response.status_code == 200 and "Ответ слишком длинный" in response.text
    assert "Сохранить длинный вопрос" in response.text
    assert client.session[SESSION_KEY] == before


@override_settings(**CONNECTED)
def test_owner_boundaries_roles_csrf_and_methods(client, identities):  # noqa: F811
    students, operator = identities
    first, second = students[:2]
    client.force_login(first)
    with patch("apps.accounts.assistant.complete", return_value="Личный ответ"):
        client.post("/assistant/", {"message": "Личный вопрос"})
    foreign = client.session[SESSION_KEY]
    second_client = Client()
    second_client.force_login(second)
    session = second_client.session
    session[SESSION_KEY] = foreign
    session.save()
    assert "Личный ответ" not in second_client.get("/assistant/").text
    with patch("apps.accounts.assistant.complete", return_value="Второй ответ") as provider:
        second_client.post("/assistant/", {"message": "Второй вопрос", "owner": first.pk})
        assert provider.call_args.args[0] == [{"role": "user", "content": "Второй вопрос"}]
    second_client.post("/assistant/clear/")
    assert client.session[SESSION_KEY] == foreign
    assert client.get("/assistant/clear/").status_code == 405
    assert client.put("/assistant/").status_code == 405
    assert client.get(f"/assistant/{second.pk}/").status_code == 404
    csrf = Client(enforce_csrf_checks=True)
    csrf.force_login(first)
    assert csrf.post("/assistant/", {"message": "Вопрос"}).status_code == 403
    assert csrf.post("/assistant/clear/").status_code == 403
    client.force_login(operator)
    assert client.get("/assistant/").status_code == 403
    assert client.post("/assistant/clear/").status_code == 403
    client.logout()
    assert client.get("/assistant/").status_code == 302


@pytest.mark.parametrize(
    "url,allowed",
    [
        ("https://provider.invalid/v1/chat/completions", True),
        ("http://127.0.0.1:1234/chat", True),
        ("http://[::1]:1234/chat", True),
        ("http://localhost/chat", True),
        ("http://provider.invalid/chat", False),
        ("file:///etc/passwd", False),
        ("https://key@provider.invalid/chat", False),
        ("https://provider.invalid:bad/chat", False),
        ("https://provider.invalid/chat#secret", False),
    ],
)
def test_configuration_url_boundary(url, allowed):
    with override_settings(**{**CONNECTED, "AI_API_URL": url}):
        assert configured() is allowed


class Response(io.BytesIO):
    status = 200


def test_adapter_contract_and_bounded_success():
    response = Response(
        json.dumps({"choices": [{"message": {"content": "Реальный текст ответа"}}]}).encode()
    )
    opener = Mock()
    opener.open.return_value = response
    with (
        override_settings(**CONNECTED),
        patch("apps.accounts.assistant.build_opener", return_value=opener) as factory,
    ):
        assert complete([{"role": "user", "content": "Вопрос"}]) == "Реальный текст ответа"
    request = opener.open.call_args.args[0]
    assert (
        request.method == "POST"
        and request.get_header("Authorization") == "Bearer " + CONNECTED["AI_API_KEY"]
    )
    assert opener.open.call_args.kwargs["timeout"] <= 40
    payload = json.loads(request.data)
    assert payload == {
        "model": "unit-model",
        "messages": [
            {"role": "system", "content": SYSTEM_INSTRUCTION},
            {"role": "user", "content": "Вопрос"},
        ],
        "max_completion_tokens": 4096,
        "stream": False,
    }
    assert isinstance(factory.call_args.args[0], NoRedirect)
    assert factory.call_args.args[0].redirect_request(None, None, 302, None, None, None) is None


@pytest.mark.parametrize(
    "url,token_parameter,model",
    [
        (
            "https://api.orcarouter.ai/v1/chat/completions",
            "max_tokens",
            "deepseek/deepseek-v4-flash-free",
        ),
        (
            "https://api.orcarouter.ai.provider.invalid/v1/chat/completions",
            "max_completion_tokens",
            "deepseek/deepseek-v4-flash-free",
        ),
        (
            "https://provider.invalid/api.orcarouter.ai/chat/completions",
            "max_completion_tokens",
            "deepseek/deepseek-v4-flash-free",
        ),
        (
            "https://openrouter.ai/api/v1/chat/completions",
            "max_tokens",
            "baidu/ernie-5.5-flash-preview:free",
        ),
    ],
)
def test_router_token_contract_uses_exact_parsed_host(url, token_parameter, model):
    messages = [{"role": "user", "content": "Только введённый вопрос"}]
    response = Response(
        json.dumps({"choices": [{"message": {"content": "Ответ stub-провайдера"}}]}).encode()
    )
    opener = Mock()
    opener.open.return_value = response
    with (
        override_settings(**{**CONNECTED, "AI_API_URL": url, "AI_MODEL": model}),
        patch("apps.accounts.assistant.build_opener", return_value=opener) as factory,
    ):
        assert complete(messages) == "Ответ stub-провайдера"
    opener.open.assert_called_once()
    request = opener.open.call_args.args[0]
    assert request.full_url == url and request.method == "POST"
    assert request.get_header("Authorization") == "Bearer " + CONNECTED["AI_API_KEY"]
    assert 0 < opener.open.call_args.kwargs["timeout"] <= 40
    assert json.loads(request.data) == {
        "model": model,
        "messages": [{"role": "system", "content": SYSTEM_INSTRUCTION}, *messages],
        token_parameter: 4096,
        "stream": False,
    }
    assert isinstance(factory.call_args.args[0], NoRedirect)


@pytest.mark.parametrize(
    "body",
    [
        b"invalid-json",
        b"[]",
        b'{"choices":[]}',
        b"x" * (MAX_RESPONSE_BYTES + 1),
        json.dumps({"choices": [{"message": {"content": ""}}]}).encode(),
        json.dumps({"choices": [{"message": {"content": "x" * (MAX_REPLY + 1)}}]}).encode(),
        json.dumps({"choices": [{"message": {"content": CONNECTED["AI_API_KEY"]}}]}).encode(),
    ],
)
def test_adapter_rejects_invalid_or_unsafe_output(body):
    opener = Mock()
    opener.open.return_value = Response(body)
    with (
        override_settings(**CONNECTED),
        patch("apps.accounts.assistant.build_opener", return_value=opener),
    ):
        with pytest.raises(ProviderUnavailable):
            complete([{"role": "user", "content": "Вопрос"}])


def test_adapter_disconnected_and_network_failure():
    with patch("apps.accounts.assistant.build_opener") as factory:
        with pytest.raises(ProviderUnavailable):
            complete([])
        factory.assert_not_called()
    with override_settings(**CONNECTED), patch("apps.accounts.assistant.build_opener") as factory:
        factory.return_value.open.side_effect = URLError("private raw provider detail")
        with pytest.raises(ProviderUnavailable):
            complete([])


@pytest.mark.parametrize(
    "url,token_parameter",
    [
        ("https://provider.invalid/chat/completions", "max_completion_tokens"),
        ("https://openrouter.ai/api/v1/chat/completions", "max_tokens"),
    ],
)
def test_length_fragments_preserve_word_and_markdown_boundaries(url, token_parameter):
    original = [{"role": "user", "content": "Учебный вопрос"}]
    parts = ("Сло", "во **важ", "но** с пробелом. ")
    opener = Mock()
    opener.open.side_effect = [
        Response(
            json.dumps(
                {
                    "choices": [
                        {
                            "message": {"content": text},
                            "finish_reason": "stop" if index == 2 else "length",
                        }
                    ]
                }
            ).encode()
        )
        for index, text in enumerate(parts)
    ]
    with (
        override_settings(**{**CONNECTED, "AI_API_URL": url}),
        patch("apps.accounts.assistant.build_opener", return_value=opener),
    ):
        assert complete(original) == "Слово **важно** с пробелом."
    assert opener.open.call_count == 3
    payloads = [json.loads(call.args[0].data) for call in opener.open.call_args_list]
    system = {"role": "system", "content": SYSTEM_INSTRUCTION}
    assert payloads[0]["messages"] == [system, *original]
    for index in (1, 2):
        sent = payloads[index]["messages"]
        assert sent[:2] == [system, *original]
        assert sent[2] == {"role": "assistant", "content": "".join(parts[:index])}
        assert sent[3]["role"] == "user" and "Не повторяй" in sent[3]["content"]
        assert payloads[index][token_parameter] == 4096
    assert original == [{"role": "user", "content": "Учебный вопрос"}]


def test_unfinished_fragments_fail_closed_and_large_context_keeps_latest_tail():
    for final in (
        {"finish_reason": "length", "message": {"content": "Ещё текст"}},
        {"finish_reason": "stop", "message": {"content": ""}},
        {"finish_reason": "content_filter", "message": {"content": "Скрыто"}},
        {"error": {"message": "private error"}, "message": {"content": "Не успех"}},
    ):
        opener = Mock()
        partial = {"finish_reason": "length", "message": {"content": "Часть "}}
        opener.open.side_effect = [
            Response(json.dumps({"choices": [choice]}).encode())
            for choice in (partial, partial, final)
        ]
        with (
            override_settings(**CONNECTED),
            patch("apps.accounts.assistant.build_opener", return_value=opener),
        ):
            with pytest.raises(ProviderUnavailable):
                complete([{"role": "user", "content": "Вопрос"}])
        assert opener.open.call_count == 3
    long_answer = "Начало" + "x" * 40000 + "Релевантное окончание"
    original = [
        {"role": "assistant", "content": "Сиротский старый ответ"},
        {"role": "user", "content": "Предыдущий вопрос"},
        {"role": "assistant", "content": long_answer},
        {"role": "user", "content": "Уточнение"},
    ]
    opener = Mock()
    opener.open.return_value = Response(
        json.dumps({"choices": [{"message": {"content": "Ответ"}}]}).encode()
    )
    with (
        override_settings(**CONNECTED),
        patch("apps.accounts.assistant.build_opener", return_value=opener),
    ):
        assert complete(original) == "Ответ"
    sent = json.loads(opener.open.call_args.args[0].data)["messages"]
    assert sent[0] == {"role": "system", "content": SYSTEM_INSTRUCTION}
    assert [message["role"] for message in sent[1:]] == ["user", "assistant", "user"]
    assert sum(len(message["content"]) for message in sent[1:]) <= MAX_CONTEXT_CHARS
    assert sent[2]["content"].endswith("Релевантное окончание")
    assert original[2]["content"] == long_answer


def test_assistant_markdown_semantics_and_untrusted_content():
    from html.parser import HTMLParser

    from apps.accounts.templatetags.assistant_markdown import assistant_markdown

    content = """# План подготовки

Абзац с **важным** и *акцентом*.

## Первые шаги

1. Прочитать тему
2. Решить задачу

### Проверка

- Ответить на вопрос
- Проверить решение

---

`<script>inline()</script>`

```python
print("<img src=https://remote.invalid/pixel>")
```

<script>alert("unsafe")</script>
<img src="https://remote.invalid/track" onerror="alert(1)">
<iframe src="https://remote.invalid/frame"></iframe>
<style>body{background:url(https://remote.invalid/style)}</style>

![Слежение **подпись**](https://remote.invalid/image.png)
[Удалённая ссылка](https://remote.invalid/target)
[Опасная ссылка](javascript:alert(1))
<https://remote.invalid/automatic>
https://remote.invalid/plain
"""

    class Tags(HTMLParser):
        def __init__(self):
            super().__init__()
            self.tags = []
            self.attributes = []

        def handle_starttag(self, tag, attrs):
            self.tags.append(tag)
            self.attributes.extend(attrs)

    rendered = str(assistant_markdown(content))
    parsed = Tags()
    parsed.feed(rendered)
    assert set(parsed.tags) <= {
        "h4",
        "h5",
        "h6",
        "p",
        "ol",
        "ul",
        "li",
        "strong",
        "em",
        "hr",
        "pre",
        "code",
    }
    assert {"h4", "h5", "h6", "ol", "ul", "strong", "em", "hr", "pre", "code"} <= set(parsed.tags)
    assert all(name in {"class", "start"} for name, _ in parsed.attributes)
    assert "<h4>План подготовки</h4>" in rendered
    assert "<strong>важным</strong>" in rendered and "<em>акцентом</em>" in rendered
    assert "&lt;script&gt;" in rendered and "&lt;img" in rendered
    assert "https://remote.invalid/plain" in rendered
    assert "Слежение подпись" in rendered and "Удалённая ссылка" in rendered
    assert "![Слежение" not in rendered and "[Удалённая ссылка]" not in rendered
    assert "https://remote.invalid/image.png" not in rendered
    assert "https://remote.invalid/target" not in rendered
    assert '<pre><code class="language-python">' in rendered
    assert "<code>&lt;script&gt;inline()&lt;/script&gt;</code>" in rendered


@override_settings(**CONNECTED)
def test_old_and_new_assistant_answers_render_but_history_and_user_input_stay_raw(
    client,
    identities,  # noqa: F811
):
    user = identities[0][0]
    client.force_login(user)
    old = "# Старый ответ\n\n**Сохранённая мысль**"
    session = client.session
    session[SESSION_KEY] = {
        "owner": user.pk,
        "messages": [{"role": "assistant", "content": old}],
    }
    session.save()
    assert "<h4>Старый ответ</h4>" in client.get("/assistant/").text
    question = '**Свой текст** <img src="https://remote.invalid/user">'
    reply = "## Новый ответ\n\n- *Первый шаг*\n- Второй шаг"
    with patch("apps.accounts.assistant.complete", return_value=reply) as provider:
        response = client.post("/assistant/", {"message": question})
    assert response.status_code == 302
    assert provider.call_args.args[0] == [
        {"role": "assistant", "content": old},
        {"role": "user", "content": question},
    ]
    assert client.session[SESSION_KEY]["messages"] == [
        {"role": "assistant", "content": old},
        {"role": "user", "content": question},
        {"role": "assistant", "content": reply},
    ]
    html = client.get("/assistant/").text
    assert "<h4>Старый ответ</h4>" in html and "<h5>Новый ответ</h5>" in html
    assert "<em>Первый шаг</em>" in html and "<ul>" in html
    assert "**Свой текст** &lt;img" in html and "<strong>Свой текст</strong>" not in html
    assert 'class="assistant-response"' in html
