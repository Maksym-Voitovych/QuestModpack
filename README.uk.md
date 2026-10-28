# All in One Adventure 2.0 — AIA2

**0.4.15-alpha** для Minecraft 1.21.1 NeoForge, FTB Quests2101.1.36, KubeJS2101.7.2 і Rhino build85. Повний0.5 ще в роботі.

**48епох,96виробничих ключів,3351квест у140главах,623рецепти,390предметів/моделей/PNG.** Цей блок додає історію залежностей Clibano. Усі старі квести, рецепти, нагороди, ID та координати незмінні; нового контенту тут0.

Плавка перевіряє поточні ingredient tags, enhancer та residue definitions. Окремий NBT-журнал фіксує historical lane snapshots і definition+кількість накопичених залишків. Зміна правил після reload/restart призупиняє операцію зі збереженням даних. Застарілий Ingredient cache й самий holder ID не підтверджують стару оплату. Один finish не може зарахувати залишок двічі.

Старі залежні paid lanes і positive residues без witness зберігаються paused. За можливості завершіть старі операції до оновлення. `/aia2clibano status x y z` дає діагностику; операторський `cancel` резервує й очищує лише cooking progress. Окремий явний `quarantine-residues` переносить stock/history до bounded8NBTbackup без результату/refund/proof, зберігаючи slots/fuel/cooking counters. Інсталятор не виконує цих команд.

233Python/57Node/5237Java/151minimal-Minecraft перевірок PASS;285нові modeled assertions і14actual-NBT checks. Повний Clibano weaving/JEI/UI/Survival/TPS — NOT RUN. Frame IO, generic copied components і universal rollback залишаються поза цим блоком.

Закрийте гру/сервер, встановіть `nbtlib==2.0.4`, виконайте `python install_runtime.py "C:\CurseForge\AllInOneAdventure2" --dry-run`, потім без прапорця. Matching0.4.15JAR/скрипти потрібні на обох сторонах; повний перезапуск обов'язковий. Оригінали й старий власний JAR резервуються; світи/прогрес/сторонні квести зберігаються.

[Звіт](docs/AIA2_0.4.15_CHECKPOINT.uk.md) · [Встановлення](implementation/INSTALL.uk.txt) · [PLAN](docs/AIA2_0.5.0_PLAN.md) · [PROGRESS](docs/AIA2_0.5.0_PROGRESS.md) · [Карти](docs/research/MOD_MECHANICS.md) · [Джерела](docs/research/SOURCE_INDEX.md) · [Приймальна перевірка](docs/testing/CLIBANO_DEPENDENCIES_ACCEPTANCE.uk.md).
