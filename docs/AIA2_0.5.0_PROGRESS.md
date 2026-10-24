# AIA2 0.5.0 — журнал прогресу

Останнє оновлення: 2026-10-24 (часовий пояс користувача Europe/Kyiv). База `90ab63f`, робоча версія 0.4.2-alpha (FTB hotfix та native observers); 0.5 ще не реліз.
Цей файл читати разом із [планом](AIA2_0.5.0_PLAN.md) перед продовженням.
Статуси: `TODO`, `IN_PROGRESS`, `DONE`, `BLOCKED`.

## Етапи

| № | Етап | Статус | Доказ / наступна дія |
|---|---|---|---|
| 0 | FTB Quests overload hotfix | DONE | Типізований міст, production script20, 16 справжніх Rhino assertions, Node41/Python23/Java5237; окремий fix-коміт |
| 1 | Аудит 0.4 | DONE | v5-baseline-audit.json; snapshot2784 квестів/569 рецептів, task/reward/dependency ID; export ≠ доступ до Windows |
| 2 | Дослідження механік | IN_PROGRESS | 54 моди/56 записів,386 перевірених файлів доказів; 51 неповна карта та решта каталогу потребують дослідження |
| 3 | Карти прогресії | IN_PROGRESS | Create/Mek/AE2 core-карти DONE по 14 етапів; інші 51 карта явно часткові |
| 4 | Перебудова координат | DONE | Усі 136 глав; стара 2784 когорта:1679→1129 перетинів; 0 накладань/зворотних;15 тестів; клієнтський UI окремо |
| 5 | Поглиблення 48 епох | IN_PROGRESS | 277 нових квестів у всіх 48 епохах реалізовано/перевірено; старі лінії та решта модів ще не повністю перероблені |
| 6 | Перегляд нагород | DONE | 2793 предметні нагороди перевірено,2780payloadзмінено(2511 старих),48 команд збережено;0 майбутніх/OP/машин |
| 7 | Розширення рецептів | IN_PROGRESS | Поточний 33-рецептнийпідблок DONE(14 тестів),569 старих збережено; подальший міжмодовий баланс у плані |
| 8 | Предмети без джерел | IN_PROGRESS | 42064 рецепти/14615loot/2261 важливийпредмет перевірено;35 безявногоджерела+49nativecontext+1implicitcodec лишаються |
| 9 | Creative/альтернативи | IN_PROGRESS | Essence/3Poolroutes/29targets DONE; глобальні native/loot/невідомі обходи ще не повністю покрито |
| 10 | Інтеграційні тести | IN_PROGRESS | Node50/Python85/Java5237/native49 PASS, rebuild1136 файлівbyte-identical; повний інстанс/Survival/JEI/TPS BLOCKED—недоступний |
| 11 | Реліз і push | TODO | Не оголошувати 0.5 готовою до завершення перевіреного обсягу |

## Окремий стан 48 епох

Статуси стосуються змін v5; наявний контент v4 не видаляється і не вважається
повністю переробленим лише через його наявність.

