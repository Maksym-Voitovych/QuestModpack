# Приймання нативних механік у повному AIA2

Статус: **NOT RUN**. Нижче сценарії для копії Windows-інстансу. Статичні
контракти, SHA та перевірка JSON не означають виконаного Mixin/event dispatch.

## Підготовка

1. Закрийте гру; зробіть копію інстансу та світу. Встановіть пакет через dry-run і резервувальний інсталятор.
2. Повністю перезапустіть клієнт і сервер. Перевірте `/aia2 status`: Machine Guard API4 активний, FTB готовий, епоха правильна.
3. Використовуйте нові тестові команди/акаунти або окремий тестовий світ. Не скидайте дані основного проходження.
4. Дійдіть до потрібної епохи; майбутня глава має залишатися заблокованою. Сам advancement не відкриває епоху.
5. Для кожної цілі спочатку отримайте результат через `/give` або передачу предмета. Ритуал/мережа/структура ще не виконані — action-задача не повинна завершитися.
6. Виконайте конкретну дію зі стовпця нижче. Перевірте нативне досягнення та відповідну FTB-задачу, потім перезайдіть і перезапустіть сервер.
7. Раніше отримані нативні досягнення є особистим прогресом гравця; FTB зараховує їх за власними правилами команди. Вони не замінюють командні виробничі записи 96 ключів.

## Конкретні приймальні випадки

