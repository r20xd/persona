# U08 implementation

Удалены decorative div `persona-sculpture` с главной, последний относящийся к нему CSS блок и obsolete browser assertion. Shared brand/nav/title, P-фон входа, SVG и серверные контракты сохранены. Новые тесты не добавлены.

Проверки: Django preview check — no issues; Ruff для test_ui_revision_browser.py — passed; git diff --check — passed; `rg -n persona-sculpture apps static tests` — нет совпадений (exit1). Commit не выполнялся. Сборка статики/обновление сервера — родителю после независимого review.
