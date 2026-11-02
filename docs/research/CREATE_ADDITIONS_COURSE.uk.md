# Create Crafts & Additions1.6.0 — електромеханічна карта

Встановлену версію1.6.0 підтверджує наданий `export/mods.json`; Windows-інстанс
не змонтований. Це карта вибраної електромеханічної лінії, а не заява про
повне освоєння всіх можливостей CCA. Оригінальний JAR, повний клієнт,
JEI, Survival і TPS у цьому дослідженні **NOT_RUN**.

## Версія та джерела

У попередній карті використовувався upstream pin
`1c81fab9aaaf157c58e16ad0acbe95c8523cd4e4`, де `mod_version=1.7.2`.
Його не можна подавати як джерело версії1.6.0. Історичні файли цього pin
залишаються збереженими; активне version-matched дослідження має окремий каталог.

Офіційний commit [`51e4a389ab044a113c02be383e66beaf69ec3110`](https://github.com/mrh0/createaddition/commit/51e4a389ab044a113c02be383e66beaf69ec3110)
змінює `mod_version=1.5.11` на `1.6.0`; `minecraft_version=1.21.1`.
Upstream не опублікував Git-тегів. Це **source-version match за version-bump**,
а не доказ тотожності конкретного випущеного або встановленого binary JAR.
Не виключено існування пізніших commit із тим самим рядком версії1.6.0.
Цей pin також оголошує `create_version=6.0.10-280`; це сумісний source-контекст,
а не доказ виконання CCA разом із встановленим Create6.0.10.

Точні початкові байти17офіційних файлів,128рецептів namespace CCA та7tag-файлів
збережено в `content/research/evidence/create_addons_core_v12/cca/`.
`manifest.json` містить SHA-256, URL і pin кожного свідчення; `recipe-index.json`
покриває всі128експортованих CCA-рецептів. Це не перелік усіх інтеграцій
із результатами CCA в інших namespace. Експорт відображає Almost Unified:
результат може належати Immersive Engineering, навіть коли upstream створює
власний CCA-предмет. Tag-файли збережені буквально; optional `?` записи самі
по собі не доводять реєстрацію відповідного item.

## Чому виробництво йде саме в такому порядку

| Крок | Реальна механіка та її роль | Що перевіряється достовірно |
|---|---|---|
| Форми металу | Rolling Mill використовує власний `createaddition:rolling`, обертання і один вхідний предмет. Зливок і пластина мають різні результати. | Item task підтверджує лише запас. Observation підтверджує блок, а не його успішний процес. |
| Порожні й заповнені котушки | Порожній `spool` — носій; чотири дроти потрібного tag перетворюють його на мідну або електрумову котушку. Пруток дріт не замінює. | Наявність конкретної котушки; не факт фізичного прокладання мережі. |
| Контакт із FE | Small Connector має4вузли, Large Connector —6. Обидва надають energy capability; ліміти залежать від конфігурації. | Наявність/спостереження потрібного виду connector; не FE/t і не з'єднання вузлів. |
| Обертання → FE | Alternator споживає stress Create і виробляє FE лише за ненульової швидкості та виконаної speed requirement. | Старі observation/item цілі не доводять роботу генератора. |
| FE → обертання | Electric Motor потребує FE, має окремий rate consumption і redstone-зупинку. Його не слід трактувати як другий безкоштовний генератор. | Наявність/спостереження; активне живлення й навантаження потребують іншого observer або ручного тесту. |
| Сплав для розширення | `createaddition:mixing/electrum`: heated gold+silver →2уніфіковані IE-зливки. Це машинний результат з окремою витратою входів. | Новий native Basin receipt має підтверджувати саме успішний процес і команду, а не готовий зливок. Сам документ не доводить реалізацію observer. |
| Від зливка до провідника | Прес формує пластину; прокат пластини дає дріт. Прокат самого зливка дає пруток. | Явно обрані матеріальні результати; без rolling-specific observer це не proof конкретного способу отримання. |
| Запас і керування | Capacitor є предметом-компонентом зі своїм energy storage; Modular Accumulator — окремий блок зі складанням сховища. Redstone Relay керує зв'язком мереж. | Предмет/блок і їхні відмінності; не заповненість сховища або пропускна здатність. |
| Рухома фабрика | Portable Energy Interface під'єднує energy handler Contraption лише під час допустимого transfer. У від'єднаному стані використовується порожній handler. | Спостереження interface й інвентарна підготовка; не доведена зарядка рухомої машини. |

`CommonConfig.java` задає налаштовувані коефіцієнти. Наприклад, upstream default
alternator efficiency0.75 і base480FE/t при256RPM не є вимірюванням активного
конфіга AIA2. З'єднання мотор→генератор не оголошується джерелом безкоштовної
енергії. Перевірку реальної FE-мережі не можна підмінити отриманням блока.

Важлива відмінність redstone: у source1.6.0 `ElectricMotorBlockEntity.tick()`
вимикає мотор при `POWERED`, а `RedstoneRelayBlockEntity.networkTick()`
передає енергію при `POWERED`. Це різні полярності керування; наявність
repeater не доводить, що гравець налаштував їх правильно.

## Точні матеріальні свідчення

| Recipe ID | Вхід → результат у наданому експорті |
|---|---|
| `createaddition:mixing/electrum` | `c:ingots/gold` + `c:ingots/silver`, heated →2 `immersiveengineering:ingot_electrum` |
| `createaddition:pressing/electrum_ingot` | `c:ingots/electrum` →1 `immersiveengineering:plate_electrum` |
| `createaddition:rolling/electrum_ingot` | `c:ingots/electrum` →2 `createaddition:electrum_rod` |
| `createaddition:rolling/electrum_plate` | `c:plates/electrum` →2 `immersiveengineering:wire_electrum` |
| `createaddition:crafting/spool` |1залізний пруток +2залізні пластини →24порожні котушки |
| `createaddition:crafting/copper_spool` |1порожня котушка +4 `c:wires/copper` →1мідна котушка |
| `createaddition:crafting/electrum_spool` |1порожня котушка +4 `c:wires/electrum` →1електрумова котушка |
| `createaddition:crafting/capacitor_1` / `_2` |Мідна й цинкова пластини +redstone torch; взаємна перестановка пластин дає той самий1capacitor, а не два різні ступені |
| `createaddition:crafting/modular_accumulator` |2capacitor +brass casing +мідний пруток +електрумовий дріт →1Modular Accumulator |

Стара CCA-стадія5посилалася на `create:cutting/compat/immersiveengineering/wire_electrum`,
хоча описувала Rolling Mill. Такий рецепт різання не може бути свідченням
прокату. Правильне матеріальне свідчення — `createaddition:rolling/electrum_plate`.
Обидва способи можуть легітимно існувати; видаляти cutting лише для відповідності
назві квесту не потрібно. Вони мають бути чесно розмежовані в карті та перевірках.

## Розподіл за епохами та сумісність

Базові CCA-блоки, включно з Rolling Mill, motor/alternator і connectors, мають
item/block floors11. Старі `E11_X_alternator` і `E11_X_rolling_mill` лишаються
обов'язковою основою згідно з наявною картою. Додаткові матеріальні та
інфраструктурні вправи не повинні змінювати ID/tasks уже завершених цілей.

`producer-reachability.json` фіксує вибрані gate-значення й SHA контракту
`0ca0c5b`. Recipe/output floor8 для електруму **не доводить доступність heat**.
Консервативний новий шлях курсу15використовує штатний Blaze Burner з floor15;
Basin/Mixer доступні з4. Водночас CDG burner має floor12 і за відповідного
ethanol/valve стану може дати SEETHING. Повна bootstrap/config досяжність
цього альтернативного паливного шляху тут не доведена. Тому15 — обрана
епоха нового підтверджуваного процесу, а не заява про абсолютно найраніше
можливе отримання heat чи заборона всіх попередніх легітимних способів сплаву.

Розширена існуюча спеціалізація19пов'язує форми металу з IE та Ender IO.
Рухомий енергетичний interface розглядається в28разом із наявною
контрапційною/пневматичною інфраструктурою. Фінальна інтеграція32пов'язує
реле з AE2-сигналами; вона не стверджує, що AE2 сам виміряв FE-мережу.

У карті необхідно зберегти та врахувати всі8наявних `V4_E11_electric_bridge_01…08`
і4цілі `V5_E11_electromechanical_work_01`,
`V5_E19_electromechanical_work_02`, `V5_E28_electromechanical_work_03`,
`V5_E32_electromechanical_work_04`, а не лише поодинокі
E11-вузли. V4містять observation та інвентарні перевірки. Вони не стають
новими машинними receipts після перейменування або додавання до карти.
Нові вузли мають доповнювати точні ланцюги форм/керування й залежати від
відповідної епохи та попередніх матеріальних/інфраструктурних цілей.

## Що лишається непідтвердженим

- Тотожність version-matched source конкретному встановленому JAR; optional binary ABI і повний клієнт не перевірені.
- Успішний rolling-specific process, FE/t, заряд акумулятора, передача через relay/interface і тривала автоматизація: existing inventory/observation tasks цього не вимірюють.
- Повний паливний bootstrap альтернативного CDG heat12і фактичні конфігурації інстансу.
- Tesla Coil/charging та інші CCA-спеціалізації не стають завершеними через цю карту; наявність source-файла ще не означає реалізований квест або hook.
- Для нового Basin goal потрібні реалізація, явний extension contract до15опублікованих правил, регресії post-consumption/accepted-output і ручне приймання оригінального модпаку. Цей research-документ сам не є доказом цих тестів.
