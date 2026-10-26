# QuestModpack — All in One Adventure 2.0

[Українська інструкція](README.uk.md).

Version **0.4.8-alpha** targets Minecraft **1.21.1 NeoForge**, FTB Quests2101.1.36, KubeJS2101.7.2 and Rhino2101.2.7 build85. The complete0.5 update remains in progress.

The runtime contains **48 epochs, 96 manufactured keys, 3280 quests in139 chapters, 618 native recipes and390 custom item models/textures**. It retains96 legacy manual goals. All3261 previously published quest/task/reward payloads and dependencies are preserved, apart from layout coordinates; all615 existing custom recipe entries remain unchanged.

This block adds18 researched Powah core quests, one EnderIO worksite tutorial and three cross-mod Nitro generator upgrades using Create mechanical crafting. Fire Crafting and Fire Water share a guarded native spawn edge. Explicitly claim a valid base at epoch19 by sneak-right-clicking its TOP face with flint and steel, then ignite normally. The base owns the process; natural/unclaimed sites cannot produce. Existing sites need one claim after updating.

Install matching `kubejs/`, `config/` and `mods/` through `install_runtime.py` with `--dry-run` first, with the game stopped. The installer backs up originals, preserves saves/foreign quests and requires the matching0.4.8/API4 companion. Fully restart client and server.

Verification results and limits are in the [checkpoint](docs/AIA2_0.4.8_CHECKPOINT.uk.md). Source/model tests are separate from the minimal native Minecraft server and full-pack acceptance. Optional EnderIO/Powah dispatch, JEI/UI, Survival andTPS remain untested. The new station ledger preserves corrupt originals and never replaces them with empty ownership.

[PLAN](docs/AIA2_0.5.0_PLAN.md) · [PROGRESS](docs/AIA2_0.5.0_PROGRESS.md) · [Mechanic maps](docs/research/MOD_MECHANICS.md) · [Sources](docs/research/SOURCE_INDEX.md) · [Remaining coverage](docs/research/REMAINING_COVERAGE.md) · [Fire/Powah acceptance](docs/testing/FIRE_WORKSITE_ACCEPTANCE.uk.md).

Core maps cover23 mods;37 maps are partial and further content remains unmapped. This is an interim development build, not the completed0.5 release.
