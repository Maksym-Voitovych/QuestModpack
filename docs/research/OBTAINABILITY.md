# Перевірені джерела без звичайного crafting-рецепта

Нативне джерело, торгівля або boss-drop не означають пропущений рецепт.
Наведені висновки перевірені за конкретними версіями й SHA файлів;
повне Survival-проходження та сторонні overrides ще не тестувалися.

[Структуровані докази](../../content/audit/v5-source-gaps-magic.json).

## `totemic:infused_flute`

Статус: `source_verified_native_path`; версія: 1.21.1-0.12.18.

Церемонія totemic:flute_infusion замінює звичайну flute на infused_flute. Обробляються предметні сутності в радіусі 6 і відповідні слоти інвентарів гравців поруч. Це нативна церемонія, не пропущений звичайний рецепт.

- https://github.com/TeamTotemic/Totemic/blob/1a253b29815842aa4359d6118b8cd84cce3048a1/gradle.properties — SHA перевірено
- https://github.com/TeamTotemic/Totemic/blob/1a253b29815842aa4359d6118b8cd84cce3048a1/src/main/java/pokefenn/totemic/ceremony/FluteInfusionCeremony.java — SHA перевірено
- https://github.com/TeamTotemic/Totemic/blob/1a253b29815842aa4359d6118b8cd84cce3048a1/src/main/java/pokefenn/totemic/init/ModContent.java — SHA перевірено
- https://github.com/TeamTotemic/Totemic/blob/1a253b29815842aa4359d6118b8cd84cce3048a1/src/main/java/pokefenn/totemic/init/ModItems.java — SHA перевірено
- https://github.com/TeamTotemic/Totemic/blob/1a253b29815842aa4359d6118b8cd84cce3048a1/src/main/resources/assets/totemic/patchouli_books/totempedia/en_us/entries/ceremonies/flute_infusion.json — SHA перевірено

## `totemic:baykok_bow`

Статус: `source_verified_native_path`; версія: 1.21.1-0.12.18.

Baykok екіпірується baykok_bow у MAINHAND і викликає setGuaranteedDrop(MAINHAND). Лук є гарантованим нативним equipment-drop боса; звичайна loot-table містить інші предмети, тому статичний аналіз лише loot JSON його пропускає. Не створювати побутовий рецепт цього boss-only предмета.

- https://github.com/TeamTotemic/Totemic/blob/1a253b29815842aa4359d6118b8cd84cce3048a1/gradle.properties — SHA перевірено
- https://github.com/TeamTotemic/Totemic/blob/1a253b29815842aa4359d6118b8cd84cce3048a1/src/main/java/pokefenn/totemic/entity/Baykok.java — SHA перевірено
- https://github.com/TeamTotemic/Totemic/blob/1a253b29815842aa4359d6118b8cd84cce3048a1/src/main/java/pokefenn/totemic/init/ModItems.java — SHA перевірено
- https://github.com/TeamTotemic/Totemic/blob/1a253b29815842aa4359d6118b8cd84cce3048a1/src/generated/resources/data/totemic/loot_table/entities/baykok.json — SHA перевірено

## `naturesaura:birth_spirit`

Статус: `source_verified_native_path`; версія: 41.10.

ItemBirthSpirit реєструє BabyEntitySpawnEvent. За server-side народженням від player-caused breeding та аурою не менше 1200000 у радіусі 30 біля ParentA виникає 1–3 Birth Spirit; списується 800 аури за одиницю. Відсутність crafting JSON очікувана.

- https://github.com/Ellpeck/NaturesAura/blob/70b93d37037f3559312834f0f42e824431090b64/gradle.properties — SHA перевірено
- https://github.com/Ellpeck/NaturesAura/blob/70b93d37037f3559312834f0f42e824431090b64/src/main/java/de/ellpeck/naturesaura/items/ItemBirthSpirit.java — SHA перевірено
- https://github.com/Ellpeck/NaturesAura/blob/70b93d37037f3559312834f0f42e824431090b64/src/main/java/de/ellpeck/naturesaura/items/ModItems.java — SHA перевірено

