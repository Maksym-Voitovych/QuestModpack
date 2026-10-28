# All in One Adventure 2.0 — AIA2

**0.4.13-alpha** для Minecraft 1.21.1 NeoForge, FTB Quests 2101.1.36, KubeJS 2101.7.2 і Rhino build85. Повний план 0.5 залишається в роботі.

**48 епох,96 виробничих ключів,3351 квест у140 главах,623 рецепти,390 предметів/моделей/PNG.** Додано 5 квестів Clibano та 3 командні виробничі докази. Усі 3346 попередніх quest/task/reward/dependency payloads і623 рецепти збережено. Нових рецептів, предметів і текстур0.

Прив’язка рамки до внутрішнього контролера перевіряє всі 26 частин і поточного власника. GUI відкриває саме цю піч; чинне меню повторно перевіряє команду та епоху. Плавка працює тільки при горінні, перевіряє поточний рецепт, фізичні входи/підсилювачі та прийняття виходу. Змінені/legacy/corrupt операції призупиняються зі збереженням. Друга лінія не втрачає прогрес через заповнений вихід або polling-кеш.

Доступні перевірки:228 Python,57 Node,5237 Java,119перевірок мінімального Minecraft у 2 JVM;776 нових модельованих умов. Повний Clibano weaving, JEI/UI, Survival і TPS — NOT RUN. Автоматичний IO через рамку не заявлено: upstream forwarding закоментовано.

Із закритою грою встановіть `nbtlib==2.0.4`, виконайте `python install_runtime.py "C:\CurseForge\AllInOneAdventure2" --dry-run`, потім без прапорця. Matching 0.4.13 JAR/скрипти потрібні на обох сторонах; потрібен повний перезапуск. Інсталятор резервує оригінали та старий власний JAR, зберігаючи світи/прогрес/сторонні квести. За можливості завершіть стару активну плавку Clibano до оновлення: операції без receipt залишаються paused. `/aia2clibano status x y z` пояснює стан; operator-only `cancel` явно резервує та скидає лише прогрес, без refund/output.

[Звіт](docs/AIA2_0.4.13_CHECKPOINT.uk.md) · [Встановлення](implementation/INSTALL.uk.txt) · [PLAN](docs/AIA2_0.5.0_PLAN.md) · [PROGRESS](docs/AIA2_0.5.0_PROGRESS.md) · [Карти](docs/research/MOD_MECHANICS.md) · [Джерела](docs/research/SOURCE_INDEX.md) · [Приймальна перевірка](docs/testing/CLIBANO_ACCEPTANCE.uk.md).
