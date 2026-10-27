# AIA2 0.4.11-alpha — основний курс EvilCraft

Це завершена й перевірена доступними тестами частина роботи над0.5.
База:`1f3ce76`/0.4.10-alpha. Повний0.5 ще не завершено.

| Показник | До | Після |
|---|---:|---:|
| Квести / глави |3314 /140|3330 /140|
| Нативні custom-рецепти |621|623|
| Scoped core-карти / часткові моди |24 /37|25 /36|
| Предмети / моделі / PNG |390 /390 /390|390 /390 /390|
| Нативні action-goals |98|99|

Додано16optional-квестів EvilCraft:5вепосі13,8вепосі19,3вепосі28. Курс
охоплює bootstrap крові, інфузор, undead ресурси, bowls0..3/promises, підготовку
Purifier, справжнє захоплення духа, конструкцію й логістику Spirit Furnace,
реанімацію, храмову погоду та домашній Sanguinary Accumulator. Карта має24етапи;
усі8попередні stage IDs/refs і їхній порядок збережено. Complete означає цей
заявлений scoped навчальний курс, не всі предмети/пасивні ефекти мода.

`evilcraft:closure` перевіряє реальну native capture-подію для entangling players.
Інші нові goals чесно відділяють підготовку/огляд/доставку від вимірювання роботи
машини; отримання випадкового предмета не оголошується автоматизацією.

Spirit Reanimator і Sanguinary Accumulator складаються в Create Mechanical
Crafters5×3: усі9native material units збережено, додано по2Source/mana/aura
компоненти попередніх епох. Проскановано42064export recipes, замінено2первинні
producer IDs. Blood Infuser/bootstrap і всі621попередні custom entries збережено.
Нових предметів/текстур0;16нових предметних нагород,3066загалом.

Нові native guards: Blood Infuser raw value-cache перевіряється перед результатом;
Spirit Furnace — перед вставленням фактичного луту; Reanimator — перед drain,
egg consumption і box clearing. Використовується фактичний канонічний receiver,
поточний owner/recipe/item policy і безумовна заборона копіювання ключів.
Наприклад, чинний floor Nether Star —30, тому ранній Spirit Furnace не
вставляє цей фактичний результат; native кров/RNG можуть уже бути сплачені.

## Збереження та перевірки

Усі3314попередні non-coordinate quest/task/reward payloads, залежності та621
recipe entries незмінні. Координати змінено лише в главі EvilCraft.140глав без
накладань, зворотних, вертикальних і довгих локальних ліній;1147перетинів,
як до16нових цілей. [Порівняння](../implementation/evilcraft-core-preservation-v5.json).

198Python-тестів,55Node-тестів,5237Java assertions і JDK21build:PASS.49нових
actual-helper/handler/real-policy умов виконано у2модельованих hosts. Реальний
Rhino85 та старі FTB/ProjectE/dual-key регресії включено до suites.

Мінімальний MC1.21.1/NeoForge21.1.264:99assertions у2JVM,650ticks і SavedData
restart. Він не містить EvilCraft/Forbidden Arcanus; це не перевірка optional
weaving. Rebuild1163runtime-файлів byte-identical з PYTHONHASHSEED89.
Результат package/dry-run/upgrade: [звіт інсталятора](../implementation/evilcraft-core-package-install-v5.json).

## Межі та продовження

Blood Infuser cache не має reload generation: stale recipe заборонено до зміни
native input/fluid-amount/tier. Blood/elapsed timer примусово не скидаються;
автоматичного rebind не реалізовано. Spirit Furnace RNG/loot effects і кров
можуть передувати output guard; refund і rollback не заявляються.

Environmental/Sanguinary paid caches, Purifier actions, ItemDarkGem world
transform, brooms/passives і generic copied components потребують окремих
адаптерів. Fullpack weaving, JEI/UI, Survival і TPS:NOT RUN.

Forbidden Arcanus2.6.1 цього разу отримав source-аудит, а не нові квести/guard.
Наступна конкретна дія: prepayment і active-ritual guard Hephaestus Forge для
current registry identity, owner/input/result/tier, зі збереженням оплаченої
операції при reload/restart. Не підміняти ritual registry RecipeSerializer.
Потім — його core-карта й перевірені native ritual_completed goals. Exact31
source files і дескриптори збережено в
[аудиті](../content/audit/v5-dark-magic-native-findings.json).

Draconic CI633, Roots unfinished ritual restart,6IFfluidgaps і решта36partial
карт лишаються відкритими. [Приймальні сценарії](testing/EVILCRAFT_CORE_ACCEPTANCE.uk.md).

Установлення із закритою грою: у папці пакета встановити `nbtlib==2.0.4`,
виконати `python install_runtime.py "C:\CurseForge\AllInOneAdventure2" --dry-run`,
потім повторити без прапорця. Matching0.4.11JAR/скрипти потрібні на обох
сторонах; повний перезапуск обов’язковий. Інсталятор резервує оригінали й старий
власний JAR, зберігаючи світи, прогрес і сторонні квести.
