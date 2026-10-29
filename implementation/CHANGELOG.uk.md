# 0.4.16-alpha — Ad Astra: наземний старт, двигуни й NASA cache/menu

- 20нових optional-квестів епох37/38:3371квест/140глав,96виробничих ключів.
- Чотири двигуни перенесено до Create mechanical crafting5×3 зі збереженням усіх7native units та4міжмодовими компонентами. Старі4простих producer-рецепти замінено; усі623попередні custom entries незмінні,627разом.
- 14функціональних предметів перевірено для38(12піднято),4block floors,28native producer floors і2custom floors. Декоративна калоритова група незмінна.
- Current recipe/output/preview NASA перевіряються до drop і shrink, live-menu guard перевіряє власника/команду/стадію/BEidentity. Нового manufacturing proof тут немає.
- Exact official source1.16.26/MC1.21.1,99SHA-файлів і Astrodux;27scoped core maps/34partial. Binary→commit provenance та fullpack dispatch/JEI/Survival/TPS не заявлені.
- 3351старий non-coordinate payload і623recipe entries збережено;20нових тематичних матеріальних нагород.36старих вузлів переміщено у3главах;1154перетини/0warnings. Нових предметів/текстур0.
- Station split-stack underpayment/ignored placement result і accepted-output NASA proof документовано як наступні окремі задачі; повний0.5 не реліз.

# 0.4.15-alpha — Clibano dependency/residue history

- Current tag/enhancer/residue snapshots і незалежний durable NBT-журнал; старий schema1 paid ledger та його hashes незмінні. Native shapeless1/2input matching, stale Ingredient cache не дозволяє обхід.
- Accepted native residue credit і conversion підтримують definition+quantity history. Прямі/повторні credits denied; один finish може спробувати лише одну одиницю. Legacy/corrupt/changed work зберігається paused без adoption.
- Explicit operator quarantine-residues резервує stock/journal у bounded8NBTbackups; без output/refund/proof, зі збереженням slots/fuel/cooking counters. Cancel progress зберігає residue history. Інсталятор не виконує recovery-команд.
- 233Python/57Node/5237Java/151minimalMC PASS;285нові modeled assertions і14actualNBT.35новихSHAджерел. Fullpack/JEI/Survival/TPS NOT RUN.
- 3351квест/623рецепти/3087itemrewards/390items+PNG/96keys unchanged; нового контенту0. Matching0.4.15JAR/preflight/installer; повний0.5 IN_PROGRESS.

# 0.4.14-alpha — історичні залежності оплачених Forge-ритуалів

- Окремий versioned snapshot поточних item-tag memberships і required/installed enhancer definitions при справжній оплаті. Теги читаються з актуального реєстру; застарілий Ingredient#getItems не є доказом.
- Зміна залежностей, невідомі custom ingredients/effects/conditions або пошкоджений snapshot призупиняють процес зі збереженням NBT. Старі schema1 receipts і hashes збережені; історичні залежності не вигадуються з поточного datapack.
- Перевірка перед запуском, після списання й перед завершенням; зміна під час оплати залишає pending-state з діагностикою. Жодної повторної оплати, автоматичного скасування чи вигаданого refund.
- 18 точних SHA-джерел; 157 нових модельованих умов і 18 actual-NBT перевірок. 230 Python/57 Node/5237 Java/137 minimal-Minecraft assertions PASS; fullpack/JEI/Survival/TPS NOT RUN.
- Усі 3351 квест, 623 рецепти, 3087 item-нагород, координати, 390 предметів/PNG і 96 ключів незмінні. Нових квестів/рецептів/нагород/предметів/текстур 0. Matching JAR та preflight інсталятора оновлено. Повний 0.5 ще IN_PROGRESS.

# 0.4.13-alpha — Clibano controller і виробничі лінії

- 5optional-квестів,3справжні командні process proofs,29етапів карти Forbidden.3351квест/140глав;96ключів,623рецепти,390предметів/PNG збережено. Нових рецептів/предметів/текстур0.
- Canonicalframe→main/26shell ownership і точний GUI target замість nearestPOI; live-menu team/stage guard і захист malformedarrays/staleresidue payload.
- Currentrecipe/physicalenhancer/inputs/results; lane receipts збережені післяrestart. Cold/fuelless progress заборонено; cache підміна другої лінії та component-mismatch merge заблоковані. Actualacceptedoutput+consumption required beforeproof.
- Explicit /aia2clibano status/cancel з bounded8backup; жодного автоматичного скидання світу/прогресу. NativeIOforwarding черезрамку щеTODO.
- 228Python/57Node/5237Java/119minimalMC;776новихmodeledassertions. Fullpack/JEI/Survival/TPS NOT RUN.0.5ще IN_PROGRESS.

