# U11 — визуальная приёмка

**GATE: OPEN32/30WARN**, formalwaivers0. Новыйfinishgateвыполнен, все32check/whereсовпали сU10; полныйперечень/причинысохраненывtaste-classification.md, rawgate/JSONприложены. Это общиепрежниезамечанияlayout/focus/marketing, неPASSвсегосайта. PerfнеповторялсядляCSSразмеров, новыхассетов/узловнет.

Root независимо проверил фактическийdiff прежнегоSol/low и6настоящихэкранов. Задача: пользовательубратьогромныйфон и сделатьмаленькиезнакикакlogin. СвязьPRD-03/04,TECH-06,BRAND-01,ARCHITECTURE§33U11/PLAN U11.

Финальныйстатус: **accepted**, замечанийкновыммаленькимфонамнет. Finishgateзавершёнпослевизуальногоревью; исходныйruntimeне менялся во времяпроверок. Версионированиеpending дообычногоcommit/push, отдельноотприёмки.

## Подтверждённый результат

Изменяются только2CSS:30добавлений/6удалений. Центральный::beforeinset6%удалён, вместо него::before/::after вtopright/bottomleft8%, наклоны12/-16deg какнаlogin. Максимум72/48px,20%/14%ширины, минимум24/18pxдляузкогоassistant. Catopacity.20/.12,assistant.16/.10, обаz0/pointer-none/static, foregroundz1. Ни новыхкартинок/DOM/текстов/движения, ниJS/renderer/данных/схем/зависимостей. Вход не менялся.

Root в отдельнойPostgreSQL17/Chromium снялcat/assistant/profile на360/1440 (6states), проверил обаcomputedpseudoразмера/background/pointer-none/aspectratio и отсутствиеhorizontaloverflow/browsererrors. Реальныйassistantpromptbutton фокусируетполе наобоихразмерах. Измерения `visual-metrics.json`: cat1440=72/48px, assistant1440=68.6/48px, profile1440=51.2/35.8px, cat/profile360=65.2/45.6px, assistant360=24/18px. Изначальныебольшиезнаки~88%портрета заменены небольшимиугловыми.

Root просмотрелactualportraitcat1440/assistant1440/assistant360 и actualTaste shoot360cat/1440assistant. Центр чистый, персонажчёткий, обаугловыхзнака видны, размеры/раскладка прежние. Портреты/страницыPNG, обезличенныеDjangoHTMLсCSRFplaceholder и7sourcehashes сохранены. Tasteиспользован с существующейпалитрой/мотивомвхода, kitнеправился.

СодержательныхновыхавтотестовCSSнеписали. ПолныйU10suiteигра/сохранение/профиль/чат4passed35.14s не повторялся: новыйdiff меняет только размер/положениефонов, функциональныепути/рендер/геометрия неизменны. В U11 фактически выполнены указанныебраузерныеметрики/визуальныйосмотр/контролфокуса и diffcheck/hashcheck, а не новыйpytestsuite. РезультатfullsuiteU10 не выдаётся за текущийзапуск. Реальныйтелефон/публичныйхостингнепроверены.

Локальноеобновление: collectstatic2copied/247unmodified/66postprocessed, reloadсобственногоGunicorn6014; health/live/readystatusok. FixtureубралсвоиБД/сервер; толькособственнаяpersona-u11-qaостановлена, пользовательскаяБД5432сохранена. Обычныйcommit/pushпослеaccepted, явноallowlistedфайлы; .gitignore/photos/прошлыеevidenceнетрогать. SHAотдельновversioning.md.