| Епоха | Дослідження | Квести v5 | Рецепти v5 | Залежності v5 |
|---|---|---|---|---|
| 01 | IN_PROGRESS | IN_PROGRESS (4) | TODO | DONE (static) |
| 02 | IN_PROGRESS | IN_PROGRESS (3) | TODO | DONE (static) |
| 03 | IN_PROGRESS | IN_PROGRESS (4) | TODO | DONE (static) |
| 04 | IN_PROGRESS | IN_PROGRESS (8) | TODO | DONE (static) |
| 05 | IN_PROGRESS | IN_PROGRESS (5) | TODO | DONE (static) |
| 06 | IN_PROGRESS | IN_PROGRESS (1) | TODO | DONE (static) |
| 07 | IN_PROGRESS | IN_PROGRESS (8) | TODO | DONE (static) |
| 08 | IN_PROGRESS | IN_PROGRESS (5) | TODO | DONE (static) |
| 09 | IN_PROGRESS | IN_PROGRESS (5) | TODO | DONE (static) |
| 10 | IN_PROGRESS | IN_PROGRESS (6) | TODO | DONE (static) |
| 11 | IN_PROGRESS | IN_PROGRESS (4) | TODO | DONE (static) |
| 12 | IN_PROGRESS | IN_PROGRESS (7) | TODO | DONE (static) |
| 13 | IN_PROGRESS | IN_PROGRESS (7) | TODO | DONE (static) |
| 14 | IN_PROGRESS | IN_PROGRESS (6) | TODO | DONE (static) |
| 15 | IN_PROGRESS | IN_PROGRESS (11) | TODO | DONE (static) |
| 16 | IN_PROGRESS | IN_PROGRESS (5) | TODO | DONE (static) |
| 17 | IN_PROGRESS | IN_PROGRESS (4) | TODO | DONE (static) |
| 18 | IN_PROGRESS | IN_PROGRESS (4) | IN_PROGRESS | DONE (static) |
| 19 | IN_PROGRESS | IN_PROGRESS (10) | TODO | DONE (static) |
| 20 | IN_PROGRESS | IN_PROGRESS (18) | TODO | DONE (static) |
| 21 | IN_PROGRESS | IN_PROGRESS (8) | TODO | DONE (static) |
| 22 | IN_PROGRESS | IN_PROGRESS (2) | TODO | DONE (static) |
| 23 | IN_PROGRESS | IN_PROGRESS (5) | TODO | DONE (static) |
| 24 | IN_PROGRESS | IN_PROGRESS (2) | TODO | DONE (static) |
| 25 | IN_PROGRESS | IN_PROGRESS (3) | TODO | DONE (static) |
| 26 | IN_PROGRESS | IN_PROGRESS (9) | TODO | DONE (static) |
| 27 | IN_PROGRESS | IN_PROGRESS (3) | TODO | DONE (static) |
| 28 | IN_PROGRESS | IN_PROGRESS (16) | TODO | DONE (static) |
| 29 | IN_PROGRESS | IN_PROGRESS (3) | TODO | DONE (static) |
| 30 | IN_PROGRESS | IN_PROGRESS (14) | IN_PROGRESS | DONE (static) |
| 31 | IN_PROGRESS | IN_PROGRESS (18) | TODO | DONE (static) |
| 32 | IN_PROGRESS | IN_PROGRESS (20) | TODO | DONE (static) |
| 33 | IN_PROGRESS | IN_PROGRESS (1) | TODO | DONE (static) |
| 34 | IN_PROGRESS | IN_PROGRESS (4) | TODO | DONE (static) |
| 35 | IN_PROGRESS | IN_PROGRESS (3) | TODO | DONE (static) |
| 36 | IN_PROGRESS | IN_PROGRESS (1) | TODO | DONE (static) |
| 37 | IN_PROGRESS | IN_PROGRESS (2) | TODO | DONE (static) |
| 38 | IN_PROGRESS | IN_PROGRESS (1) | TODO | DONE (static) |
| 39 | IN_PROGRESS | IN_PROGRESS (6) | TODO | DONE (static) |
| 40 | IN_PROGRESS | IN_PROGRESS (2) | TODO | DONE (static) |
| 41 | IN_PROGRESS | IN_PROGRESS (5) | TODO | DONE (static) |
| 42 | IN_PROGRESS | IN_PROGRESS (1) | TODO | DONE (static) |
| 43 | IN_PROGRESS | IN_PROGRESS (1) | TODO | DONE (static) |
| 44 | IN_PROGRESS | IN_PROGRESS (10) | TODO | DONE (static) |
| 45 | IN_PROGRESS | IN_PROGRESS (1) | TODO | DONE (static) |
| 46 | IN_PROGRESS | IN_PROGRESS (1) | TODO | DONE (static) |
| 47 | IN_PROGRESS | IN_PROGRESS (1) | TODO | DONE (static) |
| 48 | IN_PROGRESS | IN_PROGRESS (9) | IN_PROGRESS | DONE (static) |

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

- root: docs/PLAN/PROGRESS, скрипт 20, інтеграція генераторів, нагороди, Git.
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
  запуск був на 0.4.0, повний FTB runtime на 0.4.1 не запускався.
- Інші перевірені Java-виклики не мають підтвердженої неоднозначності.
- Наступна конкретна дія: baseline snapshot v4 ID/нагород; завершити карти
  джерел, застосувати DAG layout, додати перевірений контент та нагороди.
- Знайдено 3 exported producer recipes Creative Pool, а не 2; Creative Essence
  має namespace mysticalagradditions. Остаточні зміни ще TODO.

### 2026-10-23 — аудит бази й контроль IDs

- FTB hotfix зафіксовано окремим комітом `c620e4e`; план раніше збережено
  в `1dcdf44`. Перевірка 23Python/41Node/5237Java пройшла.
- DONE baseline: `implementation/v5-baseline-audit.json`,
  `content/audit/v4-ids.json`:2784 квести/130 глав/569 рецептів/96 ключів.