# 0.4.12-alpha — Forbidden Forge і ритуальний курс

- 16нових optional-квестів,6native ritual_completed критеріїв і24етапи scopedcore.3346квестів/140глав;96виробничихключів збережено. Новихрецептів/предметів/PNG0;623recipes незмінні.
- ActualForgeowner/currentregistry/inputs/enhancers/output/tier, точний native payment scope та durable paidNBT. Changed/removed/legacy ритуали pause без автоматичного стирання. Essenceinput guard передсписанням. Explicit /aia2forge status/cancel з boundedbackup ібезrefund/output.
- Усі3330старіtask/reward/dependency payloads збережено; одна виправлена block-only іконка.16нових тематичних нагород. Layout1152перетини/0structuralwarnings.
- PASS212Python/55Node/5237Java,297новихmodeledassertions і111мінімальнихMinecraftchecks у2JVM. OptionalForbiddenweaving/JEI/Survival/TPS NOT RUN. Clibano actualmain/Obelisk/transitivegraph щеTODO.
- Matching0.4.12JAR/scripts/installer; повний0.5ще IN_PROGRESS. Докладнийcheckpoint і ручнийacceptance збережено.

# 0.4.11-alpha — EvilCraft core та spirit guards

- 16новихoptional-квестів епох13/19/28:3330квестів/140глав. Усі3314старіnon-coordinatepayloads/dependencies/rewards і621recipe entries збережено.
- EvilCraft scopedcore24етапи; старі8IDs/refs/order збережено. NativeClosure trigger перевіряє справжнє захоплення духа; preparation/observation не оголошуються виробничими доказами.
- 2CreateMechanical5×3формули для SpiritReanimator/SanguinaryAccumulator з усіма9nativeunits і2міжмодовими компонентами.2nativeproducers замінено;623recipes. Новихпредметів/текстур0.
- BloodInfuser rawcache/currentidentity/owner/output; SpiritFurnaceactualoutput; Reanimatorpre-drain/egg/box guard. Keycopies denied. Післяreloadstalecacheчекаєnativekeychange; nativeRNG/paidcostrefund не заявляється.
- 198Python/55Node/5237Java PASS,49Evilmodeled умов;99minimalMC assertions/2JVM/650ticks. OptionalEvil/Forbiddenweaving/JEI/Survival/TPS NOTRUN.
- ForbiddenArcanus exactsource-аудит збережено; ritualguard/corequests щеTODO. Matching0.4.11JAR/installerpreflight/backup;0.5залишаєтьсянезавершеним.

# 0.4.10-alpha — passive guards ProjectE

- Серверні inventory/world-use/packet, armor/Curios і bag/chest/pedestal перевірки фактичного носія або канонічного receiver. Без зміни stacks/ACTIVE/cooldown/knowledge/EMC.
- Незмінне спорядження звіряє атрибути після stage/team/reload. Чужі різні values і дозволені спільні contributors захищені; штатне видалення старих modifiers не фільтрується.
- Окремий suction шлях перевіряє сумку та її кільце. Curios-tablet47 зберігає floor на відкритому меню; table45 не підвищено.
- Block break перевіряє фактичний mainhand tool перед native mineBlock/AOE.
- 190Python/55Node/5237Java PASS;208нових modeled умов;99minimalMC assertions/2JVM/650ticks. Optional ProjectE/Curios weaving, клієнт, Survival/TPS NOT RUN.
- 3314квестів/140глав/621рецепт/390предметів іPNG без зміни payloads чи координат. Нового контенту0. Matching0.4.10JAR/preflight класів і реєстрації, backup installer. Повний0.5 не реліз.

# 0.4.9-alpha — ProjectE та Draconic

