# Лицензии кода и материалов

Проверка Q06 от 6 ноября 2026 года, требование LIC-01. Источник версий — `uv.lock`; проверены metadata и исходные LICENSE/NOTICE установленного Linux-окружения. Хеши файлов и версии сохранены в [реестре](evidence/Q06/license-inventory.json). Для отсутствующих в Linux colorama/tzdata, text-unidecode и вложенного libargon2 дополнительно прочитаны точные sdist из lock после проверки SHA256: [источники](evidence/Q06/license-source-check.json). Код архивов не выполнялся.

Дополнение D02-02 от8ноября2026: проверены реальные серверные образы, OS copyright/common-license files, Python/native hashes и source notices Go-компонентов. Production использует12 Python-пакетов и системную libpq; бинарный extra Psycopg остаётся только в dev group. Версии всех28 сторонних пакетов lock не менялись, изменены dependency edges. Исходный Q06 реестр сохраняет историческое состояние; новые сведения — в `docs/evidence/D02-02/` и [ADR003](decisions/003-managed-runtime-libraries.md).

Дополнение REL10 от 20 ноября 2026 года сверяет `uv.lock`, локальные дистрибутивы и статику кандидата `архивная-версия`. В lock 30 сторонних Python-пакетов. Ветка Linux без dev включает 14 пакетов после добавления `markdown-it-py` и `mdurl`. Три текста лицензии этих дистрибутивов совпали побайтно с копиями ниже. При сборке установленная `.venv` переносится в образ вместе с `.dist-info`. Состав и notices конкретного релизного образа следует сверить при его сборке. [Проверки REL10](evidence/REL10/review.md)

## Серверные Python-зависимости

Ссылки ведут на конкретные upstream releases, а не на текущую плавающую версию. Все перечисленные лицензии допускают выбранное использование библиотек; условия сохранения уведомлений действуют при передаче копий.

