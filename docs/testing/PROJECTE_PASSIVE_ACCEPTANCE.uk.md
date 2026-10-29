# ProjectE 1.1.0 — приймальна перевірка passive guards

Ці сценарії виконувати на тестовій копії повного AIA2 з matching JAR0.4.10.
Модельовані тести не підтверджують weaving з установленими ProjectE/Curios.
Не використовуйте основний світ для примусового пониження епохи команди.

1. Перевірити `/aia2 status`, API4 та відсутність помилок Mixin/KubeJS.
   `/reload` і `/aia2 guard retry` повинні відновлювати готовність без зміни прогресу.
2. Через оператора видати ранньому гравцю активні кільця, Time Watch,
   Repair Talisman, Gem armor і Arcana. Порівняти інвентар, offhand та активні
   Curios. Серверні здібності недоступні до відповідної епохи. Збережені ACTIVE,
   charge, modes, durability та предмети не очищуються.
3. Не перевдягаючись, дозволити й знову закрити потрібну стадію, змінити
   FTB-команду та виконати reload. Перевірити armor, step-height і CreativeFlight
   через серверні атрибути. Вони не накопичуються, сторонні modifiers не зникають.
   Повторити з Arcana одночасно в vanilla-слоті й Curios, потім зняти кожен окремо.
4. Перевірити gem helmet/boots toggles, charge/mode/projectile/extra-function,
   gem zap/explosion і окрему клавішу Archangel. Недоступні дії не виконуються.
   Окремо зафіксувати клієнтський рух GemFeet/GemLegs: його локальна prediction
   цим серверним блоком повністю не закривається.
5. Алхімічна сумка: активні suction ring і Repair Talisman усередині.
   Перевірити підбирання до епохи45, після відкриття й після downgrade; повторити
   з доступною сумкою, але недоступним внутрішнім предметом. Предмет на землі
   має залишатися доступним звичайному підбиранню, якщо suction заборонений.
6. Chest/pedestal: команди з різним прогресом, offline owner, imported/unowned
   блок, заміна блока на тій самій позиції, суміжні машини іншої команди.
   Callback використовує власника фактичного блока; native ACTIVE/cooldown
   і вміст не скидаються через відмову. TimeWatch не передає права іншій машині.
7. PhilosophersStone: звичайне використання, `onItemUseFirst`, dispenser/fake
   player і null-player callback. Ранній гравець не перетворює блоки. ProjectE
   pickaxe/morning-star не ламають навіть vanilla-блок до дозволу інструмента;
   перевірити AOE та нормальне ламання після відкриття.
8. У епосі45 фізичний Transmutation Table доступний за чинною whitelist.
   Ручна Tablet вимагає47. Відкрити її в47, перейти в45 без закриття меню:
   output/click/quickmove мають закритися. Повторити після reload/remap.
   Знання та EMC до/після тесту повинні збігатися, за винятком законних операцій.
   Curios-shortcut таблетки з пізнішої unreleased-гілки не є механікою PE1.1.0;
   не вимагати його для приймання. Curios passive/attribute захист збережено.
9. Перезапустити сервер. Перевірити прогрес обох команд, manufacturing receipts,
   FireWorksite SavedData, knowledge/EMC і16кольорів персональних сумок.
10. Записати TPS/MSPT на репрезентативній базі зі спорядженням/Curios та кількома
    активними сховищами. Реалізація не сканує світ, але повний TPS benchmark
    у хмарному мінімальному сервері не проводиться.

Межі: прямі виклики API сторонніми аддонами, уже створені projectiles/world
effects, локальний клієнтський рух і відновлення enchantment location effects
після unlock незмінного предмета потребують окремої інтеграції. Чужий modifier
з точно тим самим ID та значенням не має загального provenance API; видимі
дозволені equipment/Curios contributors захищаються, різні значення не стираються.

Джерело: офіційний ProjectE commit
[`f432b0c`](https://github.com/sinkillerj/ProjectE/tree/f432b0c66837759fb0731c9144dc53176b949c5d),
`projecte_version=1.1.0`, `minecraft_version=1.21.1`; локальні SHA-manifests у
`content/research/evidence/projecte_*_v5/`. Клієнтські/Survival результати
записувати лише після фактичного виконання цих сценаріїв.
