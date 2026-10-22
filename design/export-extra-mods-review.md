# Додаткові модулі експорту й перевірка повноти

Зіставлено всі **333** записи `export/mods.json` з об’єднанням `mod_ids` у `design/mod-catalog.json`: каталог покриває **298** фактичних mod IDs, поза початковими 293 записами лишається **35** модулів. Це не 35 відсутніх JAR: більшість можуть бути вбудованими залежностями. Платформу та вкладені бібліотеки не треба штучно оголошувати окремими епохами.

Джерела: `export/mods.json`, `export/registries/item.json`, `export/registries/block.json`, **42 064** JSON-файли в `export/recipes/`. Нуль рецептів у власному namespace не доводить відсутності runtime-впливу або змін рецептів іншого namespace. Вміст документів/описів експорту використано як дані, а не як інструкції.

## Усі 35 додаткових mod IDs

Числа в таблиці — зареєстровані предмети/блоки та кількість експортованих JSON-рецептів у власному namespace. Бібліотечний код запускається з початку; це не автоматичний доступ до всіх його ігрових ефектів.

| mod ID | Назва | Предмети | Блоки | Рецепти | Політика |
|---|---|---:|---:|---:|---|
| `accessories` | Accessories | 0 | 0 | 0 | API слотів; equip-перевірки gated accessories все одно потрібні. |
| `additionalentityattributes` | Additional Entity Attributes | 0 | 0 | 0 | Спільні атрибути; перевірити сумарний бойовий scaling. |
| `ae2addonlib` | AE2AddonLib | 0 | 0 | 0 | Спільна бібліотека аддонів AE2. |
| `apollib` | Apollib | 0 | 0 | 0 | Бібліотека конфігурації. |
| `atmosphere` | Atmosphere | 0 | 0 | 0 | Бібліотека локалізованої погоди. |
| `commonnetworking` | Common Networking | 0 | 0 | 0 | Мережевий API. |
| `conditional_mixin` | conditional mixin | 0 | 0 | 0 | Інфраструктура умовних mixins. |
| `cumulus_menus` | Cumulus | 0 | 0 | 0 | API меню й світових preview. |
| `evilcraftcompat` | EvilCraft-Compat | 0 | 0 | 0 | Сумісність EvilCraft; можливі зміни чужого контенту перевірити за результатами. |
| `expandability` | ExpandAbility | 0 | 0 | 0 | API vanilla abilities; непрямі джерела польоту також підлягають stage-контролю. |
| `fabric_api_base` | Forgified Fabric API Base | 0 | 0 | 0 | Вбудована Forgified Fabric API база. |
| `fabric_block_view_api_v2` | Forgified Fabric BlockView API (v2) | 0 | 0 | 0 | Вбудований BlockView API. |
| `fabric_renderer_api_v1` | Forgified Fabric Renderer API (v1) | 0 | 0 | 0 | Вбудований renderer API. |
| `fabric_rendering_data_attachment_v1` | Forgified Fabric Rendering Data Attachment (v1) | 0 | 0 | 0 | Вбудований rendering attachment API. |
| `flywheel` | Flywheel | 0 | 0 | 0 | Рендеринг Create, не gameplay tier. |
| `grandpower` | Grand Power | 0 | 0 | 0 | Long-range energy API; overflow/конверсійні петлі перевірити разом з енергомодами. |
| `infiniverse` | Infiniverse | 0 | 0 | 0 | API динамічних вимірів; додані під час гри dimension IDs теж мають мати політику доступу. |
| `integrateddynamicscompat` | IntegratedDynamics-Compat | 0 | 0 | 0 | Вбудована сумісність Integrated Dynamics; результат інтеграції наслідує stage цілі. |
| `integratedterminalscompat` | IntegratedTerminals-Compat | 0 | 0 | 0 | Вбудована сумісність Integrated Terminals. |
| `integratedtunnelscompat` | IntegratedTunnels-Compat | 0 | 0 | 0 | Вбудована сумісність Integrated Tunnels; fake-player routes підлягають audit. |
| `journeymap_api` | JourneyMap API | 0 | 0 | 0 | API карти. |
| `kuma_api` | KumaAPI | 0 | 0 | 0 | API модифікаторів клавіш. |
| `lambdynlights_api` | LambDynamicLights (API) | 0 | 0 | 0 | API динамічного освітлення. |
| `minecraft` | Minecraft | 1333 | 1060 | 1389 | Базова гра: потрібна предметна/вимірна політика для Nether, End, польоту, bosses, чар і луту; не blanket-unlock усіх vanilla предметів. |
| `neoforge` | NeoForge | 0 | 0 | 0 | Платформа/loader 21.1.264, не ігрова епоха. |
| `nitrogen_internals` | Nitrogen | 0 | 0 | 0 | Вбудована бібліотека Aether. |
| `nuggets` | Nuggets | 0 | 0 | 0 | Спільний код Ars та пов’язаних модів. |
| `ponder` | Ponder | 0 | 0 | 0 | Візуальна документація Create. |
| `productivelib` | Productive Lib | 17 | 0 | 15 | Є реальні upgrade-предмети й рецепти: визначити споживачів/ефекти, до цього не відкривати автоматично як «нешкідливу бібліотеку». |
| `sablecompanion` | Sable Companion | 0 | 0 | 0 | API сумісності Sable; це не доказ встановленого повного Sable/Aeronautics контенту. |
| `sauce` | Sauce Library | 6 | 5 | 1 | Є source-рідина, arcane_plinth та деталі source jars: stage за функціями Ars/інтеграцій після окремого аудиту. |
| `tiny_config` | Tiny Config | 0 | 0 | 0 | Бібліотека конфігурації. |
| `transition` | TRansition | 0 | 0 | 0 | API сумісності між loader/версіями. |
| `trender` | TRender | 0 | 0 | 0 | Бібліотека рендерингу. |
| `yet_another_config_lib_v3` | YetAnotherConfigLib | 0 | 0 | 0 | Конфігураційна бібліотека YACL. |