- 34нові optional-квести:18ProjectE/16Draconic;3314квестів/140глав. Збережено3280старих payloads і618recipe entries.
- ProjectE core27етапів; Draconic partial23етапи, усі7старих refs/ID збережені. CI633 provenance не підтверджено й не видається за DONE.
- Current team/table45/tablet47, whitelist/EMC/components/current-inventory перевірки normal/quickmove output. CachedEMC0 не видається безкоштовно.
- FuelMapper rebuild після фінальної EMC-мапи, fail-closed error cache, без додаткового очищення знань. TimeWatch перевіряє receiver на кожному bonus tick і відновлює контекст.
- Три fusion-рецепти з незмінними native costs/tier/energy/catalyst/output, по2magitech inputs. Три primary routes замінені,2lossless IO↔relay routes збережено.
- 178Python/52Node/5237Java,90minimalMC assertions/2JVM;66output+22watch modeled assertions. Fullpack optional dispatch/JEI/Survival/TPS:NOT RUN.
- Matching0.4.9JAR, installer preflight і backup. Повний0.5 ще не реліз.

# 0.4.8-alpha — вогняні майданчики та Powah core

- 19 нових optional-квестів:18 Powah і одна підготовча EnderIO-ціль.3280квестів/139глав; старі3261payloads і615recipes збережено.
- Powah:28етапів core-карти за exact6.2.10 source/guide/export; усі8попередні stage IDs/refs незмінні.23core-карти загалом.
- Три Nitro upgrades через Create mechanical5×3; усі native9material units і попередні Spirited generators збережено, по2міжмодових компоненти додано.3дешевіnativeproducers замінено;618recipes.
- Fire Crafting/Fire Water: явно закріплені за командою основи, спільна перевірка до RNG/output/base mutation, current recipe/base/dimension/alloutputs/components/keys/postburnblock.
- Окремий dimension SavedData, mutation invalidation, корумпований ledger не перезаписується. EnderIO getRecipes /reload cache виправлено.
- 166Python/50Node/5237Java;90minimalMC assertions у2JVM;46actual-helper/handler модельованих умов. Optional EnderIO/Powah dispatch/JEI/Survival/TPS:NOT RUN.
- Matching0.4.8JAR/інсталятор і резервні копії. Повний0.5ще не реліз.

# 0.4.7-alpha — EnderIO/Powah, робота над0.5 триває

- 19 нових optional-квестів:18 EnderIO та1 Powah native batch.3261 квест/139 глав; усі3242 попередні quest/task/reward payloads та dependencies збережено.
- EnderIO core-карта за точним8.2.12-beta source/export;22 core-карти загалом. Powah залишається partial: його6.2.10 tag/build provenance підтверджено, невикористаний mod_version5.1.0-alpha виправлено як хибний критерій невідповідності.
- П’ять міжмодових машинних формул:3 Alloy Smelter і2 Energizing Orb;610 попередніх entries незмінні. Виявлено13 дешевих primary producers, включно з5 compressed energized-steel шляхами;86 lossless conversions і4 пізні MA routes збережено.
- Server guards EnderIO task/cache/actual outputs/Crafter/Tank та Powah Orb receiver. Чистий вибір callback-рецепта ізольований від Rod/hopper/startup context; виконання обов’язково перевіряється. Native smelting proxies звіряються з canonical original recipe.
- Два нові team-bound production proofs після реальної витрати входів і вставлення виходу;8 правил/11 recipe IDs, старий SavedData schema1 збережено. Powah фінальний Rod FE debit після повернення fillEnergy окремо не вимірюється.
- Відкритий ownerless EnderIO Fire Crafting описано явно; його сліпе вимкнення зламало б grain progression. Повний optional-mod dispatch/JEI/Survival/TPS не тестувалися.

# 0.4.6-alpha — MI/Oritech та серверні виробничі маршрути

- 30 нових змістовних optional-квестів:15 MI та15 Oritech;3242 квести/138 глав. Усі3212 попередні payloads/dependencies, крім координат, збережено.
- Дві основні карти за exact MI2.5.10/Oritech1.2.13 source/wiki/export.11 нових native action контрактів,97 загалом; форма мультиблока не видається за доказ виробництва.
- Чотири машинні міжмодові формули:3 MI Assembler і1 Oritech Assembler. Шість дешевих native producers замінено;606 попередніх custom entries незмінні. Початкові матеріальні витрати збережено.
- MI direct-list/cached crafter, native conversion provenance та Replicator отримали перевірки власника/рецепта/виходу. Реплікація ключів заборонена навіть після completed48.
- Oritech canonical recipe identity перевіряється до нормального процесу; окремі fluid commits і nine-small-dust conversion захищені. Atomic native fresh-lookup RF reset залишається явним обмеженням.
- Roots mutation виправлено: повний склад і щоденний noon; інші native block/dimension/effect умови та powder cost збережено.
- API4,96 ключів,390 предметів/PNG, командний SavedData і попередній FTB-прогрес збережено. Доступні перевірки й межі у docs/AIA2_0.4.6_CHECKPOINT.uk.md; fullpack/JEI/Survival/TPS ще не запускалися.
- Це перевірюваний проміжний блок роботи над0.5, не завершений реліз0.5.

