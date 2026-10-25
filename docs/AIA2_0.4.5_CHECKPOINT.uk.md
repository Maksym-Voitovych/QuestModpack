# AIA2 0.4.5-alpha — ритуали, паливна лінія та руни спавнерів

2026-10-25, Europe/Kyiv. База цього блоку:`1145f1b`. Повна0.5 ще **IN_PROGRESS**.

| Показник | До | Після |
|---|---:|---:|
| Епохи / виробничі ключі |48 /96|48 /96|
| Квести / глави |3167 /137|3212 /138|
| Змістовні квести, без96старих ручних вузлів |3071|3116|
| Нативні кастомні рецепти |603|606|
| Предмети / PNG |390 /390|390 /390|
| Основні карти модів / часткові |15 /43|19 /41|
| Моди зі структурованими картами |58|60|
| Контракти зовнішніх нативних дій |66|86|
| Окремі командні виробничі докази |4|6|

## Що реалізовано

- **Roots:12квестів.** Ритуальні кільця, параметри порошків, Imbuer, живі інструменти, Crystal Staff, Grower/Vacuum, комплекти Wildwood/Sylvan. Два окремі докази завершення ritual/crafting living_pickaxe та charged_runic_focus записуються для команди власника.
- **Actually Additions:11квестів.** Реконструктор, прес→бродіння→кристалізація source-рідини, генератор, акумулятори, чотири живлені стійки Empowerer та типізовані реле/фільтри/phantom-інтерфейси. Насіння кидати по одному: native код знищує цілу ItemEntity зі стеком.
- **Apothic Enchanting:12квестів.** Eterna/Quanta/Arcana, справжні операції інфузії, бібліотеки та високі параметри. Максимум Eterna цієї версії100; старі припущення про50 не використано.
- **Apothic Spawners:10квестів.** Чинні руни Apotheosis, керування, світло, Ascent range32, Summit count13, No AI та фінальна конфігурація Pinnacle. Прямі Sugar/Clock/Comparator та інші standalone-рецепти не приписані встановленому експорту.
- **Три міжмодові рецепти.** Canola Press використовує Manasteel/кристали AA; Fermenting Barrel — Infused Iron Nature’s Aura; Oil Generator — Manasteel і схему Mekanism. Замінено лише3дешеві native producer IDs. Усі603старі кастомні JSON збережено,3reset-рецепти й інші способи енергопостачання залишилися. Виробництво машин не потребує ще не отриманих олій.

## Захист і справжня оплата ритуалу

Roots очищає тимчасовий CustomInventory всередині `doEffect`, а справжній ItemStackHandler — наступним `emptyAltar`. Новий hook бере точний recipe holder та перевіряє відповідність трьох слотів перед завершенням, а записує доказ **після фактичного очищення вівтаря**. Перевіряються незмінна команда, актуальна політика, точні recipe ID/serializer/output та епоха. SavedData schema1 й попередні чотири докази збережено. `/give` не створює виробничого запису.

Scope доказу — оплачена нативна операція. Roots ігнорує boolean `addFreshEntity`, тому гарантоване прийняття output entity світом не заявляється. Incense витрачається на старті й не повертається. Нативне відновлення незакінченого ритуалу після restart не виправлено; збереження вже завершених командних доказів перевіряється окремо.

Для6просунутих рун встановлено item floors31/41 та15відповідних recipe floors. `ApothicSpawnerMixin` перевіряє руни в обох руках безпосередньо перед native findMatch/apply/списанням. Імпортований предмет, fake player або застаріла проєкція команди не дають раннього застосування. Прямі сторонні виклики API поза цим hook не оголошені перевіреними.

## Виправлені старі цілі й сумісність

Усі3167 попередні quest/task/reward ID, залежності й нагороди збережено. `E04_X_orchid_sample` став підготовчим гербарієм Blue Orchid/Oxeye Daisy: Flare Orchid потребує Nether, а Radiant Daisy має native помилку абсолютного dayTime. Це точковий overlay, не перезапис старого каталогу. Два optional Charged Focus квести лишилися на4: Nether Wart може трапитися в Overworld structure loot; нова штатна виробнича ціль належить епосі15.

Усі138глав пройшли layout-перевірку:0накладань/зворотних/вертикальних/надто довгих локальних ліній. Загалом1141перетин проти1133до45новихцілей. Порівнювану стару когорту й збереження даних наведено у machine-readable звіті. Перегляд GUI ще потрібний.

## Джерела й перевірки

Точні офіційні source pins і shipped книги/JSON:

- Roots1.5.10:`Lothrazar/RootsClassic@db9aa883`;
- Actually Additions1.3.26:`Ellpeck/ActuallyAdditions@cd9d9c63`;
- Apothic Enchanting1.6.4:`Shadows-of-Fire/Apothic-Enchanting@4d167fd4`;
- Apothic Spawners1.4.0:`Shadows-of-Fire/Apothic-Spawners@a5401df4`;
- ефективні рецепти інтеграції Apotheosis8.9.0 — точний наданий експорт.

[Карти](research/MOD_MECHANICS.md), [індекс джерел](research/SOURCE_INDEX.md), [повний звіт](../implementation/v5-milestone-report.json).

-126Python tests,50Node tests,5237Java assertions та JDK21/NeoForge build: **PASS**.
-49умов справжніх Roots helper/handlers і15умов spawner-handler із реальною GuardPolicy у модельованих host: **PASS**.
- Мінімальний справжній Minecraft0.4.5:49assertions у2JVM,650тіків і restart SavedData: **PASS**. Optional модів у ньому немає.
- SNBT/ID/DAG/рецепти/нагороди/ресурси/source contracts: **PASS**. Повторна генерація перевіряється окремим `rebuild-v5-report.json`.
- Повний Windows-інстанс, optional dispatch,JEI/UI,Survival та TPS: **NOT RUN**. [Приймальні сценарії](testing/NATIVE_ACTION_ACCEPTANCE.uk.md).

Аудит2320предметів підтвердив нативне створення Staff, Acacia Bark та Crystallized Oil Bucket без вигаданих рецептів.6IFfluid джерел лишаються непідтвердженими для точних3.6.38/4.0.43. Native Radiant Daisy dayTime/subset-mutation bugs та інші альтернативні виклики залишено в черзі.

## Встановлення та продовження

Закрийте гру й сервер. Із папки оновлення:

```powershell
python install_runtime.py "C:\CurseForge\AllInOneAdventure2" --dry-run
python install_runtime.py "C:\CurseForge\AllInOneAdventure2"
```

Інсталятор резервує оригінали, зберігає світи/прогрес/сторонні квести та встановлює відповідний companion0.4.5/API4. Потрібен повний перезапуск. Windows-інстанс користувача в хмарі не змінювався.

Наступний блок: поглиблення Modern Industrialization/Oritech та інших41часткових карт; продовження аудиту старих обов’язкових48епох, альтернативних рецептів і нативних мутацій Roots. Окремо потрібне приймання всіх optional hook у повному інстансі. Джерело відновлення — [PLAN](AIA2_0.5.0_PLAN.md) і [PROGRESS](AIA2_0.5.0_PROGRESS.md).
