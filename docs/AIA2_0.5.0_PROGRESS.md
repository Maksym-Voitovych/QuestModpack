# AIA2 0.5.0 — журнал прогресу

Останнє оновлення: 2026-10-25 (часовий пояс користувача Europe/Kyiv). База `90ab63f`, робоча версія 0.4.3-alpha (native action goals та component-aware mana guard); 0.5 ще не реліз.
Цей файл читати разом із [планом](AIA2_0.5.0_PLAN.md) перед продовженням.
Статуси: `TODO`, `IN_PROGRESS`, `DONE`, `BLOCKED`.

## Етапи

| № | Етап | Статус | Доказ / наступна дія |
|---|---|---|---|
| 0 | FTB Quests overload hotfix | DONE | Типізований міст, production script20, 16 справжніх Rhino assertions, Node41/Python23/Java5237; окремий fix-коміт |
| 1 | Аудит 0.4 | DONE | v5-baseline-audit.json; snapshot2784 квестів/569 рецептів, task/reward/dependency ID; export ≠ доступ до Windows |
| 2 | Дослідження механік | IN_PROGRESS | 58 модів/60 записів,765 SHA-файлів у картах; 45 часткових карт і невивчений контент лишаються |
| 3 | Карти прогресії | IN_PROGRESS | 13 core-карт DONE;45 часткових карт; повний перелік у REMAINING_COVERAGE |
| 4 | Перебудова координат | DONE | Усі136глав,0накладань/зворотних/вертикальних; стара2784когорта1679→1129перетинів; UI окремо |
| 5 | Поглиблення 48 епох | IN_PROGRESS | 361 новий квест від v4, з них84 у поточному блоці і49 native action цілей; решта старих ліній ще переглядається |
| 6 | Перегляд нагород | DONE | 2877 item-нагород перевірено;84нові тематичні,2793старі з checkpoint не змінено;48команд збережено |
| 7 | Розширення рецептів | IN_PROGRESS | 603рецепти;34v5формули(33+1variant),602попередніJSON збережено; подальший баланс у плані |
| 8 | Предмети без джерел | IN_PROGRESS | 2288важливихпредметів;29native-source доказів,одна Iron-книга виправлена;7fluid-bucket gap +49native-context +1implicit-codec |
| 9 | Creative/альтернативи | IN_PROGRESS | Essence/Pool і3creativeTablet producers закрито; guard player/pool exchange додано; прямі сторонні capability-виклики ще потребують аудиту |
| 10 | Інтеграційні тести | IN_PROGRESS | 110Python/50JS/5237Java PASS;49actualMC@0.4.3 у2JVM,22mana-model і16DE-model; fullpack/JEI/TPS не запускалися |
| 11 | Реліз і push | IN_PROGRESS | 0.4.3—проміжний перевірений блок,0.5ще не готовий; коміти/пакет фіксуються нижче |

## Окремий стан 48 епох

Статуси стосуються змін v5; наявний контент v4 не видаляється і не вважається
повністю переробленим лише через його наявність.

| Епоха | Дослідження | Квести v5 | Рецепти v5 | Залежності v5 |
|---|---|---|---|---|
| 01 | IN_PROGRESS | IN_PROGRESS (4) | TODO | DONE (static) |
| 02 | IN_PROGRESS | IN_PROGRESS (4) | TODO | DONE (static) |
| 03 | IN_PROGRESS | IN_PROGRESS (4) | TODO | DONE (static) |
| 04 | IN_PROGRESS | IN_PROGRESS (8) | TODO | DONE (static) |
| 05 | IN_PROGRESS | IN_PROGRESS (5) | TODO | DONE (static) |
| 06 | IN_PROGRESS | IN_PROGRESS (1) | TODO | DONE (static) |
| 07 | IN_PROGRESS | IN_PROGRESS (13) | TODO | DONE (static) |
| 08 | IN_PROGRESS | IN_PROGRESS (5) | TODO | DONE (static) |
| 09 | IN_PROGRESS | IN_PROGRESS (8) | TODO | DONE (static) |
| 10 | IN_PROGRESS | IN_PROGRESS (7) | TODO | DONE (static) |
| 11 | IN_PROGRESS | IN_PROGRESS (4) | TODO | DONE (static) |
| 12 | IN_PROGRESS | IN_PROGRESS (7) | TODO | DONE (static) |
| 13 | IN_PROGRESS | IN_PROGRESS (7) | TODO | DONE (static) |
| 14 | IN_PROGRESS | IN_PROGRESS (13) | TODO | DONE (static) |
| 15 | IN_PROGRESS | IN_PROGRESS (13) | TODO | DONE (static) |
| 16 | IN_PROGRESS | IN_PROGRESS (5) | TODO | DONE (static) |
| 17 | IN_PROGRESS | IN_PROGRESS (4) | TODO | DONE (static) |
| 18 | IN_PROGRESS | IN_PROGRESS (11) | IN_PROGRESS | DONE (static) |
| 19 | IN_PROGRESS | IN_PROGRESS (10) | TODO | DONE (static) |
| 20 | IN_PROGRESS | IN_PROGRESS (25) | TODO | DONE (static) |
| 21 | IN_PROGRESS | IN_PROGRESS (14) | TODO | DONE (static) |
| 22 | IN_PROGRESS | IN_PROGRESS (2) | TODO | DONE (static) |
| 23 | IN_PROGRESS | IN_PROGRESS (6) | TODO | DONE (static) |
| 24 | IN_PROGRESS | IN_PROGRESS (8) | TODO | DONE (static) |
| 25 | IN_PROGRESS | IN_PROGRESS (3) | TODO | DONE (static) |
| 26 | IN_PROGRESS | IN_PROGRESS (9) | TODO | DONE (static) |
| 27 | IN_PROGRESS | IN_PROGRESS (7) | TODO | DONE (static) |
| 28 | IN_PROGRESS | IN_PROGRESS (37) | TODO | DONE (static) |
| 29 | IN_PROGRESS | IN_PROGRESS (3) | TODO | DONE (static) |
| 30 | IN_PROGRESS | IN_PROGRESS (15) | IN_PROGRESS | DONE (static) |
| 31 | IN_PROGRESS | IN_PROGRESS (22) | TODO | DONE (static) |
| 32 | IN_PROGRESS | IN_PROGRESS (24) | TODO | DONE (static) |
| 33 | IN_PROGRESS | IN_PROGRESS (1) | TODO | DONE (static) |
| 34 | IN_PROGRESS | IN_PROGRESS (6) | TODO | DONE (static) |
| 35 | IN_PROGRESS | IN_PROGRESS (3) | TODO | DONE (static) |
| 36 | IN_PROGRESS | IN_PROGRESS (1) | TODO | DONE (static) |
| 37 | IN_PROGRESS | IN_PROGRESS (2) | TODO | DONE (static) |
| 38 | IN_PROGRESS | IN_PROGRESS (1) | TODO | DONE (static) |
| 39 | IN_PROGRESS | IN_PROGRESS (7) | TODO | DONE (static) |
| 40 | IN_PROGRESS | IN_PROGRESS (2) | TODO | DONE (static) |
| 41 | IN_PROGRESS | IN_PROGRESS (6) | TODO | DONE (static) |
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
