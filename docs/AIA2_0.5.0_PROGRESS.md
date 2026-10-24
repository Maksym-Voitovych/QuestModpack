# AIA2 0.5.0 — журнал прогресу

Останнє оновлення: 2026-10-24 (часовий пояс користувача Europe/Kyiv). База `90ab63f`, робоча версія 0.4.2-alpha (FTB hotfix та native observers); 0.5 ще не реліз.
Цей файл читати разом із [планом](AIA2_0.5.0_PLAN.md) перед продовженням.
Статуси: `TODO`, `IN_PROGRESS`, `DONE`, `BLOCKED`.

## Етапи

| № | Етап | Статус | Доказ / наступна дія |
|---|---|---|---|
| 0 | FTB Quests overload hotfix | DONE | Типізований міст, production script20, 16 справжніх Rhino assertions, Node41/Python23/Java5237; окремий fix-коміт |
| 1 | Аудит 0.4 | DONE | v5-baseline-audit.json; snapshot2784 квестів/569 рецептів, task/reward/dependency ID; export ≠ доступ до Windows |
| 2 | Дослідження механік | IN_PROGRESS | Офіційні source/book докази збережено у /tmp; перевірені каталоги112tech+150magic готові, переносні карти завершуються |
| 3 | Карти прогресії | IN_PROGRESS | Фокусний endgame_v5.json; technology/magic карти та переносні докази завершуються |
| 4 | Перебудова координат | IN_PROGRESS | Генератор v2 і15тестів готові; фінальне застосування після всіх каталогів |
| 5 | Поглиблення 48 епох | IN_PROGRESS | 271новий авторський квест у3каталогах; фінальна компіляція/карти та4native process proof у роботі |
| 6 | Перегляд нагород | IN_PROGRESS | 45профілів/41alias/132матеріали,6тестів; фінальна компіляція/аудит ще попереду |
| 7 | Розширення рецептів | IN_PROGRESS | 33рецепти/29цілей/26native-removals/9codec;14тестів; фінальна компіляція попереду |
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

### 2026-10-23 — FTB hotfix 0.4.1-alpha

- DONE: новий FtbQuestBridge явно обирає Entity overload public API FTB
  2101.1.36. UUID overload із UUID гравця не використовується.
- Перевірено: Node41, Python23 (0skip, три справжні Rhino-сценарії),
  16 FTB/Rhino assertions, 5237 Java assertions та збірка JAR, SNBT/DAG/ID.
- Файли: Java bridge/JAR, script20, fixtures, test_ftb_interop.py,
  FtbQuestInteropHarness.java, installer/package preflight, README/CHANGELOG,
  verification-report.json, ftb-hotfix-report.json, release-report.json.
- Дані, 2784 квести/130 глав/569 рецептів/96 ключів не змінено. Native41
  запуск був на0.4.0, повний FTB runtime на0.4.1 не запускався.
- Інші перевірені Java-виклики не мають підтвердженої неоднозначності.
- Наступна конкретна дія: baseline snapshot v4 ID/нагород; завершити карти
  джерел, застосувати DAG layout, додати перевірений контент та нагороди.
- Знайдено3 exported producer recipes Creative Pool, а не2; Creative Essence
  має namespace mysticalagradditions. Остаточні зміни ще TODO.

### 2026-10-23 — аудит бази й контроль IDs

- FTB hotfix зафіксовано окремим комітом `c620e4e`; план раніше збережено
  в `1dcdf44`. Перевірка23Python/41Node/5237Java пройшла.
- DONE baseline: `implementation/v5-baseline-audit.json`,
  `content/audit/v4-ids.json`:2784квести/130глав/569рецептів/96ключів.
- Аудит2516предметних+48команднихнагород; їхні IDs збережено в snapshot.
- Відомі GUI-проблеми:1679перетинів,96зворотнихі72вертикальнихлокальнихліній;
  накладаньіконок0. Layout ще не застосовано.
- Дозволено запис окремих v5 каталогів/карт/генераторів після hotfix;
  canonical SNBT змінюватиме root лише під час інтеграції.
- Наступна конкретна дія: інтегрувати готові source-backed maps/catalogs,
  зафіксувати generator layout з метриками, потім тематичні нагороди/баланс.

### 2026-10-24 — відновлення з файлів репозиторію

- Прочитано PLAN/PROGRESS, перевірено Git: `5ece770`; попередні агенти вже
  відсутні. Відновлено їхні файли та /tmp-чернетки, завдання делеговано новим.
- Нові власники: technology_v5_resume, magic_v5_resume, layout_v5_resume,
  rewards_v5_resume, balance_v5_resume, validation_v5_resume;
  mechanic_receipts_v5 — окремий native observer із4реальними процесами.
- Попередня пробна інтеграція9capstone+33рецепти:2793квести/602рецепти,
  Node41/Python67/SNBT/ID/DAG пройшли. Це НЕ фінальні кількості0.5.
- Каталоги технологій112імагії150післяцього записані, ще не включені у
  фінальний runtime. Не заявляти їх згенерованими до нового запуску.
- Layoutv2:15тестів, preview-only; очікується приблизно33%скорочення
  перетинів від початкових1679 після final-order constraints, не старі70%.
- Наступна конкретна дія: зафіксувати перевірені генератори/політики,
  завершити переносні карти; потім повна генерація і незалежний валідатор.
- Nativeobserver4процесів @епохи4/10/16/23 у роботі; не додавати proof-квести
  до готового пакета без відповідного JAR/API/конфігів/тестів.

### 2026-10-24 — native production observers завершено

- DONE окремого підблоку: чотири реальні виробничі докази Create/Mek,
  шість перевірених маршрутів; збереження команди у власному SavedData.
- Виправлено доступність E10: доказ латуні включає незагрітий bootstrap
  AIA2, бо Blaze Burner стадії15 ще недоступний. /give не є доказом.
- Файли: ProductionMilestoneBridge, existing native completion hooks,
  script40/config/4advancements, script20sync, JAR0.4.2, installer preflight,
  tests/mechanics.test.js та companion/verification/native-smoke reports.
- Перевірено:5237 Java assertions,9 Node tests нового модуля,
 49 assertions у двох реальних JVM з restart proof persistence.
- Загальний прогін після компіляції:50 Node /81 Python PASS;
  повний runtime0.5 ще проходить незалежний аудит і карти доповнюються.
- Справжній optional Create/Mek process dispatch потребує інстансу;
  мінімальний сервер перевіряв реальну ванільну модель Crafter.
- Наступна дія: закомітити source-backed контент/політики та їхню фактичну
  генерацію, оновити48статусів і залишити явні прогалини дослідження.
