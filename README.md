# All in One Adventure 2.0 — AIA2

**0.4.14-alpha** targets Minecraft 1.21.1 NeoForge, FTB Quests 2101.1.36, KubeJS 2101.7.2 and Rhino build85. The full 0.5 plan remains in progress.

**48 epochs, 96 manufactured keys, 3351 quests in 140 chapters, 623 recipes, 390 items/models/PNGs.** This checkpoint strengthens paid Forbidden Forge rituals. All existing quests, recipes, rewards, coordinates and IDs are unchanged; no new content is added here.

Payment now records current item-tag memberships and required/installed enhancer definitions. Changed dependencies after reload pause the operation while preserving its state. Existing schema1 receipts remain readable: an old dependency-free ritual may resume, while an operation with unproven historical dependencies stays paused. Current datapack data never becomes evidence of an earlier payment.

Checks: 230 Python, 57 Node, 5237 Java, 137 minimal-Minecraft assertions across 2 JVMs; 157 new modeled cases and 18 actual-NBT checks. Full Forbidden weaving, JEI/UI, Survival and TPS are NOT RUN. Clibano transitive definitions and historical residues remain open.

Stop the game/server, install `nbtlib==2.0.4`, run `python install_runtime.py "C:\CurseForge\AllInOneAdventure2" --dry-run`, then omit the flag. Matching 0.4.14 JAR/scripts and a full restart are required on both sides. Originals and the old owned JAR are backed up while worlds/progress/foreign quests are preserved. Finish old active Forge rituals before upgrading when possible. `/aia2forge status x y z` diagnoses paused work; operator-only `cancel` explicitly backs it up without essence refund or output.

[Checkpoint](docs/AIA2_0.4.14_CHECKPOINT.uk.md) · [Install](implementation/INSTALL.uk.txt) · [PLAN](docs/AIA2_0.5.0_PLAN.md) · [PROGRESS](docs/AIA2_0.5.0_PROGRESS.md) · [Maps](docs/research/MOD_MECHANICS.md) · [Sources](docs/research/SOURCE_INDEX.md) · [Acceptance](docs/testing/FORBIDDEN_DEPENDENCIES_ACCEPTANCE.uk.md).
