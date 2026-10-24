# AIA2 Machine Guard — 0.4.2-alpha

Допоміжний мод для Minecraft 1.21.1, NeoForge 21.1.264 та Java 21.
Скомпільований JAR: `mods/aia2-machine-guard-0.4.2-alpha.jar` у корені репозиторію.
Не залишайте одночасно дві версії цього моду в інстансі.

Мод перехоплює стандартний серверний `BlockEntityTicker.tick` перед виконанням
машини. Блок і рецепт перевіряються за прогресом команди-власника; власник
зберігається в `BlockEntity.getPersistentData()` під ключем `aia2_guard_owner_team`.
Відвідувач не може перепризначити вже належну іншій команді машину.
До підтвердженої ініціалізації staged-машини залишаються закритими. Невідомі
модові блоки отримують карантин 100; ванільні блоки без правила доступні.

Серверні адаптери охоплюють vanilla crafting 2×2/3×3, shift-click, Crafter,
контекстні пошуки RecipeManager, Create Basin mixing/compacting,
Mekanism CachedRecipe та Robit, AE2 Molecular Assembler і crafting terminal.
Виправлення 0.4 використовує точний JVM-дескриптор `getRecipeFor` із `RecipeHolder`:
попередній селектор за назвою пропускав кешований шлях ванільної печі.
Реальне виконання optional-адаптерів Create/Mekanism/AE2 ще треба перевірити у збірці.

Це не універсальне перехоплення всіх внутрішніх API модів. Переміщені
конструкції, сутності без адаптера, прямий обмін capabilities, пасивні
Curios/броня, сторонні crafting-меню та невідомі ритуальні кеші потребують
окремої перевірки. Не слід вважати всі обходи автоматично закритими.

## Міст KubeJS

Клас: `Java.loadClass('ua.aia2.guard.Aia2MachineGuard')`; `apiVersion()` повертає 4.
Порядок завантаження: `clearRuntime()`, `setRulesJson(json)`,
`setItemRulesJson(json)`, `configureKeyRulesJson(json)`, всі командні записи,
синхронізація гравців, тоді `setReady()`. Порожня/непідтверджена ініціалізація
не повинна відкривати машини. `isReady()` показує стан усіх частин мосту.

`syncPlayer(ServerPlayer player, String team, int completed)` отримує UUID
всередині Java, обходячи відмінності KubeJS `getUuid` / `getUUID` / `uuid`.
FakePlayer не може підтвердити гравця або отримати staged-крафт.
`setTeamProgress(team, completed)` оновлює прогрес команди.
Інші API: `getOwner`, `setOwner`, `mayCraft`, `mayProduce`, `getDeniedTicks`.
Перед staged-крафтом публічний FTB Teams API перевіряє поточне членство;
помилка API не дозволяє використати стару командну прив'язку.

`FtbQuestBridge.getTeamData(questFile, ServerPlayer)` явно вибирає публічний
`QuestFile.getOrCreateTeamData(Entity)`. Це обходить неоднозначність Rhino
між Entity/UUID/Team без підміни UUID гравця UUID команди. Повернення `null`
означає, що FTB Teams ще не підготував команду; помилки API зберігають причину
в описовому винятку. Допоміжний клас не потребує FTB залежності для компіляції.

`RhinoLongMapBridge.putValue(map, key, long)` має єдину сигнатуру та потрібен
ProjectE-мосту: Rhino неоднозначно вибирає між fastutil `put(Object,long)`
та сумісними boxed/erased перевантаженнями навіть після `Long.valueOf`.

## Два ключі та доказ виготовлення

`configureKeyRulesJson` приймає масив правил із полями `recipeId`, `output`,
`epoch` (1–48), `branch` (`tech` / `arcane`) та `serializer`.
Підтримуються `minecraft:crafting_shaped`, `create:mixing`, `create:compacting`
і `mekanism:metallurgic_infusing`.

`setTeamKeyReady(team, epoch, branch, ready)` дозволяє виробництво після
перевірки обов'язкової гілки FTB Quests серверним скриптом.
`hasProductionProof(server, team, epoch, branch)` читає незалежний доказ
фактичного завершення рецепта. Доказ виникає лише в native completion hook:
після споживання інгредієнтів гравцем, успішного Crafter, успішної
несимульованої операції Basin або `CachedRecipe.finishProcessing` Mekanism.
Підбирання, імпорт, `/give` та сама наявність предмета доказу не створюють.
Гравець у Creative не отримує доказ через звичайний crafting hook.

Докази зберігаються як SavedData у `<world>/data/aia2_key_production_v1.dat`,
окремо для команди, епохи й гілки. `clearRuntime()` очищає тимчасові правила
та дозволи, але не ці дані. Фінальний скрипт перевіряє обидва докази,
обидва фізичні ключі та обов'язкові квести; одна гілка не замінює іншу.

