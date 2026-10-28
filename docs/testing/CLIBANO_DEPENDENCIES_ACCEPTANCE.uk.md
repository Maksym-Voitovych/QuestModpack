# Clibano dependencies — приймальна перевірка 0.4.15

Ці сценарії повного модпаку **NOT RUN**. Модельовані hosts виконують
справжні helpers/handlers і чотири exact native logic classes; мінімальний
Minecraft окремо перевіряє справжній NBT. Forbidden Arcanus у мінімальному
сервері відсутній, тому ці рівні не підтверджують optional weaving/JEI/TPS.

На тестовій копії світу встановити matching 0.4.15 JAR/скрипти на клієнт
і сервер, повністю перезапустити. За можливості завершити стару плавку та
використати залишки ДО оновлення: старі positive balances/оплачений прогрес
без історичних залежностей не підтверджуються поточним datapack.

1. Повторити [базові owner/menu/production сценарії](CLIBANO_ACCEPTANCE.uk.md).
   Перевірити три нові injection points у вже зареєстрованому ResidueMixin:
   conversion RETURN, increaseType HEAD/RETURN; помилок injection бути не має.
2. Почати справжню плавку з item-tag. Залишивши recipe JSON/ID та фізичні
   входи незмінними, розширити або скоротити тег і виконати reload. Очікується
   pause без повторного списання, output/proof або втрати cooking counter.
   Відновлення exact membership дозволяє продовжити. Перестановка однакових
   членів сама по собі нічого не змінює. Memoized Ingredient#getItems не має
   дозволяти запуск із предметом, видаленим із current registry tag.
3. Два alloy inputs перевірити в обох порядках, зокрема коли перший ingredient
   приймає обидва предмети. Це native shapeless RecipeMatcher, не greedy
   правило Forge-п'єдесталів. Unknown custom ingredients залишаються denied.
4. Змінити same-ID required/installed enhancer definition або residue type
   combine price/result/name під час плавки. Оновити фізичний enhancer cache.
   Ідентичний holder ID не дозволяє завершити роботу за новими правилами.
   Перевірити також duration1 і зміну залежностей безпосередньо перед commit.
5. На SOUL_FIRE/ENCHANTED_FIRE виробити residue через native recipe finish.
   Перевірити ID/definition/count у `aia2_clibano_dependencies_v1.residues`.
   Журнал має оновитися після прийнятого increaseType і до штатного payload.
   Поза verified finish прямий increaseType не створює certified stock;
   повторний callback того самого finish не може зарахувати другу одиницю.
6. Накопичити потрібну кількість і дозволити native combine. Фізичний та
   історичний баланси зменшуються разом; component-mismatch/outputfull/future
   output не витрачають залишків. Zero map entries не означають позитивний
   stock; native save може їх не записувати. Перевірити capacity64, дві лінії,
   дві групи residues та output, який заповнюється перед cooking.
7. Повністю перезапустити світ з positive residue balance. Тотожний current
   definition дозволяє продовження; same ID зі зміненим результатом або ціною
   зберігає баланс paused. Видалений holder/частковий codec decode не мають
   стерти raw native `residues`. Save при level-null або codec omission
   повинен зберегти positive ID/count разом із journal. Unknown schema/wrong type journal зберігається
   verbatim і не дозволяє роботу чи автоматичну міграцію доказу.
8. Старий lane receipt без нового snapshot: простий рецепт без tags/enhancers/
   residue reference може продовжитися без adoption; залежний — paused.
   Усі15 native defaults мають residue reference,13мають tags. Стара schema1
   `aia2_clibano_paid_v1` і definition/input hashes лишаються незмінними.
   Старий positive residue balance без witness не конвертується й не змішується
   з новим stock, навіть коли його current ID/кількість прочиталися успішно.
9. `/aia2clibano status x y z` показує стан залежностей. Явний `cancel` своєї
   команди поблизу, тільки оператор: backup і скидання cooking counters/lanes,
   зі збереженням усіх slots/fuel/souls/residues та їхньої історії. Corrupt
   dependency journal не очищується цією командою.
10. Окремий явний `/aia2clibano quarantine-residues x y z`: оператор своєї
    команди в радіусі8блоків переміщує raw residues/history у persistent NBT
    `aia2_clibano_residue_backups_v1` (максимум8копій) і очищує тільки активний
    residue balance. Жодних output/refund/proof; slots/fuel/cooking counters
    лишаються. Corrupt history зберігається в backup перед очищенням; його
    непідтверджені lane witnesses не переносяться назад. Дев'ята копія,
    wrong-type backup, чужа команда, віддалений/неоператорський виклик мають
    відмовити ДО записів. Інсталятор ніколи не запускає quarantine/cancel.
11. Перевірити FTB/два ключі/JEI/UI/Survival та TPS із паралельними Clibano.
    Поточні бюджети:1024recipes/2lanes/64residue types і total64; Ingredient/
    enhancer/JSON budgets спільні з Forge. Component CODEC виконується до JSON
    budget; глобальну CPU-межу та відсутність TPS-впливу не доведено.

Звичайна native FIRE не генерує residues; chance/RNG не змінено. Source2.6.1
застосовує enhancer soul-duration effects без перевірки TimeCondition:
оновлення не вигадує додаткової умови. Повні enhancer/residue codecs містять
опис/назву, тому навіть візуальна зміна може консервативно викликати pause.
Frame capability forwarding upstream закоментовано; зовнішній pipe IO,
generic copied components, довільні addon callbacks та universal rollback
не оголошуються реалізованими цим блоком.
