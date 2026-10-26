# AIA2 0.4.8-alpha — вогняні майданчики та Powah

Проміжний етап роботи над0.5; база d756a9a. Повний реліз0.5 не завершено.

| Показник | До | Після |
|---|---:|---:|
| Квести /глави |3261 /139|3280 /139|
| Custom native recipes |615|618|
| Core-карти /partial моди |22 /38|23 /37|
| Предмети /PNG /моделі |390 /390 /390|390 /390 /390|

Додано18 змістовних Powah-квестів і одну підготовчу EnderIO-ціль. Powah має28етапів дослідженої core-карти; усі8попередні stage IDs/refs збережено. Квести пояснюють генерацію,36-блоковий Reactor, ресурси/охолодження, канали, персональне заряджання, cards і межі автоматизації. Inventory/observation не доводять FE або робочу структуру; наявний Blazing native proof збережено.

Три Nitro upgrades використовують Create mechanical5×3: Furnator/Thermo/Solar. Кожен зберігає всі9native матеріальних одиниць, попередній Spirited generator і додає лише2перевірені магічно-технічні компоненти. Скан42064ефективних рецептів підтверджує3source producers; їх замінено. Предметні завдання mechanical outputs не вимагають vanilla only_from_crafting.

Fire Crafting і Fire Water захищено спільним native spawn edge до RNG, предметів і зміни основи. Робоча основа явно закріплюється за командою жестом sneak+кресало по верхній грані. Це НЕ автоматичне визначення власника полум’я. Звичайне запалення після claim запускає штатну механіку; автоматизація використовує команду основи. Старі майданчики після оновлення потрібно закріпити один раз.

Перевіряються current canonical recipe, основа/вимір, усі можливі outputs/components, заборона ключів і post-burn block stage. Реєстр SavedData окремий для вимірів; заміна основи відкликає власника. Корумповані дані блокуються без перезапису. EnderIO cache після/reload виправлено за поточною генерацією RecipeManager.

Збережено всі3261попередні quest/task/reward payloads і залежності,615recipe entries,48епох і96ключів. [Доказ](../implementation/fire-powah-preservation-v5.json). Нових предметів/текстур0; нових предметних reward entries20, старі нагороди незмінні.

166 Python tests,50 Node tests,5237 Java assertions іJDK21build:PASS.
1162runtimeфайли byte-identical після повної окремої генерації PYTHONHASHSEED73.
Layout139глав:0структурнихпопереджень і1143перетини, як у0.4.7. Доставка фіксується в release-report/PROGRESS. Модельований exact-helper/handler suite:46умов; мінімальний Minecraft0.4.8:90умов,2JVM,650ticks і restart SavedData. Optional EnderIO/Powah dispatch, JEI/UI, Survival і TPS: NOT RUN. Native spawn не доводить прийняття ItemEntity світом; нового production proof тут немає.

[Приймальні сценарії](testing/FIRE_WORKSITE_ACCEPTANCE.uk.md) · [Аудит](../content/audit/v5-fire-worksites.json).
Наступне: ProjectE/Draconic core, решта37partial/невивчених модів, старі обов’язкові лінії48епох та повний ігровий приймальний тест.

ZIP CRC/повнийmanifest і1162runtimehashes PASS. Запакований installer:dry-run0записів; тестове оновлення0.4.7→0.4.8 резервуєстарийJAR і зберігаєsyntheticworld/fireledger/стороннійквест. [Звіт](../implementation/fire-powah-package-install-v5.json).
