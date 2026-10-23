# AIA2 Machine Guard — 0.4.0-alpha

Допоміжний мод для Minecraft 1.21.1, NeoForge 21.1.264 та Java 21.
Скомпільований JAR: `mods/aia2-machine-guard-0.4.0-alpha.jar` у корені репозиторію.
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

## Збирання й перевірка

```sh
./gradlew build
python run_native_smoke.py
```

Потрібен JDK 21. `--offline` працює після попереднього кешування залежностей.
`build` виконує 5 237 перевірок Java-політик без запуску Minecraft.
Mixin мають обов'язкові точки перехоплення; несумісний основний target
спричиняє видиму помилку запуску.

`run_native_smoke.py` запускає два справжні сервери в окремому ignored
`companion/run/world`, перевіряє 41 умову та збереження доказу після перезапуску.
У цьому тесті справжні піч, hopper, Crafter, CraftingMenu і FakePlayer;
тестова ванільна формула моделює рецепт ключа. Це перевірка native механіки,
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
