# QuestModpack — All in One Adventure 2.0

[Українська інструкція](README.uk.md).

Version **0.4.4-alpha** targets Minecraft **1.21.1 NeoForge**, FTB Quests 2101.1.36, KubeJS 2101.7.2 and Rhino 2101.2.7 build 85. The complete 0.5 update remains in progress.

The current runtime contains **48 epochs, 96 manufactured keys, 3167 quests in 137 chapters, 603 native recipes and 390 custom item models/textures**. The total retains 96 legacy manual goals. All 3145 published checkpoint quest/task/reward IDs, dependencies, existing reward payloads and all 603 recipe entries are preserved. Two old Petroleum item targets have documented corrections.

This block adds 22 mechanic quests for Apotheosis and Immersive Petroleum, 17 native action contracts and two completed core maps. A focused Roots mortar interaction guard checks recipes before ingredient consumption; the previous tick-context guard did not cover pestle interaction. Component-aware creative mana guards, the typed FTB bridge and both team-bound key manufacturing receipts remain active.

Install matching `kubejs/`, `config/` and `mods/` through `install_runtime.py` with `--dry-run` first, with the game stopped. The installer backs up originals and preserves saves/foreign quests. Fully restart both client and server.

Validated: 117 Python tests, 50 Node tests, 5237 Java assertions, 18 modeled Roots handler assertions, and 49 minimal native Minecraft assertions across two server JVMs with restart persistence. Optional mod dispatch, JEI/UI, full Survival and TPS remain untested.

[PLAN](docs/AIA2_0.5.0_PLAN.md) · [PROGRESS](docs/AIA2_0.5.0_PROGRESS.md) · [Milestone report](implementation/v5-milestone-report.json) · [Mechanic maps](docs/research/MOD_MECHANICS.md) · [Sources](docs/research/SOURCE_INDEX.md) · [Remaining coverage](docs/research/REMAINING_COVERAGE.md) · [Manual acceptance](docs/testing/NATIVE_ACTION_ACCEPTANCE.uk.md).

Core maps are complete for 15 mods; 43 maps are partial and additional content mods remain unmapped. This is an interim development build. [Current checkpoint](docs/AIA2_0.4.4_CHECKPOINT.uk.md) records exact counts, sources, tests and next work. The 0.5 release remains unfinished.
