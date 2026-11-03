# CDG — нативне підтвердження пресування панелей

База дослідження — checkpoint `9067fdf` /0.4.24-alpha. CDG
`1.21.1-1.3.15`, Create `6.0.10`, Minecraft1.21.1 NeoForge.
Дослідження стосується одного конкретного компресійного рецепта. Воно не
підтверджує роботу всіх рецептів CDG, Spout casting чи автоматизацію рідин.
Оригінальні optional-бінарники, weaving, клієнт, FTB UI, JEI, Survival і TPS
потребують окремого фактичного запуску; тут їхній статус **NOT_RUN**.

## Послідовність навчання

Попередня ціль `V13_E12_cdg_mold_lines` перевіряє точний компонент профілю
Mold та зразки продукції. Вона зберігає свою первісну семантику. Нова
`V14_E12_cdg_panel_native` залежить від неї та додає іншу умову: серверний
доказ успішного виробництва на машині поточної команди. Це один новий
необов’язковий вузол епохи12, а не заміна старого task або нова умова ключів.

Маршрут: залізна пластина → форма Lines, виготовлена Mechanical Saw →
Mechanical Press над Basin → одна пластина й оснащення Lines → чотири
`createdieselgenerators:sheet_metal_panel`. Форма не входить до витратних
`ingredients` рецепта. Потрібний профіль — повний ResourceLocation
`createdieselgenerators:lines`; нагрівання не потрібне.

Квест окремо вимагає нативне advancement
`aia2:mechanics/cdg_panel_compression` і наявність чотирьох панелей. Отримання
цих панелей через інший рецепт, Creative, нагороду чи `/give` задовольняє
лише предметну частину. Предмети не здаються з витратою. Нагорода — чотири
Wood Chip поточної епохи; вона не замінює прес, форму або ключ.

## Точний рецепт і доступність

Recipe ID: `createdieselgenerators:compression_molding/sheet_metal_panel`.
Serializer: `createdieselgenerators:compression_molding`.

```json
{
  "type": "createdieselgenerators:compression_molding",
  "ingredients": [{"tag": "c:plates/iron"}],
  "mold": "createdieselgenerators:lines",
  "results": [{"id": "createdieselgenerators:sheet_metal_panel", "count": 4}]
}
```

Це наданий installed export, не вигаданий новий рецепт. Item/recipe floor
панелей і Mold —12; пластина IE має floor8, Press і Basin —4. Отже, ціль12
не потребує виробника майбутньої епохи. Окремий нагрівач не додається.

## Межа успішного процесу

`CompressionMoldingRecipe` успадковує `CompactingRecipe → BasinRecipe`.
CDG HEAD-injection до `BasinRecipe.apply` під час кожної симуляції та
фактичного виклику знаходить **останній** Mold серед слотів Basin. Його
`MoldType` має відповідати `moldType` поточного рецепта. Додавання чотирьох
різних форм у чашу не робить її універсальним пресом.

Create спочатку перевіряє доступність матеріалів і виходу в симуляції, потім
вилучає справжні інгредієнти та викликає фактичний `acceptOutputs`. Чинний
AIA2 RETURN hook спостерігає лише `!test && returnValue == true`; нового
optional Mixin selector для цього рецепта не потрібно. Власник машини,
поточна команда, готовність required guard, епоха та recipe policy мають
залишатися придатними на момент зарахування.

Серверний proof означає прийнятий результат конкретного процесу, а не
доставку панелей у певну скриню або перевірку всієї фабрики. Місце та
подальше використання продукції визначають окремі завдання.

## Перевизначення рецептів і форми

Перевірки тільки ID, serializer та Item ID виходу недостатньо. Datapack
може залишити той самий ID, але замінити Lines, матеріали або кількість
панелей. Вихідний CDG також допускає небезпечний край: невідомий recipe
mold і Mold без відомого профілю можуть обидва дати `null`, а порівняння
їхніх посилань не розрізнить їх.

Тому новий proof має окремо відхиляти рецепт, якщо поточні codec-семантики
не відповідають еталону, або його public `moldType` відсутній/не має ID
`createdieselgenerators:lines`. Відхиляється саме зарахування цієї цілі;
не можна називати змінений сторонній рецепт перевіреним оригінальним
маршрутом. Повторна перевірка лише наявності форми після процесу цього
не гарантує.

Поточний recipe object звіряється з identity-index менеджера рецептів.
Після reload стара cached instance не повинна створювати новий proof.
Перевірку codec слід кешувати в межах поточного recipe generation, а не
сканувати інвентарі чи переобчислювати весь граф кожен тик. Окремо потрібно
перевіряти можливу зміну public `moldType` уже відомого рецепта.

Новий доказ додається поверх16опублікованих правил. Їхні ID, порядок,
дані schema1 та збережена історія команд не переписуються. Новий квест не
вимагає скидання старих completions. Якщо команда вже здобула правильний
доказ, його історія має зберігатися після restart і синхронізуватися з FTB.

## Джерела та межі доказів

- CDG pin `79ce136730871b6f3f7b55d3cc748ff2bec2ad12`, source-version match
  `1.21.1-1.3.15`:
  [CompressionMoldingRecipe](https://github.com/george8188625/Create-Diesel-Generators/blob/79ce136730871b6f3f7b55d3cc748ff2bec2ad12/src/main/java/com/jesz/createdieselgenerators/content/molds/CompressionMoldingRecipe.java),
  [BasinRecipeMixin](https://github.com/george8188625/Create-Diesel-Generators/blob/79ce136730871b6f3f7b55d3cc748ff2bec2ad12/src/main/java/com/jesz/createdieselgenerators/mixins/BasinRecipeMixin.java),
  `MoldRecipeParams`, `MoldItem`, `MoldType`, `MechanicalPressBlockEntityMixin`.
  Незмінені копії та SHA містяться в
  `content/research/evidence/cdg_molds_v13/manifest.json`.
- Create pin `ac0c444d9828da3453ae8cc65338e8de063286fb`, source-version match
  `6.0.10`:
  [BasinRecipe](https://github.com/Creators-of-Create/Create/blob/ac0c444d9828da3453ae8cc65338e8de063286fb/src/main/java/com/simibubi/create/content/processing/basin/BasinRecipe.java).
  Заморожена копія:
  `content/research/evidence/technology_v5/create/core_verified/official/src/main/java/com/simibubi/create/content/processing/basin/BasinRecipe.java`.
- Recipe export:
  `content/research/evidence/cdg_molds_v13/recipes/createdieselgenerators/compression_molding/sheet_metal_panel.json`.
- Попередня карта: [CDG_MOLDS](CDG_MOLDS.uk.md).
- Ручна перевірка: [CDG_PANEL_ACCEPTANCE](../testing/CDG_PANEL_ACCEPTANCE.uk.md).

Source-version match не є підтвердженням байтової тотожності встановленого
JAR. Статичний source audit, виконання actual helper на modeled host та
мінімальний Minecraft-сервер мають різні межі. Остаточні результати тестів
цього checkpoint потрібно читати в `AIA2_0.5.0_PROGRESS.md` і звіті перевірок.
