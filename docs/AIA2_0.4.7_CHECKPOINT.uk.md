# AIA2 0.4.7-alpha — EnderIO/Powah checkpoint

База:`1a3ee22`. Повний реліз0.5 залишається незавершеним.

| Показник | До | Після |
|---|---:|---:|
| Квести /глави | 3242 /138 | 3261 /139 |
| Нативні custom-рецепти | 610 | 615 |
| Виробничі правила /recipe IDs | 6 /8 | 8 /11 |
| Контракти нативних дій | 97 | 98 |
| Core-карти /partial моди | 21 /39 | 22 /38 |
| Предмети /моделі /PNG | 390 /390 /390 | 390 /390 /390 |

48 епох і96 виробничих ключів збережено. Нових предметів/текстур0.
Усі3242 старі quest/task/reward payloads та dependencies незмінні, крім
координат; усі610 попередні recipe entries збережено. [Доказ](../implementation/energy-core-preservation-v5.json).

## Реалізовано

18 optional-квестів EnderIO охоплюють сплави, конденсатори, SAG balls,
канали, душі, Slicing/Soul Binder, Vat, генерацію, обеліски, Painting та
справжню партію Energetic Alloy. Повний End Steel шлях віднесено до30,
де доступний End; старі quest IDs не змінено. Painting native criterion
доводить спробу дії, а не гарантовану доставку виходу.

Один новий Powah-квест використовує командний native proof Blazing Crystal.
Повна Powah core-карта ще partial;16 кандидатів збережено для наступного
проходу. Точний source6.2.10 підтверджено tag/build provenance:
`POWAH_VERSION` береться з release tag. Застарілий невикористаний
`mod_version=5.1.0-alpha` не є доказом іншої версії source.

П’ять міжмодових формул використовують3 Alloy Smelter та2 Energizing Orb.
Вихідні матеріальні витрати збережено; каталізатори походять із Botania та
Occultism. Перевірено48 storage-family предметів і103 native producers;
13 дешевих primary routes вилучено,86 lossless conversions і4 пізні MA
routes збережено. П’ять прихованих compressed energized-steel routes
також увійшли до аудиту. [Формули й джерела](../content/recipes/v5_enderio_powah_core.json).

Нові native guards перевіряють cached tasks і actual item outputs EnderIO,
Crafter до clearInput, Tank до зміни входів/виходу, generated smelting
conversion за canonical source та actual Orb receiver. Orb перевіряє
поточні входи, output0, containRecipe, capacity, рецепт і full output.
Кешований попередній рецепт не дозволяє порожній Orb дублювати результат.

Чистий callback lookup ізольований від Rod/hopper/startup context, щоб
одноразові кеші не залишалися порожніми після запуску/відкриття стадії.
Виконання цих процесів завжди має окремі обов’язкові перевірки. Глобальні
списки рецептів/JEI та захист інших машин не вимикаються.

Два нові proofs записуються після фактичної витрати входів/вставлення
виходу. Actual cached outputs перевіряються проти current recipe template,
включно з count/components. Старий SavedData schema1 і попередні proofs
збережено. Powah фінальний Rod FE debit після fillEnergy окремо не виміряний.

## Перевірки та межі

43 actual-helper/handler/real-policy та206 proxy/real-policy умов у
модельованому host пройдено; використовуються реальні DFU/Gson.
157 Python tests,50 Node tests,5237 Java assertions і JDK21 build: PASS.
Мінімальний Minecraft0.4.7:70 assertions,2 JVM,650 ticks і SavedData restart.
1162 runtime-файли byte-identical після окремої генерації PYTHONHASHSEED67.
Запакований CLI: dry-run без записів; тестове оновлення0.4.6→0.4.7
зберегло синтетичний прогрес і сторонній квест, зарезервувало старий JAR.
CRC, весь manifest і1162 runtime hashes перевірено.
[Звіт інсталятора](../implementation/energy-package-install-v5.json).
Подробиці — у
[release report](../implementation/release-report.json) та companion reports.
Мінімальний сервер не містить optional EnderIO/Powah і не доводить їх dispatch.

Layout усіх139 глав перевірено: накладань, зворотних, вертикальних і
довгих локальних ліній0. Повний граф1142→1143 перетини при19 додаткових
цілях; порівнянна стара2784-когорта лишається1679→1129. Додано19 тематичних
нагород; старих payload changes0,2996 предметних entries перевірено.

Відкритий source-confirmed пункт: Fire Crafting від світового вогню не має
власника; отримання infinity grain до19 не закрито, item/use лишається19.
Сліпа заборона зламала б обов’язкову прогресію. Потрібний окремий ownership
протокол для реального запалення/автоматизації, без nearby-player припущень.

EnderIO native NBT не доводить стару recipe semantics після restart;
змінений live task зупиняється зі збереженням прогресу. Native preparation
може вже оновити grinding-ball state до захисної перевірки actual outputs;
універсального refund немає. Official binary/API downloads повертали
Tunnel403, тому bytecode та actual optional Mixin dispatch не перевірені.
Fullpack/JEI/UI/Survival/TPS: NOT RUN. [Докладний аудит](../content/audit/v5-energy-native-guard.json).

Встановлення: завершити активні машинні цикли на тестовій копії, зупинити
гру, виконати matching installer з `--dry-run`, потім без нього. Installer
резервує оригінали, зберігає світи та невідомі квести й ставить matching JAR.
[Ручні сценарії](testing/ENERGY_NATIVE_ACCEPTANCE.uk.md).

Наступна конкретна дія: ownership Fire Crafting без deadlock, повний Powah
core за збереженими16 концептами, решта38 partial/невивчені моди й старі
обов’язкові лінії48 епох. Не оголошувати повний0.5 завершеним.
