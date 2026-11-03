# CDG Mold — профіль форми як компонент предмета

Minecraft1.21.1 / CDG1.21.1-1.3.15 / FTB Quests2101.1.36 /
установлена FTB Library2101.1.37. База дослідження: `2a0dcdd`.

Це перевірка джерел і формату даних. Оригінальний installed JAR, optional
dispatch, повний клієнт, JEI, Survival і TPS тут **NOT_RUN**. Новий Mixin
для перевірки профілів не потрібний. Наявний generic Mold task не змінюється.

## Версії та джерела

- CDG pin `79ce136730871b6f3f7b55d3cc748ff2bec2ad12` оголошує
  `mod_version=1.21.1-1.3.15`. Це source-version match, а не доказ тотожності
  binary JAR установленої збірки.
- FTB Quests pin `8c53f35a97d8897c861b097f1e39f4fc3beb3a15` відповідає
  версії2101.1.36. Компіляційна залежність Library у цьому pin —2101.1.36.
- Фактично встановлена Library2101.1.37 перевірена за source pin
  `ba8962d4b4dcff22041824c792fe07ae21fe28d5`. ItemMatchingSystem належить
  Quests; поведінку невідомого імені режиму визначає Library NameMap.

Публічні upstream-файли, чотири профільні model JSON і13оригінальних
експортованих рецептів заморожено без переписування байтів у
`content/research/evidence/cdg_molds_v13/`. `manifest.json` містить41SHA-запис
із URL/pin/provenance; `contracts/component-contract.json` фіксує протокол.
Повні пропрієтарні Minecraft sources не пакуються.

## Один Item ID, чотири профілі

`CDGDataComponents.MOLD_TYPE` — `DataComponentType<ResourceLocation>` із
`persistent(ResourceLocation.CODEC)` та мережевим `ResourceLocation.STREAM_CODEC`.
Предмет усіх форм — `createdieselgenerators:mold`; окремих Item ID профілів немає.

| Значення компонента `createdieselgenerators:mold_type` | Основне призначення у наданому export |
|---|---|
| `createdieselgenerators:lines` | Панелі, палички; нагріте стискання Blaze Powder у Blaze Rod |
| `createdieselgenerators:bowl` | Bowl із Wood Chips; Bucket з iron plate |
| `createdieselgenerators:chain` | Chain з iron nuggets; Minecart Coupling з Andesite Alloy |
| `createdieselgenerators:bar` | Casting шоколаду або phenolic resin; compression-рецепта цього профілю в export немає |

Усі чотири `create:cutting` рецепти беруть `#c:plates/iron` і повертають один
Mold із відповідним компонентом. Наявність такого предмета підтверджує профіль,
але не доводить, що його виготовлено саме пилкою. `only_from_crafting` не слід
використовувати для cutting або compression як заміну нативному process proof.

`MoldItem.getMold` читає компонент і знаходить відомий `MoldType`; відсутній
компонент або невідомий profile ID не надає відомого профілю. Неповне значення
`lines` не еквівалентне `createdieselgenerators:lines`: ResourceLocation без
namespace отримує стандартний namespace Minecraft.

## Коректний ItemTask

FTB Quests `ItemTask.readData` читає `item` через
`QuestObjectBase.itemOrMissingFromNBT` → `ItemStack.parse(provider, compound)`.
Сучасна структура з нижнім регістром `count` зберігає `components`:

```snbt
{
  type: "item"
  item: {
    id: "createdieselgenerators:mold"
    count: 1
    components: {
      "createdieselgenerators:mold_type": "createdieselgenerators:lines"
    }
  }
  count: 1L
  consume_items: false
  only_from_crafting: false
  match_components: "fuzzy"
}
```

Не використовувати старі поля `Count` чи `tag`: legacy-гілка FTB імпортує ID
та кількість без перетворення старого NBT у data components. Помилка формату
могла б видалити профіль фільтра й непомітно перетворити його на generic Mold.

| `match_components` | Фактична поведінка для звичайного предмета |
|---|---|
| `none` | Порівнює лише Item, профіль не перевіряється |
| `fuzzy` | Такий самий Item; усі ефективні компоненти фільтра мають існувати й дорівнювати компонентам кандидата; додаткові компоненти кандидата дозволені |
| `strict` | `ItemStack.isSameItemSameComponents`; зайві компоненти теж змінюють результат |

