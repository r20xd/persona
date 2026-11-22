# Q01 — матрица доступа и покрытие проверками

Итоговая серверная сверка Q01/Q02 выполнена от архивная-версия; новые проверки и результаты исполнителя — в docs/evidence/Q01-Q02/implementation.md. Независимая приёмка фиксируется отдельно основным агентом. Таблица описывает серверную политику; наличие строки не означает, что каждый вариант автоматически проверен во всех браузерах или на опубликованном сайте.

Обозначения: студент имеет собственный StudentProfile; учебные данные определяются персональным Enrollment. Совпадение группы само по себе не даёт доступа к занятиям/результатам. Оператор имеет доступ к заявкам студентов групп из OperatorScope, но не к их кабинету и оценкам. Общие/групповые/факультетские объявления — намеренно общий контент соответствующей аудитории; отметка прочтения персональная.

## Политика маршрутов

| Ресурс / действие | Гость | Студент-владелец | Другой студент той же / иной группы | Оператор со scope | Оператор без scope |
| --- | --- | --- | --- | --- | --- |
| GET `/` | 302 на login | 200, собственная сводка | 200, своя сводка без чужих персональных данных | 302 в очередь | 302 в пустую очередь |
| GET `/profile/` | 302 | 200, пять полей своего профиля | 200, только свой профиль | 403 | 403 |
| GET `/profile/<чужой id>/` | 404, маршрута нет | 404 | 404 | 404 | 404 |
| GET `/schedule/` | 302 | 200, свои зачисления | 200, свои зачисления, чужие не добавляются | 403 | 403 |
| GET `/grades/`, `/session/` | 302 | 200, свои опубликованные результаты/события | 200, свои результаты; чужой term возвращает404 | 403 | 403 |
| GET `/requests/`, `/requests/new/` | 302 | 200, свои записи/форма | 200, собственные записи/форма | 403 | 403 |
| POST `/requests/new/` | См. CSRF ниже | 302 на сохранённую заявку; owner из сессии | Создаётся заявка отправителя, подставленный owner игнорируется | 403 | 403 |
| GET `/requests/<uuid>/` | 302 | 200 | 404 | 403, использовать operator route | 403 |
| POST `/requests/<uuid>/cancel/` | См. CSRF ниже | Отправленная→отменена; старое состояние409 | 404 | 403 | 403 |
| GET `/operator/requests/` | 302 | 403 | 403 | 200, только разрешённые группы | 200, пустой список |
| GET/POST operator detail/transition | См. CSRF ниже | 403 | 403 | Своя scope:200/302; чужая:404 | 404 |
| GET `/notifications/` | 302 | 200, свои события/counts и доступные объявления/сроки | 200, свои события и counts | 200, свои события и общие объявления | То же; scope не расширяет аудиторию объявлений |
| POST notification read | См. CSRF ниже | 302; отметка повторяема | 404 на чужое событие | 302 только своего события | То же |
| POST announcement read | См. CSRF ниже | 302 для доступного; недоступное404 | Только доступная аудитория, собственная отметка | Только общее объявление | То же |
| GET notification open | 302 | Цель заново проверяется; доступная302, удалённая/отозванная404 | Чужое событие404 | Своя цель заявки только при действующем scope | Отозванная/чужая цель404 |
| GET `/deadlines/<uuid>/` | 302 | 200 по Enrollment | 404 без соответствующего Enrollment | 403 | 403 |

Для запросов POST включён CSRF middleware: запрос без действительного токена может получить403 до проверки входа.302 для гостя проверяется с корректной CSRF-защитой либо тестовым клиентом авторизационной матрицы; это разные проверки. Изменяющие действия доступны только POST, GET для них405. Неопубликованный/будущий GradeResult исключается до расчёта counts. Деактивированный пользователь не восстанавливает сессию штатным backend (302), доверенные сервисы повторно загружают active/role и отклоняют устаревший actor.

## Фактическое покрытие

