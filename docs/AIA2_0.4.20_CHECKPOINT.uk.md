# 0.4.20-alpha — збережувані докази нового будівництва станцій

База: `cd789e2` / 0.4.19-alpha. Це завершуваний підблок розробки0.5;
повний0.5 ще не реліз. Оригінальні optional JAR і Windows-інстанс не запускалися.

До існуючого packet scope додано read-only witness нативного per-player
реєстру. Точний Java overload `getOwnedSpaceStations(ServerPlayer,ServerLevel)`
уникає неоднозначності Rhino. Знімки прив’язані до UUID і світу, зберігають
незмінні координати й JSON-образ імені; shallow Component.copy недостатньо.
Допускається рівно один новий matching запис зі збереженням усіх старих.
Set.add no-op, старий запис, додаткові записи/видалення або змінене ім’я
не зараховуються. Межі:4096entries/16384UTF-16unitsнаім’я/1048576UTF-16unitsсумарно.

Реєстрація ще не видає proof. Після нормального повернення native Consumer
перевіряються та сама жива Survival-команда/гравець у цільовому світі й чанку,
поточний рецепт/теги/структура, retained blocks і новий реєстр. Exception,
reentry, невдала висадка чи пізня зміна контексту proof не створюють.
Легальне повернення предметів із меню при changeDimension після оплати не
потребує збереження старих inventory refs. Нативні partial effects не
відкочуються й не компенсуються. Інші станції та старі дані не adopt-яться.

Окремий SavedData `aia2_stations_v1` schema1 містить історичні командні докази.
Правила6 незалежні від старих15mechanic rules/схем. Read/load перевіряють
типи NBT, команди та64proofs/team/16384teams. Запис перевіряє ті самі межі;
регресія64→65 відтворена й виправлена. Vanilla може проковтнути помилку
читання, тому existing-unreadable-file sentinel не дозволяє заміну журналу
порожнім. Invalid loaded sentinel не dirtied і відмовляє в save.
Новий журнал записується лише після реальної успішної операції.

Додано6optional-квестів/12tasks/6нагород для окремих орбіт. Earth/Moon/Mars37,
Mercury/Venus/Glacio38. Завдання потребує server-only proof і відвідування
виміру; проєкція відкликається при зміні команди/помилці. Реальні витрати
кожного рецепта описані окремо, а не однаковою вигаданою партією.
Нагороди узгоджені з чинним профілем:4desh_nugget або4cheese.

3381квест/140глав/6груп,627рецептів,3117предметних нагород,
390предметів/моделей/PNG,96виробничих ключів. Усі3375старих non-coordinate
payloads/ID/нагород і627recipeentries збережені;50старих координат змінено
в одній Ad Astra technology главі. Layout1154перетини/0структурних попереджень,
без накладань/backwards/надто довгих local edges.31старий Ad Astra stage
незмінний, додано6. Нових рецептів/предметів/текстур0.

Перевірки й фактичні підсумки: `implementation/station-proof-verification-v9.json`,
`station-proof-preservation-v9.json`, `station-proof-jar-v9.json`,
`station-proof-package-install-v9.json`, `companion/native-smoke-report.json`.
Модельний packet не є optional binary dispatch; синтетичний station receipt
на мінімальному MC-сервері перевіряє лише справжні NBT/SavedData/restart.
Повний client/JEI/Survival/TPS — NOT_RUN; ручний план:
`docs/testing/STATION_PROOF_ACCEPTANCE.uk.md`.

Встановлення — закрити гру, installer dry-run, застосувати matching JAR+scripts,
повністю перезапустити. Backup оригіналів автоматичний; світи/FTB-прогрес
не переписуються. Наступний блок: явна сумісна migration старих required37/38,
потім34partial карти й решта required48ліній. Rootsunfinished ritual restart,
Draconic633/6IFfluid gaps та original binary/client acceptance ще не завершені.