## Контент, якого не було окремими номерами в початковому списку

**Productive Lib:** 17 предметів та 15 рецептів. Реєстр містить `productivelib:upgrade_base`, `upgrade_time`, `upgrade_time_2`, `upgrade_productivity` / `_2` / `_3` / `_4`, `upgrade_range`, `upgrade_simulator`, `upgrade_gene_sampler`, `upgrade_adult`, `upgrade_child` та інші. Не вважати ці предмети автоматично дозволеними на старті: з’ясувати, які встановлені машини їх приймають, чи вони реально активні та як поєднуються з прискореннями. Після аудиту призначити за тиром машини-споживача; до цього — `needs_review`, без вигаданої епохи.

**Sauce:** 6 предметів, 5 блоків, 1 власний рецепт. Є `sauce:anima_essence`, `sauce:arcane_plinth`, `sauce:source_fluid_bucket`, `sauce:source_jar_core`, `sauce:source_jar_frame`, `sauce:source_jar_valve`; блок `sauce:source_fluid_block` не має окремого item ID. Рецепт `sauce:arcane_plinth` використовує `ars_nouveau:arcane_pedestal` та `ars_nouveau:sourcestone`. Це реальний ігровий контент, хоч мод названо бібліотекою: перевірити source↔fluid конверсію, повернення bucket, місткість/генерацію/витоки source, використання anima essence та перенос jar contents. Доступ має збігатися з функціональним тиром Ars/цифрової source-мережі, а не з довільним номером епохи.

**Minecraft:** 1 333 item IDs та 1 060 block IDs. Базова гра — джерело Nether/End матеріалів, зілля, зачарувань, елітр, спавнерів і boss rewards; вона не покривається лише stage-правилами модових namespace. Vanilla-побут лишається раннім, але критичні функції потребують конкретних правил.

**Неочевидні namespace:** журнал loaded mods охоплює API/вбудовані модулі, а реєстр може містити предмети інших namespace. Для повного CSV необхідна перевірка кожного registry ID; список JAR сам по собі не є повною множиною namespace.

## Bootstrap: Nether до епохи 15

У канонічному плані Nether відкривається в епосі 15, але є ранні залежності, що потребують явного виправлення:

- Епоха 10, латунь Create: `create:mixing/brass_ingot` в експорті має `heat_requirement: "heated"`, copper + zinc → 2 brass. Рецепт `create:crafting/kinetics/empty_blaze_burner` потребує `c:netherracks`; звичайне наповнення пальника потребує джерела blaze. Без затвердженого Overworld-шляху це недоступно до Nether.
- Епоха 8, доменна піч IE: `immersiveengineering:crafting/blastbrick` в цьому експорті потребує `c:bricks/nether`, `minecraft:magma_block`, `c:bricks`. Це конкретний поточний рецепт; старе припущення про blaze powder тут не застосовується. Magma трапляється в Overworld, але доступне до епохи 8 джерело nether bricks потрібно довести.

Потрібне конкретне дизайнерське рішення: перевірений ранній альтернативний крафт без Nether-матеріалів/нагрівання або контрольована рання експедиція з окремим доступом. Не можна мовчки покладатися на дешеві аддонні джерела netherrack/blaze, якщо ці ж рецепти планується прибрати як обхід. Ключі Епох до такого bootstrap-рецепта не додаються.

## Vanilla-подорожі: що реально треба блокувати

