# QuestModpack — All in One Adventure 2.0

[Українська інструкція](README.uk.md).

Version **0.4.6-alpha** targets Minecraft **1.21.1 NeoForge**, FTB Quests2101.1.36, KubeJS2101.7.2 and Rhino2101.2.7 build85. The complete0.5 update remains in progress.

The runtime contains **48 epochs, 96 manufactured keys, 3242 quests in138 chapters, 610 native recipes and390 custom item models/textures**. It retains96 legacy manual goals. All3212 previously published quest/task/reward payloads and dependencies are preserved, apart from layout coordinates; all606 existing custom recipe entries remain unchanged.

This block adds30 researched MI/Oritech quests, two core maps, four cross-mod machine recipes and11 native action contracts. MI direct recipe selection, paid caches, generated conversions and Replicator output now have server policy checks. Oritech cached/direct-list processors, fluid commits and dust compaction are guarded. Roots mutations require complete ingredients and Radiant Daisy works at noon on later days.

Install matching `kubejs/`, `config/` and `mods/` through `install_runtime.py` with `--dry-run` first, with the game stopped. The installer backs up originals, preserves saves/foreign quests and requires the matching0.4.6/API4 companion. Fully restart client and server.

Verification results and scope are in the [checkpoint](docs/AIA2_0.4.6_CHECKPOINT.uk.md). The minimal native Minecraft test passed61 assertions across two JVMs with restart persistence. Optional mod dispatch, JEI/UI, full Survival andTPS remain untested. MI paid conversions/restart semantics and native Atomic Forge RF behavior have explicit limits.

[PLAN](docs/AIA2_0.5.0_PLAN.md) · [PROGRESS](docs/AIA2_0.5.0_PROGRESS.md) · [Mechanic maps](docs/research/MOD_MECHANICS.md) · [Sources](docs/research/SOURCE_INDEX.md) · [Remaining coverage](docs/research/REMAINING_COVERAGE.md) · [Industrial acceptance](docs/testing/INDUSTRIAL_NATIVE_ACCEPTANCE.uk.md).

Core maps cover21 mods;39 maps are partial and further content remains unmapped. This is an interim development build, not the completed0.5 release.