# 0.4.5-alpha — Roots/AA та split Apothic core

-45новихквестів(12Roots,11AA,12Enchanting,10Spawners),4основнікарти;3212квестів/138глав. Попередні3167ID/deps/rewards збережено.
-2нові team-bound Roots proofs після фактичного emptyAltar;6загалом,старийSavedData schema1 збережено. Нативне незавершене restart-відновлення не заявляється.
-3точкові міжмодові AAрецепти:Manasteel,NatureAuraInfusedIron,Mekcircuit.603старіcustomJSONнезмінні;3nativeproducers замінено,3reset routesзбережено.
-Чинні руни Apotheosis замість standalone vanilla Spawner modifiers;6item/15recipefloors іnativeuse guard перед застосуванням уmain/offhand.
-Ранній optional гербарій виправлено на відновлювані підготовчі квіти; ранній rare-loot Charged Focus маршрут збережено.3нові native-source шляхи підтверджено без штучних рецептів.
-126Python/50JS/5237Java PASS;Roots49/Spawner15model;49мінімальнихMCперевірок у2JVM на0.4.5. Fullpack/JEI/Survival/TPS NOT RUN.

# 0.4.4-alpha — проміжне виправлення Roots, робота над0.5 триває

- Закрито підтверджений шлях виконання компонентного рецепта ступки Roots поза машинним тиком. Недоступний рецепт зупиняється до витрати інгредієнтів.
- Новий точковий companion hook та перевірка відповідного JAR в інсталяторі; API4, дані команд і ключів збережено.
- Snapshot захищає всі3145 опублікованих квестів і136глав. Повний Roots/FTB/JEI/Survival тест залишається потрібним.
- Додано22змістовні квести:12Apotheosis і10Petroleum;17nativeactionконтрактів і3custompurity advancements. Дві основні карти завершено, ще43часткові.
- Дві старі Petroleum-цілі виправлено diesel/naphtha→diesel_sulfur без зміни taskID. Нативні LPG,компонентні Gems і sulfurousdieselbucket отримали точні source-докази без нових рецептів.
- 117Python/50JS/5237Java PASS;49native у2JVM на0.4.4. Усі603рецепти та3145попередніID/нагороди збережено.

# 0.4.2.1-alpha — cached Fusion і джерела матеріалів

## 0.4.3-alpha — 2026-10-25, продовження розробки0.5

- Додано84квести:49nativeaction цілей і35навчальних craft/setup завдань. Усього3145квестів/136глав.
- Завершено10додаткових core-карт; загалом13complete/45partial із58досліджених модів. Джерела exact-version збережено з SHA.
- Нативні критерії охоплюють Totemic/Occultism, NA, Ars/Botania, IE/PNC, IntegratedDynamics/Tunnels/Terminals; inventory-OR fallback відхиляється.
- Два Occultism miner-докази слухають чинні рецепти AIA2; початкову книгу Iron замінено на copper із збереженням quest/task IDs.
- Закрито3creativeManaTablet producers;1postgame TerraPlate рецепт додає Creative Essence, зберігає компоненти й звичайні планшетки.603рецепти,602старі JSON збережено.
- Новий Guard0.4.3: component-aware player inventory/accessories і pool exchange; native output і live-team checks; API4 збережено. Прямі сторонні capability-виклики залишені в обмеженнях.
- Snapshot усіх3061опублікованих квестів і136глав захищає також нові v5 IDs. Нові84нагороди тематичні; попередні2793предметні нагороди не змінено.
- Перевірено110Python/50JS/5237Java,22guard-model assertions,49actualMinecraft assertions у2JVM на0.4.3. Повний модпак/JEI/TPS не тестовано.
- 0.5 залишається незавершеною; стан і наступні дії в docs/AIA2_0.5.0_PROGRESS.md.


