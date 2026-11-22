# AI04 — безопасное форматирование ответов

Прежний назначенныйcat01/Sol-low, безделегации. Прочитаны TASK/AGENTS, AIконтрактARCH§29/PLAN, актуальныйTaste2.5.1. Kindsoftware, existingworkspace; оформлениеучебногоответа, прежняяпалитра/шрифты/навигация. RootведётbrowserQA/docs/приёмку.

## Серверный renderer

Новая templatefilterassistant_markdown применяется толькокmessage.roleassistant вшаблоне, включаястаруюsessionhistory. CommonMarkчерезmarkdown-it-py4.3.0: rawHTML/linkify/autolinkoff, безplugins/highlighter. Заголовкиh1/h2/h3→h4/h5/h6 (остальныеclamp6), совместимосиерархиейpageh1/chat h2/messageh3. Абзацы, ordered/unorderedlists, strong/em, hr, inline/fencedcodeсемантичны; текст/кодэкранируются. Изначальноlink/imageпарсингполностьюотключался; послеrootreviewсделанfixedlabel-onlyrenderer: обычныессылки/изображенияпоказываютчитабельнуюподписьбезMarkdownобёртки, никогдаa/img/href/src/URLattributes. Опасныесхемыостаютсяотклонённымипарсером и безактивнойссылки. СырыеHTMLвключаяscript/img/iframe/styleстановятсятекстом, неDOM. mark_safeиспользуетсятолькодлявыходафіксированногопарсера/renderer, невходногоответа.

Сообщенияпользователянепреобразуются, автоматическиэкранируютсяDjangoкакраньше. Sessionсодержимоенепереписывается, APIконтекстполучаеттотжесыройMarkdown. Adapter/лимиты/провайдер/конфиги/.envне менялись. Изменённыйциклсообщенийразвёрнутначитаемыестроки.

## Оформление

Ответполучилглубокийконтрастныйteal#20565b (8.26:1наwhitevarsurface), боковойакцентexistingvarteal#567C8D, нейтральныйwhiteфон. Текст16px/1.7, max65ch, осмысленныеотступызаголовков/списков/hr, безопасныйпереносдлинногокода/URLбезoverflow. Userbubbleпрежний. ScopedCSSне меняетобщиеtokens/ассеты/фигуры/игру. Rootпредварительнопосмотрелцвет/форматированиевChromium, финальное360/1440визуальноеревьювегоотчёте; executorне заявляетGATEPASS.

## Зависимость и лицензии

Разрешённаяruntimeзависимостьmarkdown-it-py>=4,<5 зафиксированаuvв4.3.0; transitive mdurl0.1.2. Другиеверсиипакетовне менялись, lockrevisionобновлёнuv. ОфициальныеMITлицензиипрочитаныдоиспользования:
https://raw.githubusercontent.com/executablebooks/markdown-it-py/master/LICENSE
https://raw.githubusercontent.com/executablebooks/mdurl/master/LICENSE
Securityguidance: https://markdown-it-py.readthedocs.io/en/latest/security.html (поумолчаниюHTMLвCommonMarkвключён, поэтомуздесьявноoff). Полныелицензииконкретныхустановленныхdistскопированывdocs/third-party/markdown-it-py-LICENSE.txt иmdurl-LICENSE.txt, включаяmdurlattributions. Никакихвнешнихресурсоввбраузере.

## Фактическиепроверки

`TEST_DB_PORT=55439 TEST_DB_NAME=test_ai04_agent TEST_DB_USER=deanery UV_CACHE_DIR=/tmp/persona-uv-cache uv run --locked pytest tests/test_assistant.py -q --tb=short` — финально28passed2.12s (первоначальныйвариантсdisabledlinks28passed2.10sдоlabelrefinement). Толькоroot-owneddisposablePostgreSQL, всеprovidercallsstubbed; реальныхAPI/платныхвызововнет.

НовыйрегрессионныйHTMLParserтестпроверяетallowlistреальныхвыходныхтегов, headings/абзацы/списки/strong/em/hr/code, отсутствиеактивныхanchors/resources/HTML, читабельныессылочные/imageподписи и отсутствиеихdestinations. Фиктивноесодержимоевключаетscript/img/iframe/style, code, remoteimage/URLиjavascriptlink. Интеграционныйтестпроверяетстарый/новыйответвHTMLпри неизменнойrawsession/APIhistory исыромэкранированномusertext. Существующиеadapter/CSRF/owner/лимиты/ошибкитожеpassed.

Ruffcheck/formatchangedPython иgitdiffcheckpassed. SourcefreezeпереднезависимымrootQA. Executorнечитал.env/секреты, не менялсервернуюконфигурацию/daemon/схему, не делалcommit/push/deploy. Browser/Taste/итоговаяприёмкаостаютсяroot; kitне менялся.
