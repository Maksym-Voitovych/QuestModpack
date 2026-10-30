# All in One Adventure 2.0 — AIA2

**0.4.19-alpha — оплата й розміщення станцій Ad Astra.** Повний0.5 ще в роботі.
Minecraft1.21.1 NeoForge / FTB Quests2101.1.36 / KubeJS2101.7.2 / Rhino85.

Глобальний план оплати витрачає повну кількість зі split stacks і не дозволяє
рахувати ту саму одиницю для кількох вимог. До оплати перевіряються поточна
команда та стадія орбіти; до реєстрації/teleport — прийняття всіх первинних
non-air блоків і збереження відповідних типів у світі. Помилка перериває
продовження, але не відкочує вже виконані нативні дії й не створює refund.

**48епох,96виробничих ключів,3375квестів/140глав,627рецептів,3111предметних
нагород,390предметів/моделей/PNG збережені.** Нових квестів, рецептів, нагород,
предметів і текстур цього guard-блоку0. Піднято лише шість station recipe
floors до37/38 відповідної орбіти. Старі station SavedData, NASA proofs,
ProjectE hotfix і API4 збережені.

Інсталятор перевіряє шість NASA/station Mixin contracts на наявному Ad Astra
JAR до backup/write. Підтриманий native шаблон — single-palette без entities
і blockNBT, з обмеженими розмірами. Інші визначення відхиляються до оплати.
Звичайне unscoped розміщення структур зберігає нативну поведінку.
Оригінальні optional binaries, повний клієнт, JEI, Survival і TPS не перевірені.

Зупиніть гру, розпакуйте пакет в окрему папку. Виконайте
`python install_runtime.py "C:\CurseForge\AllInOneAdventure2" --dry-run`, потім
ту саму команду без прапорця. Змінювані оригінали та старий власний JAR
резервуються. Повністю перезапустіть клієнт і сервер.

[Checkpoint](docs/AIA2_0.4.19_CHECKPOINT.uk.md) ·
[Встановлення](implementation/INSTALL.uk.txt) ·
[Ручна перевірка](docs/testing/STATION_CONSTRUCTION_ACCEPTANCE.uk.md) ·
[План](docs/AIA2_0.5.0_PLAN.md) · [Прогрес](docs/AIA2_0.5.0_PROGRESS.md).