| Епоха | Досягнення | Що саме має підтвердитися |
|---|---|---|
| 7 | `aia2:ceremonies/buffalo_dance` | Сервер Totemic розпочав ефект конкретної церемонії після збору потрібної мелодії; зарахування отримують гравці в межах 8 блоків. Це не підтверджує особисте виконання всіх нот. |
| 7 | `aia2:ceremonies/eagle_dance` | Сервер Totemic розпочав ефект конкретної церемонії після збору потрібної мелодії; зарахування отримують гравці в межах 8 блоків. Це не підтверджує особисте виконання всіх нот. |
| 7 | `aia2:ceremonies/fertility` | Сервер Totemic розпочав ефект конкретної церемонії після збору потрібної мелодії; зарахування отримують гравці в межах 8 блоків. Це не підтверджує особисте виконання всіх нот. |
| 7 | `aia2:ceremonies/flute_infusion` | Сервер Totemic розпочав ефект конкретної церемонії після збору потрібної мелодії; зарахування отримують гравці в межах 8 блоків. Це не підтверджує особисте виконання всіх нот. |
| 14 | `occultism:occultism/summon_foliot_crusher` | Occultism викликав Ritual.finish для гравця, який запустив ритуал; збігається ID активного рецепта. Сам предмет або книга не дають цього критерію. |
| 14 | `occultism:occultism/summon_foliot_lumberjack` | Occultism викликав Ritual.finish для гравця, який запустив ритуал; збігається ID активного рецепта. Сам предмет або книга не дають цього критерію. |
| 14 | `occultism:occultism/summon_foliot_transport_items` | Occultism викликав Ritual.finish для гравця, який запустив ритуал; збігається ID активного рецепта. Сам предмет або книга не дають цього критерію. |
| 14 | `pneumaticcraft:pneumatic_wrench_charged` | На серверному inventory tick гравець має Pneumatic Wrench із тиском щонайменше3bar; сам незаряджений предмет не зараховується. |
| 14 | `pneumaticcraft:pressure_chamber` | ServerPlayer установлює Pressure Chamber Valve; checkIfProperlyFormed(level,pos) повертає true. Це перевірка сформованої порожнистої камери, не тиску або результату рецепта. |
| 18 | `immersiveengineering:multiblocks/mb_crusher` | Гравець успішно сформував відповідний мультиблок інженерним молотком. Trigger спрацьовує після createStructure; FE/t і виробництво не перевіряються. |
| 18 | `immersiveengineering:multiblocks/mb_dieselgen` | Гравець успішно сформував відповідний мультиблок інженерним молотком. Trigger спрацьовує після createStructure; FE/t і виробництво не перевіряються. |
| 18 | `immersiveengineering:multiblocks/mb_fermenter` | Гравець успішно сформував відповідний мультиблок інженерним молотком. Trigger спрацьовує після createStructure; FE/t і виробництво не перевіряються. |
| 18 | `immersiveengineering:multiblocks/mb_improvedblastfurnace` | Гравець успішно сформував відповідний мультиблок інженерним молотком. Trigger спрацьовує після createStructure; FE/t і виробництво не перевіряються. |
| 18 | `immersiveengineering:multiblocks/mb_refinery` | Гравець успішно сформував відповідний мультиблок інженерним молотком. Trigger спрацьовує після createStructure; FE/t і виробництво не перевіряються. |
| 18 | `immersiveengineering:multiblocks/mb_squeezer` | Гравець успішно сформував відповідний мультиблок інженерним молотком. Trigger спрацьовує після createStructure; FE/t і виробництво не перевіряються. |
| 20 | `ars_nouveau:familiar` | Успішне перетворення придатної істоти на Bound Script RitualBinding; тригер для гравців у межах8блоків. |
| 20 | `ars_nouveau:ritual_gravity` | Гравець отримав нативний ефект gravity; немає inventory fallback. |
| 21 | `botania:main/elf_portal_open` | Серверна активація правильної Alfheim Portal структури гравцем; inventory не є альтернативою. |
| 21 | `botania:main/enchanter_make` | Wand of Forest формує Mana Enchanter після canEnchanterExist; це створення структури, не виконане зачарування. |
| 24 | `occultism:occultism/summon_foliot_crystallizer` | Occultism викликав Ritual.finish для гравця, який запустив ритуал; збігається ID активного рецепта. Сам предмет або книга не дають цього критерію. |
| 24 | `pneumaticcraft:program_drone` | Сервер успішно записав програму з Programmer у підтримуваний предмет через SavedDroneProgram.writeToItem. Trigger не доводить завершення доставок дроном або коректність довільної програми. |
| 28 | `aia2:rituals/foliot_miner` | Occultism викликав Ritual.finish для гравця, який запустив ритуал; збігається ID активного рецепта. Сам предмет або книга не дають цього критерію. |
| 28 | `integrateddynamics:advanced_network_components/variable_materialization` | Виконати нативне досягнення integrateddynamics:advanced_network_components/variable_materialization. Нативний доказ — створення змінної блоком Materializer. Отримана статична картка не оновлюватиметься разом із початковим сигналом. |
| 28 | `integrateddynamics:advanced_network_components/variable_proxying` | Виконати нативне досягнення integrateddynamics:advanced_network_components/variable_proxying. Досягнення фіксує створення змінної саме через Proxy; це перевірка операції прив’язки, а не тривалий тест усієї схеми. |
| 28 | `integrateddynamics:advanced_operations/logical_list_building` | Виконати нативне досягнення integrateddynamics:advanced_operations/logical_list_building. Досягнення порівнює серіалізований integer-список [1,10,100] на панелі, а не кількість карток у гравця. |
| 28 | `integrateddynamics:aspects/redstone_capturing` | Виконати нативне досягнення integrateddynamics:aspects/redstone_capturing. Нативна умова перевіряє redstone_reader та read_integer_redstone_value; на цьому кроці не потрібно видавати читання за готову автоматику. |
| 28 | `integrateddynamics:aspects/redstone_transmission` | Виконати нативне досягнення integrateddynamics:aspects/redstone_transmission. Нативна умова вимагає reader-aspect read_integer_redstone_value зі значенням 15 на writer-aspect write_integer_redstone. Це перевіряє налаштований логічний зв’язок, а не просту наявність двох вузлів. |
| 28 | `integrateddynamics:logic_operations/arithmetic_addition` | Виконати нативне досягнення integrateddynamics:logic_operations/arithmetic_addition. Integrated Dynamics обчислює посилання ліниво: без доступних в мережі вихідних карток ви отримаєте помилку. Досягнення перевіряє operator arithmetic_addition на панелі. |
| 28 | `integrateddynamics:logic_operations/constant_definition` | Виконати нативне досягнення integrateddynamics:logic_operations/constant_definition. Перевірка вимагає створення integer-змінної саме програматором; порожня картка або предмет із Creative цього не доводять. |
| 28 | `integrateddynamics:logic_operations/logic_programming` | Виконати нативне досягнення integrateddynamics:logic_operations/logic_programming. Цей крок перевіряє відкриття GUI програматора; запис константи буде окремою дією наступного кроку. |
| 28 | `integrateddynamics:network_foundations/networks_logic` | Виконати нативне досягнення integrateddynamics:network_foundations/networks_logic. Досягнення перевіряє подію ініціалізації та мінімум десять кабелів у мережі; це більше за запас кабелів у кишені. |
| 28 | `integrateddynamics:saving_state/variable_delaying` | Виконати нативне досягнення integrateddynamics:saving_state/variable_delaying. Досягнення вимагає створення змінної блоком Delay; налаштування тривалості та поведінку під час перезапуску перевіряйте на своїй установці окремо. |
| 28 | `integratedterminals:storage_terminal/gui_storage_terminal` | Виконати нативне досягнення integratedterminals:storage_terminal/gui_storage_terminal. Нативне досягнення підтверджує відкриття ContainerTerminalStorageBase; наповнення вкладок залежить від доступних item/fluid/energy-інтерфейсів і перевіряється окремо. |
| 28 | `integratedterminals:storage_terminal_ender/ender_upgrade_storage_terminal` | Виконати нативне досягнення integratedterminals:storage_terminal_ender/ender_upgrade_storage_terminal. Досягнення має окремий terminal_storage_ender_upgraded trigger. Нативний виклик виконується при успішному перетворенні блочного термінала, тому однієї наявності ока недостатньо. |
| 28 | `integratedterminals:storage_terminal_filtering/filter_enchantable` | Виконати нативне досягнення integratedterminals:storage_terminal_filtering/filter_enchantable. Це інший механізм, ніж текстовий пошук: нативний тригер перевіряє operator-картку itemstack_enchantable у terminal_storage, а не введення рядка в пошукове поле. |
| 28 | `integratedtunnels:export_enchantable_items/export_enchantable_items` | Виконати нативне досягнення integratedtunnels:export_enchantable_items/export_enchantable_items. Перевірений upstream-предикат вимагає operator itemstack_enchantable на вибраному аспекті; перевірку успішної доставки у приймач не підміняємо цим досягненням. |
| 28 | `integratedtunnels:filter_storage_day/filter_storage_day` | Виконати нативне досягнення integratedtunnels:filter_storage_day/filter_storage_day. Удень ресурси цієї скрині мають бути доступні мережі, вночі — приховані. Нативне досягнення перевіряє підключення саме world-isday aspect; зміну доступності перевірте на установці самі. |
| 28 | `integratedtunnels:import_all_items/import_all_items` | Виконати нативне досягнення integratedtunnels:import_all_items/import_all_items. Порівняйте ролі: interface відкриває інвентар мережі, importer намагається забрати ресурс із цільового контейнера. Нативний доказ підтверджує саме вибір аспекту з true. |
| 28 | `integratedtunnels:import_items_list/import_items_list` | Виконати нативне досягнення integratedtunnels:import_items_list/import_items_list. Досягнення в цій версії перевіряє активацію write_list_item_import; фактичний вміст списку та перенесений обсяг нативна умова не вимірює. |
| 28 | `occultism:occultism/craft_miner_djinni_ores` | Occultism викликав Ritual.finish для гравця, який запустив ритуал; збігається ID активного рецепта. Сам предмет або книга не дають цього критерію. |
| 28 | `occultism:occultism/craft_storage_remote` | Occultism викликав Ritual.finish для гравця, який запустив ритуал; збігається ID активного рецепта. Сам предмет або книга не дають цього критерію. |
| 28 | `pneumaticcraft:flight` | Серверний JetBootsHandler почав активну роботу Jet Boots і витрату повітря; item acquisition не є умовою. Критерій не вимірює тривалість польоту чи максимальну висоту. |
| 30 | `ars_nouveau:prismatic` | Той самий projectile має prismRedirect>=3; rewardNearbyPlayers у межах10блоків. |
| 31 | `aia2:ceremonies/baykok_summon` | Сервер Totemic розпочав ефект конкретної церемонії після збору потрібної мелодії; зарахування отримують гравці в межах 8 блоків. Це не підтверджує особисте виконання всіх нот. |
| 31 | `naturesaura:positive_imbalance` | Нативна перевірка раз на 200 тіків зафіксувала навколишню ауру не нижче 1500000 у радіусі 25. Це стан середовища, не доказ роботи конкретного генератора. |
| 32 | `immersiveengineering:multiblocks/mb_arcfurnace` | Гравець успішно сформував відповідний мультиблок інженерним молотком. Trigger спрацьовує після createStructure; FE/t і виробництво не перевіряються. |
| 32 | `immersiveengineering:multiblocks/mb_excavator` | Гравець успішно сформував відповідний мультиблок інженерним молотком. Trigger спрацьовує після createStructure; FE/t і виробництво не перевіряються. |
| 39 | `aia2:rituals/marid_miner` | Occultism викликав Ritual.finish для гравця, який запустив ритуал; збігається ID активного рецепта. Сам предмет або книга не дають цього критерію. |
| 41 | `botania:challenge/gaia_guardian_hardmode` | Вбивство саме hardMode Guardian, не звичайного боса і не отримання Gaia Spirit. |

