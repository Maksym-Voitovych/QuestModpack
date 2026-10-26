# AIA2 Quest & Progression System

**0.4.9-alpha** для Minecraft1.21.1 NeoForge, FTB Quests2101.1.36, KubeJS2101.7.2/Rhino build85. Повний0.5 ще розробляється.

**48 епох,96 виробничих ключів,3314 квестів у140 главах,621 нативний custom-рецепт і390 предметів/моделей/PNG.** Усі3280 попередні quest/task/reward payloads і залежності, крім координат, та618 recipe entries збережено.96legacy ручних цілей залишаються.

Додано18 квестів ProjectE та16 Draconic. У вже відкритому меню перевіряються поточна команда, доступ до table45/tablet47, whitelist, позитивна поточна EMC-вартість, компоненти й поточний inventory. FuelMapper оновлюється після EMC-фільтрації; помилка закриває обидва кеші. TimeWatch перевіряє власника фактичної машини й відновлює контекст через finally. Додаткового очищення знань або EMC немає.

Три fusion-upgrades Draconic зберігають усі native costs, catalyst, tier, energy та output і додають по2магічно-технічні компоненти. IO↔relay конверсії збережено. Draconic-карта23етапів залишається PARTIAL: джерело3.1.4/експорт перевірено, зв’язок із CI build633 не підтверджено.

Із закритою грою виконайте install_runtime.py з --dry-run, потім без прапорця. Інсталятор резервує оригінали, зберігає світи, знання та сторонні квести й вимагає matching0.4.9/API4JAR. Повністю перезапустіть клієнт і сервер.

178 Python tests,52 Node tests,5237 Java assertions і90перевірок мінімального Minecraft у2JVM:PASS. Optional ProjectE/Draconic dispatch, JEI/UI, Survival іTPS:NOT RUN. Пасивні armor/Curios/world-tool шляхи ProjectE ще потребують окремого аудиту.

[Checkpoint](docs/AIA2_0.4.9_CHECKPOINT.uk.md) · [Встановлення](implementation/INSTALL.uk.txt) · [PLAN](docs/AIA2_0.5.0_PLAN.md) · [PROGRESS](docs/AIA2_0.5.0_PROGRESS.md) · [Карти](docs/research/MOD_MECHANICS.md) · [Джерела](docs/research/SOURCE_INDEX.md) · [Приймальна перевірка](docs/testing/PROJECTE_DRACONIC_ACCEPTANCE.uk.md).

24основні карти завершені у визначеному обсязі;37partial і невивчені моди залишаються. Старі обов’язкові лінії48епох і повний ігровий приймальний тест ще не завершені.
