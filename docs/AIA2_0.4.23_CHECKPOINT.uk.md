# 0.4.23-alpha — курси Create-аддонів і виробництво електруму

База — `0ca0c5b`, версія0.4.22-alpha. Це checkpoint незавершеної0.5.0.

Додано **15 побічних квестів**:7 CCA та8 CDG в епохах11/12/15/18. Вони
навчають розрізняти форми металу, звичайні крафти компонентів, керування,
зразки палива й обслуговування.11 звичайних crafted-output IDs використовують
FTB `only_from_crafting`; механічні й рідинні процеси цим не підміняються.

Новий `cca_electrum_mixing` використовує наявний Create Basin hook. Потрібні
точний рецепт `createaddition:mixing/electrum`, власник/команда, epoch15 та
успішне несимуляційне завершення нативного процесу. Окремий item task вимагає
2 електрумові зливки. `/give`, інший alloy recipe, simulation або відмова
процесу не дають native receipt. Він зберігається в існуючій schema1 без
прийняття готових предметів за історичний доказ виробництва.

Опубліковані15 mechanic rules збережені за SHA й порядком; явне розширення
додає рівно16-те правило. Compiler, validators, reward audit і KubeJS включають
цей каталог явно. Набір правил у серверному скрипті перевіряється за16відомими
ID, а не довільним допустимим розміром. Шість process-map source SHA оновлюються
лише після перевірки незмінності15попередніх правил.

Кількості:3396 квестів /140 глав /6 груп;627 custom recipes;3132 item rewards;
390 предметів, моделей і PNG;48епох та96виробничих ключів. Нових рецептів,
предметів і текстур немає. Всі3381старі non-coordinate payloads, включно з
ID/tasks/types/counts/rewards/deps/optional/icons, незмінні.24старі координати
переміщено у двох главах аддонів. Layout:1156перетинів проти1154раніше,
0накладань/зворотних/довгих ребер/структурних попереджень.

Карти CCA/CDG мають23/24етапи й47посилань:32старі та15нових цілей.18раніше
пропущених старих цілей додано до карт. У14старих stage payloads змінено лише
одне поле: CCAphase05 recipe_evidence виправлено з cutting на справжній rolling.
Решта technology mod records збережені семантично. Карти лишаються scoped та
partial: повне проходження всіх charging/liquid/інших спеціалізацій не заявлено.

Джерела:128+130 оригінальних recipe JSON,47official source/version/license
файлів,13tags і переносні аудити. CCA source-version pin
`51e4a389ab044a113c02be383e66beaf69ec3110` оголошує1.6.0; старий1.7.2pin
збережено як історичний контекст. CDG pin
`79ce136730871b6f3f7b55d3cc748ff2bec2ad12` оголошує1.21.1-1.3.15.
Installed binary equivalence не перевірено. Загалом61мод/27scoped core/34partial,
763стадії/1136links/2598hash-verified source files.

Уроки враховують різні rod/wire результати уніфікації, capacitor як компонент,
протилежні redstone-полярності motor/relay, базовий час Bulk Fermenter,
controller-per-tank і Mold `mold_type`. Обраний Blaze Burner маршрут15 не
виключає альтернативний CDG Burner12; абсолютно найраніший heat/bootstrap
не заявляється. Inventory/observation не вимірюють FE/t або fluid completion.

JAR0.4.23 зібрано без змін Java:230classfiles і76Mixin config byte-identical
до0.4.22. Змінено лише versionmetadata. Збережено API4, ProjectE hotfix,
Machine Guard, ключі, NASA/station guards і paid pending migration.273commonMC
перевірки/2JVM/650ticks належать0.4.22 source-identical класам; у цьому
checkpoint вони не перезапускалися й не засвідчують новий Create dispatch.
Нові43actual-helper/handler перевірки виконані на modeled host; негативний
контроль без `!test` відтворює помилкове зарахування simulation.

Доступні перевірки пройдено: **431 Python /0fail /0skip,81Node,5237Java**
і43нові actual-class/handler assertions на modeled host. Rebuild із
PYTHONHASHSEED211 зберіг усі1184non-JAR runtimefiles побайтово; центральний
валідатор перевірив14JSфайлів, SNBT, ID, DAG, required closure, v12 каталог,
нагороди та SHA. Це не заміна повного Minecraft-клієнта.

Остаточні результати автоматичних тестів і доставки:
`implementation/create-addons-verification-v12.json`,
`create-addons-preservation-v12.json`, `create-addons-jar-v12.json` та
`create-addons-package-install-v12.json`. Повний клієнт/original optional
binary/JEI/Survival/TPS NOT_RUN. Не переносити ці межі на успішний запуск модпаку.

Установлення: зупинити обидві сторони, розпакувати пакет окремо, виконати
`install_runtime.py INSTANCE --dry-run`, потім без прапорця та повний restart.
Змінені оригінали/старий власний JAR резервуються; світи, TeamData й журнали
прогресу не редагуються. Ручне приймання:
[CREATE_ADDONS_ACCEPTANCE](testing/CREATE_ADDONS_ACCEPTANCE.uk.md).

Наступна дія — component-aware Mold tasks: перевірити exact Codec і FTB
matching, додати окремі профільні цілі без зміни старого generic Mold task.
Charging/liquid courses, fluid production proofs та решта48епох залишаються
незавершеними; завершені15цілей/source pins/native electrum не повторювати.
