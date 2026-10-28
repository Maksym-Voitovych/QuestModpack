# AIA2 0.5.0 — журнал прогресу

Останнє оновлення: 2026-10-28 (часовий пояс користувача Europe/Kyiv). База `90ab63f`, робоча версія 0.4.13-alpha (Clibano controller/production); 0.5 ще не реліз.
Цей файл читати разом із [планом](AIA2_0.5.0_PLAN.md) перед продовженням.
Статуси: `TODO`, `IN_PROGRESS`, `DONE`, `BLOCKED`.

## Етапи

| № | Етап | Статус | Доказ / наступна дія |
|---|---|---|---|
| 0 | FTB Quests overload hotfix | DONE | Типізований міст, production script20, 16 справжніх Rhino assertions, Node41/Python23/Java5237; окремий fix-коміт |
| 1 | Аудит 0.4 | DONE | v5-baseline-audit.json; snapshot2784 квестів/569 рецептів, task/reward/dependency ID; export ≠ доступ до Windows |
| 2 | Дослідження механік | IN_PROGRESS | 61 мод /63 записи,1997 SHA-файлів карт; exact Forbidden2.6.1 і bytecode Valhelsia1.1.5; DraconicCI633 BLOCKED |
| 3 | Карти прогресії | IN_PROGRESS | 26 scoped core-карт DONE; Forbidden29етапів;35partial та невивчені моди |
| 4 | Перебудова координат | DONE | 140глав;0накладань/зворотних/вертикальних/довгих;1154перетини після5новихцілей |
| 5 | Поглиблення 48 епох | IN_PROGRESS | 567нових відv4;5Clibano цього блоку; старі обов’язкові лінії IN_PROGRESS |
| 6 | Перегляд нагород | DONE | 3087item-нагород;5нових; усі3346попередніх rewardpayloads збережено |
| 7 | Розширення рецептів | IN_PROGRESS | 623рецепти;54v5формули; усі623попередніх entries незмінні у0.4.13 |
| 8 | Предмети без джерел | IN_PROGRESS | 2447предметів;35native-source доказів;6IFfluidgaps залишаються |
| 9 | Creative/альтернативи | IN_PROGRESS | Clibano controller/menu/currentrecipe/paidstate/residues реалізовано; transitive/historicalresidue/IOforwarding відкриті |
| 10 | Інтеграційні тести | IN_PROGRESS | 228Python/57Node/5237Java;119MC@0.4.13/2JVM;776новихmodels;fullpack NOT RUN |
| 11 | Реліз і push | IN_PROGRESS | 0.4.13 проміжний блок; package/installer PASS; commit/push перевірити черезGit;0.5не завершено |



## Окремий стан 48 епох

Статуси стосуються змін v5; наявний контент v4 не видаляється і не вважається
повністю переробленим лише через його наявність.

| Епоха | Дослідження | Квести v5 | Рецепти v5 | Залежності v5 |
|---|---|---|---|---|
| 01 | IN_PROGRESS | IN_PROGRESS (4) | TODO | DONE (static) |
| 02 | IN_PROGRESS | IN_PROGRESS (4) | TODO | DONE (static) |
| 03 | IN_PROGRESS | IN_PROGRESS (4) | TODO | DONE (static) |
| 04 | IN_PROGRESS | IN_PROGRESS (13) | TODO | DONE (static) |
| 05 | IN_PROGRESS | IN_PROGRESS (5) | TODO | DONE (static) |
| 06 | IN_PROGRESS | IN_PROGRESS (3) | TODO | DONE (static) |
| 07 | IN_PROGRESS | IN_PROGRESS (13) | TODO | DONE (static) |
| 08 | IN_PROGRESS | IN_PROGRESS (5) | TODO | DONE (static) |
| 09 | IN_PROGRESS | IN_PROGRESS (8) | TODO | DONE (static) |
| 10 | IN_PROGRESS | IN_PROGRESS (7) | TODO | DONE (static) |
| 11 | IN_PROGRESS | IN_PROGRESS (21) | IN_PROGRESS (2 формул) | DONE (static) |
| 12 | IN_PROGRESS | IN_PROGRESS (17) | TODO | DONE (static) |
| 13 | IN_PROGRESS | IN_PROGRESS (14) | IN_PROGRESS (2 формули) | DONE (static) |
| 14 | IN_PROGRESS | IN_PROGRESS (13) | TODO | DONE (static) |
| 15 | IN_PROGRESS | IN_PROGRESS (29) | TODO | DONE (static) |
| 16 | IN_PROGRESS | IN_PROGRESS (12) | IN_PROGRESS (3 формул) | DONE (static) |
| 17 | IN_PROGRESS | IN_PROGRESS (4) | TODO | DONE (static) |
| 18 | IN_PROGRESS | IN_PROGRESS (11) | IN_PROGRESS (7 формул) | DONE (static) |
| 19 | IN_PROGRESS | IN_PROGRESS (35) | IN_PROGRESS (3 формул) | DONE (static) |
| 20 | IN_PROGRESS | IN_PROGRESS (40) | TODO | DONE (static) |
| 21 | IN_PROGRESS | IN_PROGRESS (23) | TODO | DONE (static) |
| 22 | IN_PROGRESS | IN_PROGRESS (7) | IN_PROGRESS (1 формул) | DONE (static) |
| 23 | IN_PROGRESS | IN_PROGRESS (9) | TODO | DONE (static) |
| 24 | IN_PROGRESS | IN_PROGRESS (8) | TODO | DONE (static) |
| 25 | IN_PROGRESS | IN_PROGRESS (10) | IN_PROGRESS (1 формул) | DONE (static) |
| 26 | IN_PROGRESS | IN_PROGRESS (9) | TODO | DONE (static) |
| 27 | IN_PROGRESS | IN_PROGRESS (8) | TODO | DONE (static) |
| 28 | IN_PROGRESS | IN_PROGRESS (41) | TODO | DONE (static) |
| 29 | IN_PROGRESS | IN_PROGRESS (4) | TODO | DONE (static) |
| 30 | IN_PROGRESS | IN_PROGRESS (16) | IN_PROGRESS (1 формул) | DONE (static) |
| 31 | IN_PROGRESS | IN_PROGRESS (35) | TODO | DONE (static) |
| 32 | IN_PROGRESS | IN_PROGRESS (30) | IN_PROGRESS (2 формул) | DONE (static) |
| 33 | IN_PROGRESS | IN_PROGRESS (1) | TODO | DONE (static) |
| 34 | IN_PROGRESS | IN_PROGRESS (7) | TODO | DONE (static) |
| 35 | IN_PROGRESS | IN_PROGRESS (5) | TODO | DONE (static) |
| 36 | IN_PROGRESS | IN_PROGRESS (2) | IN_PROGRESS (3 формул) | DONE (static) |
| 37 | IN_PROGRESS | IN_PROGRESS (2) | TODO | DONE (static) |
| 38 | IN_PROGRESS | IN_PROGRESS (1) | TODO | DONE (static) |
| 39 | IN_PROGRESS | IN_PROGRESS (8) | TODO | DONE (static) |
| 40 | IN_PROGRESS | IN_PROGRESS (13) | TODO | DONE (static) |
| 41 | IN_PROGRESS | IN_PROGRESS (16) | IN_PROGRESS (2 формул) | DONE (static) |
| 42 | IN_PROGRESS | IN_PROGRESS (4) | IN_PROGRESS (1 формул) | DONE (static) |
| 43 | IN_PROGRESS | IN_PROGRESS (1) | TODO | DONE (static) |
| 44 | IN_PROGRESS | IN_PROGRESS (14) | TODO | DONE (static) |
| 45 | IN_PROGRESS | IN_PROGRESS (14) | TODO | DONE (static) |
| 46 | IN_PROGRESS | IN_PROGRESS (1) | TODO | DONE (static) |
| 47 | IN_PROGRESS | IN_PROGRESS (6) | TODO | DONE (static) |
| 48 | IN_PROGRESS | IN_PROGRESS (10) | TODO | DONE (static) |




## Сесії та контрольні точки

### 2026-10-27 — ProjectE passive guards: відновлення IN_PROGRESS