## Окремі докази виробничих процесів

`ProductionMilestoneBridge` не підміняє 96 ключів і не використовує їхній
SavedData. Чотири правила у `kubejs/config/aia2_mechanics.json` підтверджують
андезитове змішування (епоха 4), латунь (10), Infused Alloy (16) і Reinforced
Alloy (23). Є шість точних recipe routes: два андезитові, два латунні та два
Mekanism. Рецепт `aia2:bootstrap/epoch_10_1` без нагріву зараховується для
латуні в епосі 10; стандартний heated-рецепт лишається пізнішою альтернативою,
оскільки Blaze Burner у цій збірці відкривається тільки в епосі 15.

Єдині сигнатури: `configureJson(String rulesArray)`, `isConfigured()` та
`hasProof(MinecraftServer, String team, String id)`. Доказ записується після
успішного несимульованого завершення Basin або `CachedRecipe.finishProcessing`,
якщо власник машини має відповідний доступ. Точні recipe ID, serializer та
вихід звіряються із завантаженими рецептами. Зберігання:
`<world>/data/aia2_mechanics_v1.dat`, окремо від `aia2_key_production_v1.dat`.
Очищення оперативних правил не скидає жодного з двох журналів.

Скрипт `40_mechanics.js` проєктує збережені командні докази на чотири
advancements `aia2:mechanics/*` із `minecraft:impossible`. Наявність предмета,
`/give`, відкриття GUI або огляд машини такого доказу не створюють. Зміна
команди чи помилка читання доказів відкликає всі власні проєкції до показу
помилки. Повторне опитування без змін не надсилає advancement-команди.

## Виконання перевірок

```sh
./gradlew build
python run_native_smoke.py
```

Потрібен JDK 21. `--offline` працює після попереднього кешування залежностей.
`build` виконує 5 237 перевірок Java-політик без запуску Minecraft.
Mixin мають обов'язкові точки перехоплення; несумісний основний target
спричиняє видиму помилку запуску.

На версії 0.4.2 `run_native_smoke.py` запустив два справжні сервери в окремому ignored
`companion/run/world`, перевірив 49 умов та збереження обох незалежних типів
доказів після перезапуску. Міст FTB перевіряється окремим справжнім Rhino-тестом.
У цьому тесті справжні піч, hopper, Crafter, CraftingMenu і FakePlayer;
тестова ванільна формула моделює рецепт ключа та виробниче спостереження. Це перевірка native механіки,
не всіх 96 реальних KubeJS-рецептів. Тест вмикається лише explicit JVM-параметром,
маркером runner та dev-режимом. Він не торкається інстансу чи світів користувача.
Dev-режим Minecraft автоматично погоджується з EULA; runner не записує `eula.txt`.

`native-smoke-report.json` містить фактичні результати, а
`verification-report.json` — SHA256 JAR, версії та межі перевіреного.
Повний запуск модпаку, реальні рецепти Create/Mekanism, FTB/KubeJS lifecycle
та вимірювання TPS потребують додаткового тесту у встановленій збірці.

Після встановлення перевірте `/aia2 status`, неможливість витрати сировини
машиною майбутньої епохи, обидва ключі відповідних поточних гілок,
невизнання `/give` як виробництва та збереження доказів після рестарту.
Окремо перевірте Basin у simulation/real режимах, Metallurgic Infuser,
зміну команди, unowned-машини та AE2 автоматизацію. Не видавайте готові
ключі через Creative під час позитивного тесту переходу.

## Hotfix0.4.2.1 — кешований Draconic Fusion

У DE3.1.4 команда GUI `startCraft()` може зберегти рецепт поза контекстом
звичайного тикера. Відновлений із NBT рецепт також читається через `byKey`.
Самого перехоплення `RecipeManager.getRecipeFor` тому недостатньо для
перевірки післяігрових рецептів під час роботи вже активної машини.

Новий optional `DraconicFusionCoreMixin` перевіряє реальний кешований рецепт
на початку кожного активного серверного `tick()`. Недозволений процес
скасовується нативним `cancelCraft`: він зупиняє потребу інжекторів в енергії,
але не зменшує стеки каталізатора чи компонентів і не змінює збережений
прогрес команд/ключів. Після відкриття епохи гравець може запустити процес знову.

Перевірено точний pinned source, дві Python-регресії з16виконаними
assertions справжнього mixin-handler і GuardPolicy у модельному хості,
та складання з5237Javaassertions. Це не запуск установленого Draconic
Evolution: optional Mixin binding та реальні інжектори потрібно перевірити
в повному модпаку.49ванільних серверних перевірок належать версії0.4.2.
Докази: `implementation/draconic-cache-v5-audit.json` у корені проєкту.
