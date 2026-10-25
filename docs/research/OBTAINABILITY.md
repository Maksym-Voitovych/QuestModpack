# Перевірені джерела без звичайного crafting-рецепта

Нативне джерело, торгівля або boss-drop не означають пропущений рецепт.
Наведені висновки перевірені за конкретними версіями й SHA файлів;
повне Survival-проходження та сторонні overrides ще не тестувалися.

[Структуровані докази](../../content/audit/v5-source-gaps-core-depth.json).

## `apotheosis:gem`

Статус: `source_verified_native_path`; версія: 8.9.0.

Apotheosis8.9.0 додає компонентні самоцвіти через global GemLootModifier. Shipped gem_loot_injection має25% шанс для minecraft chests.* та20% для інших зазначених таблиць. Обраний Gem перетворюється на ItemStack(Items.GEM) із gem-ID та purity. Це навмисний динамічний loot, а не відсутній crafting-рецепт. Конфігурації й сторонні overrides можуть змінити шанс.

- https://github.com/Shadows-of-Fire/Apotheosis/blob/7dd7cec26830074f1745529eb8f1f533092733d0/gradle.properties — SHA перевірено
- https://github.com/Shadows-of-Fire/Apotheosis/blob/7dd7cec26830074f1745529eb8f1f533092733d0/src/main/java/dev/shadowsoffire/apotheosis/loot/modifiers/GemLootModifier.java — SHA перевірено
- https://github.com/Shadows-of-Fire/Apotheosis/blob/7dd7cec26830074f1745529eb8f1f533092733d0/src/main/java/dev/shadowsoffire/apotheosis/socket/gem/Gem.java — SHA перевірено
- https://github.com/Shadows-of-Fire/Apotheosis/blob/7dd7cec26830074f1745529eb8f1f533092733d0/src/main/java/dev/shadowsoffire/apotheosis/socket/gem/GemRegistry.java — SHA перевірено
- https://github.com/Shadows-of-Fire/Apotheosis/blob/7dd7cec26830074f1745529eb8f1f533092733d0/src/generated/resources/data/apotheosis/loot_modifiers/gem_loot_injection.json — SHA перевірено
- https://github.com/Shadows-of-Fire/Apotheosis/blob/7dd7cec26830074f1745529eb8f1f533092733d0/src/generated/resources/data/neoforge/loot_modifiers/global_loot_modifiers.json — SHA перевірено
- https://github.com/Shadows-of-Fire/Apotheosis/blob/7dd7cec26830074f1745529eb8f1f533092733d0/src/generated/resources/data/apotheosis/gems/core/solar.json — SHA перевірено

## `immersivepetroleum:diesel_sulfur_bucket`

Статус: `source_verified_native_path`; версія: 4.5.0-39.

Дистиляція сирої нафти і коксування бітуму дають immersivepetroleum:diesel_sulfur. Точний IPContent реєструє DIESEL_SULFUR через IPFluid.makeFluid("diesel_sulfur"); IPFluidEntry.make створює відповідне diesel_sulfur_bucket. Наповніть порожнє відро готовою рідиною; clean diesel належить наступному Hydrotreater.

- ../../content/research/evidence/source_gap_followup_v5/installed_metadata.json — SHA перевірено
- https://github.com/TwistedGate/ImmersivePetroleum/blob/659c494e044a87137547b5305bb267d2a73ab702/gradle.properties — SHA перевірено
- https://github.com/TwistedGate/ImmersivePetroleum/blob/659c494e044a87137547b5305bb267d2a73ab702/src/main/java/flaxbeard/immersivepetroleum/common/fluids/IPFluid.java — SHA перевірено
- ../../content/research/evidence/petroleum_core_next_v5/official/src/main/java/flaxbeard/immersivepetroleum/common/IPContent.java — SHA перевірено
- ../../content/research/evidence/petroleum_core_next_v5/exported_recipes/distillationtower/oil.json — SHA перевірено
- ../../content/research/evidence/petroleum_core_next_v5/exported_recipes/coking/petcoke.json — SHA перевірено

[Структуровані докази](../../content/audit/v5-source-gaps-fluids.json).

## `pneumaticcraft:lpg_bucket`

Статус: `source_verified_native_path`; версія: 8.2.23.

Thermopneumatic Processing Plant перетворює100mB бензину(c:gasoline) на80mB LPG при мінімум573K і тиску2.0. Перемістіть LPG у Fluid Tank і наповніть порожнє відро через його контейнерний слот: нативний processFluidItem переносить рідину в контейнер і повертає pneumaticcraft:lpg_bucket. Точна версія8.2.23 явно зв’язує LPG↔LPG_BUCKET; окремий рецепт предмета-відра не потрібен.

- ../../content/research/evidence/source_gap_followup_v5/installed_metadata.json — SHA перевірено
- https://github.com/TeamPneumatic/pnc-repressurized/blob/98e656af1977a2c0587c563c90c7d06e0d30c091/gradle.properties — SHA перевірено
- https://github.com/TeamPneumatic/pnc-repressurized/blob/98e656af1977a2c0587c563c90c7d06e0d30c091/src/main/java/me/desht/pneumaticcraft/common/registry/ModItems.java — SHA перевірено
- https://github.com/TeamPneumatic/pnc-repressurized/blob/98e656af1977a2c0587c563c90c7d06e0d30c091/src/main/java/me/desht/pneumaticcraft/common/fluid/FluidLPG.java — SHA перевірено
- https://github.com/TeamPneumatic/pnc-repressurized/blob/98e656af1977a2c0587c563c90c7d06e0d30c091/src/main/java/me/desht/pneumaticcraft/common/block/entity/AbstractFluidTankBlockEntity.java — SHA перевірено
- https://github.com/TeamPneumatic/pnc-repressurized/blob/98e656af1977a2c0587c563c90c7d06e0d30c091/src/main/java/me/desht/pneumaticcraft/common/block/entity/AbstractPneumaticCraftBlockEntity.java — SHA перевірено
- ../../content/research/evidence/fluid_gaps_next_v5/export/recipes/pneumaticcraft/thermo_plant/lpg.json — SHA перевірено

