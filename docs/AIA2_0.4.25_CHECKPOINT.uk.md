# 0.4.25-alpha — нативне виробництво панелей CDG

База — `9067fdf` /0.4.24-alpha. Це checkpoint незавершеної0.5.0.

Один новий optional квест12 продовжує V13 Lines. Він перевіряє неможливе
за звичайною inventory-подією advancement із durable native receipt поточної
команди та окремо чотири панелі. Попередні профільні завдання не замінено.

Exact CDG1.3.15 CompressionMoldingRecipe успадковує CompactingRecipe/BasinRecipe.
Чинний Create6.0.10 apply RETURN викликає доказ лише за !test і true після
витрати матеріалів та acceptOutputs. CDG HEAD повторно перевіряє останню
форму в слотах на кожному simulated/actual виклику. Нового Mixin немає.
Рецепт: одна c:plates/iron, Lines, гарантовані4панелі, нагрівання не потрібне.

Аудит виявив same-ID override ризик: ID/serializer/output Item ID не
гарантують незмінності форми, сировини чи кількості. Крім того, CDG може
порівняти unknown recipe mold==null із generic Mold==null і пропустити його.
Новий CdgPanelAccess перевіряє точний optional class та non-null Lines,
декодує еталон через справжній serializer codec й порівнює обидва повторно
закодовані значення. Defaults нормалізуються; partial errors відхиляються.
Обчислення codec виконується при перебудові recipe-generation index; під
час lookup лишається дешева перевірка публічного moldType від cached mutation.
Змінений рецепт може працювати за звичайними правилами доступу, але proof
за ним не видається; діагностика записується один раз на generation.

Явний17-й контракт зберігає всі16опубліковані rules/order та schema1.
NASA повторно записує власні4значення на місцях, CCA повторна генерація
підтримує лише цей узгоджений successor; невідомі18-ті правила відхиляються.
Компілятор/валідатори перевіряють native advancement, зразок, stage12 і
попередню Lines-ціль. Пакувальник та read-only інсталятор звіряють повну
пару даних/JAR до записів. Native SNBT і поточний JSON підтримуються.

3403квести/140глав/6груп,627рецептів,3139item rewards,390предметів/моделей/
PNG,48епох/96ключів. Додано1квест/1нагороду/1proof,0рецептів/предметів/
текстур. Усі3402старі non-coordinate payloads і782assets збережені.
У1главі переміщено14координат;1157перетинів як у базі,0накладань/зворотних/
вертикальних/довгих ребер/попереджень. CDG31етап зберігає30попередніх;
227старих source references та інші моди збережені;7нових portable sources.
Загалом61мод/63records/27scoped core/34partial,770стадій/1143links/
2649research SHA files. Повної binary provenance не заявлено.

JAR234classes:229старих byte-identical, змінено ProductionMilestoneBridge
і його ReceiptData class metadata;3нові класи CdgPanelAccess.76Mixins та
всі інші guard policy/key journal classes незмінні. Зібрано JDK21/NeoForge.

107modeled assertions виконують actual helper/bridge/handlers/GuardPolicy
і незмінені CDG MoldType/HEAD. CODEC, Create body, Minecraft, NBT і збереження
цього тесту змодельовані; три негативні контроли відтворюють регресії.
329actual minimal-MC checks /2JVM/650ticks повторено на0.4.25; це common
regression, а не новий запуск CDG.83Node/5237Java policy assertions PASS.
Чистий Git-index export:512Python/0fail/0skip PASS(342.738s).
Перший511test прогін виявив10відмов через застарілий NASA exact-set і
неповні fixture. Виправлено лише два тестові файли; production validation
не послаблено, додано відмову при видаленні17thcontract.35targetedPASS.
Rebuild227:1185non-JAR runtime файлів побайтово ідентичні, Root збігається;
центральний14JS/SNBT/IDs/DAG/requiredclosure/component/panel validator PASS.
Остаточні результати доставки та межі тестів — у звіті:

- implementation/cdg-panel-verification-v14.json;
- implementation/cdg-panel-preservation-v14.json;
- implementation/cdg-panel-jar-v14.json;
- implementation/cdg-panel-package-install-v14.json.

Пакет пройшов CRC/5227manifestSHA/1186runtimeSHA/installerSHA. Реальний
extracted CLI0.4.24→0.4.25:dry-run0files/dirs,backup старого JAR,opaque
world/FTB/key/fire/station/mechanics/paidpending/EMC/chunk markers і сторонній
контент збережено; повторне встановлення без змін. Це synthetic fixture,
а не завантаження справжнього світу. Final metadata перепаковуються перед
check-only і звірянням усіх архівних байтів із Root.

Повний original CDG/Create/FTBUI/client/JEI/Survival/TPS NOT_RUN.
Зупиніть обидві сторони, розпакуйте пакет окремо, виконайте installer
--dry-run, потім установіть і повністю перезапустіть. Інсталятор резервує
змінені оригінали та старий JAR; world/TeamData/SavedData не редагуються.
Ручні кроки: [CDG_PANEL_ACCEPTANCE](testing/CDG_PANEL_ACCEPTANCE.uk.md).
Наступне: точний Casting Bar/Spout boundary/ABI audit; compression proof
не підміняє лиття. Непідтверджений новий optional selector не додавати.
