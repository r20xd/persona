# PERS03 — убрать «Видно только вам»

Исполнитель gpt-6.1-sol/low, один writer. Читать AGENTS.md, TASK.md, ARCHITECTURE.md §25, PLAN.md §13. Пользователь просит не писать «Видно только вам»: удалить overline с этой фразой из persona_card.html, удалить только начальное предложение «Видно только вам.» из intro persona_edit.html. Остальной текст/приватность/данные/стили/поведение сохраняются.

Разрешено: apps/accounts/templates/accounts/persona_card.html, apps/accounts/templates/accounts/persona_edit.html, docs/evidence/PERS03/implementation.md. Без новых tests, серверных изменений, делегации и commit до accepted. Проверить diffcheck и отсутствие фразы в runtime templates (исторические evidence не менять). Кратко сообщить freeze. Родитель обновит local server и сделает review.