## `industrialforegoing:meat_bucket`

Статус: `native_context_requires_exact_release_verification`; версія: 1.21-3.6.38.

Контекст офіційних джерел показує: SlaughterFactory.work наповнює MEAT після вбивства моба; TitaniumFluidInstance реєструє відповідне відро, а TitaniumFluid.getBucket зв’язує його з рідиною. Однак exact artifact IndustrialForegoing3.6.38 і Titanium4.0.43 не зіставлено з sourcepin, тому native шлях НЕ оголошено перевіреним. Випадковий рецепт відра не додається.

- ../../content/research/evidence/source_gap_followup_v5/installed_metadata.json — SHA перевірено
- https://github.com/InnovativeOnlineIndustries/Industrial-Foregoing/blob/1f8a32527522a0b2a54cf1d7c88a6a2a1e5146e9/gradle.properties — SHA перевірено
- https://github.com/InnovativeOnlineIndustries/Industrial-Foregoing/blob/1f8a32527522a0b2a54cf1d7c88a6a2a1e5146e9/CHANGELOG.md — SHA перевірено
- https://github.com/InnovativeOnlineIndustries/Industrial-Foregoing/blob/1f8a32527522a0b2a54cf1d7c88a6a2a1e5146e9/src/main/java/com/buuz135/industrial/module/ModuleCore.java — SHA перевірено
- https://github.com/InnovativeOnlineIndustries/Industrial-Foregoing/blob/1f8a32527522a0b2a54cf1d7c88a6a2a1e5146e9/src/main/java/com/buuz135/industrial/block/agriculturehusbandry/tile/SlaughterFactoryTile.java — SHA перевірено
- https://github.com/InnovativeOnlineIndustries/Titanium/blob/f8f0461458a4a3a54aa0239c9243a7716b7be436/gradle.properties — SHA перевірено
- https://github.com/InnovativeOnlineIndustries/Titanium/blob/f8f0461458a4a3a54aa0239c9243a7716b7be436/build.gradle — SHA перевірено
- https://github.com/InnovativeOnlineIndustries/Titanium/blob/f8f0461458a4a3a54aa0239c9243a7716b7be436/src/main/java/com/hrznstudio/titanium/fluid/TitaniumFluidInstance.java — SHA перевірено
- https://github.com/InnovativeOnlineIndustries/Titanium/blob/f8f0461458a4a3a54aa0239c9243a7716b7be436/src/main/java/com/hrznstudio/titanium/fluid/TitaniumFluid.java — SHA перевірено

## `industrialforegoing:pink_slime_bucket`

Статус: `native_context_requires_exact_release_verification`; версія: 1.21-3.6.38.

Контекст офіційних джерел показує: SlaughterFactory.work наповнює PINK_SLIME після вбивства моба; TitaniumFluidInstance реєструє відповідне відро, а TitaniumFluid.getBucket зв’язує його з рідиною. Однак exact artifact IndustrialForegoing3.6.38 і Titanium4.0.43 не зіставлено з sourcepin, тому native шлях НЕ оголошено перевіреним. Випадковий рецепт відра не додається.

- ../../content/research/evidence/source_gap_followup_v5/installed_metadata.json — SHA перевірено
- https://github.com/InnovativeOnlineIndustries/Industrial-Foregoing/blob/1f8a32527522a0b2a54cf1d7c88a6a2a1e5146e9/gradle.properties — SHA перевірено
- https://github.com/InnovativeOnlineIndustries/Industrial-Foregoing/blob/1f8a32527522a0b2a54cf1d7c88a6a2a1e5146e9/CHANGELOG.md — SHA перевірено
- https://github.com/InnovativeOnlineIndustries/Industrial-Foregoing/blob/1f8a32527522a0b2a54cf1d7c88a6a2a1e5146e9/src/main/java/com/buuz135/industrial/module/ModuleCore.java — SHA перевірено
- https://github.com/InnovativeOnlineIndustries/Industrial-Foregoing/blob/1f8a32527522a0b2a54cf1d7c88a6a2a1e5146e9/src/main/java/com/buuz135/industrial/block/agriculturehusbandry/tile/SlaughterFactoryTile.java — SHA перевірено
- https://github.com/InnovativeOnlineIndustries/Titanium/blob/f8f0461458a4a3a54aa0239c9243a7716b7be436/gradle.properties — SHA перевірено
- https://github.com/InnovativeOnlineIndustries/Titanium/blob/f8f0461458a4a3a54aa0239c9243a7716b7be436/build.gradle — SHA перевірено
- https://github.com/InnovativeOnlineIndustries/Titanium/blob/f8f0461458a4a3a54aa0239c9243a7716b7be436/src/main/java/com/hrznstudio/titanium/fluid/TitaniumFluidInstance.java — SHA перевірено
- https://github.com/InnovativeOnlineIndustries/Titanium/blob/f8f0461458a4a3a54aa0239c9243a7716b7be436/src/main/java/com/hrznstudio/titanium/fluid/TitaniumFluid.java — SHA перевірено

## `industrialforegoing:ether_gas_bucket`

Статус: `native_context_requires_exact_release_verification`; версія: 1.21-3.6.38.

Контекст офіційних джерел показує: FluidLaserBase створює ETHER за нативним laser_drill_fluid/ether із вимогою відповідної сутності; TitaniumFluidInstance реєструє відповідне відро, а TitaniumFluid.getBucket зв’язує його з рідиною. Однак exact artifact IndustrialForegoing3.6.38 і Titanium4.0.43 не зіставлено з sourcepin, тому native шлях НЕ оголошено перевіреним. Випадковий рецепт відра не додається.

