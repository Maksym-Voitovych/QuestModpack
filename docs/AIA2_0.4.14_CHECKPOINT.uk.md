# AIA2 0.4.14-alpha — залежності оплачених Forge-ритуалів

Завершений проміжний блок до 0.5; база `a1b6189` (0.4.13). Повний реліз
0.5 залишається IN_PROGRESS. Наявні 48 епох, 96 виробничих ключів і прогрес
гравців не мігруються повторно.

## Реалізація

Повний DIRECT_CODEC ритуалу містив посилання на item-tags та enhancers,
але не їхній вміст. Тому незмінний ritual ID/JSON сам по собі не доводив,
що оплачена операція продовжує працювати за тими самими правилами.

Новий `ForbiddenDependencies` читає current registry bindings без кешу
`Ingredient.getItems()` і без перевірки лише identity `HolderSet.Named`.
Відбиток включає актуальні членства тегів предметів, named enhancer sets
та повні визначення required/installed enhancers. Перед native callbacks
додатково відтворюється перевірка vanilla ingredients у тому самому greedy
порядку й з тими самими кількостями pedestal inputs. Custom ingredients,
невідомі Value/effect/condition реалізації потребують окремого адаптера.

Snapshot записується лише після точного native reduce RETURN. Додаткова
перевірка між стартом та оплатою не дозволяє засвідчити змішані визначення;
за розбіжності paid active state лишається pending з діагностикою. Tick і
commit повторно звіряють історичний snapshot із поточними залежностями.
Повернення exact definitions дозволяє продовжити підтверджену операцію
без нової оплати. Змінені/видалені/пошкоджені дані зберігаються paused.

## Сумісність даних

Старі schema1 receipt, definition/input hashes та всі ID збережено.
Новий versioned extension розміщено всередині retained native
`active_ritual.aia2_gameplay_dependencies_v1`. Native codec omission не
стирає його. Старий receipt без extension може продовжитися лише для
ритуалу без відповідних transitive залежностей; поточний datapack ніколи
не приймається за доказ історичних залежностей.

Інсталятор вимагає новий helper у matching JAR, резервує старий JAR та
оригінали, не змінює світ і не скасовує активні процеси. За можливості
завершіть старі залежні ритуали до встановлення. `/aia2forge status x y z`
дає діагностику; явне операторське `cancel` має максимум 8 backups,
зберігає фізичні предмети й не повертає есенцій/не видає результат.

## Кількості й перевірки

3351 квест / 140 глав / 6 груп, 623 рецепти, 3087 item-нагород,
390 предметів/моделей/PNG, 96 виробничих ключів. У цьому блоці додано
0 квестів, рецептів, нагород, предметів і текстур; усі попередні payloads,
залежності та координати byte-identical. Layout: 1154 перетини,
0 накладань/зворотних/вертикальних/надто довгих локальних ліній.
[Порівняння](../implementation/forbidden-transitive-preservation-v6.json).

230 Python / 57 Node / 5237 Java і JDK21 build PASS. Forge harness тепер
має 369 modeled assertions (157 нових), окремий state harness — 85.
137 actual minimal-Minecraft assertions у 2 JVM / 650 ticks, зокрема
18 нових actual-NBT/compressed roundtrip перевірок. Forbidden та Clibano
у цьому мінімальному сервері відсутні; це не перевірка optional weaving.

Додано 18 SHA-перевірених джерел: exact Forbidden2.6.1 pin
`34f83feb76204fd773e1d2e1d69ecc5b2f2bb933` і patched Minecraft1.21.1/NeoForge.
[Source-аудит](../content/audit/v6-forbidden-transitive-source-review.json),
[SHA manifest](../content/research/evidence/forbidden_transitive_v6/manifest.json).
Наявні 26 scoped core-карт / 35 partial, 700 етапів / 1073 quest links
залишилися незмінними; нових повних карт тут немає.

## Межі й наступна дія

Є budgets для inputs/values/tags/members/enhancers/effects/conditions та
encoded JSON перед canonical sort/SHA; один enhancer серіалізується один
раз за capture. Повний Component CODEC виконується до JSON budget, тому
глобальна межа CPU серіалізації й відсутність TPS-впливу не заявляються.
Профілювання реальних паралельних кузень залишається обов'язковим.
Full enhancer CODEC включає description/display item, отже навіть їхня
візуальна зміна може консервативно викликати pause. Визначення текстур
magic circle виключені з нового gameplay snapshot.

Наступний блок — transitive recipe/enhancer і historical residue дані
Clibano зі збереженням schema1 lane receipts. Далі — 35 partial-карт,
невивчені моди й старі обов'язкові лінії 48 епох. Roots unfinished restart,
Draconic CI633 provenance і 6 IF fluid gaps залишаються відкритими.

Повний Forbidden dispatch, JEI/UI, Survival, реальний world upgrade і TPS
**NOT RUN**. [Ручний план](testing/FORBIDDEN_DEPENDENCIES_ACCEPTANCE.uk.md).
[Пакетний тест](../implementation/forbidden-transitive-package-install-v6.json)
перевіряє actual extracted installer на синтетичних opaque markers;
його не слід прирівнювати до міграції справжнього Minecraft-світу.

## Доставка

ZIP перевірено за CRC та всім SHA-маніфестом: 4258 entries, 1172 runtime
файли й actual installer. Його CLI dry-run не змінив файлів або директорій.
Тестове оновлення 0.4.13→0.4.14 резервує старий JAR і зберігає opaque
world/FTB/fire/knowledge+EMC/paidchunk markers та сторонні quest/mod/script;
повторне встановлення ідемпотентне. Це синтетичний installer test, не
перевірка справжнього світу. Windows-інстанс користувача не змінювався.

Новий JAR містить 186 classes / 68 mixins; 176 старих classes byte-identical.
SHA256: `77dd673976ae228c82cfc8f18c3af95da0c8303c504c4f947162e47609395d09`.
[Class audit](../implementation/forbidden-transitive-jar-v6.json). Фінальний
commit і push перевіряються через Git/origin та окремий delivery report
біля архіву, щоб не включати self-referential hash до власного пакета.