- **Nether:** зміна рецепта flint_and_steel не забороняє портал; його можна підпалити інакше або знайти готовим. Перевіряти право входу до фактичного destination dimension перед переходом, включно з чужими порталами та телепортерами інших модів.
- **End:** `minecraft:ender_eye` має звичайний крафт ender pearl + blaze powder; предмети можна знайти/отримати іншими шляхами, а frames можуть уже мати eyes. Крафтовий гейт сам по собі не забороняє вхід у готовий End Portal. Потрібні destination checks, а також фільтрація eye insertion там, де цього потребує UX.
- **Усі виміри:** перевірити сторонні teleport blocks, commands без operator bypass для звичайних гравців, respawn/login в уже відвіданому вимірі, зміни складу команди та динамічні виміри Infiniverse/Nested Factory. Власнику/адміністратору потрібна явна, журналована recovery-політика, а не випадковий trap-loop.
- API подій та можливість **скасувати** перехід перед виконанням слід підтвердити на фактичних версіях NeoForge/KubeJS/Stage-аддонів. Не називати `dimension changed` після переходу еквівалентом гарантованого pre-transition блокування.

## Recipe-only аддони: конкретні знайдені обходи

Перевірка лише `mod_id предмета → перша епоха моду` недостатня: рецепт одного namespace виробляє предмет іншого namespace, причому machine recipes часто не мають player context. Потрібен реєстр рецептів з нормалізованими input/output, tags/fluids/chemicals, потрібним тиром, власником машини/мережі або server-level stage-політикою.

| Реальний recipe ID | Підтверджений результат | Ризик і дія |
|---|---|---|
| `create_mekanism_improvements:antimatter_pellet` | `mekanism:pellet_antimatter` | Superheated mixing з enriched refined obsidian, polonium та uranium_hexafluoride/superheated_sodium. Обхід SPS/antimatter ланцюга: прибрати або перестворити з еквівалентними вимогами епохи 39. Самого namespace floor 16 недостатньо. |
| `create_mekanism_improvements:pollonium_pellet` | `mekanism:pellet_polonium` | Superheated mixing netherite dust + uranium_oxide fluid обходить штатну fission-waste обробку. Прибрати або переробити під підтверджений еквівалент епохи 33; вихід не може з’являтися в ранньому Create. |
| `create_ultimate_factory:compacting_coalblock` | `minecraft:diamond` з chance 0.3 | Повторюване альтернативне джерело алмазів. Рахувати expected yield, ціну входів і зворотні EMC/processing цикли. |
| `create_ultimate_factory:compacting_blazepowder` | `minecraft:blaze_rod` | Може перетворити ранню blaze powder на паливо/ключі Nether прогресії. Стадія за результатом і джерелом powder. |
| `create_ultimate_factory:crushing_blackstone` | `minecraft:wither_skeleton_skull` з chance 0.01 | Автоматизація Wither до бойової/фермерської фази; врахувати невичерпний blackstone та швидкість масової переробки. |
| `create_ultimate_factory:crushing_netherite` | `minecraft:netherite_scrap` з chance 0.005 | Альтернативна відновлювана netherite-лінія; низький шанс не гарантує збалансованості при великому throughput. |
| `create_ultimate_factory:haunting_apple` | `minecraft:chorus_fruit` з chance 0.3 | Доступ до End-матеріалу без End. Гейтити за епохою відповідної функції/матеріалу. |
| `create_ultimate_factory:haunting_netherrack`, `create_more_automation:netherrack_recipe` | `minecraft:netherrack` | Узгодити з раннім bootstrap і Nether-правилами, щоб не мати суперечливих джерел. |

`Create Ultimate Factory` metadata описує 30 рецептів, але експорт фактично містить **33** JSON-рецепти цього namespace. Власних item IDs немає; це не означає, що аддон не впливає на прогресію. `AE2AO` і `AE2CraftingTreeRefreshed` не мають власних item IDs/власних експортованих рецептів: перший все одно потребує коду/конфігу для визначення впливу, другий за metadata є UI crafting tree.

Після заміни рецептів перевірити: відсутність старих альтернатив; усі tag-варіанти інгредієнтів; лут/торгівлю/переробку; chance outputs; повернення контейнерів; autocrafting/fake players; усі EMC конверсії. Нуль власних item IDs або нуль рецептів не є дозволом відкрити чужі результати раніше.

## Політика невизначеності

Підтверджені інфраструктурні модулі завантажуються від початку. Виявлений gameplay, точні ефекти якого не перевірено, отримує `needs_review`/карантин і не стає обов’язковим інгредієнтом. Після встановлення функції предмет переходить до епохи за реальною силою та залежностями. Це інвентаризація й дизайн-аудит, а не підтвердження робочого runtime-блокування.