- ../../content/research/evidence/source_gap_followup_v5/installed_metadata.json — SHA перевірено
- https://github.com/InnovativeOnlineIndustries/Industrial-Foregoing/blob/1f8a32527522a0b2a54cf1d7c88a6a2a1e5146e9/gradle.properties — SHA перевірено
- https://github.com/InnovativeOnlineIndustries/Industrial-Foregoing/blob/1f8a32527522a0b2a54cf1d7c88a6a2a1e5146e9/CHANGELOG.md — SHA перевірено
- https://github.com/InnovativeOnlineIndustries/Industrial-Foregoing/blob/1f8a32527522a0b2a54cf1d7c88a6a2a1e5146e9/src/main/java/com/buuz135/industrial/module/ModuleCore.java — SHA перевірено
- https://github.com/InnovativeOnlineIndustries/Industrial-Foregoing/blob/1f8a32527522a0b2a54cf1d7c88a6a2a1e5146e9/src/main/java/com/buuz135/industrial/block/resourceproduction/tile/FluidLaserBaseTile.java — SHA перевірено
- ../../content/research/evidence/fluid_gaps_next_v5/export/recipes/industrialforegoing/laser_drill_fluid/ether.json — SHA перевірено
- https://github.com/InnovativeOnlineIndustries/Titanium/blob/f8f0461458a4a3a54aa0239c9243a7716b7be436/gradle.properties — SHA перевірено
- https://github.com/InnovativeOnlineIndustries/Titanium/blob/f8f0461458a4a3a54aa0239c9243a7716b7be436/build.gradle — SHA перевірено
- https://github.com/InnovativeOnlineIndustries/Titanium/blob/f8f0461458a4a3a54aa0239c9243a7716b7be436/src/main/java/com/hrznstudio/titanium/fluid/TitaniumFluidInstance.java — SHA перевірено
- https://github.com/InnovativeOnlineIndustries/Titanium/blob/f8f0461458a4a3a54aa0239c9243a7716b7be436/src/main/java/com/hrznstudio/titanium/fluid/TitaniumFluid.java — SHA перевірено

[Структуровані докази](../../content/audit/v5-source-gaps-followup.json).

## `actuallyadditions:canola_oil_bucket`

Статус: `source_verified_native_path`; версія: 1.3.26.

Canola Press виробляє actuallyadditions:canola_oil за нативним pressing-рецептом. FluidAA реєструє canola_oil_bucket як відро цієї рідини; взаємодія з резервуаром наповнює порожнє відро. Відсутність окремого item-output JSON для повного відра очікувана.

- ../../content/research/evidence/source_gap_followup_v5/installed_metadata.json — SHA перевірено
- https://github.com/Ellpeck/ActuallyAdditions/blob/cd9d9c63254f471f966ee51b078afdf47af5f852/gradle.properties — SHA перевірено
- https://github.com/Ellpeck/ActuallyAdditions/blob/cd9d9c63254f471f966ee51b078afdf47af5f852/src/main/java/de/ellpeck/actuallyadditions/mod/fluids/InitFluids.java — SHA перевірено
- https://github.com/Ellpeck/ActuallyAdditions/blob/cd9d9c63254f471f966ee51b078afdf47af5f852/src/main/java/de/ellpeck/actuallyadditions/mod/fluids/FluidAA.java — SHA перевірено
- https://github.com/Ellpeck/ActuallyAdditions/blob/cd9d9c63254f471f966ee51b078afdf47af5f852/src/main/java/de/ellpeck/actuallyadditions/mod/blocks/base/BlockContainerBase.java — SHA перевірено
- ../../content/research/evidence/source_gap_followup_v5/actuallyadditions/export/recipes/actuallyadditions/pressing/canola.json — SHA перевірено

## `apotheosis:mysterious_scrap_metal`

Статус: `source_verified_native_path`; версія: 8.9.0.

Матеріал отримується у Salvaging Table зі спорядження звичайного рівня affix-rarity. Нативний рецепт apotheosis:salvaging/affix_item/common містить вихід у outputs[].stack. Це пропуск парсера джерел, не відсутній рецепт; звичайний верстак додавати не потрібно.

- ../../content/research/evidence/source_gap_followup_v5/installed_metadata.json — SHA перевірено
- https://github.com/Shadows-of-Fire/Apotheosis/blob/7dd7cec26830074f1745529eb8f1f533092733d0/gradle.properties — SHA перевірено
- https://github.com/Shadows-of-Fire/Apotheosis/blob/7dd7cec26830074f1745529eb8f1f533092733d0/src/main/java/dev/shadowsoffire/apotheosis/affix/salvaging/SalvagingRecipe.java — SHA перевірено
- https://github.com/Shadows-of-Fire/Apotheosis/blob/7dd7cec26830074f1745529eb8f1f533092733d0/src/main/java/dev/shadowsoffire/apotheosis/affix/salvaging/SalvagingMenu.java — SHA перевірено
- ../../content/research/evidence/source_gap_followup_v5/apotheosis/export/recipes/apotheosis/salvaging/affix_item/common.json — SHA перевірено

## `apotheosis:timeworn_fabric`

Статус: `source_verified_native_path`; версія: 8.9.0.

Матеріал отримується у Salvaging Table зі спорядження незвичайного рівня affix-rarity. Нативний рецепт apotheosis:salvaging/affix_item/uncommon містить вихід у outputs[].stack. Це пропуск парсера джерел, не відсутній рецепт; звичайний верстак додавати не потрібно.

- ../../content/research/evidence/source_gap_followup_v5/installed_metadata.json — SHA перевірено
- https://github.com/Shadows-of-Fire/Apotheosis/blob/7dd7cec26830074f1745529eb8f1f533092733d0/gradle.properties — SHA перевірено
- https://github.com/Shadows-of-Fire/Apotheosis/blob/7dd7cec26830074f1745529eb8f1f533092733d0/src/main/java/dev/shadowsoffire/apotheosis/affix/salvaging/SalvagingRecipe.java — SHA перевірено
- https://github.com/Shadows-of-Fire/Apotheosis/blob/7dd7cec26830074f1745529eb8f1f533092733d0/src/main/java/dev/shadowsoffire/apotheosis/affix/salvaging/SalvagingMenu.java — SHA перевірено
- ../../content/research/evidence/source_gap_followup_v5/apotheosis/export/recipes/apotheosis/salvaging/affix_item/uncommon.json — SHA перевірено

