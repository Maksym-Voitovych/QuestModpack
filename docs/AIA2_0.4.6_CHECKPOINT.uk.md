# AIA2 0.4.6-alpha — проміжний checkpoint розробки0.5

Дата підготовки:26 жовтня2026. База: `8c699fa`. Повний реліз0.5 ще не завершено.

| Показник | До | Після |
|---|---:|---:|
| Епохи / виробничі ключі | 48 /96 | 48 /96 |
| Квести | 3212 | 3242 |
| Глави | 138 | 138 |
| Нативні custom-рецепти | 606 | 610 |
| Власні предмети / моделі / PNG | 390 /390 /390 | 390 /390 /390 |
| Завершені основні карти модів | 19 | 21 |
| Часткові карти модів | 41 | 39 |
| Контракти нативних дій | 86 | 97 |
| Командні виробничі правила /recipe IDs | 6 /8 | 6 /8 |

Нових предметів і текстур у цьому блоці немає. Усі3212 попередні квести
зберігають ID, tasks, rewards і залежності; змінювати можна лише координати.
Усі606 попередні custom recipe entries залишилися незмінними. Повний
порівняльний доказ: [preservation JSON](../implementation/industrial-core-preservation-v5.json).

## Серверний захист

MI2.5.10 вибирає рецепти через власні списки, оминаючи захищений
`RecipeManager.getRecipeFor`. Конкретний приклад: steam quarry епохи6 може
вибрати `modern_industrialization:quarry/bronze` з gate16 та виходом osmium,
якщо перевіряти лише доступ до блока. Нові hooks перевіряють рецепт до
списання входів і продовження оплаченого процесу.

Нативні MI smelting/cutting/compost конверсії мають окремий облік походження:
дозвіл не виводиться з самого class name або схожого Recipe ID. Застарілий
неоплачений кеш очищається; оплачений рецепт після live reload повторно
прив’язується лише за тотожним повним codec, serializer і type. Змінений або
видалений оплачений рецепт зупиняється без скидання його EU.

Replicator відкривається за completed48, перевіряє власника й вихід перед
UU-matter transaction. Копіювання всіх сімейств ключів і зареєстрованих
manufacture-receipt outputs заборонено завжди; копія не видає доказ крафту.

Oritech1.2.13 повертає кешований holder з ID типу рецепта, тому політика
перевіряє canonical recipe object identity. Захищено base selection/commit,
direct-list overrides Centrifuge/Refinery/Cooler/Tainted Refinery, три fluid
commit boundaries та nine-small-dust compaction. Перевірка базового tick
відбувається після поліморфного Atomic Forge capacity adjustment.

[Аудит джерел і меж](../content/audit/v5-industrial-native-guard.json).
API4, FTB/UUID/ProjectE typed bridges,96 ключів і SavedData збережено.

## Квести, рецепти та баланс

15 нових цілей MI охоплюють mixer, Steam Blast Furnace, Steel Upgrade,
LV sides, Overdrive, електричні й теплові мультиблоки, ядерну/термоядерну
гілки й післяігровий Replicator.11 native action contracts перевіряють
реальне формування або відповідну дію. Саме формування не доводить EU,
безперервну автоматизацію чи кількість вироблених предметів.

15 цілей Oritech навчають волокна, біопалива, полімерів, byproducts,
декількох виходів Refinery, laser-only Atomic Forge, обчислень, реакторного
охолодження, дронів і частинок. Setup, crafting, observation та продукти
чесно відокремлені від непідтверджених нативних production proofs.

Чотири формули використовують3 MI Assembler та1 Oritech Assembler,
магічні руни/матеріали й зберігають вихідні матеріальні витрати. Прибрано
шість дешевих native producer recipes, не решту альтернатив автоматично.
Для30 контролерів/компонентів узгоджено item/block gates,41 native producer
gate і5 custom gates. Історичний laser recipe entry лишив metadata epoch25,
але його чинний серверний gate тепер32; JSON і ID збережені.

Ранній wafer-шлях Oritech25 лишається через fluid centrifuge/silicon wash;
Atomic Forge формально освоюється32 разом із лазером. Overcharged Crystal
має також верстакову альтернативу: deep drill44 є рішенням балансу AIA2,
а не вигаданою particle-exclusive залежністю.

Додано30 тематичних нагород, попередні payloads незмінні. Перевірено2977
предметних entries. Layout перевірено у всіх138 главах; координати оновилися
в трьох. Накладань, зворотних/вертикальних/довгих локальних ліній0.
Перетини повного графа:1141→1142 при30 додаткових цілях; стара порівнянна
когорта2784 незмінна:1679→1129.

Roots Classic1.5.10: повний набір інгредієнтів мутації обов’язковий;
Radiant Daisy має щоденне вікно5000<time%24000<7000. Native блоки, виміри,
ефекти й витрата одного powder навіть за невдалого match збережені.

## Перевірки

- 143 Python tests,50 Node tests,5237 Java assertions і JDK21/NeoForge build: PASS.
- 53 MI actual-handler/proxy/real-policy умови з реальними DFU/Gson: PASS.
- 16 Oritech actual-handler/real-policy і48 Roots actual-handler/незмінених
  pinned native predicate умов у модельованому Minecraft host: PASS.
- Справжній мінімальний Minecraft0.4.6:61 assertions,2 JVM,650 ticks,
  перевірка SavedData після перезапуску: PASS. Optional модів у ньому немає.
- JavaScript syntax, SNBT, ID/DAG,96 ключів, registry/gates, recipes,
  resources, source hashes та міграційні перевірки: PASS.
- Ідемпотентна генерація1158 runtime-файлів у новому Python-процесі з
  PYTHONHASHSEED43: PASS. ZIP CRC/повний SHA-маніфест: PASS. Розпакований
  інсталятор: dry-run0writes і тестове оновлення0.4.5→0.4.6 PASS; старий
  JAR резервовано, synthetic world-progress і сторонній квест збережено.
  Фінальний metadata-repack повторює перевірку; результати в release/rebuild/package reports.

## Межі та наступний крок

Fullpack optional Mixin dispatch, JEI/UI, Survival і TPS не запускалися.
Оплачені generated MI conversions після зміни source залишаються paused;
нативні cache timers можуть затримати новий lookup приблизно на20 секунд
або довше. MI NBT не містить fingerprint старої семантики рецепта: її
незмінність після перезапуску не доведена. Oritech може штатно скинути
прогрес/RF на fresh denied lookup Atomic Forge; універсального відшкодування
енергії немає. Незавершений altar ritual Roots після restart не відновлено.

Наступна дія: основні карти EnderIO/Powah за точними встановленими версіями,
далі решта39 часткових карт, старі обов’язкові лінії48 епох і глобальний
баланс. Шість IF fluid-source прогалин залишаються явними; штучних рецептів
для них не створено. [План](AIA2_0.5.0_PLAN.md), [прогрес](AIA2_0.5.0_PROGRESS.md),
[manual acceptance](testing/INDUSTRIAL_NATIVE_ACCEPTANCE.uk.md).

Перед оновленням на тестовій копії дайте активним машинним рецептам
завершитися: native відновлення вилучених Recipe ID не гарантує збереження
оплачених входів. Це окремо від незмінного прогресу гравців і FTB.

Встановлення: зупинити гру, запустити matching installer з `--dry-run`,
потім без нього. Він резервує оригінали, мігрує лише власний companion JAR
та зберігає світи й невідомі квести. Windows-інстанс користувача з хмари не змінювався.