- Відновлено checkpoint `7539c6b`; main/origin перевірено. Backup до змін: `/workspace/aia2-backups/before-projecte-passive-20261026T224959Z/checkpoint-7539c6b.tar.gz`.
- IN_PROGRESS: actual wearer/receiver checks для інвентарних ефектів, броні, Curios, bag/chest/pedestal, клавіш і world-use. Tablet Curios shortcut потребує окремого source floor47, який зберігається на відкритому меню після reload.
- Нові квести/рецепти/предмети/текстури цього guard-блоку:0; baseline3314/621/390/390 не змінюється. Проміжна версія0.4.10 готується лише після перевірок;0.5 не реліз.
- Наступна дія: завершити orphaned armor tests, Curios reconciliation, перевірити точні mixin selectors, JDK/native smoke і пакет; потім оновити результати, commit/push. Повний Windows-інстанс недоступний.

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

## Власники та відновлення незавершених файлів

Поточну інтеграцію, тести й Git веде root. Допоміжні агенти цього блоку
завершилися або вичерпали доступний ліміт; активних власників файлів немає.
Не вважати старі імена агентів доказом незавершеної фонової роботи.

Portable результати й SHA збережено в `content/audit/v5-pending-research.json`.
Попередні Apotheosis/IP/Roots/AA/split Apothic та поточні ProjectE passive
файли інтегровані; наступну дію брати з останньої контрольної точки нижче.
Не покладатися на /tmp або історію чату.

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

### 2026-10-24 — checkpoint07e93a6 та підтверджені native-виправлення

- Основну інтеграцію source/квестів/координат/нагород надіслано у main:
  `07e93a6ab59d2907db35cc1b08e15bae491341dd`.
- Виявлено і виправлено справжній обхід Draconic cached Fusion через
  packet-start/byKey/NBT. Перевірка перед активним тиком скасовує недозволений
  процес і заряджання без витрати входів. Новий JAR0.4.2.1, API4 збережено.
- Дві нові contract/handler регресії:16умов із реальним GuardPolicy
  у модельованому Minecraft/DE host. LiveDEdispatch не запускався;
  попередні49native2JVM-перевірок стосуються0.4.2, це не приховано.
- Закрито11native-sourceвипадків, без нових рецептів: Amadron3,
  IEwrappers2, implicitEternalSingularity, Totemicцеремонія/Baykokdrop,
  NAbirth_spirit, FAblood_test_tube/eternal_stella.
- Виправлено2optionalцілі після AlmostUnified зі збереженням ID:
  EnderIOobsidian→Create, Oritechnickel→IE. Жодного з602recipeJSON
  ці заміни не торкнулися;569старих хешів знову перевірено.
- Додано зрозумілі примітки матеріалів у квестах, не змінюючи старі
  SHA-pinned авторські каталоги. Дані міграції: v5-item-normalization-migrations.json.
- Аудит має22невідомі статичні джерела замість35;49раніше описаних native
  випадків та1implicit-codec залишаються. Не створювати випадкові рецепти.
- Остаточний послідовний прогін після генерації:91Python/50Node PASS;
  5237Java build,16DEhandler, статичні SNBT/IDs/DAG/gates PASS.
- Один паралельний тестовий прогін прочитав проміжний base-runtime під час
  генерації; його результат НЕ зараховано. Повторний прогін на стабільних
  файлах пройшов. Надалі: генерація завершується ПЕРЕД залежними тестами.
- Незалежний огляд hotfix не знайшов блокерів. Виправлено також старий ID
  у тексті нікелевого завдання; вихідний авторський каталог не змінено.
- Архів перевірено за CRC і повним SHA-маніфестом; інсталятор з розпакованого
  пакета пройшов dry-run без записів у тестовий інстанс або його world-marker.
- Наступна дія після поточного hotfix checkpoint: продовжити неповні карти
  (51мод) і22source-gapвипадки; actualDE/Create/Mek/AE2/FTB/JEI/Survival/TPS
  перевіряти в повному інстансі, а не оголошувати за статичним тестом.

### 2026-10-24 — продовження: доказові механіки та захист нових ID

- Відновлено чистий `4a4f993`; резервна копія перед змінами:
  `/workspace/aia2-backups/before-depth-20261024/checkpoint-4a4f993.tar.gz`.
- DONE інфраструктури: валідатор нативних advancement-доказів перевіряє
  JSON, SHA джерел, версії мода та власника тригера, обов'язкову дію в
  AND/OR-вимогах. Inventory-fallback не вважається доказом ритуалу.
  Прямі native-grant `minecraft:impossible` потребують окремого контракту
  місця видачі; це не підтвердження запуску повного модпаку.
- Додано вузький механізм виправлення предметних цілей без зміни ID,
  порядку завдань, нагород і залежностей; самі виправлення ще інтегруються.
- Snapshot checkpoint `4a4f993` тепер захищає всі 3061 опубліковані квести,
  136 глав і 602 рецепти; генератор зберігає також нові глави v5.
- Аудит джерел розуміє точні вкладені виходи Apotheosis, IP і Roots,
  не сканує інгредієнти як продукти й не створює автоматичних рецептів.
- Перевірено 39 релевантних Python-тестів і поточний v5-валідатор.
  На цьому інфраструктурному checkpoint кількості runtime не змінено:
  3061 квест,602 рецепти,390 предметів/текстур,96 виробничих ключів.
- IN_PROGRESS: карти й реальні механічні завдання Occultism/NA/Totemic,
  Ars/Botania, IE/PNC/IF та логістики; 22 source-gap випадки й творчий
  варіант Mana Tablet. Чернетки не вважаються встановленим runtime.
- Наступна конкретна дія: інтегрувати перевірені карти/контракти/квести,
  виправити стартову книгу Iron's Spells та альтернативи creative tablet;
  завершити генерацію ПЕРЕД повним прогоном тестів і оновленням пакета.

### 2026-10-25 — інтегровано поглиблення механік і творчої мани

- Інфраструктуру нативних доказів/міграцій/нового snapshot збережено й push у `6e7e174`.
- DONE цього підблоку:84 нові квести (natural22,Ars/Botania17,industrial23,logistics22),49 контрактів нативних дій і7AIA2advancementJSON. Поточний runtime3145квестів/136глав/603рецепти.
- 10додаткових core-карт завершено: Occultism, NatureAura, Totemic, Ars, Botania, IE, PNC, IntegratedDynamics/Tunnels і ModularRouters. Усього13complete,45partial,58модів/60записів/482етапи. IF збережено partial: newer3.6.39source не видається за точний3.6.38artifact.
- Nativeцілі перевіряють ритуали, церемонії, формування мультиблоків, логічні типи/оператори, конфігурацію та конкретні магічні дії. Proof_scope не обіцяє виробництва лише за формування машини. ORinventoryfallback відхиляється.
- Виправлено два Occultism miner-докази під чинні AIA2recipe IDs. Iron beginnerbook замінено wimpy→copper точково без зміни task/quest IDs. Пил біодизельного каталізатора описаний як tag, без необґрунтованої вимоги дубліката конкретного мода.
- Source-аудит усіх22попередніх випадків:18 підтверджених nativeшляхів,1ремонт книги,3IFпрогалини. Нові fluid-цілі додають4випадки, разом7явних gap; без вигаданих рецептів.
- Закрито3creativeManaTablet producers, збережено2ordinaryroutes і gate5. Новий TerraPlate вимагає completed48/CreativeEssence/фінальних матеріалів;602старіrecipeJSON byte-preserved.
- Guard0.4.3 з новими native player inventory/accessories та pool exchange mixin блокує творчий компонент до completed48, включно з імпортом. Native crafting/automation output також перевіряються. Стек/NBT не змінюються, окремого tick-сканера немає. Прямі сторонні ManaItem capability-виклики поза цими маршрутами лишаються в обмеженнях.
- Тести:110Python/50JS PASS,5237Java build PASS;22 productionhelper/realpolicy умови в модельованому host PASS. Реальний мінімальний Minecraft0.4.3 пройшов49assertions у2JVM і restart SavedData. Botania/DE та інші optional моди в цьому сервері відсутні — це НЕ fullpack dispatch.
- Повторна генерація:1144runtime-файли byte-identical. Останній точковий перегляд прибрав зайвий матеріальний task із нової IE-цілі; повторний static/DAG/SNBT/контрактний прогін пройшов.
- Усі3061попередніquest/task/reward ID,136контейнерів глав і залежності збережено.84нові тематичні нагороди;2793старі payload з checkpoint не змінено.390предметів/PNG і96виробничих ключів збережено; нових предметів/текстур0.
- Наступна конкретна дія: завершити core-карти Roots Classic, Apotheosis та Immersive Petroleum за новими exact-version джерелами з followup-аудиту; далі решту45часткових карт і старі обов'язкові лінії. Паралельно перевірити7fluid-bucket джерел (IF6,PNC1). Fullpack49action-proof/96key/JEI/Survival/TPS сценарії наведені в docs/testing/NATIVE_ACTION_ACCEPTANCE.uk.md.
- Пакет0.4.3-alpha створено й перевірено за CRC та повним SHA-маніфестом. Dry-run з розпакованого пакета не змінює інстанс; справжнє встановлення у тимчасовий інстанс успішно резервує старий0.4.2.1JAR і зберігає world-marker. Windows-інстанс користувача не змінювався.
- 0.5не оголошено завершеною. Код, ресурси, документація й інсталятор цього підблоку збережені разом; точний фінальний commit/push перевіряти через git log/origin і delivery-звіт поруч із ZIP.