## `apotheosis:luminous_crystal_shard`

Статус: `source_verified_native_path`; версія: 8.9.0.

Матеріал отримується у Salvaging Table зі спорядження рідкісного рівня affix-rarity. Нативний рецепт apotheosis:salvaging/affix_item/rare містить вихід у outputs[].stack. Це пропуск парсера джерел, не відсутній рецепт; звичайний верстак додавати не потрібно.

- ../../content/research/evidence/source_gap_followup_v5/installed_metadata.json — SHA перевірено
- https://github.com/Shadows-of-Fire/Apotheosis/blob/7dd7cec26830074f1745529eb8f1f533092733d0/gradle.properties — SHA перевірено
- https://github.com/Shadows-of-Fire/Apotheosis/blob/7dd7cec26830074f1745529eb8f1f533092733d0/src/main/java/dev/shadowsoffire/apotheosis/affix/salvaging/SalvagingRecipe.java — SHA перевірено
- https://github.com/Shadows-of-Fire/Apotheosis/blob/7dd7cec26830074f1745529eb8f1f533092733d0/src/main/java/dev/shadowsoffire/apotheosis/affix/salvaging/SalvagingMenu.java — SHA перевірено
- ../../content/research/evidence/source_gap_followup_v5/apotheosis/export/recipes/apotheosis/salvaging/affix_item/rare.json — SHA перевірено

## `apotheosis:arcane_sands`

Статус: `source_verified_native_path`; версія: 8.9.0.

Матеріал отримується у Salvaging Table зі спорядження епічного рівня affix-rarity. Нативний рецепт apotheosis:salvaging/affix_item/epic містить вихід у outputs[].stack. Це пропуск парсера джерел, не відсутній рецепт; звичайний верстак додавати не потрібно.

- ../../content/research/evidence/source_gap_followup_v5/installed_metadata.json — SHA перевірено
- https://github.com/Shadows-of-Fire/Apotheosis/blob/7dd7cec26830074f1745529eb8f1f533092733d0/gradle.properties — SHA перевірено
- https://github.com/Shadows-of-Fire/Apotheosis/blob/7dd7cec26830074f1745529eb8f1f533092733d0/src/main/java/dev/shadowsoffire/apotheosis/affix/salvaging/SalvagingRecipe.java — SHA перевірено
- https://github.com/Shadows-of-Fire/Apotheosis/blob/7dd7cec26830074f1745529eb8f1f533092733d0/src/main/java/dev/shadowsoffire/apotheosis/affix/salvaging/SalvagingMenu.java — SHA перевірено
- ../../content/research/evidence/source_gap_followup_v5/apotheosis/export/recipes/apotheosis/salvaging/affix_item/epic.json — SHA перевірено

## `apotheosis:godforged_pearl`

Статус: `source_verified_native_path`; версія: 8.9.0.

Матеріал отримується у Salvaging Table зі спорядження міфічного рівня affix-rarity. Нативний рецепт apotheosis:salvaging/affix_item/mythic містить вихід у outputs[].stack. Це пропуск парсера джерел, не відсутній рецепт; звичайний верстак додавати не потрібно.

- ../../content/research/evidence/source_gap_followup_v5/installed_metadata.json — SHA перевірено
- https://github.com/Shadows-of-Fire/Apotheosis/blob/7dd7cec26830074f1745529eb8f1f533092733d0/gradle.properties — SHA перевірено
- https://github.com/Shadows-of-Fire/Apotheosis/blob/7dd7cec26830074f1745529eb8f1f533092733d0/src/main/java/dev/shadowsoffire/apotheosis/affix/salvaging/SalvagingRecipe.java — SHA перевірено
- https://github.com/Shadows-of-Fire/Apotheosis/blob/7dd7cec26830074f1745529eb8f1f533092733d0/src/main/java/dev/shadowsoffire/apotheosis/affix/salvaging/SalvagingMenu.java — SHA перевірено
- ../../content/research/evidence/source_gap_followup_v5/apotheosis/export/recipes/apotheosis/salvaging/affix_item/mythic.json — SHA перевірено

## `apotheosis:gem_dust`

Статус: `source_verified_native_path`; версія: 8.9.0.

Обробник AdventureEvents.gemSmashing(AnvilLandEvent) замінює предметні сутності apotheosis:gem у клітині приземлення ковадла на gem_dust у тій самій кількості. Це навмисна світова дія; відсутність crafting JSON не означає прогалину.

- ../../content/research/evidence/source_gap_followup_v5/installed_metadata.json — SHA перевірено
- https://github.com/Shadows-of-Fire/Apotheosis/blob/7dd7cec26830074f1745529eb8f1f533092733d0/gradle.properties — SHA перевірено
- https://github.com/Shadows-of-Fire/Apotheosis/blob/7dd7cec26830074f1745529eb8f1f533092733d0/src/main/java/dev/shadowsoffire/apotheosis/AdventureEvents.java — SHA перевірено
- https://github.com/Shadows-of-Fire/Apotheosis/blob/7dd7cec26830074f1745529eb8f1f533092733d0/src/main/java/dev/shadowsoffire/apotheosis/Apoth.java — SHA перевірено

## `create:incomplete_precision_mechanism`

Статус: `source_verified_native_path`; версія: 6.0.10.

Незавершений precision mechanism — проміжний стек Sequenced Assembly. Метод advance() після нефінальної операції повертає transitionalItem з компонентом прогресу SEQUENCED_ASSEMBLY. Нативний рецепт precision_mechanism визначає цей transitionalItem; його не слід додавати як окремий побутовий рецепт.

