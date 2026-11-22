# AI03 — ERNIE Flash через OpenRouter

Пользователь выбрал бесплатный вариант baidu/ernie-5.5-flash-preview:free. TECH-03, SEC-02 и ARCHITECTURE §29. Исполнитель cat01 / gpt-6.1-sol low. Для точного хоста openrouter.ai отправлять max_tokens по карточке модели, сохраняя контракт остальных хостов. Проверить тело запроса на заглушке. Файлы исполнителя: apps/accounts/assistant.py, tests/test_assistant.py, implementation.md. Существующий ключ OrcaRouter нельзя использовать для OpenRouter. Реальный запрос после настройки отдельного ключа. Основной агент проверяет diff и тесты.