- Аудит 2516 предметних+48 команднихнагород; їхні IDs збережено в snapshot.
- Відомі GUI-проблеми:1679 перетинів,96 зворотнихі 72 вертикальнихлокальнихліній;
  накладаньіконок 0. Layout ще не застосовано.
- Дозволено запис окремих v5 каталогів/карт/генераторів після hotfix;
  canonical SNBT змінюватиме root лише під час інтеграції.
- Наступна конкретна дія: інтегрувати готові source-backed maps/catalogs,
  зафіксувати generator layout з метриками, потім тематичні нагороди/баланс.

### 2026-10-24 — відновлення з файлів репозиторію

- Прочитано PLAN/PROGRESS, перевірено Git: `5ece770`; попередні агенти вже
  відсутні. Відновлено їхні файли та /tmp-чернетки, завдання делеговано новим.
- Нові власники: technology_v5_resume, magic_v5_resume, layout_v5_resume,
  rewards_v5_resume, balance_v5_resume, validation_v5_resume;
  mechanic_receipts_v5 — окремий native observer із 4 реальними процесами.
- Попередня пробна інтеграція 9capstone+33 рецепти:2793 квести/602 рецепти,
  Node41/Python67/SNBT/ID/DAG пройшли. Це НЕ фінальні кількості 0.5.
- Каталоги технологій 112 імагії 150 післяцього записані, ще не включені у
  фінальний runtime. Не заявляти їх згенерованими до нового запуску.
- Layoutv2:15 тестів, preview-only; очікується приблизно 33%скорочення
  перетинів від початкових 1679 після final-order constraints, не старі 70%.
- Наступна конкретна дія: зафіксувати перевірені генератори/політики,
  завершити переносні карти; потім повна генерація і незалежний валідатор.
- Nativeobserver4 процесів @епохи 4/10/16/23 у роботі; не додавати proof-квести
  до готового пакета без відповідного JAR/API/конфігів/тестів.

### 2026-10-24 — native production observers завершено

- DONE окремого підблоку: чотири реальні виробничі докази Create/Mek,
  шість перевірених маршрутів; збереження команди у власному SavedData.
- Виправлено доступність E10: доказ латуні включає незагрітий bootstrap
  AIA2, бо Blaze Burner стадії 15 ще недоступний. /give не є доказом.
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
  генерацію, оновити 48 статусів і залишити явні прогалини дослідження.

### 2026-10-24 — source-backed контент і перевірена інтеграція

- Реалізовано 277 нових цілей:112technology,150magic/adventure,9postgame,
  4nativeprocess,2coregaprepairs. Усі 48 епох мають нові цілі.
- Поточний runtime:3061 квест/136 глав/602 рецепти/96 виробничихключів;
  збережено всі 2784 старі ID/task/reward/dependencies і 569 старих recipeJSON.
- Реалізовано 3 повні core-карти(Create/Mek/AE2 по 14 етапів),
  54 унікальні моди/56 записів/377 етапів/678 посилань/386SHAфайлів.
  Powahupstream5.1.0-alpha не видається за встановлену 6.2.10.
- Архівні джерела зберігаються у content/research/evidence з незмінними
  байтами; docs/research містить читабельні карти, індекс та явні прогалини.
- Ключові виправлення:3 простих/альтернативнихPoolrecipes прибрано,
  Essence мистAgradditions синтезується після 48 завершень і витрачається
  у 22 рецептах; Hephaestus tier3/4 мають monotonic item/block floor21.
- Audit2261 важливого предмета не додавав жодних випадкових рецептів.
  35unresolved+49nativecontext+1implicitcodec потребують наступного аудиту.
- Поточні перевірки:50Node,85Python,5237Java,49nativeв 2JVM;
  повний цикл генерації дає 1136 однакових runtime-файлів.
- Табличний DONE(static) означає DAG/ID/gates, НЕ повне Survival-проходження.
  Квести кожної епохи лишаються IN_PROGRESS, поки решта великих ліній не
  перероблена. Збережені старі цілі не оголошено автоматично переосмисленими.
- Наступна конкретна дія ПІСЛЯ цього checkpoint: продовжити неповні карти
  з docs/research/REMAINING_COVERAGE.md (Occultism/NatureAura/Totemic та інші),
  розібрати 35static-source gaps за obtainability-v5-items.csv; потім
  перевірити реальні optional Create/Mek/AE2/FTB та UI на копії інстансу.
- 0.5 не є завершеним релізом. Тестовий проміжний пакет має версію 0.4.2-alpha.