### 2026-10-25 — окреме виправлення взаємодії зі ступкою Roots

- Відновлено `61cc7ab`, створено backup `/workspace/aia2-backups/before-core-next-20261025/checkpoint-61cc7ab.tar.gz` і snapshot усіх3145 quest/task/reward ID,136глав,603recipe ID. Старий0.4.3JAR також збережено поза Git.
- DONE: точний Roots1.5.10 `MortarBlockEntity.tryActivateRecipe` запускається від пестика поза BlockEntityTicker. Тому контекстний RecipeManager hook не перевіряв gate15/30 компонентних рецептів при gate1 ступки. `RootsMortarMixin` перевіряє вибраний native holder через чинну політику власника до assemble/spawn/очищення входів. Вставлення/повернення інгредієнтів і клієнтський preview збережено.
- Новий companion0.4.4-alpha, API4 збережено. Installer/package preflight відхиляє JAR без цього hook до backup/запису в інстанс. Це цілісний hotfix, а не завершений реліз0.5.
- Перевірено: JDK21/NeoForge build і5237Java assertions;2Rootstests із18умовами actual-handler/real-policy у модельованому Minecraft host;18installer tests PASS. Реальний optional Roots dispatch ще НЕ запускався; нових proof-квестів цей hook не видає.
- Runtime-контент на цьому кроці незмінний:3145квестів,603рецепти,390предметів/PNG,96виробничих ключів. Надалі завершити готову карту Apotheosis/12квестів, nativeконтракти, LPG source та точкові IP-предметні виправлення.
- Перервані підзадачі Roots/AA/IP залишили portable source-evidence; незавершені карти/чернетки не вважаються інтегрованими. Коли допоміжні агенти вичерпали ліміт, інтеграцію й перевірки продовжує root.

### 2026-10-25 — core-depth checkpoint0.4.4

- Roots hotfix `396b539cb02e99c7cbef84d0106a204beab3ea51` збережено окремо та push у main підтверджено.
- DONE поточного контентного підблоку:22нові квести(12Apotheosis/10Petroleum),17нативних контрактів і3purity advancementJSON. Runtime3167квестів/137глав/603рецепти/390предметів іPNG/96ключів. Нових рецептів/предметів/текстур0.
- DONE двох основних карт:Apotheosis8.9.0 та Petroleum4.5.0-39. Усього15core/43partial/58mapped mods. Roots точні source отримано й збережено, але поглиблення карти лишається IN_PROGRESS.
- Два збережені IP-таргети виправлено на diesel_sulfur за точним export. Усі3145старіID/task/reward/dependencies та старі нагороди збережено; повний603-entryrecipebundle незмінний. Результат у implementation/core-depth-next-preservation.json.
- Source-аудит2293предметів:32native-source докази; LPG підтверджено exact8.2.23. Динамічний Gem loot та sulfurousdieselbucket підтверджено без crafting-заглушок. Залишилося6IFfluid gaps; точніIF3.6.38/Titanium4.0.43 артефакти BLOCKED, новіші source не підміняють їх.
- PASS:117Python/50Node/5237Java та build;18Rootsactual-handler/real-policy модельованих умов. Реальний мінімальний MC0.4.4:49assertions у2JVM,650тіків і restart SavedData. Fullpack optional/JEI/UI/Survival/TPS NOT RUN.
- Повторна генерація1148runtime-файлів byte-identical. SNBT/DAG/ID/key/source/reward/layout checks PASS; усі137глав без накладань/зворотних/вертикальних/довгих локальних ліній. Перетинів1133, як до22новихцілей. Однакова2784когорта1679→1129.
- README/CHANGELOG/інсталятор/звіти й ручні сценарії оновлено; читабельний звіт docs/AIA2_0.4.4_CHECKPOINT.uk.md. Повний0.5не оголошено готовим.
- Наступна конкретна дія: основна карта Roots Classic (вівтар/Imbuer/standing stones/реальні ритуальні результати), потім AAcore. Split Apothic1.6.4/1.4.0 джерела й SHA в pending-research. Після них решта43часткових карт і старі обов’язкові лінії48епох.
- Пакет `/workspace/shared/downloads/AIA2-runtime-0.4.4-alpha.zip` пройшов CRC/повний SHA-маніфест. Розпакований інсталятор: dry-run0записів; справжній тимчасовий upgrade резервує0.4.3JAR, ставить0.4.4 і зберігаєworld-marker. User Windows інстанс не змінювався.
- Проміжне пакування відхилено через зміну report-файла під час обчислення маніфесту. Повторний пакет на стабільному дереві пройшов перевірку; надалі завершувати метадані ПЕРЕД пакуванням і не змінювати включені файли до його завершення.

### 2026-10-25 — Roots/AA/split Apothic: інтеграція в роботі

- Почато з чистого1145f1b; backup before-roots-aa-20261025T090419Z/checkpoint-1145f1b.tar.gz. Інкрементний snapshot1145f1b захищає22додатковіID поверх попередніх3145 та137глав/603recipeID.
- IN_PROGRESS перевірки нового блоку:45нових квестів(12Roots,11AA,22split Apothic),4основні карти,3AAміжмодові рецепти; перша генерація3212quests/606recipes пройшла static.
- НовийRootsnative observer ловить не тимчасовий doEffect.clear, а фактичний emptyAltar після оплати.2нові team-bound SavedData proofs; існуючі4збережено.49modelумов actual-helper/handler та JDK21build PASS; fullpack NOT RUN.
- Native spawner hook перевіряє обидві руки до findMatch/apply/списання;6rune itemfloors і15recipefloors, live team/fake/unready.15actual-handler/real-policy модельованих умов PASS. Ефективні Apotheosis-rune recipes мають пріоритет над standaloneSpawners defaults.
- СтарийE04_X_orchid_sample виправлено точковим overlay на vanilla підготовчі квіти. ChargedFocus07/08 залишено на4: підтверджено rareOverworldNetherWartloot; новий штатнийnativeproof15не заперечує ранній альтернативний шлях.
- FullPython/native2JVM/audit запущено, результат ще перевіряється. Наступна конкретна дія: завершити ці перевірки, ідемпотентний rebuild, звіти/README/manualacceptance; зафіксувати весь цілісний0.4.5блок і push.

### 2026-10-25 — перевірений checkpoint0.4.5

