# QuestModpack — All in One Adventure 2.0

[Українська інструкція](README.uk.md).

Version **0.4.2.1-alpha** targets Minecraft **1.21.1 NeoForge**, FTB Quests **2101.1.36**, KubeJS **2101.7.2** and Rhino **2101.2.7 build.85**.
This interim version adds four native team-bound production observations. Their persistence is separate from epoch keys. The complete 0.5 update remains in progress; see PROGRESS.


The FTB team lookup hotfix selects the Entity overload in a typed Java bridge; the UUID overload expects a team UUID. Install its matching companion JAR and scripts together. Ongoing 0.5 work is tracked in [PLAN](docs/AIA2_0.5.0_PLAN.md) and [PROGRESS](docs/AIA2_0.5.0_PROGRESS.md).

The update fixes the reported UUID and ProjectE overload failures, requires Machine Guard **API 4**, and adds **two manufactured keys per epoch**. Native production receipts are saved separately from item possession; `/give` does not manufacture a key or open the next epoch. Existing epoch IDs and completed team progress are retained.

The pack contains **48 epochs, 2784 quests across 130 chapters**, six groups, 569 native recipes and 390 custom item models/textures. The quest total includes 96 preserved legacy manual goals, leaving 2688 substantive quests.

Installable files are in `kubejs/`, `config/` and `mods/`. Use `install_runtime.py` for preflight, backups, merging and rollback. Update the companion JAR and scripts together, then fully restart the game/server.

Current counts, validation results and remaining acceptance work are in [release-report.json](implementation/release-report.json). See [v4 progression](design/progression-v4.md), [guard audit](implementation/guard-v4-audit.json) and [known limits](implementation/KNOWN_LIMITATIONS.uk.txt). Full-pack gameplay, optional mod hooks and TPS are separate from static/Rhino/native smoke tests.

The current 0.5 development milestone contains 3,061 quests in 136 chapters and 602 native recipes. All 2,784 v4 quest IDs and 569 recipe JSONs are retained. See [mechanic maps](docs/research/MOD_MECHANICS.md), [source index](docs/research/SOURCE_INDEX.md), [remaining coverage](docs/research/REMAINING_COVERAGE.md), and the [milestone report](implementation/v5-milestone-report.json). Complete core maps cover Create/Mekanism/AE2; remaining maps and full-pack acceptance are unfinished. This is not a completed 0.5 release.