| Риск | Тесты в репозитории |
| --- | --- |
| Профиль и подстановка адреса, роли, отсутствие профиля, деактивация | `tests/test_accounts.py`: login_profiles_and_direct_substitution, local_next_and_role_routing, deactivation_and_missing_profile |
| Расписание без Enrollment даже в той же группе, подстановка student/date/view, POST | `tests/test_schedule.py`: scoping_filters_and_access, bad_filters |
| Свои результаты студентов одной группы, term другого студента, скрытые grades/counts | `tests/test_grades.py`: visibility_counts_and_filtering, own_terms_and_same_group_personal_results, hidden_points_and_missing_are_identical |
| Чужой UUID заявки и отмена, чужая группа оператора, отзыв scope, counts/пагинация/фильтр | `tests/test_requests.py`: access_urls_filters_pagination_and_xss |
| Подмена owner/status/version при создании, одинаковый submission_key у разных студентов | `tests/test_requests.py`: creation_idempotency_quota_and_forgery |
| Устаревшие active/role и переходы | `tests/test_requests.py`: model_constraints_immutability_and_stale_actor, transition_table_versions_and_public_history |
| Announcement all/group/faculty, время публикации, личное прочтение, scope оператора | `tests/test_notifications.py`: audiences_time_read_scope_and_xss |
| Чужое событие/read/open, точный unread_count, удалённая цель, отзыв Enrollment/scope | `tests/test_notifications.py`: personal_pagination_owner_read_and_targets, operator_target_rechecks_scope_and_read_csrf |
| Главная, same-group без Enrollment, разные студенты, published-only summary и личные requests | `tests/test_dashboard_demo.py`: dashboard_scopes_published_results_and_deadlines, dashboard_role_empty_and_term_selection |
| Настоящие сессии студента/оператора, чужая заявка404 после повторного входа | `tests/test_dashboard_browser.py`: full_cabinet_path на360/1440 |

Имена в таблице опускают префикс `test_`. HTTP API/HTMX partial endpoints сейчас не реализованы; страницы отдают полноценный HTML. При их добавлении матрицу нужно расширить на новые обработчики и режимы ответа. URL нового endpoint/фильтра не получает доступ автоматически от соседнего маршрута.

## Оставшиеся ограничения

Точечная параметризованная матрица добавлена в `tests/test_access_matrix.py`: `test_personal_read_policy` проверяет 13 маршрутов × 6 субъектов; `test_personal_write_policy_and_effects` — пять реальных POST × 6 субъектов с проверкой сохранённого владельца, событий, получателя и отсутствия effects при отказе. Субъекты: гость, владелец, same-group без Enrollment, other-group, scoped и unscoped оператор. Списки заявок/очереди, личные уведомления и unread_count проверены точно; персональные текстовые маркеры проверены в карточках. Специализированные tests из таблицы выше сохраняют детальные проверки оценок, расписания и главной.

`test_all_mutations_require_csrf` отдельно проверяет все пять изменяющих предметных POST, login и logout с enforce_csrf_checks=True:403 без token, неизменные записи/marks и сохранённая сессия. Гостевой302 на предметных POST проверяется авторизационным клиентом отдельно; `test_guest_with_valid_csrf_redirects_to_login` дополнительно получает настоящий token через GET login и проверяет enforce_csrf POST302 для home/profile и всех пяти защищённых mutation routes без effects. `test_mutation_get_is_rejected` проверяет GET405 четырёх предметных action routes; logout GET405 покрыт `tests/test_accounts.py`. `test_read_route_rejects_post_without_effects` проверяет POST405 всех читающих маршрутов кроме GET/POST формы new. Для `/` и `/profile/` добавлен require_GET по решению root: прежде POST возвращал200 read-only; это исправление HTTP-контракта, не обнаруженная утечка. `test_hx_request_does_not_expand_object_access` повторяет запреты same-group для student/operator detail, notification open и deadline с HX-Request:true; отдельных partial endpoints нет.

Q01 ограничен текущими серверными endpoints. Production-проверка, CSP/proxy, несколько вкладок/Back на всех движках и физический телефон остаются отдельными Q03/Q04/D задачами. После изменения прав, нового фильтра или export/partial повторяется соответствующий серверный негативный сценарий.