- ../../content/research/evidence/source_gap_followup_v5/installed_metadata.json — SHA перевірено
- https://github.com/Creators-of-Create/Create/blob/ac0c444d9828da3453ae8cc65338e8de063286fb/gradle.properties — SHA перевірено
- https://github.com/Creators-of-Create/Create/blob/ac0c444d9828da3453ae8cc65338e8de063286fb/src/main/java/com/simibubi/create/content/processing/sequenced/SequencedAssemblyRecipe.java — SHA перевірено
- ../../content/research/evidence/source_gap_followup_v5/create/export/recipes/create/sequenced_assembly/precision_mechanism.json — SHA перевірено

## `createdieselgenerators:diesel_bucket`

Статус: `source_verified_native_path`; версія: 1.21.1-1.3.15.

Дистиляція crude_oil виробляє дизель як рідинний вихід. Реєстрація CDGFluids для diesel викликає .bucket(); повне відро отримується наповненням порожнього відра цією рідиною, а не окремим рецептом верстака.

- ../../content/research/evidence/source_gap_followup_v5/installed_metadata.json — SHA перевірено
- https://github.com/george8188625/Create-Diesel-Generators/blob/79ce136730871b6f3f7b55d3cc748ff2bec2ad12/gradle.properties — SHA перевірено
- https://github.com/george8188625/Create-Diesel-Generators/blob/79ce136730871b6f3f7b55d3cc748ff2bec2ad12/src/main/java/com/jesz/createdieselgenerators/CDGFluids.java — SHA перевірено
- ../../content/research/evidence/source_gap_followup_v5/createdieselgenerators/export/recipes/createdieselgenerators/distillation/crude_oil.json — SHA перевірено

## `createdieselgenerators:gasoline_bucket`

Статус: `source_verified_native_path`; версія: 1.21.1-1.3.15.

Дистиляція crude_oil виробляє бензин як рідинний вихід. Реєстрація CDGFluids для gasoline викликає .bucket(); повне відро отримується наповненням порожнього відра цією рідиною, а не окремим рецептом верстака.

- ../../content/research/evidence/source_gap_followup_v5/installed_metadata.json — SHA перевірено
- https://github.com/george8188625/Create-Diesel-Generators/blob/79ce136730871b6f3f7b55d3cc748ff2bec2ad12/gradle.properties — SHA перевірено
- https://github.com/george8188625/Create-Diesel-Generators/blob/79ce136730871b6f3f7b55d3cc748ff2bec2ad12/src/main/java/com/jesz/createdieselgenerators/CDGFluids.java — SHA перевірено
- ../../content/research/evidence/source_gap_followup_v5/createdieselgenerators/export/recipes/createdieselgenerators/distillation/crude_oil.json — SHA перевірено

## `forbidden_arcanus:xpetrified_orb`

Статус: `source_verified_native_path`; версія: 2.6.1.

Black Hole поглинає ExperienceOrb у своїй зоні. За stored_xp не менше60 нативний serverTick викидає XPETRIFIED_ORB і обнуляє накопичувач. Це спеціальна світова механіка; XP-значення предмета визначається його компонентом і не є звичайним рецептом.

- ../../content/research/evidence/source_gap_followup_v5/installed_metadata.json — SHA перевірено
- https://github.com/stal111/Forbidden-Arcanus/blob/34f83feb76204fd773e1d2e1d69ecc5b2f2bb933/gradle.properties — SHA перевірено
- https://github.com/stal111/Forbidden-Arcanus/blob/34f83feb76204fd773e1d2e1d69ecc5b2f2bb933/neoforge/src/main/java/com/stal111/forbidden_arcanus/common/block/entity/BlackHoleBlockEntity.java — SHA перевірено
- https://github.com/stal111/Forbidden-Arcanus/blob/34f83feb76204fd773e1d2e1d69ecc5b2f2bb933/neoforge/src/main/java/com/stal111/forbidden_arcanus/core/init/ModItems.java — SHA перевірено

## `immersivepetroleum:bitumen`

Статус: `source_verified_native_path`; версія: 4.5.0-39.

Точний installed рецепт immersivepetroleum:distillationtower/oil має byproducts[0].output.id=immersivepetroleum:bitumen із chance0.07. Це реальний побічний продукт дистиляції, який старий парсер не читав; додатковий crafting-рецепт зруйнував би логіку нафтохімії.

- ../../content/research/evidence/source_gap_followup_v5/installed_metadata.json — SHA перевірено
- https://github.com/TwistedGate/ImmersivePetroleum/blob/659c494e044a87137547b5305bb267d2a73ab702/gradle.properties — SHA перевірено
- ../../content/research/evidence/source_gap_followup_v5/immersivepetroleum/export/recipes/immersivepetroleum/distillationtower/oil.json — SHA перевірено

## `immersivepetroleum:lubricant_bucket`

Статус: `source_verified_native_path`; версія: 4.5.0-39.

Distillation Tower виробляє мастило як рідинний result у рецепті oil. IPContent реєструє цю рідину, а IPFluidEntry.make створює відповідне lubricant_bucket. Повне відро є результатом наповнення рідиною, не пропущеним рецептом верстака.

- ../../content/research/evidence/source_gap_followup_v5/installed_metadata.json — SHA перевірено
- https://github.com/TwistedGate/ImmersivePetroleum/blob/659c494e044a87137547b5305bb267d2a73ab702/gradle.properties — SHA перевірено
- https://github.com/TwistedGate/ImmersivePetroleum/blob/659c494e044a87137547b5305bb267d2a73ab702/src/main/java/flaxbeard/immersivepetroleum/common/fluids/IPFluid.java — SHA перевірено
- https://github.com/TwistedGate/ImmersivePetroleum/blob/659c494e044a87137547b5305bb267d2a73ab702/src/main/java/flaxbeard/immersivepetroleum/common/IPContent.java — SHA перевірено
- ../../content/research/evidence/source_gap_followup_v5/immersivepetroleum/export/recipes/immersivepetroleum/distillationtower/oil.json — SHA перевірено

