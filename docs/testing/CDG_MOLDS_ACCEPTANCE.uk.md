# CDG Mold0.4.24 — приймання повного інстансу

Повний клієнт, original CDG/FTB dispatch, JEI та Survival: **NOT_RUN**.
Мінімальний Minecraft-сервер перевірив справжній ItemStack CODEC з окремим
синтетичним компонентом; це не запуск оригінального CDG чи його renderer.

1. Зупинити клієнт і сервер. Створити незалежну резервну копію інстансу/світу,
   без Junction на оригінал. Усі тестові команди й навмисно пошкоджені пакети
   застосовувати лише до одноразових копій. Installer `--dry-run` не повинен
   створювати backup або змінювати файл. Звичайне встановлення резервує
   змінені оригінали/старий JAR і не торкається world/TeamData/SavedData.
2. Перевірити `/aia2 status`, required Machine Guard, відсутність AIA2 errors
   та 16попередніх механічних правил.329common-MC checks і88FTB-host checks
   мають окремі межі; normal play не реєструє native-test component.
3. У FTB Quests знайти6нових побічних цілей: Lines/Bowl/Chain в12, Bar і
   нагріте Lines в15, Duroplast в18. Вони заблоковані майбутніми епохами,
   мають українські описи/звичайні іконки продуктів. Старий generic Mold task
   та його completed status залишаються незмінними. Нові цілі не є новою
   вимогою старих ключів; перевірити старий завершений прогрес після restart.
4. Для кожної з чотирьох профільних цілей підготувати матрицю предметів із
   Mechanical Saw: правильний профіль, три інші профілі, bare Mold без
   компонента, правильна форма після перейменування. Лише правильний
   профіль проходить; додаткова custom_name допускається. Форма не здається
   з витратою. `fuzzy` порівнює також effective default components предмета,
   а не довільну підмножину тільки одного поля.
5. Звірити task data: `item.id=createdieselgenerators:mold`, lowercase `count`,
   `item.components[createdieselgenerators:mold_type]` дорівнює повному ID
   `createdieselgenerators:lines|bowl|chain|bar`, top-level `match_components`
   дорівнює literal `fuzzy`. Не використовувати старі `Count`/`tag`, `ALL`,
   `none`, помилковий регістр або пробіли в назвах полів.
6. На окремій копії пакета прибрати компонент/режим, змінити профіль або
   поставити число замість ResourceLocation. Запустити normal installer та
   `--dry-run` на ще одній копії інстансу: обидва мають відмовити **до записів**.
   Minecraft може повертати частковий предмет без некоректного компонента,
   тому перевірка не повинна покладатися лише на відсутність крашу.
7. Перевірити реальні маршрути JEI: Lines/Bowl/Chain використовують прес над
   Basin; Bar має Spout-over-Basin casting і не потребує Mechanical Press.
   Для compression залишити одну потрібну форму: нативний match бере останню
   Mold у чаші. Casting шукає будь-яку відповідну форму. Звірити рецепти
   шоколаду, phenolic resin, Duroplast і повернення blaze powder→rod.
8. Огляд і зразки продукції не засвідчують запуск/оплату цих процесів: нові
   quests не видають native receipts. Виконати процеси вручну в Survival,
   перевірити доступність матеріалів/нагріву та фактичні outputs. Уточнити
   datapack/config overrides. Якщо додатковий ItemFilterAdapter розпізнає
   Mold як filter stack, окремо перевірити його вплив на FTB matching.
9. Перевірити вигляд task Mold після декодування: native назва/модель профілю,
   іконки продуктів, відсутність missing texture і накладань. Зберегти результати
   й журнали тільки з disposable-інстансу; не переносити негативні фікстури
   або тестовий компонент у користувацький світ.

Джерела: [CDG_MOLDS](../research/CDG_MOLDS.uk.md),
`content/research/evidence/cdg_molds_v13/contracts/component-contract.json`,
`content/research/evidence/cdg_mold_codec_native_v13/minecraft-codec-facts.json`.