- DONE цього підблоку:45 нових квестів (Roots12, AA11, Enchanting12, Spawners10),4 основні карти,20 контрактів нативних дій і2 командні докази Roots. Runtime:3212 квестів,138 глав,606 рецептів,390 предметів/PNG,96 виробничих ключів. Нових предметів/текстур0.
- Збережено всі3167 попередні quest/task/reward ID, залежності та нагороди, а також603 попередні custom recipe JSON. Ранній optional гербарій має точкове виправлення цілей і пояснення; два старі Charged Focus квести лишилися в епосі4 з поясненням рідкісного Overworld-луту.
- Реалізовано3 міжмодові формули AA; замінено3 native producer IDs, збережено3 reset-рецепти. Bootstrap не потребує олій. Native Spawner hook перевіряє обидві руки до застосування/списання;6 item floors і15 recipe floors. Чинний експорт із рунами має пріоритет над standalone-припущеннями про Comparator/Sugar/Clock.
- Виробничих правил6 (старі4 плюсRoots2), перевірених recipe IDs8. Roots proof записується після фактичного emptyAltar, із перевіркою входів/owner/policy. Гарантію прийняття output entity світом не заявлено: native код ігнорує addFreshEntity boolean. Незакінчений native ритуал після restart цей hook не відновлює.
- PASS:126 Python tests,50 Node tests,5237 Java assertions і JDK21 build. Нові модельовані перевірки справжніх helper/handlers із GuardPolicy:Roots49, Spawner15. Справжній мінімальний Minecraft0.4.5:49 assertions у2JVM,650 ticks і restart SavedData. Fullpack optional/JEI/UI/Survival/TPS:NOT RUN.
- SNBT/DAG/ID/96key/gates/rewards/recipes/resources/source checks:PASS.138 глав без накладань, зворотних, вертикальних і надто довгих локальних ліній;1141 перетин проти1133 до45нових цілей. Стара порівнянна2784-когорта лишилася1679→1129.
- Rebuild виявив випадковий set-порядок трьох нових recipe gates. Виправлено sorted IDs; регресія в окремих Python-процесах із PYTHONHASHSEED11/29 пройшла. Повторна повна генерація1157 runtime-файлів byte-identical. Аудит2320 предметів має35 native-source доказів і6 IF-прогалин; штучних рецептів для них не додано.
- PLAN і таблицю48епох оновлено. Виправлено формат рядків10/11 після попереднього надто широкого regex; надалі оновлювати таблиці лише в межах окремих секцій. README/CHANGELOG/докладний checkpoint0.4.5 та manual acceptance збережено.
- Наступна конкретна дія:основні карти Modern Industrialization2.5.10/Oritech1.2.13, потім решта41 часткової карти й невивчені моди, старі обов’язкові лінії48епох та глобальний баланс. Native Roots dayTime/subset-mutation/unfinished-restart залишаються TODO; точні IF-артефакти BLOCKED. Повний0.5 не оголошено готовим.
- Пакет0.4.5 пройшов CRC/повний SHA-маніфест. Розпакований інсталятор:dry-run без записів; тимчасове справжнє оновлення резервує0.4.4JAR, ставить0.4.5 і зберігає маркер світу. Фінальний metadata-repack має зберегти всі1158 перевірені runtime+installer хеші. Windows-інстанс користувача не змінювався.

### 2026-10-25 — MI/Oritech та мутації Roots: інтеграція в роботі

- Відновлено8c699fa; backup: `/workspace/aia2-backups/before-industrial-core-20261025T121559Z/checkpoint-8c699fa.tar.gz`. Snapshot захищає всі3212квестів/138глав/606recipeIDs.
- IN_PROGRESS: Modern Industrialization2.5.10 — власний direct-list crafter, оплачений кеш, нативні smelting/cutting/compost proxies і Replicator поза Recipe API. Oritech1.2.13 — cached value identity, Centrifuge/Refinery/Cooler/Tainted direct-list/commit та dust compaction.
- DONE реалізації, ще не фінальної інтеграції: Roots full-input mutation match і щоденний noon.4релевантні Pythonтести PASS:48Roots actual-handler/native-predicate і14Oritech actual-handler/real-policy умов у модельованому host. Optional mod dispatch не запускався.
- Наступна дія: завершити MI reload/cache регресії, точні controller floors і карти/квести; потім стабільна генерація, повний прогін, JAR0.4.6 і package. Старий0.4.5 не замінювати без перевіреного0.4.6.

### 2026-10-26 — перевірений MI/Oritech підблок0.4.6

- DONE коду й контенту:30 нових optional-квестів(15MI/15Oritech),2core-карти,11nativeactionконтрактів та1customadvancement. Усього3242квести/138глав/610рецептів/390предметів іPNG/96ключів. Новихпредметів/текстур0.
- 4 міжмодові машинні формули зберігають native матеріальні витрати;6cheapproducers замінено. 30item/block floors,41native+5custom gates узгоджено. Replicator99, keycopy завжди denied. Ранній Oritech wafer25 лишається fluid-centrifuge шляхом; laser32/deepdrill44 не перетворено на вигадану particle-exclusive вимогу.
- MI direct-list/cached/proxy/replication та Oritech cached/direct-list/fluid/dust маршрути отримали server checks. Unpaid MI cache відновлюється, paid live-rebind тільки при тотожному full codec; слабкі кеші без world scanner.
- Roots mutation вимагає повного складу; Radiant noon працює щодня. Інші native predicates/powder cost збережено. Незавершений altar restart recovery щеTODO.
- PASS:143Python/50Node/5237Java build;53MI+16Oritech+48Roots нових actual-helper/handler model assertions. Справжній мінімальний MC0.4.6:61assertions,2JVM,650ticks,restart SavedData. Optional mod dispatch/JEI/UI/Survival/TPS NOT RUN.
- Усі3212 попередні non-coordinate quest payloads, dependencies та606 custom recipe entries незмінні; старих reward payload changes0. Layout усіх138глав PASS; координати змінилися у3главах, перетини1141→1142 при30новихцілях. Стара2784когорта1679→1129.
- Явні межі:paid generated MI conversion після source reload paused; cache timers~20s+, native NBT не доводить старий codec післяrestart. Oritech Atomic fresh denied lookup може штатно скинутиRF; універсального refund немає.
- IN_PROGRESS доставки:ідемпотентний rebuild, installer/package, commit/push. Не оголошувати0.5релізом. Точні підсумки у docs/AIA2_0.4.6_CHECKPOINT.uk.md та implementation/release-report.json.
- Наступна конкретна дія після доставки:core-карти EnderIO8.2.12-beta/Powah6.2.10 за exact джерелами; решта39partial, невивчені моди, старі обов’язкові лінії48епох і fullpack acceptance.6IFfluid gaps залишаютьсяBLOCKED.

- DONE доставки до коміту:1158 runtime-файлів byte-identical після окремої генерації з PYTHONHASHSEED43. ZIP CRC/повний SHA-маніфест PASS. Extracted installer dry-run0writes; справжнє тестове оновлення0.4.5→0.4.6 резервує старийJAR, зберігає synthetic world-progress marker та чужий квест усередині власної глави. Фінальний metadata-repack повторює маніфест і перевіряє ті самі1159 runtime+installer hashes.
- Усі зміни цього цілісного підблоку підготовлені для main commit/push. Точний hash/status визначати через git log/origin та delivery-report поруч із ZIP; не вигадувати self-referential hash у цьому файлі. Наступну сесію починати з першої незавершеної дії вище.

### 2026-10-26 — EnderIO/Powah: продовження

- Відновлено чистий1a3ee22, main/origin перевірено. Резервна копія: `/workspace/aia2-backups/before-energy-core-20261025T232905Z/checkpoint-1a3ee22.tar.gz`. Snapshot захищає30новихID поверх3212, усі138глав і610рецептів.
- IN_PROGRESS: exact EnderIO8.2.12-beta core та аудит його машинних кешів; Powah6.2.10 source потрібно спочатку підтвердити, бо старий cachedsource5.1.0-alpha не відповідає встановленійверсії.
- Незавершена робота не позначенаDONE. Наступна дія:отримати exact source, перевірити native selection/consumption, інтегрувати обґрунтовані квести й рецепти, потім тести/коміт/push.

### 2026-10-26 — EnderIO/Powah 0.4.7: перевірений код і контент

