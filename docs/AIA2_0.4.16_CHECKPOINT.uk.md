# AIA2 0.4.16-alpha — космічна інфраструктура Ad Astra

Це завершений проміжний блок розробки0.5. Повний реліз0.5 ще IN_PROGRESS.
Базу15380e8 зарезервовано до змін; Windows-інстанс не змінювався.

Реалізовано20optional-квестів для епох37/38, без нових предметів чи текстур.
Наземне бюро доступне до старогоM1, який уже вимагає ракету. Курс пояснює
Compressor, кисень із ручної води, паливну переробку, скафандри й усі чотири
ступені: Moon/Desh→Mars/Ostrum→Venus/Calorite→Glacio. Автоматизація води й
Oxygen Sensor з'являються після потрібних позаземних металів. Cryo Fuel можна
підготувати з Blue Ice до першого Glacio-польоту.59tasks:37item,14observation,
8dimension;15itemtasks перевіряють справжній player crafting.

| Двигун | Епоха | Збережений native склад | Додані компоненти |
|---|---|---|---|
| Steel | 37 | 5steel plates, Engine Frame, Fan | matrix36, catalyst36, Air Essence, Advanced Control Circuit |
| Desh | 37 | 5desh plates, Steel Engine, Fan | matrix36, catalyst36, Rune of Earth, Oritech Processing Unit |
| Ostrum | 37 | 5ostrum plates, Desh Engine, Fan | matrix36, catalyst36, Rune of Fire, Printed Circuit Board |
| Calorite | 38 | 5calorite plates, Ostrum Engine, Fan | matrix36, catalyst36, Gaia Ingot, Ultimate Control Circuit |

Чотири Create mechanical crafting формули5×3 замінюють чотири прості
native producers. Перевірено closure всіх42064експортованих рецептів для
визначеної групи. Нові інгредієнти не використовують ключів; ancestry
матриці/каталізатора36 не містить Ad Astra й доступна до першого польоту.
14функціональних предметів перевірено на floor38(12піднято),4block floors
(3піднято),28native та2custom producer floors. Декоративну калоритову групу
не блокували масово. Netherite Space Suit лишається на37.

Виправлено підтверджений cache/menu обхід NASA Workbench. Native `update()`
кешує рецепт поза ticker, а `craft()` раніше перевіряв лише non-null recipe.
Новий серверний адаптер звіряє canonical BE, готовий Guard, власника,
поточну recipe identity, стадію,14входів, точний output і preview перед
будь-якими native particles/drop/slot writes/оплатою. GUI й автоматичний
tick проходять одну перевірку. Live-menu guard перевіряє поточну команду,
власника, стадію, reach і original BE; direct quickMove preview14 заборонено.
Майбутній/corrupt/stale рецепт лишає входи незмінними. Інші Ad Astra меню
не отримують цих NASA-специфічних правил.

Усі3351попередні quest/task/reward/dependency payloads і623custom recipes
збережено. Разом3371квест/140глав/6груп,627рецептів,3107itemнагород,
390предметів/моделей/PNG та96виробничих ключів.20нових матеріальних нагород,
старих змінених нагород0.36старих координат переміщено у3главах Ad Astra.
Глобально1154перетини, як на базі;0overlaps/backwards/vertical/long warnings.

Exact source pin45abf0ec декларує1.16.26/MC1.21.1. Збережено99SHA-файлів,
у тому числі Astrodux, NASA, станції, ракети, recipe codecs та advancements.
Source/export recipe comparison:533/518,517спільних ID,461канонічно однаковий,
56відмінних. Source-version збіг не доводить походження конкретного binary;
для bills використано installed export. Карта Ad Astra має27етапів; загалом
27scoped core maps і34partial для61мода. Карта ядра не означає повне
покриття всіх функцій мода або успішне внутрішньоігрове тестування.

255Python/57Node/5237Java/151minimal-Minecraft assertions PASS. Мінімальний
сервер виконав650ticks у2JVM.13JS syntaxfiles і1172byte-identical runtime
files післяповноїгенераціїPYTHONHASHSEED113 перевірено. Інсталятор оновив
synthetic0.4.15 fixture з0dry-run writes, backupoldJAR і збереженням opaque
world/progress/foreign markers; repeatinstallідемпотентний. Це неworldmigration
реального модпаку. Автоматичні результати й точні лічильники збережено в
`implementation/release-report.json`, `implementation/validation-report.json`,
`implementation/ad-astra-jar-v6.json` та package-install report.
NASA має244модельовані assertions на справжніх helper/handlers/GuardPolicy;
тіло native craft у host byte-identical джерелу. Повний optional weaving,
JEI, UI, Survival і TPS не запускалися. Мінімальний сервер має інший склад
модів і не є runtime-тестом NASA. Приймальні сценарії:
[AD_ASTRA_ACCEPTANCE](testing/AD_ASTRA_ACCEPTANCE.uk.md).

Наступний конкретний блок:

1. NASA accepted output + exact payment witness: upstream спочатку виконує
   `dropItemStack`, потім shrink. Сам RETURN не підтверджує прийняття виходу.
   Rocket advancements використовують `inventory_changed` і не підходять.
2. Station split-stack payment: native перевірка сумує весь inventory, але
   списання бере лише перший matching stack; packet ігнорує `placeInWorld`
   boolean. Потрібен окремий adapter із підтвердженою оплатою та placement.
3. Явна міграція старих required умов37/38, які досі мають постфактум-кроки;
   новий optional курс не переписує збережені tasks/dependencies.

Далі34partial/невивчені моди й решта required ліній48епох. Roots unfinished
ritual restart лишаєтьсяTODO; DraconicCI633 і6IFfluid source gaps BLOCKED.
Machine Guard, подвійні ключі, FTB-міст та EMC-міст збережені.
