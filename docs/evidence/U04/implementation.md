# U04 — отчёт исполнителя

Изменения подготовлены для независимого ревью; commit/push/public deploy исполнитель не выполнял. Источник палитры colors.jpg не изменялся и не включался в assets.

## Результат

- Общие semantic tokens: ink #121524, muted #384C65, primary #485F88, accent-soft #9DACCC, line #C0C9DB; нейтральные white/paper/surface-soft. Старые зелёные брендовые оттенки заменены во всех CSS, mark.svg контрастный navy на светлом фоне. Оттенки ошибок/предупреждений сохранены по семантике. Существующая компоновка сохранена.
- Основная навигация «Успеваемость», grades содержит только итоги/работы и semester filter. Сессия расположена в schedule/session.html; schedule tabs День/Неделя/Сессия. reverse('session') ведёт /schedule/session/, /session/ — авторизованный alias session-legacy с тем же view/template и прежней валидацией/scoping. Источник занятий/схема/селекторы не менялись.
- requests list студента/оператора и notifications GET-формы помечены data-auto-filter. Local filters.js проверяет GET, слушает change только select/checkbox и вызывает native requestSubmit. Скрывает fallback submit после установки listener. Подсказка связана с контролами через aria-describedby с сохранением прежних дескрипторов. Нет автоматического POST. Формы не содержат параметров страниц, поэтому изменение сбрасывает все пагинации. Без JS остаётся рабочая кнопка.
- Проверка выявила восстановление select Chromium после Back независимо от серверного URL. pageshow сбрасывает только помеченные GET-формы к серверным defaults; browser back тест теперь проходит.
- Единственная shared concept_notice в обоих independent base: «Конкурсный концепт · Неофициальный сервис». Повторы login/errors/footer/preview удалены. Preview сохраняет объяснение отсутствия входа/данных. Ready request сообщает «Заявка обработана. Подробности в истории ниже.»; fictional records не менялись.

## Проверки

Реальные PostgreSQL 17.11 и Chromium 156 / Playwright v1248; .venv Python 3.13.14, Django 5.2.19 из существующего lock. Проверки выполнялись в собственной временной QA среде, не на пользовательской dev5432/8000.

- Targeted run: tests/test_ui_revision_browser.py, test_grades.py, test_schedule.py, test_grades_browser.py, test_requests_browser.py, test_dashboard_browser.py, test_preview_browser.py и test_keyboard_validation_and_reflow: 36 passed, 2 failed только из-за оставшегося прежнего перехода grades→session в dashboard browser test.
- Этот тест обновлён на grades→главная навигация Расписание→вкладка Сессия. Финальный повтор U04 browser + dashboard browser + keyboard validation/reflow: **6 passed, 1 warning, 30.73s**. Предыдущее ошибочное ожидание malformed term=invalid 400 в новом тесте исправлено на существующий 404; доступ/negative checks не ослаблялись.
- U04 browser на 360/1440: login/home/local-user/grades/day/week/canonical+legacy session/student+operator lists/notifications/preview; horizontal overflow отсутствует; ровно одна видимая отметка концепта на каждой проверенной странице; корректна активная навигация и отсутствие exam UI в grades.
- Реальные auto GET status фильтры дают соответствующие карточки/empty states и URL без page; Back восстанавливает selected status. Notifications kind+unread и снятие checkbox сохраняют комбинацию/сбрасывают page/news_page/deadline_page. read_at count до/после GET неизменен. Operator GET фильтр не посылает POST; смена operator status dropdown не отправляет форму. JS-off оба фильтра остаются ручными и рабочими.
- Targeted server tests проверяют canonical reverse, guest auth, оба адреса, template relocation, invalid/duplicate/foreign term и запрет POST; существующие проверки оценок/расписания прошли.
- Keyboard/contrast/reflow проверка из Q04 прошла без снижения порога 4.5; focus на тёмной навигации имеет светлый accent-soft. Визуально просмотрены home1440/session360; поля/текст/статусы читаемы.
- `ruff check .`: passed; `ruff format --check .`: 250 files already formatted; `git diff --check`: passed.
- Django check: no issues. Отдельная собственная temporary DB: migrate passed; makemigrations --check --dry-run passed, DB удалена. Первый запуск makemigrations на уже удалённой pytest DB дал warning о недоступной history; повтор на реальной временной БД закрыл это ограничение.
- Full suite намеренно оставлен root после code freeze. Единственный warning финального browser run — upstream PytestRemovedIn10Warning session-scoped fixture.

