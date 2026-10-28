# Forge dependencies — приймальна перевірка 0.4.14

Ці сценарії повного модпаку поки **NOT RUN**. У хмарі виконано modeled-host
регресії, компіляцію проти Minecraft/NeoForge та actual-NBT перевірки
мінімального сервера, де Forbidden Arcanus не встановлено.

Працювати на тестовій копії світу з matching 0.4.14 JAR на клієнті й сервері.
До оновлення за можливості завершити активні ритуали. Зберегти копію світу.
Базові власник/стадія/оплата/ритуальні критерії перевіряються також за
[основним планом Forge](FORBIDDEN_RITUAL_ACCEPTANCE.uk.md); старі обмеження
щодо Clibano у тому історичному документі уточнює
[план Clibano](CLIBANO_ACCEPTANCE.uk.md).

1. Запустити звичайний дозволений ритуал без enhancers і перевірити єдине
   списання, завершення й output. Перевірити weaving наявних трьох Forge hooks,
   `/aia2 status`, 140 глав і українські повідомлення.
2. На тестовому datapack зробити копію справжнього ритуалу, замінивши один
   vanilla ingredient на item-tag із тим самим предметом. Назви registry
   і поля брати з фактичного 2.6.1 JSON; це data registry, не RecipeSerializer.
   Почати ритуал. Не змінюючи сам ritual JSON і фізичні входи, додати інший
   предмет до тегу та виконати reload. Очікується pause без output, повторної
   оплати, очищення pedestal/main чи втрати counter. Відновити попередній тег:
   операція може продовжитися. Самий порядок однакових членів не є зміною.
3. Повторити для pedestal ingredient, тегу в OR-альтернативах, видаленого
   та порожнього тегу. Застарілий Ingredient item cache не повинен дозволяти
   новий запуск із предметом, якого вже немає в поточному тегу.
4. Почати з enhancer. Змінити визначення того самого enhancer ID, оновити
   його фізичний слот і cache. Сам ID/предмет не повинні дозволяти продовження
   старої оплати з новим ефектом. Відновити exact definition. Окремо перевірити
   потрібний enhancer та named enhancer-tag, зокрема порожній named set.
5. Перевірити підтримувані три native effects і TimeCondition. Невідомий
   custom ingredient/effect/condition повинен блокувати нову оплату, а стару
   операцію зберігати paused. Візуальні текстури magic circle не входять у
   новий snapshot. Повний enhancer CODEC включає description/display item:
   їхня зміна може консервативно призупинити роботу.
6. Зберегти оплачений ритуал і повністю перезапустити сервер. Перевірити
   `active_ritual.aia2_gameplay_dependencies_v1` разом зі schema1 receipt.
   Повторний native encode, який знає лише ID/counter/starter, не повинен
   стерти snapshot. Зміна/відсутність registry definition зберігає raw NBT.
7. На копії світу перевірити старий schema1 paid receipt без extension:
   простий ритуал без item-tags, required/installed enhancers може продовжитися;
   залежний ритуал зберігається paused. Tick/save не мають автоматично
   приписувати старій оплаті поточні залежності. Без receipt оплата також
   не підтверджується. Unknown schema/extra fields/wrong types не приймаються.
8. Перевірити `/aia2forge status x y z`. За потреби оператор своєї команди
   поруч може явно виконати `cancel`: не більше 8 persistent backups,
   фізичні предмети збережено, есенції не повертаються, output/proof немає.
   Інсталятор автоматично цього не робить. При зміні залежностей саме під
   час оплати запис лишається PENDING із діагностикою, без винятку в server event.
9. Виміряти TPS із реальними паралельними кузнями та великими тегами.
   Membership/effect/JSON budgets обмежують перевірку; серіалізація Component
   усередині повного enhancer CODEC передує JSON budget і не має глобальної
   оцінки CPU. Перевірити JEI, клієнт, survival-завершення й два ключі епох.

Цей блок стосується paid Forge. Clibano transitive recipe/enhancer/residue
snapshots, Obelisk/passives, прямі addon callbacks та загальний rollback
залишаються окремими завданнями. Нативні витрати, RNG і midpoint effects
не відкочуються автоматично.
