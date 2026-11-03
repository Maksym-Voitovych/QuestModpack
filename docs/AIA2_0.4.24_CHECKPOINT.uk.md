# 0.4.24-alpha — точні профілі CDG Mold

База — `2a0dcdd` /0.4.23-alpha. Це checkpoint незавершеної0.5.0.

Додано6побічних квестів: Lines/Bowl/Chain в12, Bar і нагріте Lines в15,
Duroplast в18. Вони перевіряють точний профіль Mold і зразки застосування.
Форма не витрачається; наявність форми/панелі/шоколаду не видається за
незалежний native proof виробничого процесу. Bar використовує Spout-over-Basin,
а не Mechanical Press. Compression розрізняє останню Mold у чаші; casting
шукає будь-яку відповідну форму. Ці деталі підтверджено pinned source1.3.15.

Компонент `createdieselgenerators:mold_type` має тип ResourceLocation.
Значення — повні ID `createdieselgenerators:lines|bowl|chain|bar`, не bare назва.
ItemTask має modern `item.components`, lowercase count і literal `fuzzy`.
FTB2101.1.36 fuzzy порівнює всі effective filter components, допускаючи
додаткові компоненти кандидата, наприклад custom_name. STRICT відкинув би
перейменований предмет; невідомий режим, зокрема ALL, переходить у NONE.

Тому авторська схема відхиляє невідомі/неповні профілі, типи, помилкові режими
та назви полів, null/небулеві прапорці й нецілі count. Компілятор зберігає
компоненти; duplicate signatures розрізняють профілі, а не лише кількості.
Compiled validator, пакувальник і read-only installer preflight перевіряють
кожен із6фільтрів. Пошкоджений/пропущений predicate або старий Count/tag
відхиляється до backup/write; чужі файли/світи не редагуються.

Реальна перевірка Minecraft виявила помилкове припущення тесту:
ItemStack.parse викликає resultOrPartial й може повернути предмет без
некоректного компонента. Raw CODEC повідомляє помилку, але partial filter
може стати ширшим. Тест виправлено під фактичну поведінку; source/schema та
installer guard закривають цей шлях до запуску гри. Це не замаскований crash.

Перевірено329actual minimal-MC assertions /2JVM /650ticks, включно з56новими
CODEC/component-map cases. Fixture використовує vanilla paper та окремий
синтетичний ResourceLocation-компонент guard namespace; лише nativeSmoke flag
разом із IDE mode та явним regular owned marker дозволяють його реєстрацію.
Це не декодування оригінального CDG component чи запуск FTB UI.88перевірок
незміненого FTB matcher та77debug-fixture-gate assertions/19cases мають
окремі modeled host APIs. Негативні контроли демонструють simulation/
matching/gate regressions без послаблення production guard.

Додатково пройшли472Python-тести з чистого Git-index export (0fail/0skip),
81Node-тест і5237Java policy assertions. Повторна генерація з
PYTHONHASHSEED=223 дала1184побайтово ідентичні non-JAR runtime файли.
Центральний валідатор перевірив14JS-файлів, SNBT, ID, DAG, залежності
обов’язкових цілей та компонентні predicates.

Кількості:3402квести/140глав/6груп,627рецептів,3138item rewards,390предметів/
моделей/PNG,48епох і96виробничих ключів. Нових рецептів/предметів/текстур0.
Усі3396старі non-coordinate payloads збережені, включно з ID/tasks/rewards/
deps/flags/icons.20координат переміщено в одній CDGглаві; layout1157перетинів
проти1156,0накладань/зворотних/довгих ребер/структурних попереджень.

Runtime keys, recipe bundle,16mechanic rules, station config і782assets
збережені побайтово. API4/76Mixin registrations і guard policy classes
незмінні. Новий JAR231classes:229старих byte-identical, змінено лише
NativeSmokeTests і додано NativeComponentFixtures; нормальна гра не
реєструє fixture. Жодного нового optional injection selector не додано.

CDGкарта30етапів зберігає24попередні повністю; інші моди та coverage_v12
не змінено.43source/recipe файли+manifest додають44research sources,
окремий native API fact містить SHA трьох Minecraft source entries.
Загалом61мод/27scoped core/34partial,769стадій/1142links/2642research
source files. Installed binary equivalence та повне проходження модів
не заявляються. Деталі й останні підсумки QA/доставки:

- implementation/cdg-molds-verification-v13.json;
- implementation/cdg-molds-preservation-v13.json;
- implementation/cdg-molds-jar-v13.json;
- implementation/cdg-molds-package-install-v13.json.

Пакет перевірено: CRC,5201SHA manifest entries,1185runtime files, exact
installer. Реальний extracted CLI пройшов upgrade0.4.23→0.4.24, dry-run
без записів, backup старого JAR, збереження opaque synthetic progress та
сторонніх файлів, повторне встановлення без змін. Це перевірка інсталятора,
а не завантаження справжнього світу.

Повний клієнт/original CDG/FTB UI/JEI/Survival/TPS NOT_RUN.
Установлення: зупинити обидві сторони, розпакувати пакет окремо, перевірити
installer --dry-run, потім установити й повністю перезапустити. Installer
резервує змінені оригінали/старий JAR, не змінює world/TeamData/SavedData.
Ручний план: [CDG_MOLDS_ACCEPTANCE](testing/CDG_MOLDS_ACCEPTANCE.uk.md).

Наступне: підтвердити нативну межу CDG compression_molding для панелей
через чинний Create Basin hook; лише потім додати явний17-й контракт
і окремий новий квест без заміни старих профільних tasks. Casting Bar
потребує іншої межі; він не оголошений перевіреним виробництвом.
