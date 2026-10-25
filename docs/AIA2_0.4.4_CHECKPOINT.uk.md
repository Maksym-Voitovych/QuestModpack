# AIA2 0.4.4-alpha — продовження розробки0.5

Дата:2026-10-25, Europe/Kyiv. Початковий checkpoint:`61cc7ab`.
Це завершений підблок розробки. Повний реліз0.5 ще **IN_PROGRESS**.

| Показник | До | Після |
|---|---:|---:|
| Епохи / виробничі ключі |48 /96|48 /96|
| Квести |3145|3167|
| Змістовні квести без старих ручних вузлів |3049|3071|
| Глави |136|137|
| Нативні рецепти |603|603|
| Власні предмети / PNG |390 /390|390 /390|
| Контракти нативних дій |49|66|
| Завершені основні карти модів |13|15|
| Часткові карти модів |45|43|

## Виправлення й збереження

- `396b539`: окремий hotfix ступки Roots. Пестик викликає рецепт поза BlockEntityTicker, тому попередній контекстний hook не перевіряв gate15/30 компонентів при gate1 ступки. Новий `RootsMortarMixin` фільтрує native holder через чинну політику власника перед assemble/spawn/очищенням входів. Не додано постійного tick-сканера.
- Machine Guard0.4.4 зберігає API4, типізований FTB-міст, ProjectE/Rhino-міст, захист Draconic cache і компонентів творчої Mana Tablet. Інсталятор відхиляє старий JAR без нового hook до запису в інстанс.
- Усі3145 попередні quest/task/reward ID та залежності збережено. Старі нагороди не змінено. У двох optional Petroleum-цілях виправлено лише предметний результат і пояснення; самі авторські каталоги залишено незмінними.
- Дистиляція дає `diesel_sulfur`, а чистий дизель потребує Hydrotreater. Коксування бітуму дає petcoke та `diesel_sulfur`, а не naphtha. Обидва виправлені квести тепер відповідають цим процесам.
- Рецепти цього підблоку:0нових,0перероблених,0видалених. Повний попередній603-entry bundle незмінний. Creative Essence/Pool/Tablet та96 виробничих ключів збережено.

## Нові механічні цілі

- **Apotheosis:12квестів.** Справжні native equipment-критерії та world-tier цілі; три окремі purity-докази Gem Cutting після витрати входів; підготовка reforge/socket/augment. Підготовчий комплект не названо доказом самої операції. Frontier перевіряє історичні дії в п’яти слотах, не одночасний комплект.
- **Immersive Petroleum:10квестів.** Розвідка нафтового резервуара, формування шести мультиблоків, реальне застосування Oil Can, правильне розміщення Auto Lubricator й успішний обмін рідиною з генератором. Обмін рідиною не названо доказом генерації FE; формування не названо доказом виробництва.
-22нові тематичні нагороди проходять чинну stage-safe політику. Безкоштовних обов’язкових машин або предметів майбутніх епох немає.
- Нова глава Petroleum й нові вузли пройшли стабільний DAG layout. Усі137глав перевірено:0накладань,0зворотних,0вертикальних і0надто довгих локальних ліній. Загальна кількість перетинів лишилася1133 при22нових цілях. Порівняння однакової старої2784-когорти:1679→1129(-32.76%). Це геометричний аудит, не перегляд GUI.

## Джерела

Використано офіційні source, shipped advancements/посібники та точний експорт рецептів. Відвідування зовнішніх вікі в цьому підблоці не заявляється.

- [Apotheosis8.9.0](https://github.com/Shadows-of-Fire/Apotheosis/tree/7dd7cec26830074f1745529eb8f1f533092733d0): codec/dispatch Gem Cutting, component-aware equipment, world-tier JSON, Patchouli, динамічний Gem loot.
- [Immersive Petroleum4.5.0-39](https://github.com/TwistedGate/ImmersivePetroleum/tree/659c494e044a87137547b5305bb267d2a73ab702): server grants, IE multiblock proofs, manuals; кількості рецептів взято з експорту, якщо текст посібника відрізняється.
- [Roots Classic1.5.10](https://github.com/Lothrazar/RootsClassic/tree/db9aa883b7a54a1558dbc710546be1f42544be72): точна взаємодія ступки, вівтар і cache. Основна карта Roots ще не оголошена завершеною.
- PneumaticCraft8.2.23: точні реєстрація LPG bucket, native tank fill та thermo_plant/lpg збережено в `content/audit/v5-source-gaps-fluids.json` і загальному індексі.
- IE12.4.2-194: раніше збережені точні trigger/dispatch джерела використано для Petroleum formed-контрактів.

Загалом58модів мають карти,15основних карт завершено. Portable SHA-джерела, карти й межі перевірки: [SOURCE_INDEX](research/SOURCE_INDEX.md), [MOD_MECHANICS](research/MOD_MECHANICS.md), [REMAINING_COVERAGE](research/REMAINING_COVERAGE.md).

Аудит2293важливих предметів підтвердив LPG-відро та нові native джерела компонентних Gems/сірчистого дизеля. Залишилися6непідтверджених IF-відер; точні IF3.6.38/Titanium4.0.43 артефакти недоступні. Новішу версію не видаємо за встановлену й не вигадуємо рецепти.

## Перевірки

-117Python tests,50Node tests,5237Java assertions і JDK21/NeoForge build: **PASS**.
- Новий Roots actual handler із реальною GuardPolicy:18умов у модельованому Minecraft host: **PASS**. DE16/Botania22 модельовані умови також пройшли.
- Мінімальний справжній Minecraft0.4.4:49assertions у2JVM,650тіків і restart SavedData: **PASS**. Optional моди в цьому сервері відсутні.
- SNBT/ID/DAG/96key/recipe/resource/reward/source contracts та збереження603рецептів/3145ID: **PASS**.
- Повторна повна генерація:1148runtime-файлів byte-identical: **PASS**.
- Fullpack Roots/APOTH/IP/FTB dispatch,JEI/UI,Survival,TPS: **NOT RUN**. [Конкретні ручні сценарії](testing/NATIVE_ACTION_ACCEPTANCE.uk.md).

## Встановлення та наступна дія

Закрийте гру й сервер. У папці оновленого репозиторію або розпакованого пакета:

```powershell
python install_runtime.py "C:\CurseForge\AllInOneAdventure2" --dry-run
python install_runtime.py "C:\CurseForge\AllInOneAdventure2"
```

Інсталятор резервує оригінали, зберігає світи/прогрес/сторонні квести та замінює лише власний companion. Потрібен повний перезапуск клієнта й сервера. Windows-інстанс користувача в хмарі не змінювався.

Далі: завершити карти й квести Roots Classic та Actually Additions; використати збережені точні Apothic Enchanting1.6.4/Spawners1.4.0 source-архіви для окремих карт. Потім продовжити решту43часткових карт, перегляд обов’язкових ліній усіх48епох і подальший рецептний баланс. [План](AIA2_0.5.0_PLAN.md), [PROGRESS](AIA2_0.5.0_PROGRESS.md), `content/audit/v5-pending-research.json` зберігають чергу й SHA між сесіями.
