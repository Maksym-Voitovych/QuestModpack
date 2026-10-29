# Station adapter — наступний незавершений блок

Статус: **TODO реалізації; source-review виконано 2026-10-30**.
Цей документ не означає виправлення коду станцій або тест повного клієнта.
Pin Ad Astra: `45abf0ec05ea837c3df457f42ae440b6675e9cf0`, version properties
1.16.26/MC1.21.1; відповідність встановленого binary цьому commit не доведена.

## Підтверджені джерелами проблеми

У замороженому [SpaceStationRecipe](../../content/research/evidence/ad_astra_core_v6/official/src/main/java/earth/terrarium/adastra/common/recipes/SpaceStationRecipe.java):

- `matches(RecipeInput, Level)`, рядки49–60, незалежно підсумовує всі слоти
  для кожної вимоги. Overlapping ingredients можуть повторно використати
  ту саму одиницю для кількох вимог.
- `consumeIngredients(Player, Level)`, рядки83–99, списує з першого відповідного
  слота й робить `break`. Для вимоги64 зі стеків1+63 списується лише1.
- Creative/Spectator обходять оплату. Такий виклик не може підтверджувати
  survival-виробництво навіть при збереженні зручності native поведінки.

У [packet handler](../../content/research/evidence/ad_astra_core_v6/official/src/main/java/earth/terrarium/adastra/common/network/packets/ServerboundConstructSpaceStationPacket.java)
`Type.handle(packet): Consumer<Player>`, рядки88–94, результат
`StructureTemplate.placeInWorld(...)` ігнорується. Навіть `false` веде до
реєстрації станції, spawn location, teleport і Cadmus claims.

Native `StructureTemplate.placeInWorld` може повернути `true`, навіть коли
окремі `setBlock` відхилені. Сам boolean не доводить повністю побудовану станцію.
У поточному runtime шість `ad_astra:space_station/*` recipe floors=0;
dimension guard37/38 спрацьовує під час teleport після побудови. Потрібна
явна перевірка destination-stage і синхронізованої live-команди до оплати/placement.

## План обмеженого адаптера

Обгорнути повернений `Consumer<Player>` у точному `Type.handle` одноразовим
`try/finally` scope, не прив'язуючись до synthetic `lambda$handle$0`.
Зв'язати конкретного ServerPlayer, поточну команду, target world/chunk,
recipe object/generation, структуру та inventory snapshot.

План оплати має розподіляти capacity глобально між усіма вимогами й слотами,
з обмеженнями розміру й current tag membership. Greedy matching може дати
помилкову відмову при альтернативних інгредієнтах; незалежні суми допускають
подвійне використання. Після плану потрібні точні split-stack debits з перевіркою
refs/count/components. Не змінювати існуючі station SavedData чи прогрес.

Реєстрацію/teleport/claims не допускати після відхиленого placement. Визначити
чесну межу доказу accepted structure operation окремо від повноти всіх block writes.
Якщо оплата залишиться до placement, явно зберегти відсутність автоматичного
refund/rollback; не обіцяти атомарну транзакцію.

Стабільні точки: `SpaceStationRecipe.hasIngredients(Player,Level,SpaceStationRecipe)Z`,
`consumeIngredients(Player,Level)V`, `SpaceStationHandler.constructSpaceStation(ServerPlayer,ServerLevel,Component)V`,
`StructureTemplate.placeInWorld(ServerLevelAccessor,BlockPos,BlockPos,StructurePlaceSettings,RandomSource,int)Z`.
Один production call конструктора знайдено в цьому packet consumer.

## Необхідні регресії

- 64 із1+63 сплачує64; із63 не будує; overlapping вимоги не рахують одиницю двічі.
- Перестановка альтернатив не викликає greedy false negative.
- Creative/Spectator/fake player/несинхронізована команда/закрита орбіта не дають proof.
- Recipe/tag reload, підміна stack refs/count/components/team, повторний вхід і exception cleanup.
- Missing/empty structure та placement=false не реєструють і не телепортують.
- Placement=true із нульовими accepted writes не називається повним будівництвом.
- Чужий/unscoped constructor callback і повторний callback не позичають proof.
- Наявні станції та всі старі SavedData збережені; installer не виконує recovery/reset.

Перед кодингом перевірити exact compiled selectors на наданому JAR, якщо він
з'явиться. За його відсутності продовжувати source/model реалізацію з явними
межами, не оголошуючи fullpack weaving або успішний клієнт.