## `forbidden_arcanus:blood_test_tube`

Статус: `source_verified_native_path`; версія: 2.6.1.

Під час LivingDamageEvent.Post від PLAYER_ATTACK по неблеклістованій сутності порожня TEST_TUBE в offhand замінюється BLOOD_TEST_TUBE. Потім storage отримує 20×фактична шкода есенції крові. Це взаємодія у світі, а не окремий crafting recipe.

- https://github.com/stal111/Forbidden-Arcanus/blob/34f83feb76204fd773e1d2e1d69ecc5b2f2bb933/gradle.properties — SHA перевірено
- https://github.com/stal111/Forbidden-Arcanus/blob/34f83feb76204fd773e1d2e1d69ecc5b2f2bb933/neoforge/src/main/java/com/stal111/forbidden_arcanus/common/event/EntityEvents.java — SHA перевірено
- https://github.com/stal111/Forbidden-Arcanus/blob/34f83feb76204fd773e1d2e1d69ecc5b2f2bb933/neoforge/src/main/java/com/stal111/forbidden_arcanus/core/init/ModItems.java — SHA перевірено
- https://github.com/stal111/Forbidden-Arcanus/blob/34f83feb76204fd773e1d2e1d69ecc5b2f2bb933/neoforge/src/main/java/com/stal111/forbidden_arcanus/common/item/BloodTestTubeItem.java — SHA перевірено

## `forbidden_arcanus:eternal_stella`

Статус: `source_verified_native_path`; версія: 2.6.1.

Eternal Stella створюється реальним Hephaestus ritual eternal_stella: diamond як центральний вхід,3XPetrified Orb та Stellarite Piece; вимога мінімум Forge Tier3. Ритуал міститься у власному datapack registry мода, а не у RecipeManager/RecipeSerializer export.

- https://github.com/stal111/Forbidden-Arcanus/blob/34f83feb76204fd773e1d2e1d69ecc5b2f2bb933/gradle.properties — SHA перевірено
- https://github.com/stal111/Forbidden-Arcanus/blob/34f83feb76204fd773e1d2e1d69ecc5b2f2bb933/neoforge/src/main/java/com/stal111/forbidden_arcanus/data/hephaestus_forge/rituals/ModRituals.java — SHA перевірено
- https://github.com/stal111/Forbidden-Arcanus/blob/34f83feb76204fd773e1d2e1d69ecc5b2f2bb933/neoforge/src/main/java/com/stal111/forbidden_arcanus/core/init/ModItems.java — SHA перевірено

[Структуровані докази](../../content/audit/v5-source-gaps-technology.json).

## `avaritia:eternal_singularity`

Статус: `source_verified_native_path`; версія: 1.4.2.

Наявний рецепт навмисно не містить result/output. Конструктор EternalSingularityCraftRecipe задає ModItems.eternal_singularity та tier4; getIngredients і matches отримують активні singularity з SingularityReloadListener. JSON ingredients:[] не означає відсутність рецепта: склад формується нативним кодом. Новий звичайний рецепт не потрібен.

- https://github.com/Nova-Committee/Re-Avaritia/blob/8e2f0f7bdfbd1bc229e14c3c4dc0808d55ed526a/gradle.properties — SHA перевірено
- https://github.com/Nova-Committee/Re-Avaritia/blob/8e2f0f7bdfbd1bc229e14c3c4dc0808d55ed526a/LICENSE — SHA перевірено
- https://github.com/Nova-Committee/Re-Avaritia/blob/8e2f0f7bdfbd1bc229e14c3c4dc0808d55ed526a/src/main/java/committee/nova/mods/avaritia/common/crafting/recipe/EternalSingularityCraftRecipe.java — SHA перевірено
- https://github.com/Nova-Committee/Re-Avaritia/blob/8e2f0f7bdfbd1bc229e14c3c4dc0808d55ed526a/src/generated/resources/data/avaritia/recipe/eternal_singularity.json — SHA перевірено
- https://github.com/Nova-Committee/Re-Avaritia/tree/8e2f0f7bdfbd1bc229e14c3c4dc0808d55ed526a — SHA перевірено