- DONE: 19 optional-квестів (18 EnderIO / 1 Powah), одна основна карта EnderIO, 5 машинних формул, один native Painting контракт і 2 командні виробничі докази. Runtime: 3261 квест, 139 глав, 615 рецептів, 390 предметів/PNG і 96 виробничих ключів. Нових предметів і текстур: 0.
- Усі 3242 попередні quest/task/reward payloads і залежності, крім координат, та 610 custom recipe entries збережено. Перевірено 48 предметів storage-family і 103 native producers: замінено 13 дешевих шляхів (зокрема 5 compressed steel), збережено 86 lossless conversions і 4 пізні MA26 маршрути.
- EnderIO: перевірки task/cache, фактичного виходу, Crafter, Tank і native smelting proxies. Powah перевіряє власника Orb, а не Rod. Додано виробничі докази Blazing (епоха29) і Energetic Alloy (епоха19); загалом 8 правил / 11 recipe IDs, SavedData schema1 збережено. Фінальне списання FE у Rod окремо не виміряне.
- Callback-вибір рецепта ізольований від контексту виклику, щоб одноразовий кеш не залишався порожнім після запуску або відкриття стадії. Фактичне виконання завжди перевіряє recipe/item/owner policy. Незмінний codec дозволяє переприв’язку кешу зі збереженням прогресу; змінений task зупиняється.
- PASS: 157 Python tests, 50 Node tests, 5237 Java assertions і JDK21 build; 206 proxy та 43 energy actual-helper/handler/real-policy модельованих умов. Мінімальний Minecraft0.4.7: 70 assertions у 2 JVM, 650 ticks і SavedData restart. Optional EnderIO/Powah dispatch, JEI/UI, Survival і TPS: NOT RUN.
- DONE: перевірка джерела Powah — офіційний v6.2.10 tag і POWAH_VERSION release environment задають версію. Невикористаний mod_version5.1.0-alpha не доводить іншої версії source. Powah core: PARTIAL; 16 концептів збережено в content/audit/v5-powah-core-pending.json, це ще не реалізовані квести.
- Відкритий підтверджений шлях: Fire Crafting від світового вогню може створити grain до епохи19; item/use gate залишається19. Сліпа заборона зламала б обов’язкову прогресію. Потрібна явна атрибуція вогню й автоматизації, без припущення про найближчого гравця. Binary/API download повернув Tunnel403 навіть після escalation; source/model тести не доводять optional dispatch.
- DONE: 1162 runtime-файли byte-identical після окремої генерації PYTHONHASHSEED67. Layout усіх139 глав PASS: 1142→1143 перетини при19 нових цілях; стара2784-когорта лишається1679→1129. Додано19 тематичних нагород; старі нагороди не змінено.
- DONE: ZIP CRC і весь SHA256 manifest, 1162 runtime hash та hash інсталятора. Запакований CLI dry-run: 0 записів. Тестове оновлення0.4.6→0.4.7 зберегло синтетичний прогрес світу та сторонній квест і зарезервувало старий JAR. Звіт: implementation/energy-package-install-v5.json. Реальний Windows-інстанс не змінювався.
- Git: цей блок призначений для окремого коміту в main та push без force. Остаточний hash/status перевіряються через git log/origin/main і зовнішній delivery report, щоб не вбудовувати самопосилальний hash у пакет. Повний0.5 не реліз.
- Наступна конкретна дія: атрибуція EnderIO Fire Crafting без deadlock, потім повний Powah core за16 збереженими концептами, решта38 partial/невивчених модів і старі обов’язкові лінії48 епох. Шість IF fluid gaps залишаються BLOCKED.

### 2026-10-26 — Fire Crafting / Powah0.4.8

- DONE реалізації та доступних перевірок:19нових квестів (18Powah/1EnderIO),3Nitro mechanical recipes, одна Powah core-карта28етапів і одна нова EnderIO worksite стадія.3280квестів/139глав/618рецептів/390предметів іPNG/96ключів. Новихпредметів/текстур0.
- Backup до змін: /workspace/aia2-backups/before-fire-powah-20261026T102902Z/checkpoint-d756a9a.tar.gz. Incremental snapshot захищає19новихID поверх3242 і615recipes; незалежний fullpayload audit зберігає всі3261попередні квести/нагороди/dependencies без змін, крім координат.
- Fire Crafting: серверний explicit worksite claim, current canonical recipe/base/dimension, allpossible outputs/components, key blacklist іpostburn block floor. Звичайний вогонь таFireWater сходяться уguard до RNG/предметів/зміни основи. Не приписувати цей протокол конкретному полум’ю: команді належить робоча ОСНОВА.
- SavedData dimension-specific, збереження післяrestart; base mutation відкликаєowner, extinguishне відкликає. Семантично корумповані дані повертають cleanblocked sentinel; unreadable existingbinary не замінюється empty. DimensionDataStorage swallowing виключень враховано. Порожній ledgerне записується до реальногоclaim.
- /reload raw list оновлюється за generation snapshot, currentidentity завжди перевіряється. Native EnderIOspawnігноруєentityacceptance; нового production proof не заявляється.
- PASS:166Python/50Node/5237Java іJDK21build;46actual-helper/handler/real-policy модельованих умов. МінімальнийMC0.4.8:90assertions у2JVM,650ticks/SavedDatarestart. Optionaldispatch/JEI/UI/Survival/TPS:NOT RUN.
- Повний42064producer scan перевіряє3Nitrotargets. Усі9native units і попередніSpiritedgenerators збережено; по2magitechinputsдодано. Машинні outputs не мають vanilla craft:true пастки. Powah16концептів перетворено на17цілей плюсNitroкомпаратор; scopedcore23,partial37.
- Layout139глав:0structuralwarnings;1143перетини, як у0.4.7. Предметнихrewardentries3016,20нових, старихpayloadchanges0.
- DONE rebuild/пакування:1162runtimeфайли byte-identical PYTHONHASHSEED73; ZIPCRC/весьmanifest перевірено. ЗапакованийCLI dry-run0writes; тестове оновлення0.4.7→0.4.8 зберігає synthetic world/fireledger ічужийквест, резервуєстарийJAR. Звіт implementation/fire-powah-package-install-v5.json. Windows-інстанс не змінювався.
- Git: цей цілісний блок зберігається окремим комітом уmain іpushбезforce; фінальнийhash/status визначати черезgit log/origin/main таexternaldeliveryreport. Повний0.5не реліз.
- Наступна конкретна дія: exact core-карти ProjectE1.1.0/Draconic Evolution3.1.4; решта37partial/невивчених модів істаріобов’язковілінії48епох. RootsunfinishedritualrestartTODO;6IFfluidgapsBLOCKED. Повнийігровийacceptanceзалишаєтьсяокремим.

### 2026-10-27 — ProjectE/Draconic0.4.9: інтеграція IN_PROGRESS

- Відновлено1915b80; backupдо змін:/workspace/aia2-backups/before-projecte-draconic-20261026T193423Z/checkpoint-1915b80.tar.gz. Incremental snapshot зберігає19новихID поверх3261 і618recipeIDs.
- DONE коду, ще не фінальної доставки: ProjectEAccess і3menu/output hooks; чинні team/stage/whitelist/EMC/component перевірки, нормальний/quickmove output іcurrentmenu association. Tablet47відрізняєтьсявідtable45. Знання й EMCгравця не очищуються.
- FuelMapperоновлюється ПІСЛЯfilteredEMCmap; errorочищуєmap/fuelcache іpauseaccess. Whitelistконфігурація не скидається вgenericclearRuntime,боscript25викликаєйого післяEMCeventнаfirsttick. Окреміpauseнаscriptload/remap/error/serverstop збережено.
- TimeWatchdirectbonus ticks перевіряють receiverowner передкожноюітерацією; targetcontext встановлено/відновлено черезfinally. ModelPASS:66output/22watch; Node52PASS, Java5237/buildPASS. МінімальнийMC0.4.9:90assertions/2JVM/650ticksPASS, optionalProjectEdispatchNOT RUN.
- ProjectEcore:18новихoptionalквестів/27етапів карти/74SHAджерела.3Draconicfusionформули за exactexport зберігають усіnative costs/tier/energy/catalyst і2losslessconversions;7boundedtestsPASS. Повнийsuite/інсталятор ще перевірити.
- Draconiccore IN_PROGRESS:джерело3.1.4prefix є; exactCIbuild633provenance BLOCKED черезнезавершенепідтвердження. Не називатиexact633перевіреним. Агентdraconic_core_next_v5записуєpartialmap/16questdraftбезподальшихмережевихочікувань.
- Наступна конкретнадія:завершитиDEdraft, regenerate/validate,повнийtest/rebuild,package/installer,оновленнястатусів іcommit/push. Не повторювати реалізованікод/джерела; див.gitstatus.0.5не реліз.