## `immersivepetroleum:naphtha_bucket`

Статус: `source_verified_native_path`; версія: 4.5.0-39.

Distillation Tower виробляє нафта-фракція як рідинний result у рецепті oil. IPContent реєструє цю рідину, а IPFluidEntry.make створює відповідне naphtha_bucket. Повне відро є результатом наповнення рідиною, не пропущеним рецептом верстака.

- ../../content/research/evidence/source_gap_followup_v5/installed_metadata.json — SHA перевірено
- https://github.com/TwistedGate/ImmersivePetroleum/blob/659c494e044a87137547b5305bb267d2a73ab702/gradle.properties — SHA перевірено
- https://github.com/TwistedGate/ImmersivePetroleum/blob/659c494e044a87137547b5305bb267d2a73ab702/src/main/java/flaxbeard/immersivepetroleum/common/fluids/IPFluid.java — SHA перевірено
- https://github.com/TwistedGate/ImmersivePetroleum/blob/659c494e044a87137547b5305bb267d2a73ab702/src/main/java/flaxbeard/immersivepetroleum/common/IPContent.java — SHA перевірено
- ../../content/research/evidence/source_gap_followup_v5/immersivepetroleum/export/recipes/immersivepetroleum/distillationtower/oil.json — SHA перевірено

## `immersivepetroleum:diesel_bucket`

Статус: `source_verified_native_path`; версія: 4.5.0-39.

Нативний Hydrotreater за sulfur_recovery перетворює diesel_sulfur у immersivepetroleum:diesel. IPFluidEntry.make зв’язує рідину diesel із diesel_bucket; відро наповнюється готовим десульфурованим паливом. Не плутати з окремим diesel_sulfur_bucket.

- ../../content/research/evidence/source_gap_followup_v5/installed_metadata.json — SHA перевірено
- https://github.com/TwistedGate/ImmersivePetroleum/blob/659c494e044a87137547b5305bb267d2a73ab702/gradle.properties — SHA перевірено
- https://github.com/TwistedGate/ImmersivePetroleum/blob/659c494e044a87137547b5305bb267d2a73ab702/src/main/java/flaxbeard/immersivepetroleum/common/fluids/IPFluid.java — SHA перевірено
- https://github.com/TwistedGate/ImmersivePetroleum/blob/659c494e044a87137547b5305bb267d2a73ab702/src/main/java/flaxbeard/immersivepetroleum/common/IPContent.java — SHA перевірено
- ../../content/research/evidence/source_gap_followup_v5/immersivepetroleum/export/recipes/immersivepetroleum/hydrotreater/sulfur_recovery.json — SHA перевірено

## `rootsclassic:charged_runic_focus`

Статус: `source_verified_native_path`; версія: 1.21.1-1.5.10.

Ритуал rootsclassic:ritual/crafting/charged_runic_focus створює заряджений рунічний фокус. Вихід закодовано в effectConfig.result, а не на верхньому рівні result; RitualCrafting читає його та створює предмет після ритуалу. Не додавати звичайний рецепт для обходу жаровні й пахощів.

- ../../content/research/evidence/source_gap_followup_v5/installed_metadata.json — SHA перевірено
- https://github.com/Lothrazar/RootsClassic/blob/db9aa883b7a54a1558dbc710546be1f42544be72/gradle.properties — SHA перевірено
- https://github.com/Lothrazar/RootsClassic/blob/db9aa883b7a54a1558dbc710546be1f42544be72/src/main/java/elucent/rootsclassic/ritual/rituals/RitualCrafting.java — SHA перевірено
- https://github.com/Lothrazar/RootsClassic/blob/db9aa883b7a54a1558dbc710546be1f42544be72/src/main/java/elucent/rootsclassic/recipe/RitualRecipe.java — SHA перевірено
- ../../content/research/evidence/source_gap_followup_v5/rootsclassic/export/recipes/rootsclassic/ritual/crafting/charged_runic_focus.json — SHA перевірено

## `rootsclassic:living_pickaxe`

Статус: `source_verified_native_path`; версія: 1.21.1-1.5.10.

Ритуал rootsclassic:ritual/crafting/living_pickaxe створює живу кирку. Вихід закодовано в effectConfig.result, а не на верхньому рівні result; RitualCrafting читає його та створює предмет після ритуалу. Не додавати звичайний рецепт для обходу жаровні й пахощів.

- ../../content/research/evidence/source_gap_followup_v5/installed_metadata.json — SHA перевірено
- https://github.com/Lothrazar/RootsClassic/blob/db9aa883b7a54a1558dbc710546be1f42544be72/gradle.properties — SHA перевірено
- https://github.com/Lothrazar/RootsClassic/blob/db9aa883b7a54a1558dbc710546be1f42544be72/src/main/java/elucent/rootsclassic/ritual/rituals/RitualCrafting.java — SHA перевірено
- https://github.com/Lothrazar/RootsClassic/blob/db9aa883b7a54a1558dbc710546be1f42544be72/src/main/java/elucent/rootsclassic/recipe/RitualRecipe.java — SHA перевірено
- ../../content/research/evidence/source_gap_followup_v5/rootsclassic/export/recipes/rootsclassic/ritual/crafting/living_pickaxe.json — SHA перевірено

## `rootsclassic:spruce_bark`

Статус: `source_verified_native_path`; версія: 1.21.1-1.5.10.

Bark Knife (DruidKnifeItem) на spruce_log або spruce_wood створює RootsRegistry.SPRUCE_BARK. Ніж втрачає міцність; перетворення блока на обтесаний залежить від конфігурації. Це нативна взаємодія зі світом, а не рецепт верстака.

