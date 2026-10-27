# All in One Adventure 2.0 — AIA2

**0.4.12-alpha** для Minecraft 1.21.1 NeoForge, FTB Quests 2101.1.36, KubeJS 2101.7.2 і Rhino build85. Повний 0.5 ще розробляється.

**48 епох, 96 виробничих ключів, 3346 квестів у 140 главах, 623 нативні custom-рецепти і 390 предметів/моделей/PNG.** Додано 16 цілей Forbidden Arcanus і шість нативних ритуальних критеріїв. Усі 3330 попередні task/reward/dependency payloads і 623 recipe entries збережено; виправлено одну відсутню іконку Forge. Нових рецептів, предметів і текстур: 0.

Курс Forbidden має 24 етапи: формування кузні, носії есенцій, справжні ритуали й підвищення рівня, підготовка Clibano. Три hooks перевіряють власника, поточне визначення, фізичні входи/підсилювачі, оплату й результат. Змінені або видалені оплачені ритуали призупиняються зі збереженням NBT; старі операції без доказу не отримують вигаданої оплати. `/aia2forge status x y z` пояснює стан; операторське `cancel` зберігає bounded backup і фізичні входи, без повернення есенцій та видачі результату.

212 Python-тестів, 55 Node-тестів, 5237 Java assertions і 111 перевірок мінімального Minecraft у двох JVM: PASS. Ще 297 нових умов перевірено в модельованих hosts. Повний Forbidden weaving, JEI/UI, Survival і TPS: NOT RUN. Власник внутрішнього Clibano controller і transitive registry effects ще відкриті; native ритуальний критерій передує прийняттю output.

Із закритою грою встановіть nbtlib==2.0.4 і виконайте `python install_runtime.py "C:\CurseForge\AllInOneAdventure2" --dry-run`, потім повторіть без прапорця. Інсталятор резервує оригінали й старий власний JAR, зберігає світи, прогрес, знання та сторонні квести. Matching JAR/скрипти 0.4.12 потрібні на обох сторонах; повністю перезапустіть клієнт і сервер. За можливості завершіть старі активні Forge-ритуали перед оновленням: їхню оплату неможливо підтвердити заднім числом.

[Checkpoint](docs/AIA2_0.4.12_CHECKPOINT.uk.md) · [Встановлення](implementation/INSTALL.uk.txt) · [PLAN](docs/AIA2_0.5.0_PLAN.md) · [PROGRESS](docs/AIA2_0.5.0_PROGRESS.md) · [Карти](docs/research/MOD_MECHANICS.md) · [Джерела](docs/research/SOURCE_INDEX.md) · [Приймальна перевірка](docs/testing/FORBIDDEN_RITUAL_ACCEPTANCE.uk.md).