### 2026-10-27 — перевірений ProjectE / Draconic0.4.9

- DONE: 34нові optional-квести (18ProjectE/16Draconic),3fusion-рецепти, ProjectE core27етапів. Draconic partial23етапи з реальними залежностями;7попередніх stage IDs/refs і порядок збережено. CI633→commit BLOCKED; source3.1.4prefix і точний експорт не видаються за binaryverification.
- Runtime:3314квестів/140глав/621рецепт/390предметів іPNG/96ключів. Усі3280попередні non-coordinate payloads/dependencies/rewards та618recipe entries незмінні. Нових предметів/текстур0;34нові предметні нагороди,3050загалом.
- ProjectE: current team/table45/tablet47, active menu/slot association, whitelist/currentpositiveEMC/rawcomponents/keypolicy до списання. FuelMapper після finalmap; error очищує map/fuel іpause. Додаткового prune/видаленнязнань/ЕМСнемає. GenericclearRuntime НЕ скидаєPЕ-конфігураціюпісляfirsttick.
- TimeWatch: кожен bonus тик перевіряє targetowner, встановлюєtargetcontext івідновлюєparent черезfinally. Passive armor/Curios/rings/world tools залишаються IN_PROGRESS, не називати цей блок універсальним захистоммода.
- PASS:178Python/52Node/5237Java іJDK21build;66output/22watch actual-helper/handler models. СправжнійRhino85 перевіривновий map→fuel→ready іerrorclosure; застарілуfixture оновлено, потім весьsuiteперезапущеноуспішно. МінімальнийMC0.4.9:90assertions/2JVM/650ticks/SavedDatarestart; optionalProjectE/Draconic dispatch NOT RUN.
- Повний42064producer scan:3fusionprimaryroutes замінено,2lossless IO↔relay збережено; всіnativecosts/catalyst/tier/energy/output ігеометріядо11інжекторів перевірені статично. Emptylowertier не знижуєminimumtier, враховуютьсязайнятіinjectors.
- Rebuild1163runtimeфайлів byte-identical PYTHONHASHSEED79. Layout140глав безstructuralwarnings;1143→1147перетини після34новихцілей. Fullpack/JEI/UI/Survival/TPS NOT RUN.
- DONE пакування: ZIP CRC/повний manifest і1163runtime hashes перевірено. Запакований CLI dry-run0writes; тестове оновлення0.4.8→0.4.9 резервуєстарийJAR і зберігає synthetic world/fire/knowledge+EMC та стороннійквест. Звіт implementation/projecte-draconic-package-install-v5.json; реальнийWindows-інстанс не змінювався.
- Git: цей блок зберігається окремим комітом уmain іpushбезforce; фінальнийhash/status через git log/origin/main та externaldeliveryreport. Повний0.5не реліз.
- Наступна конкретна дія: ProjectE passive inventory/Curios/armor/world-tool аудит; підтвердження exactDraconicCI633заJAR/source (BLOCKED до доступногодоказу). Далі37partial/невивчені моди, старіобов’язковілінії48епох, Rootsunfinishedritualrestart і6IFfluidgaps. Не повторювати вже завершеніguard/карти/рецепти.


### 2026-10-27 — ProjectE passive0.4.10: перевірений код

- DONE реалізації:5helpers/20mixins, actual wearer/live team/item floors; inventory/useOn/onItemUseFirst, key/Archangel/GemMode, armor/Curios views і attributes, bag/chest/pedestal callbacks та pickup suction. Canonicalreceiver/finally, без stack/ACTIVE/cooldown/knowledge/EMC writes.
- Curios-tablet47 source floor прив’язано до фактично відкритого меню і збережено через pause/remap; physicaltable45 доступний. Mainhand tool floor перевіряється до native mineBlock/AOE. Shared vanilla/Curios attribute contributors захищені, native old-modifier removal не фільтрується.
- Новихквестів/рецептів/нагород/предметів/PNG0. Усі3314quest payloads із координатами/dependencies/rewards та621recipe entries збережені.140глав/48епох/96ключів/390предметів; incremental snapshot7539c6b захищає34новіID поверх3280 і621recipeIDs.
- PASS:190Python/55Node/5237Java іJDK21build;208новихactual-helper/handler/real-policy modeled умов (world63/storage43/armor49/Curios32/suction21). МінімальнийMC0.4.10:99assertions/2JVM/650ticks/SavedDatarestart;9нових receiver/FakePlayer/vanillaequipment checks. OptionalProjectE/Curiosdispatch NOT RUN.
- Rebuild1163runtimeфайлів byte-identical PYTHONHASHSEED83. SNBT/ID/DAG/keys/recipes/resources/layout PASS; координати без змін,1147перетинів/0structuralwarnings. JAR136classes/SHA cb45780e7b95c99f30158c8adcf76ba63cc576f185e949f568bc9248b7ecbe65.
- Межі:client GemFeet/GemLegsmotion, directaddonAPI/spawnedeffects, unchangedarmorenchantmentlocationeffects та identical-ID+valueforeign provenance. ПовнийJEI/UI/Survival/TPS NOT RUN. Див.docs/testing/PROJECTE_PASSIVE_ACCEPTANCE.uk.md і content/audit/v5-projecte-passive-guard.json.
- IN_PROGRESS доставки:ZIP/actualpackagedinstaller, finalreview/commit/push. Після цього наступна конкретна дія:core-аудит EvilCraft1.2.99/ForbiddenArcanus2.6.1 за exact source/book/export;37partial/невивченімоди, старіобов’язковілінії48епох. DraconicCI633 BLOCKED, Roots ritualrestart TODO,6IFfluidgaps BLOCKED. Повний0.5не реліз.

- DONE пакування0.4.10:CRC/повнийSHAmanifest та1163runtime hashes PASS. Extracted installer dry-run0writes; справжній тестовий upgrade0.4.9→0.4.10 резервуєстарийJAR, зберігає synthetic world-progress/fireledger/knowledge+EMC markers і стороннійквест у власнійглаві. Звіт implementation/projecte-passive-package-install-v5.json. Windows-інстанс не змінювався.
- Стан цього guard-підблоку зберігається окремим комітом уmain іpushбезforce. Точнийhash/status — через gitlog/origin/main та externaldeliveryreport біляZIP; self-referentialhash не вигадується. Наступна сесія:перша незавершена core-дія EvilCraft/ForbiddenArcanus вище; повний0.5не завершено.


### 2026-10-27 — EvilCraft / Forbidden Arcanus: IN_PROGRESS

- Відновлено чистий `1f3ce76`; main/origin синхронні. Backup перед змінами: `/workspace/aia2-backups/before-dark-magic-core-20261027T095531Z/checkpoint-1f3ce76.tar.gz`.
- Наступний підблок: exact EvilCraft1.2.99 і ForbiddenArcanus2.6.1 — джерела/книги, scoped core-карти, змістовні optional квести й аудит native machine/ritual обходів. Поточні3314квести/621рецепт/390предметів/PNG — база, нові кількості ще не підтверджено.
- Власники: evilcraft_core_v5 — новий EvilCraftcatalog/evidence/replacemententry; forbidden_core_v5 — Forbiddencatalog/evidence/replacemententry; dark_magic_native_audit — readonly native findings. Root інтегрує sharedmap, рецепти/генератори, перевірки й Git. СтаріID/прогрес зберігати.
- Наступна конкретна дія: перевірити джерела й effective recipes, підтверджені guard findings; інтегрувати тільки перевірені зміни, запустити тести, зберегти окремий checkpoint/commit/push. Повний0.5 ще не реліз.


### 2026-10-27 — EvilCraft0.4.11: перевірений код і контент