| Пакет | Версия | Лицензия |
| --- | --- | --- |
| [argon2-cffi](https://pypi.org/project/argon2-cffi/25.1.0/) | 25.1.0 | MIT |
| [argon2-cffi-bindings](https://pypi.org/project/argon2-cffi-bindings/26.1.0/) | 26.1.0 | MIT; вложенный libargon2 — CC0-1.0 OR Apache-2.0 |
| [asgiref](https://pypi.org/project/asgiref/3.13.0/) | 3.13.0 | BSD-3-Clause |
| [cffi](https://pypi.org/project/cffi/2.1.1/) | 2.1.1 | MIT-0 |
| [Django](https://pypi.org/project/Django/5.2.19/) | 5.2.19 | BSD-3-Clause; сохраняются также LICENSE.python и вложенные notices |
| [django-axes](https://pypi.org/project/django-axes/9.0.0/) | 9.0.0 | MIT |
| [gunicorn](https://pypi.org/project/gunicorn/23.0.0/) | 23.0.0 | MIT |
| [markdown-it-py](https://pypi.org/project/markdown-it-py/4.3.0/) | 4.3.0 | MIT, включая исходную реализацию markdown-it. Тексты [markdown-it-py](third-party/markdown-it-py-LICENSE.txt) и [markdown-it](third-party/markdown-it-LICENSE.txt). |
| [mdurl](https://pypi.org/project/mdurl/0.1.2/) | 0.1.2 | MIT. Полный текст сохраняет уведомления авторов пакета и исходной реализации Node.js. [Текст лицензии](third-party/mdurl-LICENSE.txt) |
| [packaging](https://pypi.org/project/packaging/26.3/) | 26.3 | Apache-2.0 OR BSD-2-Clause |
| [psycopg](https://pypi.org/project/psycopg/3.3.8/) | 3.3.8 | LGPL-3.0-only |
| [pycparser](https://pypi.org/project/pycparser/3.12/) | 3.12 | BSD-3-Clause |
| [sqlparse](https://pypi.org/project/sqlparse/0.6.1/) | 0.6.1 | BSD-3-Clause |
| [WhiteNoise](https://pypi.org/project/whitenoise/6.12.0/) | 6.12.0 | MIT |
| [tzdata](https://pypi.org/project/tzdata/2026.6/) | 2026.6 | Apache-2.0; условная Windows-зависимость, в проверенном Linux не установлена |

## Инструменты тестирования и разработки из lock

Они не нужны runtime-образу приложения. Их лицензии учитываются отдельно, включая транзитивные пакеты.

| Пакет | Версия | Лицензия |
| --- | --- | --- |
| [colorama](https://pypi.org/project/colorama/0.4.6/) | 0.4.6 | BSD-3-Clause; условная Windows-зависимость |
| [greenlet](https://pypi.org/project/greenlet/3.5.6/) | 3.5.6 | MIT AND PSF-2.0; сохранять оба текста |
| [iniconfig](https://pypi.org/project/iniconfig/2.3.1/) | 2.3.1 | MIT |
| [playwright](https://pypi.org/project/playwright/1.64.1/) | 1.64.1 | Apache-2.0; browsers и вложенный driver имеют дополнительные notices |
| [pluggy](https://pypi.org/project/pluggy/1.7.0/) | 1.7.0 | MIT |
| [pyee](https://pypi.org/project/pyee/14.0.0/) | 14.0.0 | MIT |
| [psycopg-binary](https://pypi.org/project/psycopg-binary/3.3.8/) | 3.3.8 | LGPL-3.0-only; dev-only binary extra, не входит в production; вложенные native libraries имеют собственные лицензии |
| [Pygments](https://pypi.org/project/Pygments/2.21.0/) | 2.21.0 | BSD-2-Clause |
| [pytest](https://pypi.org/project/pytest/9.2.0/) | 9.2.0 | MIT |
| [pytest-django](https://pypi.org/project/pytest-django/4.14.0/) | 4.14.0 | BSD-3-Clause |
| [pytest-playwright](https://pypi.org/project/pytest-playwright/0.10.0/) | 0.10.0 | Apache-2.0 |
| [python-slugify](https://pypi.org/project/python-slugify/9.1.3/) | 9.1.3 | MIT |
| [ruff](https://pypi.org/project/ruff/0.17.3/) | 0.17.3 | MIT |
| [text-unidecode](https://pypi.org/project/text-unidecode/1.3/) | 1.3 | Выбор GPL/GPLv2+ либо Artistic License из LICENSE; для этого проекта выбран Artistic |
| [typing-extensions](https://pypi.org/project/typing-extensions/4.16.0/) | 4.16.0 | PSF-2.0 |

## Как сохраняем условия

- Установленные зависимости используются без модификаций. Не удалять `.dist-info/licenses`, LICENSE, AUTHORS, NOTICE и вложенные license files при сборке/упаковке. MIT/BSD требуют сохранения соответствующих notices; Apache-2.0 — текста лицензии и применимых NOTICE. Таблица не заменяет исходные тексты. Основание: [MIT](https://spdx.org/licenses/MIT.html), [BSD-3-Clause](https://spdx.org/licenses/BSD-3-Clause.html), [Apache-2.0](https://www.apache.org/licenses/LICENSE-2.0).
- `cffi 2.1.1` использует MIT-0; не приписывать ему условия старых выпусков cffi. Проверен фактический LICENSE. [Текст MIT-0](https://spdx.org/licenses/MIT-0.html).
- Для libargon2 выбран вариант CC0; исходный полный dual-license notice сохранён без изменений в [libargon2-LICENSE.txt](third-party/libargon2-LICENSE.txt), его нужно включать в передаваемую сборку вместе с notice wrapper. Это дополнение к Python metadata, где вложенная лицензия не перечислена.
- Psycopg 3 имеет LGPLv3. Не менять библиотеку, не запрещать её замену/модификацию или исследование для отладки такой модификации. При передаче образа/бинарной копии обеспечить применимые notices, тексты GPL/LGPL, доступ к соответствующему исходному коду передаваемой версии библиотеки и возможность замены по условиям лицензии; одной ссылки на PyPI для любых форм распространения недостаточно. В production сохраняются wrapper LGPL в dist-info, полный GPLv3 из supplementary bundle и динамическая системная libpq; собственного запрета на замену нет. Это не разрешение публиковать произвольный binary archive без соответствующих источников/условий. Основание — [LICENSE Psycopg 3.3.8](https://raw.githubusercontent.com/psycopg/psycopg/3.3.8/LICENSE.txt).
- Для text-unidecode сохранять исходный Artistic License и copyright notices, поставлять неизменённый upstream package. Выбор Artistic явно записан здесь; пакет не объявляется MIT. Его лицензия проверена в точном sdist, указанном в source-check.
- Собственный код не получает новую общую лицензию этим реестром. Здесь перечислены сторонние компоненты и их условия.

## Материалы интерфейса

| Материал в текущем кабинете | Где используется | Происхождение и статус |
| --- | --- | --- |
| `static/icons/persona-mark.png`, `persona-mark-small.png` | Фон входа, знак в шапке, favicon и узор за персонажами. | Большая версия получена в ImageGen с сохранением формы предоставленной буквы P из `persona.jpeg`. Малую экспортировал проектный скрипт из того же PNG. В журнале есть история обработки и запрос на применение знака. Для исходного изображения требуется подтверждение разрешения на публичное использование и распространение производных. [U07](evidence/U07/imagegen.md) · [Экспорт CAT09](../scripts/build_cat_art.py) |
| `static/icons/campus.svg`, встроенные SVG фигурок в `cat.html` | Навигация, служебные иконки и предметы мини-игры. | Проектная векторная графика из шаблонов и общего спрайта по истории разработки. Подключения отдельного набора иконок в проверенных путях не найдено. [Иконки кабинета](../apps/accounts/templates/accounts/icon.html) · [Предметы игры](../apps/accounts/templates/accounts/cat.html) |
| `static/images/persona-assistant.png`, `persona-assistant-motion.png` | Портрет помощника и четыре анимационные позы. | Портрет создан в ImageGen для persōna. Атлас создан редактированием этого портрета. Инструмент и преобразования зафиксированы для конкурсного отчёта. [Портрет AI01](evidence/AI01/imagegen.md) · [Атлас AI08](evidence/AI08/imagegen.md) |
| `static/images/cat-assistant-style48/{sleepy,scholar,chaos}.png` | Игра, профиль и прогулки кота. | Три портрета созданы ImageGen по палитре и стилю проектного помощника. Из мастер-файлов CAT08 скрипт экспортировал сетки 48 × 48. Движение строит локальный Canvas-код. [Референсы CAT08](evidence/CAT08/imagegen.md) · [Экспорт CAT09](evidence/CAT09/review.md) |
| `static/images/cat-pixel48/toy-{yarn,ball,mouse,fish}.png` | Выбираемые игрушки и награды. | Фигурки 32 × 32 нарисованы проектным генератором CAT07. [Текущий генератор](../scripts/generate_cat_toys.py) · [Описание CAT07](evidence/CAT07/implementation.md) |
| Шрифты | Основной текст, цитаты и код. | CSS обращается к локальным семействам, в том числе Inter, Georgia и системным заменам. В манифесте сборки нет файлов шрифтов. `@font-face` и подключений шрифтов с CDN в проверенных шаблонах и CSS нет. |

Источник знака описан в U07 как пользовательский референс. Права на входные изображения и условия сервиса генерации учитываются отдельно. Условия OpenAI описывают распределение прав между сервисом и пользователем и требуют, чтобы загрузивший изображение имел нужные разрешения. Для производных сохраняется связь с происхождением исходника. [Условия OpenAI для частных пользователей](https://openai.com/policies/terms-of-use/#content) · [OpenAI Services Agreement, §4](https://openai.com/policies/services-agreement/)

### Архивные материалы

В текущей сборке 12 графических файлов. Только три мастер-портрета CAT08 остаются в `artwork/` для локального экспортёра. Происхождение предыдущих спрайтов сохранено в записях этапов. [Инвентаризация](evidence/REL10/review.md)

| Группа вне текущих экранов | Документированный источник |
| --- | --- |
| `backpack-cat.jpeg`, три старых портрета WebP и пять аксессуаров `cat-*.png` | Оптимизированный пользовательский `cat.jpeg`, его обработка в ImageGen и аксессуары по полученному портрету. [CAT01](evidence/CAT01/implementation.md) · [CAT02](evidence/CAT02/imagegen.md) · [CAT03](evidence/CAT03/imagegen.md) · [Подгонка мантии](evidence/CAT04-outfits20/imagegen.md) |
| Четыре `pixel-{duo,chaos}-{sheet,clean}.png` и четыре старых растровых `toy-*.png` в `artwork/images/` | Скопированные пользовательские листы, их очистка в ImageGen и старые игрушки, для которых лист служил стилевым референсом. [CAT04](evidence/CAT04/imagegen.md) · [CAT05](evidence/CAT05/imagegen.md) |
| Исторические кадры `cat-pixel32/` и `cat-pixel48/`, знаки `mark.svg` и `persona-word.svg` | Ранние спрайты рисовали проектные генераторы. SVG использовались на предыдущих этапах оформления кабинета. [CAT07](evidence/CAT07/implementation.md) · [U06](evidence/U06/review.md) |

Перед выдачей конкурсной сборки нужно подтвердить права на источник знака. При передаче исходников нужно отдельно проверить права на материалы из `artwork/` и исторические скриншоты, которые войдут в архив или будут доступны жюри. В проверенной статической сборке нет HTMX, ресурсов Django Admin и браузерных инструментов QA.

## Серверные образы и source notices D02-02

| Область | Фактический источник/проверка | Как сохраняются условия |
| --- | --- | --- |
| Python3.13.14 и Debian13 packages | Реальный image SBOM, installed package versions, `/usr/share/doc/*/copyright`, `/usr/share/common-licenses`, Python и native file hashes | Установленные copyright/license files не вырезаются. Upstream package/source/version и image ID фиксируются в audit; разные лицензии OS packages не приписываются собственному приложению |
| libpq5=17.11-0+deb13u1 | Подписанный Debian repository, системная shared library; [PostgreSQL license](https://www.postgresql.org/about/licence/) | Нет15 скрытых vendor `.so` production wheel. Лицензия libpq и copyright её системных зависимостей сохраняются как Debian package metadata |
| Caddy2.11.9, gosu1.19, Go runtimes и modules | [Manifest bundle](third-party/runtime-notices/manifest.json), реальные Go module inventories и exact upstream source notices | В каждый из3 образов включён общий каталог `/usr/share/doc/deanery/third-party`;207 файлов (206 текстов и manifest) проверяются по SHA256 перед build и внутри image |
| Алгоритмы/обёртки Argon2/CFFI | Pinned Python distribution metadata/native hashes, сохранённый libargon2 LICENSE | Не подменять номер протокола Argon2 значением software release. Wrapper/source identity и полный CC0/Apache notice сохраняются отдельно от scanner coverage |

Общий bundle охватывает152 Go identities:149 module archives проверены по Go `h1`;2 stdlib набора получены по точным официальным Go tags; gosu имеет отдельно разрешённое сопоставление нормализованного `v1.19.0` с официальным tag1.19/commit6456aaa0f3c854d199d0f037f068eb97515b7513. Gosu не имеет записи sumdb для нормализованной версии: это явно отмечено, а не выдано за h1. Доверие к checksum lookup в этом проходе основано на HTTPS официального sumdb; отдельная криптографическая проверка signed checkpoint не заявляется.

Сохранены205 неизменённых Go LICENSE/NOTICE/COPYRIGHT/PATENTS/AUTHORS текстов и canonical GPLv3. Основные проверенные тексты относятся к Apache/MIT/BSD/ISC/CC0 и сопровождающим copyright/patent grants; полные условия каждого компонента читаются через manifest→files. Нельзя делать юридический вывод по одному scanner label или распространять лицензию одного файла на весь image. Root независимо сверил все file hashes; GPLv3 также побитно совпал с доверенным системным `/usr/share/common-licenses/GPL-3`. Повторные ошибки сети GNU и ранее успешное получение отражены в provenance, не скрыты.

Из широкого имени LICENSE исключены2 testdata fixtures и2 точных notice для непоставляемых Windows Wintun binary/QUIC logo assets. Исключения, причины и исходные hashes записаны в manifest; корневые лицензии этих Go modules сохранены. Никаких Windows drivers, SVG/логотипов библиотек, исходников или executable archives в bundle нет. `h1` вычислялся по всем файлам архива, включая затем исключённые fixtures.

D02-02 относится к компонентам проверенного тогда серверного контура. При передаче бинарных образов или архивов venv нужно выполнить применимые условия доступа к соответствующим исходникам, заменяемости библиотек и сохранения уведомлений. Состав, лицензии и хеши нужно сверять для конкретной новой сборки. Доступность жюри и фактическая сдача проверяются при размещении.
