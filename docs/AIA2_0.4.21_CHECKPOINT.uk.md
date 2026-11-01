# 0.4.21-alpha — сумісна обов’язкова прогресія космічних епох

База: `21dad21` /0.4.20-alpha. Повний0.5 ще не реліз.

Чотири вже реалізовані NASA-цілі включено до обов’язкових нових переходів:
T1+T2 для технологічного ключа37, T3+T4 для38. Разом із залежностями21попередня
ціль стала required. Шість station goals залишилися optional. Нових квестів,
рецептів, предметів чи текстур0:3381квест/140глав/627рецептів/3117item rewards,
390предметів/моделей/PNG,48епох і96виробничих ключів.

Типи, умови, кількості, task IDs і reward payloads усіх3381квестів незмінні.
3356non-coordinate quest payloads незмінні повністю. Змінено21optional flag,
додано4пояснення й4точні dependency migrations; старі залежності не видалено.
Координати всіх цілей незмінні. Layout1154перетини,0накладань/зворотних/довгих
ребер/структурних попереджень. Інші46epoch runtime contracts незмінні.

FTB2101.1.36 зберігає numeric progress і completed timestamp за ID без типу.
Тому item→advancement на тому самому ID може успадкувати завершення або
застрягнути на100%. Ця міграція не змінює старі tasks і не редагує TeamData.
Pinned джерела й API-факти наведено в
`docs/research/FTB_PROGRESS_MIGRATION.uk.md`.

`RequiredSpaceActions` читає існуючі командні NASA receipts. `KeyProductionBridge`
перевіряє їх перед нативним процесом і перед записом key receipt; stale ready
flag, старе завершення FTB або старий key receipt не підміняють нову вимогу.
Виправлено також зміну власника Crafter A→B між begin/finish: регресія
FAIL без перевірки власника й PASS після. Весь час зберігається API4.

У скрипті готовність обох гілок публікується лише після читання всіх proof
джерел; помилка відкликає обидва кешовані дозволи. Нові37/38pending мають
pendingActionContract1 й перевіряють NASA перед завершенням після restart.
Старі markerless pending вже були оплачені: вони зберігають старий контракт
з обома native key receipts, milestones/trial/final і не чекають branch-key
quest, який могли заблокувати нові залежності. Completed/recovery незмінні.
Жодних безкоштовних предметів, stage або proof міграція не створює.

Виробничий journal aia2_mechanics_v1 schema1/15rules збережено. Суворий loader,
blocked sentinel і lazy installation не дозволяють vanilla IO/load failure
перетворитися на порожній журнал із наступним перезаписом історії. Межі
read/write64proofs/16384teams узгоджені; unknown valid historical IDs збережені.

Перевірки: `implementation/space-required-verification-v10.json`,
`space-required-preservation-v10.json`, `space-required-jar-v10.json`,
`space-required-package-install-v10.json`, `companion/native-smoke-report.json`.
Actual helper hosts, справжній Rhino й actual minimal Minecraft мають окремі
межі. NASA receipts у native persistence fixture синтетичні й належать лише
згенерованій тестовій команді; це не optional Ad Astra dispatch.

Оригінальні optional binaries/fullclient/JEI/Survival/TPS — NOT_RUN.
Ручне приймання: `docs/testing/SPACE_REQUIRED_ACCEPTANCE.uk.md`.
Встановлення: зупинити гру, installer dry-run, matching JAR+scripts, повний
restart обох сторін. Backup змінюваних оригіналів/старого JAR автоматичний;
світи й прогрес не переписуються.

Наступний блок — виправити оманливі назви/описи старих віх37/38 відповідно до
фактичних предметних умов; далі34partial карти та решта required48ліній.
Не оголошувати всі48епох повністю переробленими через завершення цього блоку.