- Усунуто підтверджений обхід кешованого Draconic Fusion: дозвіл перевіряється до активного тіку, зокрема для packet-start/byKey/NBT кешів. Заборонене завдання скасовує заряджання інжекторів без витрати інгредієнтів.
- Два optional-завдання тепер використовують реальні канонічні матеріали після AlmostUnified, з тими самими quest/task/reward IDs: порошок Create замість EnderIO-дубліката та нікель IE замість Oritech-дубліката.602рецепти, зокрема569старихJSON, не змінено.
- Додано перевірені source-докази11нативних джерел: Amadron, wrapper-рецепти IE, implicitEternalSingularity, церемонія Totemic, nativeBaykokdrop, аура при розмноженні, кров у пробірці та Hephaestusритуал. Нових рецептів для цих предметів не додано.
- Уточнено аудит вкладених output.resource/item/baseRecipe; rawID у реєстрі більше не видається за доступний у Survival дублікат. Версії та SHA джерел перевіряються автоматично.
- Окремі DE contract/handler tests перевіряють16умов; liveDEmoddispatch не запускався. Попередні49native-перевірок лишаються результатом0.4.2.

# Розробка 0.5 — перевірений контентний milestone на runtime0.4.2

- Додано277цілей у всіх48епохах:112технічних,150магічних/пригодницьких,9післяігрових,4справжні виробничі докази та2виправлення базових ліній.
- Усі2784попередні квести, task/reward/dependency ID та569recipeJSON збережено. Разом3061квест/136глав/602рецепти;96виробничихключів не замінено.
- Генератор координат працює з графом і візуальними обмеженнями фіналу. На тій самій старій когорті:1679→1129перетинів, -32.22%довжини;0накладань/зворотнихліній.
- Перевірено2793предметні нагороди; змінено2780payload(2511старих);48команд збережено. Матеріали тематичні, без машин, ключів чи Creative.
- 33адресні рецепти/29цілей,26старих native-шляхів замінено. Creative Essence із Mystical Agradditions отримується після48завершень;22рецепти її витрачають. Закрито всі3джерела Creative Mana Pool.
- 54моди задокументовано у56записах;3повні основні карти(Create/Mek/AE2 по14етапів),51часткова;386перевіренихSHAфайлів. Невірний exact-version статус Powah виправлено.
- Аудит42064рецептів/14615loot-таблиць не створював автоматичних рецептів для невідомих або boss-only предметів.35безявногоджерела+49nativecontext+1implicitcodec потребують подальшого дослідження.
- Перевірено50Node/85Python/5237Java/49nativeassertions та повторювану генерацію. Повний інстанс/Survival/JEI/UI/TPS ще не перевірено. Оновлення0.5не оголошено повністю завершеним.

# 0.4.2-alpha — проміжна native-інтеграція для розробки 0.5

- Додано чотири нативні виробничі докази: андезитовий сплав, латунь, infused/reinforced alloys. Записи виникають після успішного процесу та витрати входів і належать FTB-команді.
- Латунь епохи10 враховує рецепт AIA2 без нагріву; стандартний heated-рецепт потребує пізнішого Blaze Burner.
- Окремий SavedData переживає рестарт і /reload; помилка пошуку відкликає проєкції доказів, а не залишає старі дозволи іншої команди.
- Нативний JAR/API4 та FTB hotfix збережено. Перевірено5237 Java assertions,9Node-тестів script40 і49 перевірок у2справжніх JVM. Це ванільна тестова формула; actual Create/Mek у повному інстансі ще не запускались.
- Квести, карти модів, координати та баланс0.5 інтегруються окремим наступним блоком;0.5не оголошено готовим релізом.

# 0.4.1-alpha

- FTB team-data lookup передається через єдиний типізований Java-метод, який обирає public Entity overload та актуальне членство гравця. UUID overload не викликається з UUID гравця.
- Окремий регресійний тест перевіряє межу Java/Rhino, перемикання команд та відмову за несумісного API. Потрібен спільний новий JAR і скрипти.
- Створено постійні PLAN/PROGRESS для відновлення розробки 0.5 між сесіями. Поглиблення контенту не оголошено завершеним.

# 0.4.0-alpha

- Журнал відхиляє масиви замість словників команд, щоб JSON не губив записи з UUID-ключами. Незавершений оплачений перехід також проходить перевірку порядку.
- Повторна перевірка виробничих доказів не надсилає однакових advancement-команд кожні 40 тіків; авторитетним джерелом залишається native SavedData.