- DONE цього scoped підблоку:16новихoptional-квестів (13→5,19→8,28→3),1основна карта EvilCraft24етапи,2CreateMechanical5×3формули,1nativecapturegoal.3330квестів/140глав/623рецепти/390предметів іPNG/96виробничихключів. Новихпредметів/текстур0;16новихitemrewards,3066загалом.
- Усі3314попередні non-coordinate quest/task/reward payloads і dependencies та621recipe entries незмінні. Координати змінилися лише в EvilCraftглаві;1147перетинів,0structuralwarnings.8старих researchstageIDs/refs/order збережено; помилкове decompression-evidence DarkPowerGem замінено actualinfusion.
- Native closure criterion доводить actualcapture дляentanglingplayers; інвентарне /give не є подією. Не додано фіктивного виробничогодоказу для інших підготовчих/observation цілей. Nativeactiongoals99; teamprocessproofs8/11recipeIDs незмінні.
- SpiritReanimator/SanguinaryController: по9native material units і2Source/mana/aura inputs; CreateMechanicalCrafter доступний10≤13.42064exportscan підтвердив2primaryproducers; замінено2, старі custom formulas не видалено. Craft:true пасток для машинних виходів немає.
- DONE3targetednative entries: BloodInfusergetRecipeRETURN перевіряє currentidentity/receiverowner/output; rawSingleCache не фільтрується. SpiritFurnaceactualoutput gated передinsertion; Reanimator gated передdrain/egg/boxclear. Keys/copyoutputs denied; жодного nearestplayer fallback.
- PASS198Python/55Node/5237Java іJDK21build;49actualhelper/handler/realpolicy modeledassertions у2hosts. МінімальнийMC0.4.11:99assertions/2JVM/650ticks/SavedDatarestart. Він не містить EvilCraft/Forbidden; optionalweaving/JEI/UI/Survival/TPS NOT RUN.
- Rebuild1163runtimeфайлів byte-identical PYTHONHASHSEED89.25scopedcoremaps/36partial;61мод/63records/679researchstages/1052questlinks/1914SHA-файлів карт. Exactguard31sources і дескриптори збережено окремо вdark_magic_native_v5.
- Limits: післяrecipeReloadstaleInfusercache denied доnativeinput/fluidamount/tierchange, безавтоматичногоrebind. SpiritFurnaceblood/RNG/loot effects можутьпередуватиoutputguard; refund/rollback не заявлено. Nativeoutertimers, Env/Sanguinarypaidcaches, Purifier/worldgem/brooms/passives іgenericcopiedcomponents залишаютьсяокремимиадаптерами.
- Допоміжні агенти цього блоку завершилися злімітом; root відновив наявні файли, завершив sourcefreeze/контент/код/тести. Активних власників файлів немає. Неперевіреного Forbidden Java-коду в runtime немає.
- IN_PROGRESS доставки:пакет/actualinstaller upgrade0.4.10→0.4.11, finalreview/commit/push. Точнийcommit черезgitlog/origin/main та externaldeliveryreport, безself-referentialhash.
- Наступна конкретна дія: ForbiddenArcanus2.6.1 current-registry/prepayment/active-ritual guard із збереженнямpaidоперації приreload/restart; source31filesіточнідескриптори вжеportable. Потім core-карта/квести зnative ritual_completed. Не називати ritual registry RecipeSerializer. Докладнийhandoff:content/audit/v5-dark-magic-native-findings.json. Roots ritualrestartTODO/DraconicCI633BLOCKED/6IFfluidgapsBLOCKED, решта36partial істаріrequiredлінії48епох ще відкриті. Повний0.5не реліз.

- DONE пакування0.4.11: CRC/повнийSHAmanifest та1163runtime hashes PASS. Запакований CLI dry-run0writes; справжній тестовий upgrade0.4.10→0.4.11 резервуєстарийJAR, зберігає synthetic world-progress/fireledger/knowledge+EMC markers і стороннійквест у власнійглаві. Звіт implementation/evilcraft-core-package-install-v5.json. Реальний Windows-інстанс не змінювався.
- Цей цілісний EvilCraft-блок зберігається окремим комітом уmain іpushбезforce; finalhash/status черезgitlog/origin/main та externaldeliveryreport біляZIP. Наступну сесію починати з Forbidden prepayment/active ritual задачі вище; не повторювати16квестів,2рецепти й3готовіEvil adapters. Повний0.5не завершено.

- Після основного5f52395 окремо уточнено тексти16новихEvil goals: прибрано dev-only зауваги з ігрового UI, залишено практичні інструкції й чесні умови зарахування. Усі3330IDs/tasks/rewards/dependencies/coordinates незмінні; proof implementation/evilcraft-ui-preservation-v5.json. Повторити static/rebuild/package перевірки; Java-код і JAR не змінювалися.

- DONE UI-followup:7targetedEviltests/static SNBT/IDs/graph/resources PASS, повнийrebuild поточних1163runtimefiles byte-identical зPYTHONHASHSEED89. Backup: `/workspace/aia2-backups/before-evil-ui-20261027T174445Z/checkpoint-5f52395.tar.gz`. Змінилися лише описи16новихцілей і дослідницькі пояснення/звіти; код/JAR незмінні. Подальша конкретна дія — Forbidden ritual guard, як вище.


### 2026-10-27 — Forbidden Arcanus: IN_PROGRESS

- Відновлено чистий80051c0, main/origin звірено. Backup:/workspace/aia2-backups/before-forbidden-ritual-20261027T185709Z/checkpoint-80051c0.tar.gz.
- Root: native ritual permission/persistence/diagnostics; forbidden_paid_state_v6: окремий NBT statehelper/tests; forbidden_course_v6: scopedcorecatalog/evidence/pendingmap; readonlyreviewзавершено. Критичні verified findings: payment всерединіlambda, failRitualпідчасload, RegistryDirectCodecпотрібендляfingerprint.
- Наступна дія: реалізувати scopeпередоплатою/післяreduce, tick/fail/load/save захист без втратиpaidstate; source-backed course інтегрувати післятестів. База3330квестів/623рецепти/390предметівіPNG.0.5не реліз.


### 2026-10-28 — Forbidden Forge0.4.12: перевірений код і контент

- DONE цілісного підблоку:16новихoptional-квестів (15→7,21→6,31→2,34→1),24етапи scopedcore,6native ritual_completed критеріїв.3346квестів/140глав/623рецепти/390предметів іPNG/96ключів. Новихрецептів/предметів/текстур0;16новихitemrewards,3082загалом.
- Snapshot80051c0 і fullpayload audit зберігають усі3330старіtasks/dependencies/rewards та623recipeentries. Єдина non-coordinate зміна — icon-only виправлення старого Forgegoal на real MundabiturDust. Координати змінилися лише в Forbiddenглаві:1147→1152перетини,0structuralwarnings.
- DONE Java:3optional hooks (RitualManager/EssencesStorage/Forgeinput), actualowner/liveplayer/currentregistry/physicalmain+pedestals+enhancers/results+tiers. Scoped Optional.map доnative lambda; receipt тількипісля exactstorage+cost reduceRETURN. Keys/copyoutputs/essenceinputkeys denied. Paid rawNBT іreceipt читаютьсядоnativeparse, codec omission не стирає операцію; exactdefinition можеresume/rebind безновоїоплати.
- Legacy/pending/corrupt іchanged/removeddefinition pause зі збереженням. Load/onDataChanged fail не чиститьп'єдестали. /aia2forge status; explicitnearbyoperator cancel у своїйкоманді змаксимум8persistentbackups, безphysicalinputwrites/refund/output. Інсталятор нічого не скасовує.
- PASS212Python/55Node/5237Java іJDK21build.297новихmodelassertions(85state+212actualhelper/3handlers/realpolicy), включноnested scopes/exceptions/payment/reload/removeddefinition/latecommit/cancel. МінімальнийMinecraft0.4.12:111assertions/2JVM/650ticks;12новихactualNBT/UUID/compressedbinary checks. OptionalForbiddenweaving/JEI/UI/Survival/TPS NOT RUN.
- Rebuild1169runtimeфайлів byte-identical PYTHONHASHSEED97. JAR157classes;140попередніхclasses byte-identical, NativeSmokeTests навмиснооновлений. SHA6f6246d6013e20655aa1cd5903c0982ced3598f4f30667dc7c434292c50e92e3.26scopedcore/35partial;695researchstages/1068questlinks/1963SHA-файли карт.
- Limits: fingerprint фіксуєDIRECT_CODECритуал, неувесьtransitivegraph; nativeRNG/midpoint/worldeffects неrollback; native modifier/rawcost semantics збережено. Nativecriterion потребуєonlineініціатора увимірікузні йпередуєfinaloutput. Clibano internalmain ownership/production,Obelisk/passives/genericcomponents щеTODO.
- IN_PROGRESS доставки:ZIP/actualinstallerupgrade0.4.11→0.4.12, finalreview/commit/push. Точнийhash/status черезgitlog/origin/main таexternaldeliveryreport, безself-referentialhash.
- Наступна конкретна дія:Forgetransitive-definitionreview іClibano actualmain-controller owner/production guard заexact2.6.1source; далі35partial/невивченімоди істаріrequiredлінії48епох. RootsunfinishedritualrestartTODO,DraconicCI633BLOCKED,6IFfluidgapsBLOCKED. Повний0.5не реліз.

