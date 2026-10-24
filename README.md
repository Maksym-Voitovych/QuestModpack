# QuestModpack — All in One Adventure 2.0

[Українська інструкція](README.uk.md).

Version **0.4.3-alpha** targets Minecraft **1.21.1 NeoForge**, FTB Quests 2101.1.36, KubeJS 2101.7.2 and Rhino 2101.2.7 build 85. The complete 0.5 update remains in progress.

The current runtime contains **48 epochs, 96 manufactured keys, 3145 quests in 136 chapters, 603 native recipes and 390 custom item models/textures**. The total retains 96 legacy manual goals. All 3061 published checkpoint quest/task/reward IDs and dependencies, 602 existing recipe JSONs and completed team progress are preserved.

This block adds 84 mechanic quests, 49 native action contracts, 10 completed core maps and a postgame creative Mana Tablet recipe. Component-aware guards cover its native player mana-source lists and pool exchange. Three creative tablet producer routes are closed; ordinary tablets remain available at epoch 5. FTB team lookup uses a typed Java bridge; key manufacture uses separate team-bound post-consumption receipts.

Install matching `kubejs/`, `config/` and `mods/` through `install_runtime.py` with `--dry-run` first, with the game stopped. The installer backs up originals and preserves saves/foreign quests. Fully restart both client and server.

Validated: 110 Python tests, 50 Node tests, 5237 Java assertions, 22 modeled creative-mana guard assertions, and 49 minimal native Minecraft assertions across two server JVMs with restart persistence. Optional mod dispatch, JEI/UI, full Survival and TPS remain untested.

[PLAN](docs/AIA2_0.5.0_PLAN.md) · [PROGRESS](docs/AIA2_0.5.0_PROGRESS.md) · [Milestone report](implementation/v5-milestone-report.json) · [Mechanic maps](docs/research/MOD_MECHANICS.md) · [Sources](docs/research/SOURCE_INDEX.md) · [Remaining coverage](docs/research/REMAINING_COVERAGE.md) · [Manual acceptance](docs/testing/NATIVE_ACTION_ACCEPTANCE.uk.md).

Core maps are complete for 13 mods; 45 maps are partial and additional content mods remain unmapped. This is an interim development build. The 0.5 release remains unfinished.