## `pneumaticcraft:assembly_program_drill`

Статус: `source_verified_native_path`; версія: 8.2.23.

Наявна статична пропозиція Amadron обмінює 8 смарагдів на один предмет. Вихід збережено у output.resource.id; простий обхід output.id його пропускав. Офіційна книга пояснює отримання торгівлею, а не звичайним крафтом.

- https://github.com/TeamPneumatic/pnc-repressurized/blob/98e656af1977a2c0587c563c90c7d06e0d30c091/gradle.properties — SHA перевірено
- https://github.com/TeamPneumatic/pnc-repressurized/blob/98e656af1977a2c0587c563c90c7d06e0d30c091/LICENSE — SHA перевірено
- https://github.com/TeamPneumatic/pnc-repressurized/blob/98e656af1977a2c0587c563c90c7d06e0d30c091/src/main/java/me/desht/pneumaticcraft/common/recipes/amadron/AmadronOffer.java — SHA перевірено
- https://github.com/TeamPneumatic/pnc-repressurized/blob/98e656af1977a2c0587c563c90c7d06e0d30c091/src/api/java/me/desht/pneumaticcraft/api/crafting/AmadronTradeResource.java — SHA перевірено
- https://github.com/TeamPneumatic/pnc-repressurized/tree/98e656af1977a2c0587c563c90c7d06e0d30c091 — SHA перевірено
- https://github.com/TeamPneumatic/pnc-repressurized/blob/98e656af1977a2c0587c563c90c7d06e0d30c091/src/main/resources/assets/pneumaticcraft/patchouli_books/book/en_us/entries/manufacturing/assembly_programs.json — SHA перевірено
- ../../content/research/evidence/source_gap_v5/technology/pneumaticcraft/export/recipes/pneumaticcraft/amadron/assembly_program_drill.json — SHA перевірено

## `pneumaticcraft:assembly_program_laser`

Статус: `source_verified_native_path`; версія: 8.2.23.

Наявна статична пропозиція Amadron обмінює 8 смарагдів на один предмет. Вихід збережено у output.resource.id; простий обхід output.id його пропускав. Офіційна книга пояснює отримання торгівлею, а не звичайним крафтом.

- https://github.com/TeamPneumatic/pnc-repressurized/blob/98e656af1977a2c0587c563c90c7d06e0d30c091/gradle.properties — SHA перевірено
- https://github.com/TeamPneumatic/pnc-repressurized/blob/98e656af1977a2c0587c563c90c7d06e0d30c091/LICENSE — SHA перевірено
- https://github.com/TeamPneumatic/pnc-repressurized/blob/98e656af1977a2c0587c563c90c7d06e0d30c091/src/main/java/me/desht/pneumaticcraft/common/recipes/amadron/AmadronOffer.java — SHA перевірено
- https://github.com/TeamPneumatic/pnc-repressurized/blob/98e656af1977a2c0587c563c90c7d06e0d30c091/src/api/java/me/desht/pneumaticcraft/api/crafting/AmadronTradeResource.java — SHA перевірено
- https://github.com/TeamPneumatic/pnc-repressurized/tree/98e656af1977a2c0587c563c90c7d06e0d30c091 — SHA перевірено
- https://github.com/TeamPneumatic/pnc-repressurized/blob/98e656af1977a2c0587c563c90c7d06e0d30c091/src/main/resources/assets/pneumaticcraft/patchouli_books/book/en_us/entries/manufacturing/assembly_programs.json — SHA перевірено
- ../../content/research/evidence/source_gap_v5/technology/pneumaticcraft/export/recipes/pneumaticcraft/amadron/assembly_program_laser.json — SHA перевірено

