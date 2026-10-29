# All in One Adventure 2.0 — AIA2

**0.4.17-alpha — hotfix запуску ProjectE.** Minecraft 1.21.1 NeoForge,
FTB Quests 2101.1.36, KubeJS 2101.7.2 / Rhino85. Повний 0.5 ще в роботі.

Виправлено `ProjectETabletSourceMixin`: PE1.1.0 відкриває меню в `use(...)`,
а `openContainer(...)` з'явився в пізнішій гілці з тим самим version properties.
Redirect тепер відповідає релізному commit `6aea247f`; `require=1`,
серверні перевірки доступу та рівень47 для таблетки збережено.

Інсталятор перед зміною файлів перевіряє критичну сигнатуру таблетки у
ProjectE JAR інстансу, якщо його встановлено. Старий несумісний redirect
відхиляється до backup/write. Окремий інструмент перевіряє всі ProjectE
method/invocation contracts за наданим JAR; це не повне Mixin weaving.

**48 епох, 96 виробничих ключів, 3371 квест / 140 глав, 627 рецептів,
390 предметів/моделей/PNG — без змін.** Змінений один Java-клас;
решта201клас і всі1171non-JAR runtime-файли збережені byte-identical.

Справжній Sponge0.8.7 відтворив старий InvalidInjectionException і застосував
виправлений redirect до класу, скомпільованого з релізного джерела, з моделями
залежностей. Це не прогін оригінального ProjectE JAR чи повного клієнта.
Бінарне відтворення позначено BLOCKED: JAR не надано, download дає HTTP403.
FTB theme/QuestShape і Aether skyroot_log у наданих логах — наступні збої
після broken mod state; їхні конфіги й дані не змінювалися.

Закрийте Minecraft, розпакуйте пакет і виконайте
`python install_runtime.py "C:\CurseForge\AllInOneAdventure2" --dry-run`,
потім без прапорця. Оригінали й старий власний JAR резервуються;
світи, прогрес, сторонні квести та моди зберігаються. Потрібен повний restart.

[Hotfix-звіт](docs/AIA2_0.4.17_HOTFIX.uk.md) · [Встановлення](implementation/INSTALL.uk.txt) · [Client acceptance](docs/testing/PROJECTE_CLIENT_HOTFIX_ACCEPTANCE.uk.md) · [PLAN](docs/AIA2_0.5.0_PLAN.md) · [PROGRESS](docs/AIA2_0.5.0_PROGRESS.md) · [Попередній Ad Astra checkpoint](docs/AIA2_0.4.16_CHECKPOINT.uk.md).