## Скриншоты

14 новых PNG: login/home/local-user/session/requests-filter/notifications-filter/operator-filter, каждый 360/1440. Старые evidence PNG не перезаписаны. Screenshots full_page фиксируют настоящий рендер; fixed bottom nav в full-page снимке видна на исходной позиции viewport.

## Skill и ограничения

Прочитаны Taste Skill и references/system.md; применены consistency/colors/accessibility в существующем Django кабинете. Marketing hero/effects/kit не входят в scope. Фактически вызван `node /home/local-user/.codex/plugins/cache/taste-skill/taste-skill/2.5.1/skills/taste-skill/scripts/gate.mjs` без аргументов из корня репозитория; exit0 и реальный вывод **GATE: OFF (no build active)**. Полный marketing checker не выполнялся: отсутствует `.taste-skill/build.json`; private authenticated app проверен реальным Playwright, marketing gate не является свидетельством приёмки кабинета. Публичный доступ/телефон/сети России здесь не проверялись.

## Передача QA

Private state /tmp/u04-qa-state.json (0600), wrapper /tmp/u04-qa.py. PostgreSQL оставлен root для full suite; browser/static/temporary databases fixtures после своих тестов очищены. В state сохранены exact CID/image identity/anonymous volume/network IDs; owner+project labels, единственный container attachment/endpoint проверены. /tmp/u04-capture-identity.py повторяет проверку; /tmp/u04-cleanup.py предназначен для точной уборки только этих ресурсов после root suite и проверяет отсутствие. Он не запускался до передачи. Служебные пароли в отчёт не включены. Anonymous volume появился из PostgreSQL image VOLUME; это учтено в exact cleanup, не объявляется общей гарантией безопасности helper.

## Финальная правка после root review

- Для login, request form/filter, notification filter, semester и date controls добавлен единый token `--control-border:#485F88`; декоративные рамки карточек остаются `--line`. Изменялся только цвет рамок, размеры/компоновка сохранены.
- Статическая подпись «Вымышленный университет» удалена из story-fine двух login templates; название университета и честное описание ограничений preview сохранены. Записи БД не менялись.
- Новый browser assertion измеряет фактические computed CSS foreground/background/border colors видимых input/select/textarea: border against nearest opaque outside surface ≥3:1, текст ≥4.5:1. Проверены login, student request form/filter, notification filter, semester/date, disabled preview fields на360/1440.
- Финальный targeted U04 browser и keyboard/validation/reflow: **4 passed, 2 warnings, 21.08s**; 14 U04 screenshots обновлены после изменения рамок. Один warning — upstream pytest fixture; второй был SyntaxWarning `\d` в строке нового проверочного JS, исправлен эквивалентным `[0-9]` после прогона (поведение assertion не меняется). Root full suite проверит итоговый исходник.
- Финальные Ruff check, format check (250 files) и git diff --check чистые. Code freeze повторно передан root.

## Test-only correction после root full suite

Root сообщил фактический полный прогон: 396 passed, 1 failed, 1 warning, 215.77s, inputs_unchanged=true. Единственная ошибка — прежнее ожидание строки «настоящий подписанный документ» в tests/test_requests.py::test_transition_table_versions_and_public_history. По разрешению root обновлён только этот текстовый assert: ready page содержит «Заявка обработана», единственную class=concept-notice и «Неофициальный сервис». Остальные проверки истории, статусов и ролей сохранены; application/CSS/JS/templates не менялись.

Повтор всего tests/test_requests.py на собственном PostgreSQL: **37 passed, 4.29s**. Ruff check passed; Ruff format --check: 250 files already formatted; git diff --check passed. Полный suite исполнитель не повторял; независимый root requests/check/migrations и последующий cleanup остаются у root. Code freeze сохранён.


## Независимая финальная проверка и cleanup

По сообщению root: исправленный tests/test_requests.py независимо **37 passed, 3.67s**; Django check — 0 issues, makemigrations — No changes на existing test_u04_root. Дополнительно проверены canonical/legacy session: guest GET и valid-CSRF guest POST —302, operator GET —403/no-store. Результат root — final-checks-independent.json. После full suite application не менялся; root визуально просмотрел home1440/session360/login1440.

После разрешения root exact cleanup успешно удалил только собственные container/anonymous volume/network, отсутствие проверено. Private state с QA credentials удалён. Подробности без секретов — cleanup.md. Код/templates/static/tests не менялись в ходе cleanup.