- DONE пакування0.4.12:4159manifestentries/1169runtimeSHA/installerSHA/CRC PASS. ActualextractedCLI dry-run0file+directorywrites; syntheticupgrade0.4.11→0.4.12 резервуєстарийJAR і зберігає world/FTB/fire/knowledge+EMC/paidchunkmarkers, сторонніquest/mod/script. Repeatinstallідемпотентний. Це opaqueсинтетичніmarkers, неfullpackритуальнийrestartтест. Звіт:implementation/forbidden-ritual-package-install-v5.json. Windowsінстанс не змінювався.
- Всі власники цього підблоку завершили роботу. Source-review знайшов і root виправив physicalenhancerbinding таexactnativecostidentity; новий6fileSHAmanifest/sourcecontract регресія збережені. Післядоданоїsourcecontractперевірки остаточнийPythonнабір212;297modeledassertions незмінні. JavaScript syntax13filesPASS.
- Стан зберігається окремим main-комітом іpushбезforce. Фінальнийhash/status визначати черезgitlog/origin/main таexternaldeliveryreport біляZIP; self-referentialhash уsourceархів не вбудовувати. Наступнийстарт — перша незавершенаClibano/transitiveдія вище, не повторювати16цілей або3готовіhooks.


### 2026-10-28 — Clibano: IN_PROGRESS

- Відновлено129ca0e/main; backup чинних файлів і незавершених чернеток: /workspace/aia2-backups/resume-clibano-20261028T093345Z. Попередній baselinebackup:/workspace/aia2-backups/before-clibano-20261027T233641Z/checkpoint-129ca0e.tar.gz.
- Root: canonical frame→main ownership/GUI, sharedintegration/version/Git. clibano_native_finish: production/cache/paidstate; clibano_native_tests: модельовані handler regressions; clibano_owner_tests: власник і точний GUI target; clibano_content_finish:5source-backedoptionalgoals/pendingmap/rules.
- База3346квестів/623рецепти/390предметів/PNG/96ключів збережена. Незавершений Forge transitivehash-дизайн ще не змінюєruntime; не вважати його реалізованим. Наступна дія: завершити coherentClibanoowner/nativeguard, перевірити й зафіксувати. Повний0.5не реліз.


### 2026-10-28 — Clibano0.4.13: реалізований підблок

- DONE коду й контенту:5нових optional-квестів (15→2,21→3),3командні process proofs,29етапів Forbidden-карти.3351квест/140глав/623рецепти/390предметів іPNG/96ключів. Нових рецептів/предметів/текстур0;5нових матеріальних нагород,3087загалом.
- Усіх3346попередніх non-coordinate quest/task/reward/dependency payloads і623recipeentries збережено. Snapshot129ca0e захищає16попередніх ForbiddenIDs поверх3330. Координати лише Forbiddenглави:1152→1154перетини,0structuralwarnings.
- Root canonicalframe→actualmain і26частин shell, усі права/floors/owners перевірені до ownerwrites. TypedclaimClibano прибирає JS UUID/overload проблеми. GUI не використовує nearestPOI; live stillValid перевіряє команду/стадію/власника. Constructor binding утримує початкову BEidentity: Valhelsia getBlockEntity динамічно resolve за позицією і без цього може підмінити старий inventory після replacement. Corruptarrays/staleresidueholders до GUI не допускаються.
- Native main tick/cache/finish/residue guard: поточний recipe/physicalenhancer/inputs/outputcomponents. Lane receipts schema1 збережені черезrestart; legacy/corrupt/changed операції pause. Cold/unlit прогрес заборонений; duration1 не дає output до fuelpayment. Native polling queue не підміняє другий рецепт; outputfill не стирає іншу лінію. Proof лише після exactinputdecrement і acceptedoutputdelta. Rules11/recipeIDs14; попереднє SavedData не скидається.
- /aia2clibano status/cancel: тільки своя цілісна піч поруч; cancel operator-only, максимум8persistentbackups. Скидає лише cookingprogress/receipt; slots/residues/burn/soul збережено, refund/output/proof0. Автоматичного installercancel немає.
- Доступні suites:228Python/57Node/5237Java іJDK21build;776новихmodelassertions (175state/351owner+menu/250native). МінімальнийMC119assertions/2JVM/650ticks,8новихactualNBT/binary cases. Exact4native logic files у модельованому host byte-identical. Повний Clibano optionalweaving/JEI/UI/Survival/TPS NOT RUN.
- Source34SHA + Valhelsia1.1.5bytecode artifact;700researchstages/1073questlinks/1997SHA-файлів карт,26scopedcore/35partial. Джерельний аудит і manualacceptance збережені в docs/AIA2_0.4.13_CHECKPOINT.uk.md і docs/testing/CLIBANO_ACCEPTANCE.uk.md.
- Під час інтеграції виправлено staleSHA mutable mechanicsconfig у processes-карті та hardcoded8→11 у40_mechanics.js. Це реальні regression checks; невдалий перший installernegativefixture без mods/ виправлено і перевірено повторно.
- Limits: automaticframeIO upstream закоментовано; original residue definition черезrestart не доведене; generic copiedcomponents/directaddon callbacks і fullrollback не заявлено. Поточна перевірка bounded26parts/2lanes/15native recipes; TPS benchmark TODO. Forge/Clibano transitive tag/registry fingerprint щеTODO; дизайн у content/audit/v6-forbidden-transitive-design.json, runtime ним не змінений.
- IN_PROGRESS доставки: остаточний пакет/actualCLI upgrade0.4.12→0.4.13, metadata і commit/push безforce. Після цього наступна конкретна дія — transitive залежності оплачених Forgeритуалів зі збереженням старих schema1 receipts, потім35partial/невивчені моди та старі requiredлінії48епох. Rootsunfinishedrestart/DraconicCI633/6IFfluidgaps залишаються відкритими. Повний0.5не реліз.
- Допоміжні агенти завершилися з лімітом; root відновив файли, довів source/handler/model перевірки. Активних власників немає; продовжувати за останнім checkpoint, а не старими іменами агентів.

- DONE доставки до коміту:1172runtimeфайли byte-identical після повної генерації PYTHONHASHSEED103;13JS syntaxfiles PASS. Фінальний JAR181classes/68mixins,154попередніclasses byte-identical; змінені лише Aia2MachineGuard/ProductionMilestoneBridge/NativeSmokeTests. SHA:a15c1a6a258b98f9a155f63b0e92d5dbded9c7c3b9f8afdacb725f6501b0efe9.
- Actual ZIP4230entries/CRC/весьSHAmanifest PASS. Запакований CLI --dry-run:0змін файлів/директорій. Upgrade129ca0e(0.4.12)→0.4.13 резервує старийJAR і зберігає opaque world/FTB/fire/knowledge+EMC/paidchunk markers та сторонніquest/mod/script; повторне встановлення ідемпотентне. Звіт:implementation/clibano-package-install-v6.json. Реального Windows-інстансу не торкалися.
- Останній додатковий source/bytecode review знайшов dynamic Valhelsia MenuCreationContext: root додав constructor-binding початкової BEidentity. Host відтворює динамічне resolve; same-owner replacement і повторнийbind не можуть оживити старий handler. Після цього повторні228Python і119minimalMC PASS;351owner/menu assertions входять у776нових.
- Цей цілісний checkpoint зберігається в main-коміт і push безforce. Точнийhash/status — gitlog/origin/main та externaldeliveryreport біляZIP; self-referentialhash уsource не вбудовувати. Наступна сесія починає transitive залежності вище; цейClibanoблок і5новихцілей не генерувати повторно. Повний0.5ще IN_PROGRESS.
