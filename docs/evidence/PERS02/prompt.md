# PERS02 — заголовки внутри блоков редактора

Исполнитель gpt-6.1-sol/low, один writer. Читать AGENTS.md, TASK.md, ARCHITECTURE.md §25 и PLAN.md §13. Требования PRD-03/04, TECH-06. Пользователь просит Сильные стороны/Интересы/Хочу научиться/Вне учёбы внутри прямоугольных блоков, а не в разрыве верхней рамки.

Разрешено только static/css/persona.css и docs/evidence/PERS02/implementation.md. Сохранить semantic fieldset+legend, доступное имя группы и все поля/поведение. Самое простое: legend float:left;width:100%;padding:0;margin-bottom + clear next p, чтобы legend располагался внутри padding рамки. Либо другой простой CSS без absolute/transform фиксации координат. Никаких новых тестов или изменений server/template/deps. Новые screenshots выполнит родитель при необходимости в PERS02, исторические не менять. Не делегировать, не commit до accepted.

Проверки diff check и глазами CSS, не усложнять. Родитель проверит live editor360/1440. Краткий отчёт. После freeze сообщи готовность, не менять код во время root checks.
