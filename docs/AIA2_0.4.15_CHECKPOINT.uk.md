# AIA2 0.4.15-alpha — історія залежностей Clibano

Проміжний блок до0.5, база `d5c225c` (0.4.14). Повний реліз0.5 залишається
IN_PROGRESS; завершені епохи, квести й дані гравців не мігруються повторно.

## Реалізація

Clibano recipe CODEC містить посилання на tags/enhancer/residue, а native
residue NBT — лише ID→кількість. Раніше після restart той самий ID міг
означати іншу ціну або результат об'єднання. Тепер `ClibanoDependencies`
читає current tag membership і повні required/installed enhancer та residue
визначення, а `ClibanoDependencyState` незалежно зберігає historical lane
snapshots і definition+amount кожного позитивного residue balance.

Інгредієнти перевіряються за native shapeless правилом для1/2слотів,
включно з обома перестановками перекривних alternatives. Stale Ingredient
cache не є доказом; custom ingredients/effects/conditions потребують
окремого адаптера. Dependency snapshot перевіряється до витрат і повторно
перед finish, навіть якщо duration1 завершується до tick-finally.

Новий residue witness з'являється лише після прийнятого native increaseType
у scoped перевіреному finish; один finish може спробувати зарахувати одну
одиницю. Прямі або повторні credits не змішують непідтверджений stock із
сертифікованим. Після native combine перевіряється фактичний баланс, і
historical quantities оновлюються разом із ним. Нульові записи не є stock.

## Збереження й відновлення

Існуючий `aia2_clibano_paid_v1` schema1 та definition/input hashes не змінено.
Новий журнал — окремий `aia2_clibano_dependencies_v1`. Невідомі/пошкоджені
формати й неповний native residue decode зберігаються без adoption.
Якщо native save не записав positive residues (level-null або codec omission),
зберігаються фактичні ID/count без підтвердження їхньої історії з current registry.
Старий залежний paid lane і positive residues без історичного witness
залишаються paused. Dependency-free старий lane може продовжитися без
приписування нового snapshot. Усі15 native recipes посилаються на residue,
13 використовують item-tags: за можливості завершіть стару плавку й
використайте залишки перед установленням.

`cancel` резервує й очищує лише cooking progress/lanes, зберігаючи residue
history. Новий явний `quarantine-residues` у радіусі8блоків для оператора
власної команди резервує raw stock/journal у persistent NBT (максимум8),
прибирає його з активного балансу й не видає предметів/refund/proof. Slots,
fuel/souls і cooking counters збережені. Corrupt lane witnesses не
відновлюються з поточного datapack. Інсталятор не виконує цих команд.

## Контент і перевірки

3351квест/140глав/6груп,623рецепти,3087item-нагород,390предметів/моделей/PNG,
96виробничих ключів. Нових квестів/рецептів/нагород/предметів/текстур цього
блоку0. Усі1171non-JARruntimeфайли, ID/tasks/rewards/dependencies/coordinates
байтово незмінні. Layout1154перетини,0structuralwarnings.
[Порівняння](../implementation/clibano-dependencies-preservation-v6.json).

233Python/57Node/5237Java і JDK21build PASS. Clibano native harness368умов
(118нових), незалежний dependency-state harness167:285нові modeled assertions.
Чотири native logic sources byte-identical; це modeled MC/container host,
не optional weaving. Actual minimal Minecraft151assertions/2JVM/650ticks,
14нових actual-NBT/compressed roundtrip checks. Forge regression369умов
також збережена після спільних current-Ingredient helper змін.

Додано35SHA-source файлів:8native classes,15recipes,11residue definitions
і actual NeoForge RecipeMatcher. Exact Forbidden2.6.1 pin
`34f83feb76204fd773e1d2e1d69ecc5b2f2bb933`.
[Source-аудит](../content/audit/v6-clibano-dependencies-source.json),
[manifest](../content/research/evidence/clibano_dependencies_v6/manifest.json).
26scoped core-карт/35partial/700етапів/1073questlinks не змінювалися.

## Межі й наступна дія

Повний Component CODEC виконується до bounded JSON sort/SHA; TPS/CPU
профілювання потрібне. Full enhancer/residue codecs включають descriptions/
name, отже візуальна зміна може призупинити роботу. Нативний RNG/fire/enhancer
семантику збережено; universal rollback, довільні addon callbacks, generic
copied components та frame IO forwarding не заявляються. Source forwarding
закоментовано в upstream. Одна проблемна lane/history може зупинити весь цикл.

Повний Forbidden/Clibano dispatch, JEI/UI, Survival і справжній world upgrade
**NOT RUN**. [Ручний план](testing/CLIBANO_DEPENDENCIES_ACCEPTANCE.uk.md).
Наступний конкретний контентний блок — перевірити exact Ad Astra1.16.26,
поглибити його partial map і квестовий шлях за реальними механіками космосу.
Далі35partial-карт і старі required-лінії48епох. Roots unfinished restart,
DraconicCI633 provenance та6IFfluidgaps залишаються відкритими.

## Доставка

Фінальна генерація всіх1172runtimeфайлів byte-identical з PYTHONHASHSEED109.
ZIP4306entries пройшов CRC/весьSHAmanifest і перевірку actual extracted CLI.
Dry-run0записів файлів/директорій; upgrade0.4.14→0.4.15 резервує старий JAR,
зберігає opaque world/FTB/fire/knowledge+EMC/paidchunk markers і сторонні
quest/mod/script; повторне встановлення ідемпотентне. Це synthetic installer
test, не перевірка справжнього світу. Windows-інстанс не змінювався.
[Пакетний звіт](../implementation/clibano-dependencies-package-install-v6.json).

JAR194classes/68mixins;174старихclasses byte-identical. SHA256:
`830237f6289791abb733fb5d0dfc0902156b548e46290a1e745a500b59d06082`.
[Class audit](../implementation/clibano-dependencies-jar-v6.json). Точні
commit/push identity фіксуються в Git/origin і окремому delivery report біля
ZIP, щоб не включати self-referential hash до власного пакета.
