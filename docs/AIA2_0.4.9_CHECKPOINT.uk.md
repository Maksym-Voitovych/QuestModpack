# AIA2 0.4.9-alpha — ProjectE та Draconic

Це проміжний етап роботи над 0.5. База: `1915b80`. Повний реліз 0.5 ще не завершено.

| Показник | До | Після |
|---|---:|---:|
| Квести / глави |3280 / 139|3314 / 140|
| Custom-рецепти з нативними serializers |618|621|
| Основні карти / partial моди |23 / 37|24 / 37|
| Досліджені моди / записи карт |60 / 62|61 / 63|
| Предмети / моделі / PNG |390 / 390 / 390|390 / 390 / 390|

Додано 18 квестів ProjectE й 16 Draconic. Усі 3280 попередні quest/task/reward payloads і залежності, крім координат, та 618 recipe entries збережено. 48 епох і 96 виробничих ключів незмінні. Нових предметів і текстур: 0. Додано 34 предметні нагороди; старі не змінено. [Аудит збереження](../implementation/projecte-draconic-preservation-v5.json).

## ProjectE

Карта має 27 етапів за source 1.1.0, експортом і чинною політикою AIA2. Знання й сумки персональні; FTB-команда не робить їх спільним сховищем. EMC whitelist містить 14 звичайних матеріалів. Нові квести не обіцяють EMC-синтез палив, матерії або repair через ковалентний пил із нульовою EMC. Collector і RM-цілі віднесено до 47, відповідно до фактичних рецептів. Inventory/observation завдання чесно означають підготовку, а не вимір EMC-потоку.

Уже відкрите меню перевіряє поточну команду та стадію: table 45, tablet 47. Звичайне й ShiftClick-витягування перевіряють чинний whitelist, позитивну поточну EMC-вартість, raw components, item/key policy та належність slot поточному меню. Cached output із EMC0 більше не видається безкоштовно. Старі знання та EMC додатково не очищуються.

FuelMapper перебудовується ПІСЛЯ фінальної фільтрації EMC. Помилка очищує item map і fuel cache та закриває видобування. Не додається повторний pruneStaleKnowledge. Generic guard clearRuntime не скидає цю конфігурацію: перший тик script25 відбувається після EMCRemap.

Time Watch більше не передає права pedestal прискорюваній машині: кожен bonus tick перевіряє фактичного receiver й відновлює контекст через finally. Це не універсальний захист усіх пасивних предметів ProjectE. Armor, Curios, rings та world tools залишаються окремим відкритим аудитом.

## Draconic

Додано 16 квестів із реальними залежностями та 23-етапну карту; усі 7 старих stage IDs, refs і їхній порядок збережено. Карта залишається PARTIAL: source підтверджує 3.1.4 / MC1.21.1, але зв’язок commit із CI build633 не встановлено. Точний експорт рецептів використано як джерело встановлених формул; source не видається за перевірений binary build633.

Три fusion-формули: Awakened Injector41, Chaotic Injector42 і Draconic Relay41. Усі native матеріали, catalyst/count, energy, tier та output збережено; додано по два магічно-технічні компоненти. Максимум 11 інжекторів підтверджено статично. Скан 42064 рецептів класифікує три замінювані primary routes і дві збережені IO↔relay конверсії. Мінімальний tier враховує лише зайняті інжектори.

## Перевірки та межі

66 output/menu та 22 TimeWatch actual-helper/handler/real-policy умов пройдено в модельованому host. Реальний Rhino85 перевіряє script35, primitive-long bridge, порядок map→fuel→ready й закриття при помилці. Мінімальний Minecraft0.4.9 пройшов 90 наявних перевірок у двох JVM зі збереженням SavedData; він не містить ProjectE/Draconic.

178 Python tests,52 Node tests,5237 Java assertions і JDK21 build:PASS.
1163runtime-файли byte-identical після повної генерації PYTHONHASHSEED79.
Layout140глав:0структурних попереджень;1143→1147перетини при34нових цілях.
Доставка фіксується в release-report та PROGRESS. Optional dispatch, JEI/UI, Survival і TPS: NOT RUN. [Ручний приймальний тест](testing/PROJECTE_DRACONIC_ACCEPTANCE.uk.md) · [Native-аудит](../content/audit/v5-projecte-native-guard.json).

Наступне: пасивні ProjectE-шляхи, CI633 provenance Draconic, решта partial/невивчених модів і старі обов’язкові лінії всіх 48 епох. Шість IF fluid gaps і Roots unfinished-ritual restart залишаються відкритими.

ZIP CRC/повний manifest і 1163 runtime hashes перевірено. Запакований CLI dry-run не записує файлів. Тестове оновлення 0.4.8→0.4.9 резервує старий JAR, зберігає синтетичні world/fire/knowledge+EMC дані та сторонній квест. [Звіт інсталятора](../implementation/projecte-draconic-package-install-v5.json).
