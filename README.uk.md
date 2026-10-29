# All in One Adventure 2.0 — AIA2

**0.4.16-alpha** для Minecraft1.21.1 NeoForge, FTB Quests2101.1.36,
KubeJS2101.7.2 і Rhino85. Повний0.5 ще в роботі.

**48епох,96виробничих ключів,3371квест у140главах,627власних рецептів,
390предметів/моделей/PNG.** Додано20optional цілей Ad Astra й чотири
механічні формули двигунів Create. Усі3351старі non-coordinate quest/task/
reward/dependency payloads і623власні рецепти збережено. Переміщено36старих
вузлів у трьох главах Ad Astra; загалом1154перетини,0структурних попереджень.

Курс починається на Землі до старогоM1, який уже вимагає ракету, та послідовно
веде через Moon/Desh, Mars/Ostrum, Venus/Calorite до Glacio/кріопалива.
Двигуни зберігають native матеріали й додають магію та техніку. Матриця36
та каталізатор36 не створюють залежності першого польоту від місячних ресурсів.
Функціональне пізнє спорядження й відповідні producer-рецепти відкриваються
на38; декоративні калоритові блоки не отримали масового нового блокування.

NASA тепер перевіряє кешований рецепт, вихід і живе меню на сервері перед
викиданням результату чи списанням матеріалів. Source-version1.16.26 перевірено;
походження конкретного binary та повний optional Mixin dispatch ще не доведені.
Наявність ракети не видається за manufacturing proof. Наступні задачі —
accepted output/payment witness NASA й оплата/успішне розміщення станцій.

Закрийте гру/сервер, встановіть `nbtlib==2.0.4`, виконайте
`python install_runtime.py "C:\CurseForge\AllInOneAdventure2" --dry-run`, потім
без прапорця. Matching0.4.16JAR/скрипти й повний restart потрібні на обох
сторонах. Оригінали та старий власний JAR резервуються; світи й прогрес
зберігаються. Раніше описані правила recovery Forge/Clibano залишаються чинними.

[Звіт](docs/AIA2_0.4.16_CHECKPOINT.uk.md) · [Встановлення](implementation/INSTALL.uk.txt) · [PLAN](docs/AIA2_0.5.0_PLAN.md) · [PROGRESS](docs/AIA2_0.5.0_PROGRESS.md) · [Карти](docs/research/MOD_MECHANICS.md) · [Джерела](docs/research/SOURCE_INDEX.md) · [Приймальна перевірка](docs/testing/AD_ASTRA_ACCEPTANCE.uk.md).
