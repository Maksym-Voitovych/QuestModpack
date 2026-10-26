# QuestModpack — All in One Adventure 2.0

[Українська інструкція](README.uk.md).

Version **0.4.7-alpha** targets Minecraft **1.21.1 NeoForge**, FTB Quests2101.1.36, KubeJS2101.7.2 and Rhino2101.2.7 build85. The complete0.5 update remains in progress.

The runtime contains **48 epochs, 96 manufactured keys, 3261 quests in139 chapters, 615 native recipes and390 custom item models/textures**. It retains96 legacy manual goals. All3242 previously published quest/task/reward payloads and dependencies are preserved, apart from layout coordinates; all610 existing custom recipe entries remain unchanged.

This block adds18 EnderIO core quests, one actual-production Powah quest, five native machine recipes and two durable team-bound process rules. EnderIO cached tasks, actual item outputs, Crafter and Tank operations are checked before production. Powah validates the receiving Orb rather than borrowing its Rod caller's stage; callback recipe selection stays independent of startup/caller readiness while actual execution remains guarded. Generated EnderIO smelting conversions are checked against their native source.

Install matching `kubejs/`, `config/` and `mods/` through `install_runtime.py` with `--dry-run` first, with the game stopped. The installer backs up originals, preserves saves/foreign quests and requires the matching0.4.7/API4 companion. Fully restart client and server.

Verification results and limits are in the [checkpoint](docs/AIA2_0.4.7_CHECKPOINT.uk.md). Source and modeled helper tests are distinct from minimal native Minecraft and full-pack tests. Optional mod dispatch, JEI/UI, Survival andTPS remain untested. Unattributed EnderIO world Fire Crafting remains an explicit ownership gap; its legitimate grain progression has not been disabled.

[PLAN](docs/AIA2_0.5.0_PLAN.md) · [PROGRESS](docs/AIA2_0.5.0_PROGRESS.md) · [Mechanic maps](docs/research/MOD_MECHANICS.md) · [Sources](docs/research/SOURCE_INDEX.md) · [Remaining coverage](docs/research/REMAINING_COVERAGE.md) · [Industrial acceptance](docs/testing/INDUSTRIAL_NATIVE_ACCEPTANCE.uk.md).

Core maps cover22 mods;38 maps are partial and further content remains unmapped. This is an interim development build, not the completed0.5 release.