## `pneumaticcraft:pcb_blueprint`

Статус: `source_verified_native_path`; версія: 8.2.23.

Наявна статична пропозиція Amadron обмінює 8 смарагдів на один предмет. Вихід збережено у output.resource.id; простий обхід output.id його пропускав. Офіційна книга пояснює отримання торгівлею, а не звичайним крафтом. Mechanic Villager також продає креслення на першому рівні, якщо конфіг whichTrades це дозволяє; це умовний запасний шлях.

- https://github.com/TeamPneumatic/pnc-repressurized/blob/98e656af1977a2c0587c563c90c7d06e0d30c091/gradle.properties — SHA перевірено
- https://github.com/TeamPneumatic/pnc-repressurized/blob/98e656af1977a2c0587c563c90c7d06e0d30c091/LICENSE — SHA перевірено
- https://github.com/TeamPneumatic/pnc-repressurized/blob/98e656af1977a2c0587c563c90c7d06e0d30c091/src/main/java/me/desht/pneumaticcraft/common/recipes/amadron/AmadronOffer.java — SHA перевірено
- https://github.com/TeamPneumatic/pnc-repressurized/blob/98e656af1977a2c0587c563c90c7d06e0d30c091/src/api/java/me/desht/pneumaticcraft/api/crafting/AmadronTradeResource.java — SHA перевірено
- https://github.com/TeamPneumatic/pnc-repressurized/tree/98e656af1977a2c0587c563c90c7d06e0d30c091 — SHA перевірено
- https://github.com/TeamPneumatic/pnc-repressurized/blob/98e656af1977a2c0587c563c90c7d06e0d30c091/src/main/resources/assets/pneumaticcraft/patchouli_books/book/en_us/entries/components/pcb_blueprint.json — SHA перевірено
- ../../content/research/evidence/source_gap_v5/technology/pneumaticcraft/export/recipes/pneumaticcraft/amadron/pcb_blueprint.json — SHA перевірено
- https://github.com/TeamPneumatic/pnc-repressurized/blob/98e656af1977a2c0587c563c90c7d06e0d30c091/src/main/java/me/desht/pneumaticcraft/common/villages/VillagerTradesRegistration.java — SHA перевірено

## `enderio:powdered_obsidian`

Статус: `unverified_context`; версія: 8.2.12-beta.

Точний upstream-рецепт SAG Mill виробляє enderio:powdered_obsidian, але встановлений експорт уже уніфіковано на create:powdered_obsidian. Вихід вкладено у outputs[].item.id. Source не доводить доступності старого дублікату після уніфікації; потрібна перевірка канонічної цілі, не новий рецепт.

- https://github.com/Team-EnderIO/EnderIO/blob/9d35cace6895f451b4478a8608ff0fa0506530a5/gradle.properties — SHA перевірено
- https://github.com/Team-EnderIO/EnderIO/blob/9d35cace6895f451b4478a8608ff0fa0506530a5/LICENSE.txt — SHA перевірено
- https://github.com/Team-EnderIO/EnderIO/blob/9d35cace6895f451b4478a8608ff0fa0506530a5/enderio/src/generated/resources/data/enderio/recipe/sag_milling/obsidian.json — SHA перевірено
- ../../content/research/evidence/source_gap_v5/technology/enderio/export/recipes/enderio/sag_milling/obsidian.json — SHA перевірено
- https://github.com/Team-EnderIO/EnderIO/tree/9d35cace6895f451b4478a8608ff0fa0506530a5 — SHA перевірено

## `oritech:nickel_ingot`

Статус: `unverified_context`; версія: 1.2.13.

