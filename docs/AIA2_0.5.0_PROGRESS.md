# AIA2 0.5.0 — журнал прогресу

Останнє оновлення: 2026-10-23. База `90ab63f`, робоча версія 0.4.0-alpha.
Цей файл читати разом із [планом](AIA2_0.5.0_PLAN.md) перед продовженням.
Статуси: `TODO`, `IN_PROGRESS`, `DONE`, `BLOCKED`.

## Етапи

| № | Етап | Статус | Доказ / наступна дія |
|---|---|---|---|
| 0 | FTB Quests overload hotfix | IN_PROGRESS | Перевірено Entity overload та командний зміст UUID overload; міст і Rhino-регресія в роботі |
| 1 | Аудит 0.4 | IN_PROGRESS | HEAD збігається з 90ab63f, початкове дерево чисте; завершити baseline-звіт |
| 2 | Дослідження механік | IN_PROGRESS | Read-only дослідження technology/magic/adventure; до hotfix-коміту контент не записувати |
| 3 | Карти прогресії | TODO | Після перевірки джерел записати карти та зв'язати з квестами |
| 4 | Перебудова координат | IN_PROGRESS | Read-only вимірювання бази, алгоритм готується поза canonical SNBT |
| 5 | Поглиблення 48 епох | TODO | Створити перевірені механічні лінії на основі карт |
| 6 | Перегляд нагород | TODO | Аудит усіх нагород, тематичні таблиці й перевірка безпечності |
| 7 | Розширення рецептів | TODO | Після дослідження та hotfix-коміту |
| 8 | Предмети без джерел | TODO | Перевіряти export/native/loot, не додавати рецепти boss-only предметам |
| 9 | Creative/альтернативи | IN_PROGRESS | Read-only аудит точних Creative Essence/Pool ID і джерел |
| 10 | Інтеграційні тести | TODO | Виконати після завершення відповідних блоків |
| 11 | Реліз і push | TODO | Не оголошувати 0.5 готовою до завершення перевіреного обсягу |

## Окремий стан 48 епох

Статуси стосуються змін v5; наявний контент v4 не видаляється і не вважається
повністю переробленим лише через його наявність.

| Епоха | Дослідження | Квести v5 | Рецепти v5 | Залежності v5 |
|---|---|---|---|---|
| 01 | TODO | TODO | TODO | TODO |
| 02 | TODO | TODO | TODO | TODO |
| 03 | TODO | TODO | TODO | TODO |
| 04 | TODO | TODO | TODO | TODO |
| 05 | TODO | TODO | TODO | TODO |
| 06 | TODO | TODO | TODO | TODO |
| 07 | TODO | TODO | TODO | TODO |
| 08 | TODO | TODO | TODO | TODO |
| 09 | TODO | TODO | TODO | TODO |
| 10 | TODO | TODO | TODO | TODO |
| 11 | TODO | TODO | TODO | TODO |
| 12 | TODO | TODO | TODO | TODO |
| 13 | TODO | TODO | TODO | TODO |
| 14 | TODO | TODO | TODO | TODO |
| 15 | TODO | TODO | TODO | TODO |
| 16 | TODO | TODO | TODO | TODO |
| 17 | TODO | TODO | TODO | TODO |
| 18 | TODO | TODO | TODO | TODO |
| 19 | TODO | TODO | TODO | TODO |
| 20 | TODO | TODO | TODO | TODO |
| 21 | TODO | TODO | TODO | TODO |
| 22 | TODO | TODO | TODO | TODO |
| 23 | TODO | TODO | TODO | TODO |
| 24 | TODO | TODO | TODO | TODO |
| 25 | TODO | TODO | TODO | TODO |
| 26 | TODO | TODO | TODO | TODO |
| 27 | TODO | TODO | TODO | TODO |
| 28 | TODO | TODO | TODO | TODO |
| 29 | TODO | TODO | TODO | TODO |
| 30 | TODO | TODO | TODO | TODO |
| 31 | TODO | TODO | TODO | TODO |
| 32 | TODO | TODO | TODO | TODO |
| 33 | TODO | TODO | TODO | TODO |
| 34 | TODO | TODO | TODO | TODO |
| 35 | TODO | TODO | TODO | TODO |
| 36 | TODO | TODO | TODO | TODO |
| 37 | TODO | TODO | TODO | TODO |
| 38 | TODO | TODO | TODO | TODO |
| 39 | TODO | TODO | TODO | TODO |
| 40 | TODO | TODO | TODO | TODO |
| 41 | TODO | TODO | TODO | TODO |
| 42 | TODO | TODO | TODO | TODO |
| 43 | TODO | TODO | TODO | TODO |
| 44 | TODO | TODO | TODO | TODO |
| 45 | TODO | TODO | TODO | TODO |
| 46 | TODO | TODO | TODO | TODO |
| 47 | TODO | TODO | TODO | TODO |
| 48 | TODO | TODO | TODO | TODO |

## Сесії та контрольні точки

### 2026-10-23 — початок v5

- Git: перевірено чистий базовий HEAD `90ab63f`; створено резервний Git-архів
  до масштабних змін (шлях у PLAN).
- Підтверджена помилка: Rhino не обирає `getOrCreateTeamData` з ServerPlayer.
  За фактичним кодом FTB UUID overload очікує UUID команди; Entity overload
  звертається до актуального членства гравця через FTB Teams API.
- Змінювані файли hotfix: `20_progression.js`, Java `FtbQuestBridge`, JAR,
  Node/Rhino fixtures й регресійні тести. Перевірки ще не завершено.
- Наступна конкретна дія: виконати реальний Rhino-регресійний тест мосту,
  зібрати JAR, перевірити поточну прогресію, створити окремий hotfix-коміт.
- Повний Windows-інстанс недоступний у хмарі; ручні перевірки не заявляти
  виконаними. Нічого не встановлено у C:\CurseForge користувача.

## Власники незавершених файлів у поточній сесії

- root: docs/PLAN/PROGRESS, скрипт20, інтеграція генераторів, нагороди, Git.
- native_guard_v4: companion Java/JAR typed FTB bridge.
- guard_fix_v4: справжній Rhino-регресійний тест FTB overload.
- dual_textures_v4: layout генератор/метрики/тести.
- quests_v4: technology research maps і механічні квести.
- magic_research_v5: magic/adventure research maps і квести.
- recipes_v4: Creative Essence/Pool, альтернативи та баланс рецептів.

У новій сесії перевірити активність цих агентів, фактичні файли та Git;
імена агентів не гарантують, що попередні процеси досі працюють.