- Виправлено підтверджені помилки UUID: `uuid()` викликав властивість як функцію, а `getUUID()` прихований remap KubeJS. Новий типізований `syncPlayer(ServerPlayer, team, completed)` отримує UUID всередині Java.
- Machine Guard вимагає API 4, починає ініціалізацію із серверного тіку, очікує готовності FTB із обмеженим backoff, показує фазу та причину помилки. Операторська `/aia2 guard retry` повторює ініціалізацію після усунення причини; required-режим збережено.
- ProjectE використовує `RhinoLongMapBridge.putValue` з однією примітивною сигнатурою замість неоднозначного fastutil `put`. Помилка конфігурації/конвертації очищає EMC і залишає навчання закритим, не приховуючи причину.
- Додано 96 окремих технологічних і магічно-дослідницьких ключів із рецептами shaped, Create mixing/compacting та Mekanism metallurgic infusing. Нативні записи виробництва створюються після витрати матеріалів і зберігаються у SavedData; `/give` та отримання предмета їх не створюють.
- Наступний незавершений перехід потребує двох обов'язкових гілок, двох виготовлених ключів і FTB-фіналу. `/aia2 key` витрачає два ключі та попередній артефакт; стадія зберігається лише після підтвердження фінальних умов. Першу епоху можна почати без попереднього ключа.
- Завершені старі епохи, ID квестів, старі артефакти й журнал команд не скидаються. `/aia2 recover` зберігає попередню платну формулу й не підвищує епоху.
- Додано 190 змін нативних рецептів для 170 цілей у 22 просторах імен, використовуючи наявні компоненти. Збережено вісім безвитратних конверсій і попередні 283 рецепти AIA2. Разом із новими ключами — 569 рецептів та 48 серверних формул гравіювання.
- Додано 176 авторських квестів і 96 перевірок виробництва ключів. Загалом 2784 квести, з них 2688 змістовних без 96 старих ручних цілей. Збережено 48 епох, разом 130 глав. Додано шосту групу «Автоматизація»; нові поглиблені курси необов'язкові для збереження старої прогресії.
- Додано 96 унікальних текстур ключів і піктограму автоматизації: загалом 390 власних предметів, моделей і прозорих PNG. Додано відтворюваний генератор ресурсів.
- Оновлено інсталятор для спільного встановлення API 4 і скриптів, перевірки комплектності та безпечної міграції власного JAR. Резервування, злиття сторонніх квестів і відкат збережено.
- Додано перевірки відкладеної ініціалізації, повторних спроб, стану guard, двох ключів, походження, EMC і справжнього Java/Rhino/fastutil-виконання. Нативний smoke-test виконав 41 перевірку у двох серверних JVM, включно з відновленням виробничого доказу з диска. Фікстура використовує ванільний рецепт; повні KubeJS/FTB та модові машини залишаються окремою перевіркою. Межі наведено в `companion/verification-report.json`.

Повна Minecraft-збірка, необов'язкові Create/Mekanism/AE2 перехоплення, JEI, клієнтські ресурси й TPS потребують окремої перевірки у грі. Ця alpha не означає завершення всіх сторонніх адаптерів.

# 0.3.0-alpha

- Виправлено readonly `global` у KubeJS/Rhino: спільні контейнери створюються на startup, сервер змінює вкладені властивості. Потрібен повний перезапуск.
- Збережено всі старі ID квестів, завдань, нагород, ключів і формат командного журналу.
- Додано 1840 авторських модових квестів, 192 виробничі завдання й 48 фінальних випробувань. Разом 2512; 96 старих ручних цілей не враховано як новий змістовний контент.
- Уведено п’ять груп, окремі модові глави, реальні огляди блоків, бої, виміри, статистику й досягнення поряд із ресурсними завданнями.
- Додано 192 компоненти й нативні рецепти; загалом 283 рецепти та 48 серверних формул ключів. Узгоджено недоступні дублікати матеріалів AlmostUnified.
- Наступний ключ потребує нового випробування до списання інвентарю. Уже завершені старі епохи зберігаються.
- Додано 293 прозорі PNG і моделі, включно з 48 різними силуетами ключів, генератор і каталог ресурсів.
- Розширено Machine Guard перевірками рецептів у тіку, кешів Mekanism, Basin Create, Molecular Assembler і термінала AE2; додаткові адаптери описано у звіті сумісності.
- Інсталятор спочатку резервує всі оригінали, виконує атомарні заміни та відкат, зберігає сторонні квести/групи й мігрує тільки власні старі JAR.
- Додано справжній Rhino-тест, перевірки контенту/графа/реєстру/ресурсів, транзакційні сценарії інсталятора й розширені Java-тести.

Повна збірка у Minecraft, TPS і всі сторонні механіки ще потребують приймального тестування. Це не позначення завершеної сертифікації.
