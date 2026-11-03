# All in One Adventure 2.0 — AIA2

**0.4.24-alpha — точні профілі CDG Mold.**
Minecraft 1.21.1 NeoForge / FTB Quests 2101.1.36 / KubeJS 2101.7.2 / Rhino85.
Повний 0.5 ще в роботі.

Додано 6 побічних цілей для профілів Lines, Bowl, Chain і Bar та їхніх
застосувань у пресуванні й литті. Item tasks перевіряють повний компонент
профілю через `fuzzy`; bare Mold або інша форма не підходять, додаткова
назва допускається. Це перевірка профілю й зразків, не native production proof.

**3402 квести / 140 глав / 6 груп, 627 рецептів, 3138 предметних нагород,
390 предметів/моделей/PNG, 48 епох і 96 виробничих ключів.** Усі 3396 старі
payloads без координат збережено; 20 координат пересунуто в одній главі.
Старі generic Mold tasks, нагороди, залежності й прогрес не замінюються.

Source schema, компілятор, валідатори, пакувальник та інсталятор відхиляють
пошкоджені або пропущені predicates. Minecraft може частково завантажити
некоректний ItemStack без компонента, тому перевірки виконуються до запуску гри.
43 pinned source/recipe файли й окремий Minecraft API fact збережено.

Мінімальний Minecraft-сервер: 329 перевірок у двох JVM, включно з 56 новими
CODEC/component-map checks. Синтетичний компонент доступний лише в opt-in
IDE smoke fixture, не у звичайній грі. Оригінальні CDG/FTB UI, повний клієнт,
JEI, Survival і TPS не перевірялися; 88 FTB matcher checks мають modeled host.
API4, 16 native rules, 76 Mixins і всі guard policy classes збережені.

Зупиніть гру, розпакуйте пакет окремо й виконайте
`python install_runtime.py "C:\CurseForge\AllInOneAdventure2" --dry-run`.
Після перевірки повторіть без прапорця й повністю перезапустіть обидві сторони.
Інсталятор резервує змінені файли/старий JAR і не редагує світи чи прогрес.

[Checkpoint](docs/AIA2_0.4.24_CHECKPOINT.uk.md) ·
[Встановлення](implementation/INSTALL.uk.txt) ·
[Ручна перевірка](docs/testing/CDG_MOLDS_ACCEPTANCE.uk.md) ·
[План](docs/AIA2_0.5.0_PLAN.md) · [Прогрес](docs/AIA2_0.5.0_PROGRESS.md).