- ../../content/research/evidence/source_gap_followup_v5/installed_metadata.json — SHA перевірено
- https://github.com/Lothrazar/RootsClassic/blob/db9aa883b7a54a1558dbc710546be1f42544be72/gradle.properties — SHA перевірено
- https://github.com/Lothrazar/RootsClassic/blob/db9aa883b7a54a1558dbc710546be1f42544be72/src/main/java/elucent/rootsclassic/item/DruidKnifeItem.java — SHA перевірено

## `industrialforegoing:biofuel_bucket`

Статус: `native_context_requires_exact_release_verification`; версія: 1.21-3.6.38.

Офіційний код у release-context3.6.38 показує: BioReactor перетворює рослинні входи та воду на BIOFUEL через fillForced. Однак точне зіставлення CI artifact3.6.38 із sourcepin та Titanium-fluid↔bucket ще не підтверджено; випадок лишається незавершеним. Не додавати випадковий рецепт відра.

- ../../content/research/evidence/source_gap_followup_v5/installed_metadata.json — SHA перевірено
- https://github.com/InnovativeOnlineIndustries/Industrial-Foregoing/blob/1f8a32527522a0b2a54cf1d7c88a6a2a1e5146e9/gradle.properties — SHA перевірено
- https://github.com/InnovativeOnlineIndustries/Industrial-Foregoing/blob/1f8a32527522a0b2a54cf1d7c88a6a2a1e5146e9/CHANGELOG.md — SHA перевірено
- https://github.com/InnovativeOnlineIndustries/Industrial-Foregoing/blob/1f8a32527522a0b2a54cf1d7c88a6a2a1e5146e9/src/main/java/com/buuz135/industrial/module/ModuleCore.java — SHA перевірено
- https://github.com/InnovativeOnlineIndustries/Industrial-Foregoing/blob/1f8a32527522a0b2a54cf1d7c88a6a2a1e5146e9/src/main/java/com/buuz135/industrial/block/generator/tile/BioReactorTile.java — SHA перевірено
- https://github.com/InnovativeOnlineIndustries/Titanium/blob/f8f0461458a4a3a54aa0239c9243a7716b7be436/gradle.properties — SHA перевірено
- https://github.com/InnovativeOnlineIndustries/Titanium/blob/f8f0461458a4a3a54aa0239c9243a7716b7be436/build.gradle — SHA перевірено
- https://github.com/InnovativeOnlineIndustries/Titanium/blob/f8f0461458a4a3a54aa0239c9243a7716b7be436/src/main/java/com/hrznstudio/titanium/fluid/TitaniumFluidInstance.java — SHA перевірено
- https://github.com/InnovativeOnlineIndustries/Titanium/blob/f8f0461458a4a3a54aa0239c9243a7716b7be436/src/main/java/com/hrznstudio/titanium/fluid/TitaniumFluid.java — SHA перевірено

## `industrialforegoing:sewage_bucket`

Статус: `native_context_requires_exact_release_verification`; версія: 1.21-3.6.38.

Офіційний код у release-context3.6.38 показує: Sewer знаходить Animal у робочій області й заповнює SEWAGE. Однак точне зіставлення CI artifact3.6.38 із sourcepin та Titanium-fluid↔bucket ще не підтверджено; випадок лишається незавершеним. Не додавати випадковий рецепт відра.

- ../../content/research/evidence/source_gap_followup_v5/installed_metadata.json — SHA перевірено
- https://github.com/InnovativeOnlineIndustries/Industrial-Foregoing/blob/1f8a32527522a0b2a54cf1d7c88a6a2a1e5146e9/gradle.properties — SHA перевірено
- https://github.com/InnovativeOnlineIndustries/Industrial-Foregoing/blob/1f8a32527522a0b2a54cf1d7c88a6a2a1e5146e9/CHANGELOG.md — SHA перевірено
- https://github.com/InnovativeOnlineIndustries/Industrial-Foregoing/blob/1f8a32527522a0b2a54cf1d7c88a6a2a1e5146e9/src/main/java/com/buuz135/industrial/module/ModuleCore.java — SHA перевірено
- https://github.com/InnovativeOnlineIndustries/Industrial-Foregoing/blob/1f8a32527522a0b2a54cf1d7c88a6a2a1e5146e9/src/main/java/com/buuz135/industrial/block/agriculturehusbandry/tile/SewerTile.java — SHA перевірено
- https://github.com/InnovativeOnlineIndustries/Titanium/blob/f8f0461458a4a3a54aa0239c9243a7716b7be436/gradle.properties — SHA перевірено
- https://github.com/InnovativeOnlineIndustries/Titanium/blob/f8f0461458a4a3a54aa0239c9243a7716b7be436/build.gradle — SHA перевірено
- https://github.com/InnovativeOnlineIndustries/Titanium/blob/f8f0461458a4a3a54aa0239c9243a7716b7be436/src/main/java/com/hrznstudio/titanium/fluid/TitaniumFluidInstance.java — SHA перевірено
- https://github.com/InnovativeOnlineIndustries/Titanium/blob/f8f0461458a4a3a54aa0239c9243a7716b7be436/src/main/java/com/hrznstudio/titanium/fluid/TitaniumFluid.java — SHA перевірено

## `industrialforegoing:sludge_bucket`

Статус: `native_context_requires_exact_release_verification`; версія: 1.21-3.6.38.

Офіційний код у release-context3.6.38 показує: PlantGatherer заповнює SLUDGE під час збирання рослин. Однак точне зіставлення CI artifact3.6.38 із sourcepin та Titanium-fluid↔bucket ще не підтверджено; випадок лишається незавершеним. Не додавати випадковий рецепт відра.