У точному NeoForge source Oritech1.2.13 виплавка raw_nickel дає oritech:nickel_ingot. Встановлений експорт і виплавку, і рецепт дев’яти самородків уже спрямовує на immersiveengineering:ingot_nickel. Наявність старого ID у реєстрі не доводить отримуваності дублікату; потрібна канонізація цілі, не новий рецепт.

- https://github.com/Rearth/Oritech/blob/4069b6dd14b05dfe0c80126618739b64054630ea/gradle.properties — SHA перевірено
- https://github.com/Rearth/Oritech/blob/4069b6dd14b05dfe0c80126618739b64054630ea/LICENSE.md — SHA перевірено
- https://github.com/Rearth/Oritech/blob/4069b6dd14b05dfe0c80126618739b64054630ea/neoforge/src/main/generated/data/oritech/recipe/nickel_ingot_from_smelting_raw_nickel.json — SHA перевірено
- ../../content/research/evidence/source_gap_v5/technology/oritech/export/recipes/oritech/nickel_ingot_from_smelting_raw_nickel.json — SHA перевірено
- ../../content/research/evidence/source_gap_v5/technology/oritech/export/recipes/oritech/nickel_ingot.json — SHA перевірено
- https://github.com/Rearth/Oritech/tree/4069b6dd14b05dfe0c80126618739b64054630ea — SHA перевірено

## `immersiveengineering:maintenance_kit`

Статус: `source_verified_native_path`; версія: 12.4.2-194.

Предмет уже виготовляється за нативним рецептом immersiveengineering:crafting/maintenance_kit. Serializer immersiveengineering:no_container_item зберігає vanilla shaped-рецепт у baseRecipe та делегує йому assemble/getResultItem. Відсутність джерела в аудиті є прогалиною обходу wrapper-поля, а не відсутнім рецептом; дубль додавати не слід.

- https://github.com/BluSunrize/ImmersiveEngineering/blob/583a182549d284a35c813b55ac2a0d1fddcf945a/gradle.properties — SHA перевірено
- https://github.com/BluSunrize/ImmersiveEngineering/blob/583a182549d284a35c813b55ac2a0d1fddcf945a/LICENSE — SHA перевірено
- https://github.com/BluSunrize/ImmersiveEngineering/blob/583a182549d284a35c813b55ac2a0d1fddcf945a/src/main/java/blusunrize/immersiveengineering/common/crafting/serializers/NoContainerSerializer.java — SHA перевірено
- https://github.com/BluSunrize/ImmersiveEngineering/blob/583a182549d284a35c813b55ac2a0d1fddcf945a/src/generated/resources/data/immersiveengineering/recipe/crafting/maintenance_kit.json — SHA перевірено

## `immersiveengineering:survey_tools`

Статус: `source_verified_native_path`; версія: 12.4.2-194.

Предмет уже виготовляється за нативним рецептом immersiveengineering:crafting/survey_tools. Serializer immersiveengineering:no_container_item зберігає vanilla shaped-рецепт у baseRecipe та делегує йому assemble/getResultItem. Відсутність джерела в аудиті є прогалиною обходу wrapper-поля, а не відсутнім рецептом; дубль додавати не слід.

- https://github.com/BluSunrize/ImmersiveEngineering/blob/583a182549d284a35c813b55ac2a0d1fddcf945a/gradle.properties — SHA перевірено
- https://github.com/BluSunrize/ImmersiveEngineering/blob/583a182549d284a35c813b55ac2a0d1fddcf945a/LICENSE — SHA перевірено
- https://github.com/BluSunrize/ImmersiveEngineering/blob/583a182549d284a35c813b55ac2a0d1fddcf945a/src/main/java/blusunrize/immersiveengineering/common/crafting/serializers/NoContainerSerializer.java — SHA перевірено
- https://github.com/BluSunrize/ImmersiveEngineering/blob/583a182549d284a35c813b55ac2a0d1fddcf945a/src/generated/resources/data/immersiveengineering/recipe/crafting/survey_tools.json — SHA перевірено
