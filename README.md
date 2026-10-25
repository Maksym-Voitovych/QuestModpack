# QuestModpack — All in One Adventure 2.0

[Українська інструкція](README.uk.md).

Version **0.4.5-alpha** targets Minecraft **1.21.1 NeoForge**, FTB Quests2101.1.36, KubeJS2101.7.2 and Rhino2101.2.7 build85. The complete0.5 update remains in progress.

The runtime contains **48 epochs,96 manufactured keys,3212 quests in138 chapters,606 native recipes and390 custom item models/textures**. It retains96 legacy manual goals. All3167 published quest/task/reward IDs, dependencies and reward payloads are preserved;603 existing custom recipe entries remain unchanged.

This block adds45 mechanic quests, four core maps, three cross-mod AA recipes and two team-bound Roots ritual proofs. The Roots hook records after the actual altar inventory clears. A native Spawner hook checks advanced runes in both hands before application; six item floors and15 recipe floors match their researched tiers. A misleading early flower objective has a narrow, documented repair.

Install matching `kubejs/`, `config/` and `mods/` through `install_runtime.py` with `--dry-run` first, with the game stopped. The installer backs up originals, preserves saves/foreign quests and requires companion0.4.5/API4. Fully restart client and server.

Validated:126 Python tests,50 Node tests,5237 Java assertions,49 Roots and15 Spawner modeled handler assertions, and49 minimal native Minecraft assertions across two JVMs with restart persistence. Optional mod dispatch,JEI/UI,full Survival andTPS remain untested.

[PLAN](docs/AIA2_0.5.0_PLAN.md) · [PROGRESS](docs/AIA2_0.5.0_PROGRESS.md) · [Current checkpoint](docs/AIA2_0.4.5_CHECKPOINT.uk.md) · [Mechanic maps](docs/research/MOD_MECHANICS.md) · [Sources](docs/research/SOURCE_INDEX.md) · [Remaining coverage](docs/research/REMAINING_COVERAGE.md) · [Manual acceptance](docs/testing/NATIVE_ACTION_ACCEPTANCE.uk.md).

Core maps are complete for19 mods;41 maps are partial and further content remains unmapped. This is an interim development build. The0.5 release remains unfinished.