Для цілі профілю обрано `fuzzy`: перейменування справжньої форми не має
перетворювати правильний профіль на неправильний. Це не перевірка лише одного
поля: `getComponents()` містить також стандартні компоненти Item. Якщо кандидат
замінив значення стандартного компонента фільтра, fuzzy також може відмовити.

**Небезпечна помилка формату:** `ALL`, `partial`, `FUZZY`, друкарська помилка
або невідоме ім’я не є новими режимами. Library `NameMap.get` повертає default
`NONE`. Генератор/валідатор мають відхиляти непогоджений режим, а не покладатися
на цей fallback, інакше перевірка профілю зникає.

`ItemMatchingSystem` спочатку шукає ItemFilterAdapter. Описана поведінка стосується
звичайних item stacks; предмет, який сторонній адаптер визнав фільтром, може мати
іншу семантику. Mold у дослідженій CDG-реалізації — звичайний `MoldItem`.

## Іконка з профілем

`QuestObjectBase.readData` читає `icon` через `ItemStack.SINGLE_ITEM_CODEC`,
тому іконка може містити той самий `components` compound. CDG `MoldItemRenderer`
вибирає модель за `MoldType`, а `MoldItem.getName` використовує профільну назву.
`MoldType.getModelId` дає `createdieselgenerators:item/mold/<profile>`;
чотири model JSON посилаються на відповідні `textures/item/mold/<profile>`.
Це перевірка структури джерел, не фактичного client bake або готового UI.

## Реальні compression та casting маршрути

Для compression потрібні Press над Basin та відповідна форма в Basin.
`MechanicalPressBlockEntityMixin` допускає тип CDG COMPRESSION_MOLDING.
`BasinRecipeMixin` переглядає всі слоти, залишає **останній** знайдений Mold
і порівнює його `MoldType` з рецептом. Практична схема — одна потрібна форма
на Basin; чотири різні форми разом не є універсальним оснащенням.
Mold не входить до списку витратних ingredients цих13свідчень рецептів.

Bar casting має інший маршрут: Spout над Basin з потрібною формою.
`BasinSpoutCasting.fillBlock` підбирає CASTING recipe за формою та рідиною.
`CastingRecipe.matches` допускає будь-яку відповідну форму в Basin; правило
«останній Mold» належить compression і не переноситься на casting.
Механічний Press для цього bar casting не потрібний.

| Точний рецепт | Умова та продукт |
|---|---|
| `compression_molding/sheet_metal_panel` | lines +1 iron plate →4панелі |
| `compression_molding/stick` | lines +4wood chips →4sticks |
| `compression_molding/blaze_rod` | lines +4blaze powder +heated →1blaze rod |
| `compression_molding/bowl` | bowl +4wood chips →1bowl |
| `compression_molding/bucket` | bowl +1iron plate →1bucket |
| `compression_molding/chain` | chain +6iron nuggets →1chain |
| `compression_molding/minecart_coupling` | chain +1andesite alloy →1coupling |
| `casting/chocolate_bar` | bar +250mB `create:chocolate` →1chocolate bar |
| `compat/immersiveengineering/duroplast_sheet` | bar +250mB `#c:phenolic_resin` →1IE duroplast plate |

Усі Recipe ID у таблиці мають namespace `createdieselgenerators:`. Наявність
output-предмета поруч із правильною формою лишається перевіркою комплекту,
а не доказом compression/casting, витрати inputs чи прийнятого виходу.
Особливо не слід видавати bucket/sample/observation за fluid production receipt.

## Межі й приймання

Потрібні автоматичні перевірки чотирьох правильних значень, відсутнього/
помилкового/чужого профілю, додаткового custom name, режимів none/fuzzy/strict,
відмови unknown-mode, task/icon serialization і збереження generic task IDs.
Actual matcher можна виконувати на modeled ItemStack host, але це не тест
оригінального CDG JAR, registry decode або FTB GUI.

Фактичне завантаження component codec, профільної іконки, machine route,
автозарахування ItemTask, client/server синхронізація й survival-доступність
потребують окремого запуску повної тестової копії AIA2. Дані існуючого світу
або завершені старі завдання для перевірки не перезаписуються.
