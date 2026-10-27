# All in One Adventure 2.0 — AIA2

**0.4.11-alpha** для Minecraft 1.21.1 NeoForge, FTB Quests 2101.1.36, KubeJS 2101.7.2 і Rhino build85. Повний 0.5 ще розробляється.

**48 епох, 96 виробничих ключів, 3330 квестів у 140 главах, 623 нативні custom-рецепти і 390 предметів/моделей/PNG.** Додано 16 цілей EvilCraft і дві механічні формули. Усі 3314 попередні quest/task/reward payloads і залежності, крім координат, та 621 recipe entries збережено. Нових предметів і текстур: 0.

Основний курс EvilCraft має 24 етапи: кров та інфузія, чаші й promises, undead ресурси, захоплення духів, Spirit Furnace/Reanimator, погода та домашня логістика. Native Closure перевіряє справжню подію захоплення. Три адаптери перевіряють інфузію, фактичний лут і реанімацію перед витратами. Після reload старий кеш інфузора чекає зміни native input/fluid/tier; повернення вже сплаченої крові та відмотування RNG не реалізовано.

198 Python-тестів, 55 Node-тестів, 5237 Java assertions і 99 перевірок мінімального Minecraft у двох JVM: PASS. Ще 49 нових умов перевірено в модельованих hosts. Повний EvilCraft/Forbidden weaving, JEI/UI, Survival і TPS: NOT RUN. Forbidden ritual guard ще TODO; точний source-аудит збережено.

Із закритою грою встановіть nbtlib==2.0.4 і виконайте `python install_runtime.py "C:\CurseForge\AllInOneAdventure2" --dry-run`, потім повторіть без прапорця. Інсталятор резервує оригінали й старий власний JAR, зберігає світи, прогрес, знання та сторонні квести. Matching JAR/скрипти 0.4.11 потрібні на обох сторонах; повністю перезапустіть клієнт і сервер.

[Checkpoint](docs/AIA2_0.4.11_CHECKPOINT.uk.md) · [Встановлення](implementation/INSTALL.uk.txt) · [PLAN](docs/AIA2_0.5.0_PLAN.md) · [PROGRESS](docs/AIA2_0.5.0_PROGRESS.md) · [Карти](docs/research/MOD_MECHANICS.md) · [Джерела](docs/research/SOURCE_INDEX.md) · [Приймальна перевірка](docs/testing/EVILCRAFT_CORE_ACCEPTANCE.uk.md).
