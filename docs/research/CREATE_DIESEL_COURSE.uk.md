# Create Diesel Generators — карта паливної та матеріальної ділянки

Досліджувана версія: **1.21.1-1.3.15**, Minecraft1.21.1 NeoForge.
Source pin: `79ce136730871b6f3f7b55d3cc748ff2bec2ad12`, офіційний
[Create-Diesel-Generators](https://github.com/george8188625/Create-Diesel-Generators/tree/79ce136730871b6f3f7b55d3cc748ff2bec2ad12).

Статус: версійний source/export аудит виконано у наведених межах; повний мод,
Survival-bootstrap усіх альтернатив, installed-binary equivalence, JEI,
клієнт і TPS **не перевірено**. Fluid production proof не реалізовано.
Ця карта не замінює старі quest IDs, tasks, dependencies або нагороди.

## Джерела й виправлення provenance

[Manifest](../../content/research/evidence/create_addons_core_v12/cdg/manifest.json)
містить30точних pinned source/resource файлів,6реєстрових tags та переносні
знімки аудиту. [Recipe index](../../content/research/evidence/create_addons_core_v12/cdg/recipe-index.json)
охоплює **всі130рецептів** namespace; їхні оригінальні export-байти збережено
поряд у `recipes/createdieselgenerators/`. Це рецепти наданого запуску,
а не новий dump недоступного Windows-інстансу.

Попередній `technology_v5.json` ставив `version_match:false` для цього самого
pin. Проте точний `gradle.properties` задає `minecraft_version=1.21.1`,
`mod_version=1.21.1-1.3.15`, `create_version=6.0.10-280` і NeoForge21.1.228.
Отже source-version відповідає експорту. Release tag чи еквівалентність
скомпільованому встановленому JAR не доведені: один version string не є ABI-тестом.
Нові source-файли отримано через Git на точному commit, без нормалізації байтів.
Спроба GitHub API завершилася tunnel403 і не використовувалася як джерело.

## Реальна послідовність освоєння

CDG виробляє обертальну енергію Create. Наявність дизельного двигуна не є
доказом FE-мережі; електричне перетворення належить окремому CCA-обладнанню.

| Фаза | Епоха наявного курсу | Чого вчиться гравець | Фактична перевірка і межі |
|---|---|---|---|
| Вхід і матеріали | 12 | Андезитовий сплав, листи/стрижні, Hammer і Wire Cutters дають ручні матеріальні альтернативи; тара потрібна до постійної паливної мережі | Craft item tasks підтверджують верстак; inventory підтверджує запас, а не машинний процес |
| Розвідка і видобування | 12 | Oil Scanner і Canister передують насосній інфраструктурі; Head/Crank/Bearing/Hole мають різні ролі | Старі observation tasks бачать блоки; форму/роботу Pumpjack не підтверджують |
| Перший споживач | 12 | Diesel Engine, поршень, передача і від'єднання навантаження дають контрольоване місце для паливної проби | Наявність корпуса/палива не доводить витрату рідини або обертальний вихід |
| Два бродильні апарати | 12; спеціалізація18 | Basin Lid і Bulk Fermenter мають окремі serializers і різний вихід з того самого fermentable+bone meal | Виготовлення апаратів перевіряється; етанол в інвентарі не означає справжнє бродіння |
| Рослинна олія й біодизель | 12; агроінтеграція18 | Seeds→олія через Press/Basin; олія й етанол зберігаються окремо до Mixer | Точні рецепти наведено нижче; вдале прийняття fluid outputs не перевіряється чинним ItemStack bridge |
| Тепло й нафтові фракції | 12; явний Blaze-контракт15 | Правильне паливо Burner, контроль тепла, Fluid Tank з контролерами й окремі виходи diesel/gasoline | Рецепт потребує heat level; observation нагрівача не доводить його температуру чи успішну дистиляцію |
| Матеріальна спеціалізація | 12–15 | Saw вирізає компонентну форму; Press/Basin використовує саме потрібний mold для панелей чи відер | Generic mold не доводить `mold_type`; stock панелей не доводить Compression Molding |
| Сервіс і масштабування | 12; додаткові28 | Large Engine, поршні, Silencer, Clutch, Stressometer; перевірка локального механічного навантаження | Налаштування/стрес/час роботи — ручне приймання; універсальну SU/FE величину не вигадуємо |
| Пізня інтеграція | 12; додаткові44 | Huge Engine, Turbocharger, окремий паливний запас і сигнал рівня; аварійне від'єднання локального заводу | Existing late contracts не відкривають машини раніше й не доводять довільну автоматизацію |

`producer-floors.json` заморожує явні gates бази `0ca0c5b`. Core CDG items
мають namespace-floor12, Create Basin/Press/Mixer/Saw —4, Mechanical Crafter —10,
Captured Blaze Burner —15, Empty Blaze Burner —2. Це **нижні межі доступу**,
а не доказ, що кожний ingredient і виробничий цикл досяжні в Survival саме тоді.
Старі V4 tasks залишаються в12; переставляти їх у15/18/28 без міграції не можна.

## Конкретні виробничі контракти

| Точний Recipe ID | Вхід | Вихід / умова |
|---|---|---|
| `createdieselgenerators:basin_fermenting/fermentable` | 1 `#createdieselgenerators:fermentable` +1 Bone Meal | 200mB ethanol, `processing_time:400` |
| `createdieselgenerators:bulk_fermenting/fermentable` | Той самий набір | 400mB ethanol, `processing_time:400`; фактичний tick rate залежить від native multiblock logic |
| `createdieselgenerators:compacting/plant_oil` | 1 `#c:seeds` | 100mB plant oil через Create compacting |
| `createdieselgenerators:mixing/biodiesel` | 100mB `#c:plantoil` +100mB `#c:ethanol` | 200mB biodiesel через Create mixing |
| `createdieselgenerators:distillation/crude_oil` | 100mB `#c:crude_oil` | `heated`,60processing_time,50mB diesel +50mB gasoline |
| `createdieselgenerators:distillation/superheated_crude_oil` | 100mB `#c:crude_oil` | `superheated`,40processing_time,75mB diesel +75mB gasoline |
| `createdieselgenerators:cutting/wood_chips` | 1 `#c:rods/wooden` | 1 Wood Chip |
| `createdieselgenerators:cutting/lines_mold` | 1 `#c:plates/iron` | Mold із component `createdieselgenerators:mold_type=createdieselgenerators:lines` |
| `createdieselgenerators:compression_molding/sheet_metal_panel` | 1 `#c:plates/iron`, потрібна форма `lines` | 4 Sheet Metal Panel; це не звичайне compacting без перевірки форми |
| `createdieselgenerators:compression_molding/bucket` | 1 `#c:plates/iron`, форма `bowl` | 1 Bucket |

Точний експортований `fermentable` tag містить Apple, Potato, Sugar і Sugar Cane,
а також optional food tags onion/tomato. **Wheat не є його прямим членом.**
Для гарантованої ванільної навчальної сировини можна обрати Sugar Cane.
`#c:seeds` посилається на `#c:seeds/wheat`, що включає Wheat Seeds;
`#c:plantoil` приймає як CDG Plant Oil, так і CCA Seed Oil. Ці вкладені
tags заморожено з export, а не виведено з подібної назви предмета.
Невдала або скасована машинна спроба не повинна отримувати майбутній production
proof лише за наявністю цих bucket/items.

## Три механічні нюанси, які курс має пояснювати

1. **Тепло залежить від палива й клапана.** `BurnerBlock` використовує спільну
   `BlazeBurnerBlock.HEAT_LEVEL`. У pinned `BurnerBlockEntity.tick` heat дорівнює
   `(valveOrRedstoneState+1)*burnerStrength`; `calculateHeatLevel` переводить
   1.4уKINDLED і1.8уSEETHING. Source-default Ethanol має multiplier0.9, Plant Oil —0.5.
   Відкрита до1 механічна заслінка без redstone дає1.8для етанолу й1.0для олії:
   «будь-яка горюча рідина» не означає однаковий heat level. Runtime fuel data
   можуть бути замінені datapack/config; exported registry містить лише IDs і
   Java-class names, не підтверджує ці значення. Recipe Burner використовує
   Empty Blaze Burner, тому Captured Blaze Burner15 не є єдиним можливим шляхом
   тепла; остаточний ранній bootstrap латуні/палива тут не сертифіковано.
2. **Контролер сплачується за кожний блок.** Ponder показує Fluid Tank висотою
   щонайменше3, але це source-default: `CDGConfig.DISTILLATION_MIN_HEIGHT` має
   default3і діапазон2..7. `DistillationControllerItem` вимагає стек не менший
   за `width*width*height` і списує поодному контролеру на перетворений tank block.
   Recipe `crafting/distillation_controller` дає4предмети. Один controller не
   є повним комплектом для трьохблокової вежі.
3. **Форми відрізняються компонентом.** Bar/Bowl/Lines/Chain мають один item ID
   `createdieselgenerators:mold`. `MoldItem.getMold` читає `CDGDataComponents.MOLD_TYPE`,
   а CDG `BasinRecipeMixin` відмовляє рецепту, якщо форми немає або вона інша.
   Item task без component predicate не можна назвати перевіркою правильної форми.

## Включення старих квестів без втрати прогресу

Поточна семистадійна карта має3baseline-квести і4V5contracts. Її8V4цілей
та окремий mandatory `E12_X_engine` не входять до memberships стадiй.
Повна звірка повинна охоплювати16наявних цілей, не створюючи їх повторно.
Знімок незмінених payloads: `existing-quest-map.json` поруч із manifest.

| Старий стабільний ID | Місце в карті |
|---|---|
| `E12_X_survey`, `E12_X_canister`, `V4_E12_diesel_01` | Розвідка/тара |
| `E12_X_pumpjack_parts`, `V4_E12_diesel_02`, `V4_E12_diesel_03` | Видобувні складники |
| `E12_X_engine`, `V4_E12_diesel_04`, `V5_E12_diesel_contract_01` | Контрольований механічний споживач |
| `V4_E12_diesel_05`, `V5_E18_diesel_contract_02` | Біологічна сировина й окрема аграрна інтеграція |
| `V4_E12_diesel_06`, `V5_E28_diesel_contract_03` | Великий двигун/сервіс |
| `V4_E12_diesel_07` | Дистиляційна оснастка |
| `V4_E12_diesel_08`, `V5_E44_diesel_contract_04` | Huge Engine/запас палива/пізня інтеграція |

Нові additive goals доцільно присвятити виготовленню двох типів ферментера,
розділеним запасам сировини, явній підготовці тепла/контролерів і матеріальному
ланцюгу Saw→Mold→Press/Basin→Panel. Для ручного crafting застосовувати справжній
crafting task; inventory/observation goals так і називати. Ця документація сама
не засвідчує, що нові goals вже згенеровано у SNBT.

## Незавершене приймання

- Підтвердити original installed JAR та його ABI перед новими спеціальними hooks.
- Перевірити effective fuel data/server minimum-height config і Survival-bootstrap.
- Якщо додається fluid production proof: перевіряти recipe identity, реальну оплату
  item/fluid inputs, прийняття виходу, власника/команду й post-completion межу.
  Чинний `ProductionMilestoneBridge` із `ItemStack` не доводить цього.
- Component-aware mold tasks потребують окремої фактичної FTB/KubeJS перевірки.
- Повний клієнт, JEI, справжня нафтова структура/вежа, автоматика, TPS — NOT_RUN.
