# EvilCraft 1.2.99 — перевірка курсу й native guards0.4.11

Проводити на тестовій копії повного інстансу з matching JAR0.4.11 та його
KubeJS/config. Модельовані helpers не доводять Mixin weaving з EvilCraft.
Основний світ і особисті збереження хмарні тести не використовують.

1. Перевірити запуск без Mixin/KubeJS errors і `/aia2 status`: Machine Guard
   API4 активний, епоха обох тестових FTB-команд відповідає ledger.
2. У Magic→EvilCraft перевірити16нових optional цілей епох13/19/28: українські
   назви, іконки, порядок і приховування майбутніх цілей. Старі task/reward IDs
   та завершення повинні залишитися. Дві manufacturing-гілки48епох незмінні.
3. Bootstrap: отримати Dark Power Gem із5сусідніх Blood source blocks; далі
   виконати native Blood Infuser recipe. Decompression з блока не вважати
   первинним джерелом. Перевірити redstone pause, інвентарні сторони й bowls0..3.
4. Механічно скласти Spirit Reanimator і Sanguinary Accumulator у Create5×3.
   Звичайний верстак більше не повинен давати ці контролери. Зіставити всі
   native9material units і2додані міжмодові компоненти з JEI. Перевірити pickup
   з Mechanical Crafters/автоматичне транспортування; goals не мають craft:true.
5. Blood Infuser: дозволена команда/рецепт, замкнений owner, unowned/imported
   машина, output наступної епохи, підроблений key-output і component variants.
   Відмова має бути до addToProduceSlot/input/fluid/xp. При зміні лише стадії
   незмінний raw cache повинен знову працювати після відкриття.
6. Reload рецептів: видалити/змінити вибрану формулу; старий raw value не
   повинен виготовляти результат. Кеш не має generation key: після reload
   потрібно змінити native input/fluid-amount/tier для нового вибору. Таймер
   примусово не скидається; це обмеження, а не автоматичний cache-rebind.
7. Vengeance Focus має заморожувати духа; Piercing Focus його знищує. Реально
   захопити духа в Box of Eternal Closure: goal повинен зарахувати native
   `evilcraft:closure`. Порожня коробка через /give не є подією захоплення.
8. Зібрати порожнистий Spirit Furnace під розміри істоти, підвести Blood і
   відвести лут. Для дозволеного/забороненого фактичного loot-output перевірити
   вставлення. Нативний RNG, побічні loot effects і кров до onItemDrop вже
   можуть бути сплачені; цей адаптер не відмотує їх і не повертає витрати.
9. Reanimator: дозволений дух/звичайне Egg/Blood; тип без Spawn Egg; future
   egg; downgrade owner під час роботи. Заборонений callback не виконує
   native drain, egg consumption чи clearBoxContents. Окремо перевірити
   native elapsed timers і відновлення після restart — універсального
   збереження всіх лічильників outer tick framework не заявлено.
10. Перевірити реальну роботу Spirit Furnace/Reanimator через hopper/труби,
    offline owner, replacement блока на тій самій позиції й дві сусідні команди.
    Фактичний receiver має визначати права; найближчий гравець їх не надає.
11. Sanguinary Accumulator потребує8резервуарів з Blood у визначених позиціях.
    Огляд/інвентарні goals лише готують установку; вони не вимірюють її роботу.
    Environmental/Sanguinary paid caches і Purifier action registry ще не
    отримали повних output/paid-state adapters, що записано в аудиті.
12. Перезапустити клієнт/сервер; перевірити owner NBT, FTB progress, дві ключові
    гілки, receipts, FireWorksites і ProjectE knowledge/EMC. Записати MSPT/TPS
    репрезентативної фабрики; хмарний мінімальний сервер цього не вимірює.

Джерела й SHA: `content/research/evidence/evilcraft_core_next_v5/manifest.json`,
`content/research/evidence/dark_magic_native_v5/manifest.json`. Exact pin:
[`de23efdb`](https://github.com/CyclopsMC/EvilCraft/tree/de23efdb83ea1b84addad6e3b1dc51a37147dc1a).
Стан наступного Forbidden Arcanus блока:
[`v5-dark-magic-native-findings.json`](../../content/audit/v5-dark-magic-native-findings.json).