- ../../content/research/evidence/source_gap_followup_v5/installed_metadata.json — SHA перевірено
- https://github.com/InnovativeOnlineIndustries/Industrial-Foregoing/blob/1f8a32527522a0b2a54cf1d7c88a6a2a1e5146e9/gradle.properties — SHA перевірено
- https://github.com/InnovativeOnlineIndustries/Industrial-Foregoing/blob/1f8a32527522a0b2a54cf1d7c88a6a2a1e5146e9/CHANGELOG.md — SHA перевірено
- https://github.com/InnovativeOnlineIndustries/Industrial-Foregoing/blob/1f8a32527522a0b2a54cf1d7c88a6a2a1e5146e9/src/main/java/com/buuz135/industrial/module/ModuleCore.java — SHA перевірено
- https://github.com/InnovativeOnlineIndustries/Industrial-Foregoing/blob/1f8a32527522a0b2a54cf1d7c88a6a2a1e5146e9/src/main/java/com/buuz135/industrial/block/agriculturehusbandry/tile/PlantGathererTile.java — SHA перевірено
- https://github.com/InnovativeOnlineIndustries/Titanium/blob/f8f0461458a4a3a54aa0239c9243a7716b7be436/gradle.properties — SHA перевірено
- https://github.com/InnovativeOnlineIndustries/Titanium/blob/f8f0461458a4a3a54aa0239c9243a7716b7be436/build.gradle — SHA перевірено
- https://github.com/InnovativeOnlineIndustries/Titanium/blob/f8f0461458a4a3a54aa0239c9243a7716b7be436/src/main/java/com/hrznstudio/titanium/fluid/TitaniumFluidInstance.java — SHA перевірено
- https://github.com/InnovativeOnlineIndustries/Titanium/blob/f8f0461458a4a3a54aa0239c9243a7716b7be436/src/main/java/com/hrznstudio/titanium/fluid/TitaniumFluid.java — SHA перевірено

## `irons_spellbooks:wimpy_spell_book`

Статус: `confirmed_unsuitable_quest_target`; версія: 1.21.1-3.16.3.

WIMPY_SPELL_BOOK зареєстровано як SpellBook(0), тобто без слотів заклять; підтвердженого survival-рецепта не знайдено. Офіційний early_game посібник прямо показує copper_spell_book як початкову книгу. Квест V5_MAG_IRONS_SPELLBOOKS_01 має вимагати craftable copper_spell_book (gate15), зберігаючи його quest/task IDs; не створювати рецепт для нуль-слотової книги.

- ../../content/research/evidence/source_gap_followup_v5/installed_metadata.json — SHA перевірено
- https://github.com/iron431/Irons-Spells-n-Spellbooks/blob/532c98dfa5b219f3927aca9b23d9042c00e767bb/gradle.properties — SHA перевірено
- https://github.com/iron431/Irons-Spells-n-Spellbooks/blob/532c98dfa5b219f3927aca9b23d9042c00e767bb/src/main/java/io/redspace/ironsspellbooks/registries/ItemRegistry.java — SHA перевірено
- https://github.com/iron431/Irons-Spells-n-Spellbooks/blob/532c98dfa5b219f3927aca9b23d9042c00e767bb/src/main/resources/assets/irons_spellbooks/patchouli_books/iss_guide_book/en_us/entries/progression/early_game.json — SHA перевірено
- ../../content/research/evidence/source_gap_followup_v5/irons_spellbooks/export/recipes/irons_spellbooks/copper_spell_book.json — SHA перевірено

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

[Структуровані докази](../../content/audit/v5-source-gaps-roots-aa.json).

## `rootsclassic:acacia_bark`

Статус: `source_verified_native_path`; версія: 1.21.1-1.5.10.

Ножем Roots використайте Acacia Log/Wood: BLOCK_BARK_MAP повертає ACACIA_BARK, а useOn створює barkDrop через spawnAtLocation. Рецепт предмета не потрібний; деревина може бути знята з кори за шансом конфігурації.

- https://github.com/Lothrazar/RootsClassic/blob/db9aa883b7a54a1558dbc710546be1f42544be72/gradle.properties — SHA перевірено
- https://github.com/Lothrazar/RootsClassic/blob/db9aa883b7a54a1558dbc710546be1f42544be72/src/main/java/elucent/rootsclassic/item/DruidKnifeItem.java — SHA перевірено

## `rootsclassic:staff`

Статус: `source_verified_native_path`; версія: 1.21.1-1.5.10.

Покладіть wooden rod та Spell Powder із component RootsComponents.SPELL в Imbuer. Серверний цикл після progress>40 створює RootsRegistry.STAFF, переносить параметри закляття й очищає обидва входи. Порожній порошок без потрібного компонента посоха не створює.

- https://github.com/Lothrazar/RootsClassic/blob/db9aa883b7a54a1558dbc710546be1f42544be72/gradle.properties — SHA перевірено
- https://github.com/Lothrazar/RootsClassic/blob/db9aa883b7a54a1558dbc710546be1f42544be72/src/main/java/elucent/rootsclassic/block/imbuer/ImbuerBlockEntity.java — SHA перевірено

## `actuallyadditions:crystallized_oil_bucket`

Статус: `source_verified_native_path`; версія: 1.3.26.

Киньте один Crystallized Canola Seed у source-блок refined_canola_oil. CanolaSeed міняє блок на CRYSTALLIZED_OIL; InitFluids реєструє його як crystallized_oil, а FluidAA зв’язує crystallized_oil_bucket. Наповніть відро рідиною. Кидайте насіння по одному: native kill видаляє весь стек-сутність.

- https://github.com/Ellpeck/ActuallyAdditions/tree/cd9d9c63254f471f966ee51b078afdf47af5f852 — SHA перевірено
- https://github.com/Ellpeck/ActuallyAdditions/tree/cd9d9c63254f471f966ee51b078afdf47af5f852 — SHA перевірено
- https://github.com/Ellpeck/ActuallyAdditions/tree/cd9d9c63254f471f966ee51b078afdf47af5f852 — SHA перевірено
- https://github.com/Ellpeck/ActuallyAdditions/tree/cd9d9c63254f471f966ee51b078afdf47af5f852 — SHA перевірено

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