## Особливі негативні перевірки

- Totemic: передача Infused Flute або Buffalo-матеріалів не видає нові `aia2:ceremonies/*`; потрібен `performed_ceremony`. Перевірте всі п’ять церемоній.
- Occultism: шахтарі Foliot/Marid мають слухати чинні `aia2:rebalance/...` ritual IDs, а не видалені upstream-рецепти.
- Nature’s Aura: `positive_imbalance` підтверджує навколишню ауру в радіусі25 під час періодичної перевірки, а не конкретну генераційну машину.
- Ars Gravity: доводиться отримання ефекту, без висновку про власника жаровні або витрати Source.
- Integrated Tunnels: writer-задача підтверджує налаштування аспекту/змінної, без висновку про фактичний обсяг переданих ресурсів. Upstream `part_type` не вважати перевіреним полем codec.
- Botania: енчантер-задача підтверджує створення структури. Gaia II потребує hardMode; Gaia I не повинен задовольняти цей advancement.

## Creative Mana Tablet — окремий тест варіанта

- У JEI відсутні `avaritia:botania_mana_tablet`, `botania:cre/creative_mana_tablet_extreme`, `botania:cre/terra_plate/creative_mana_tablet`.
- `botania:mana_tablet` та `botania:mana_tablet_alt` залишилися. Звичайна планшетка доступна за старою епохою5.
- Новий `aia2:v5/variants/creative_mana_tablet` заблокований до **завершення**48 епох. Перевірте реальний Terra Plate з витратою6млн мани й Creative Essence.
- Результат має `minecraft:custom_data` з creative:1 та mana:500000 і epic rarity. Перевірте нескінченну поведінку після виготовлення.
- Імпортована/видана командою творча планшетка до completed48 не повинна живити предмети в inventory/accessories або передавати ману через ранній Mana Pool. Перевірте зміну команди, fake player, незареєстрований pool і відновлення доступу після completed48. Прямі сторонні ManaItem-виклики поза цими маршрутами ще не сертифіковані.
- FTB strict component matching ще не використано як доказ виготовлення планшетки; числові типи NBT та справжній matcher потребують перевірки у грі.

## Збереження й продуктивність

- Перевірте дві FTB-команди, зміну членства, offline-машини, fake players, повторне завантаження рецептів і повернення у світ.
- 96 ключів: `/give` не створює запис виробництва; обидві гілки, два виробничі докази та фінал лишаються обов’язковими.
- Збережіть показники TPS/MSPT до й після на однаковому світі; жодного виміру TPS у хмарному checkpoint не проведено.

Повні контрактні джерела: `content/audit/v5-native-advancement-contracts.json`.
