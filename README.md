# QuestModpack — All in One Adventure 2.0

[Українська інструкція](README.uk.md).

Version **0.4.1-alpha** targets Minecraft **1.21.1 NeoForge**, FTB Quests **2101.1.36**, KubeJS **2101.7.2** and Rhino **2101.2.7 build.85**.

The FTB team lookup hotfix selects the Entity overload in a typed Java bridge; the UUID overload expects a team UUID. Install its matching companion JAR and scripts together. Ongoing 0.5 work is tracked in [PLAN](docs/AIA2_0.5.0_PLAN.md) and [PROGRESS](docs/AIA2_0.5.0_PROGRESS.md).

The update fixes the reported UUID and ProjectE overload failures, requires Machine Guard **API 4**, and adds **two manufactured keys per epoch**. Native production receipts are saved separately from item possession; `/give` does not manufacture a key or open the next epoch. Existing epoch IDs and completed team progress are retained.

The pack contains **48 epochs, 2784 quests across 130 chapters**, six groups, 569 native recipes and 390 custom item models/textures. The quest total includes 96 preserved legacy manual goals, leaving 2688 substantive quests.

Installable files are in `kubejs/`, `config/` and `mods/`. Use `install_runtime.py` for preflight, backups, merging and rollback. Update the companion JAR and scripts together, then fully restart the game/server.

Current counts, validation results and remaining acceptance work are in [release-report.json](implementation/release-report.json). See [v4 progression](design/progression-v4.md), [guard audit](implementation/guard-v4-audit.json) and [known limits](implementation/KNOWN_LIMITATIONS.uk.txt). Full-pack gameplay, optional mod hooks and TPS are separate from static/Rhino/native smoke tests.
