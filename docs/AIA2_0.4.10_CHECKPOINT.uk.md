# AIA2 0.4.10-alpha — пасивні здібності ProjectE

Проміжний перевірений блок роботи над0.5. База: `7539c6b` /0.4.9-alpha.
Повний0.5 залишається незавершеним.

## Зміст і збереження

48 епох,96 виробничих ключів,3314 квестів/140 глав,621 custom-рецепт і390
предметів/моделей/PNG збережено. У цьому блоці нових квестів, рецептів,
нагород, предметів та текстур:0. Усі3314 quest payloads, включно з координатами,
залежностями, task/reward IDs, та621 recipe entries незмінні.
[Порівняння з базою](../implementation/projecte-passive-preservation-v5.json).

## Підтверджені обходи та реалізація

- `inventoryTick` працює незалежно від правого кліку. Серверні ефекти перевіряють
  фактичного носія, live FTB-команду, готовність і floor предмета.
- Native damage/fire/water/lava розрахунки читають броню напряму. Їм передається
  дозволений view; реальні stacks і режими не змінюються.
- Свіжі equipment/Curios attributes фільтруються. Уже застосовані звіряються
  після зміни стадії/команди/reload без перевдягання. Vanilla removal лишається
  штатним; дозволені спільні contributors і чужі значення не підміняються.
- Bag/chest/pedestal callbacks використовують фактичного гравця або початковий
  канонічний block entity. Контекст машини відновлюється через `finally`.
  Native ACTIVE, cooldown, inventory, durability та EMC не очищуються.
- Pickup suction має окремий шлях: перевіряються і справжня сумка, і кільце
  всередині до штатного вибору. Недоступний предмет не змінює порядок решти.
- Key capability, gem-mode packet, Archangel і gem zap/explosion отримали
  серверні перевірки. Native cleanup власних InternalAbilities продовжується.
- Curios-tablet створює меню без hand. Його source floor47 тепер прив’язано до
  фактично відкритого меню; pause/remap не перетворює його на table45.
- `onItemUseFirst` перехоплюється разом із `useOn`; null/fake/unattributed
  серверні виклики не отримують прав сусіднього гравця. KubeJS break event
  перевіряє також mainhand tool до native `mineBlock`/AOE.

Додано5 helpers і20 mixins; загалом58 зареєстрованих mixins,136 compiled classes.
Machine Guard API4, FTB hotfix, manufacturing receipts і SavedData schema збережено.
[Native-аудит, SHA та межі](../content/audit/v5-projecte-passive-guard.json).

## Перевірки

-190 Python-тестів,55 Node-тестів,5237 pure-Java assertions і JDK21 build:PASS.
-208 нових actual-helper/handler/GuardPolicy умов у модельованих hosts:
  world/packets/tablet63, storage43, armor49, Curios32, suction21.
- Мінімальний Minecraft1.21.1/NeoForge21.1.264:99 assertions,2 JVM,650 ticks,
  SavedData restart. Нові9 умов перевіряють реальні receiver/FakePlayer та
  vanilla equipment application/stability/removal через новий hook.
-1163 runtime-файли byte-identical після генерації з `PYTHONHASHSEED=83`.
  SNBT/ID/DAG/96keys/resources/recipe shapes і140 глав перевіряються загальним
  валідатором; координати й1147 перетинів залишаються незмінними.
- Інсталятор відхиляє неповний JAR або незареєстровані passive mixins до backup
  та записів у світ. Результат запакованого dry-run/upgrade:
  [звіт доставки](../implementation/projecte-passive-package-install-v5.json).

Мінімальний сервер не містить ProjectE/Curios. Optional weaving, повний
KubeJS/FTB runtime, JEI/UI, Survival і TPS:NOT RUN.

## Встановлення й наступна дія

Зупинити клієнт/сервер. У пакеті встановити `nbtlib==2.0.4`, виконати
`python install_runtime.py "C:\CurseForge\AllInOneAdventure2" --dry-run`, потім
повторити без прапорця. Інсталятор резервує старий власний JAR і змінювані
файли, зберігає світи/знання/прогрес та сторонні квести. Повністю перезапустити
клієнт і сервер. [Повна інструкція](../implementation/INSTALL.uk.txt).

Далі: [приймальна перевірка ProjectE](testing/PROJECTE_PASSIVE_ACCEPTANCE.uk.md)
на повному інстансі та core-дослідження EvilCraft1.2.99/Forbidden Arcanus2.6.1.
Клієнтський Gem-рух, прямі API сторонніх аддонів, уже створені effects і
enchantment location effects незмінної броні після unlock лишаються окремими
межами. Draconic CI633 provenance, Roots ritual restart,6IF fluid gaps,
решта37partial карт і старі обов’язкові лінії48 епох ще не завершені.
