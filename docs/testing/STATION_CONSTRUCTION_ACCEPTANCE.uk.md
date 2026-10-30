# Station adapter0.4.19 — приймання повного інстансу

Статус: **NOT RUN**. Виконувати на окремій копії інстансу й світу, з однаковим
JAR/скриптами на клієнті та сервері. Оригінальний Ad Astra1.16.26 binary
не був наданий у хмару; source-shaped Sponge і minimalMC його не замінюють.

1. Зупинити гру, виконати installer `--dry-run`, перевірити compiled preflight
   NASA/station і ProjectE. Застосувати matching пакет і повністю перезапустити.
   `/aia2 status` має показувати активний API4. Перевірити відсутність injection errors.
2. На Survival-команді до37 спробувати Earth/Moon/Mars station; до38 —
   Mercury/Venus/Glacio. Не має бути списань, блоків чи нової станції.
   Відповідна орбіта відкривається лише зі своєю стадією.
3. У відкритій орбіті залишити native меню/ракету й доступ до планети.
   Для вимоги64 розкласти матеріал1+63. Після побудови списано рівно64,
   усі інші вимоги сплачені, структура, station entry і teleport працюють.
4. За вимоги64 подати63; перевірити повну відмову до оплати. На test-only
   datapack перевірити overlapping ingredients і альтернативи з не-greedy
   розподілом. Та сама одиниця не може оплачувати дві вимоги.
5. Future tag-member не витрачається раніше власної стадії. Застарілий native
   Ingredient cache, recipe/tag reload, заміна slot refs/count/components або
   команди під час операції не дозволяють продовження. Стандартні матеріали
   працюють; нестандартні компоненти не витрачаються й не дають обхід.
6. Missing/empty/all-air/multi-palette/entity/blockNBT/custom template відхиляється
   до оплати. Нативний31×32×31 шаблон має бути підтриманий. Перевірити українські
   повідомлення й відсутність видалення наявних станцій.
7. Test-only callback відхиляє один первинний non-air setBlock або видаляє блок
   перед реєстрацією. Немає нового station entry/teleport/claims. Native false
   чи zero writes також не зараховуються. Платні ресурси/частково поставлені
   блоки можуть залишитися: адаптер не обіцяє refund/rollback.
8. Creative/Spectator/FakePlayer, off-thread або застаріла FTB-команда не будують.
   Прямий unscoped constructor, повторний packet/constructor, reentry й exception
   не позичають чужий scope; після відмови наступна законна операція працює.
9. Звичайні структури, сусідні shape/waterlogging updates та старі станції
   працюють. Перевірити persistence старих станцій, FTB-прогресу й96 ключів
   після restart, а також попередні15 mechanic rules і чотири NASA proofs.
10. Повторити ProjectE client-hotfix acceptance, JEI шести station recipes,
    Survival37→38 та виміряти час/tick impact реального будівництва.
    Наявність station entry сама по собі не є новим durable manufacture proof.

Фіксувати exact JAR SHA, команду/стадію, input counts до/після, результат
placement/registration і teleport. Приватні логи й світи не комітити.
