# All in One Adventure 2.0 — AIA2

**0.4.15-alpha** targets Minecraft1.21.1 NeoForge, FTB Quests2101.1.36, KubeJS2101.7.2 and Rhino85. Full0.5 remains in progress.

**48epochs,96manufactured keys,3351quests in140chapters,623recipes,390items/models/PNGs.** This checkpoint records historical Clibano dependencies. Existing quests, recipes, rewards, IDs and coordinates remain unchanged; no new content is added here.

Cooking checks current ingredient tags, enhancer definitions and residue definitions. A separate NBT ledger records historical lane snapshots and definition+quantity for accumulated residues. Changed rules after reload/restart pause the operation while preserving data. Stale Ingredient caches and unchanged holder IDs cannot certify earlier payment. One finish cannot credit a residue twice.

Old dependent paid lanes and positive residue balances without witnesses remain paused. Finish old work before upgrading when possible. `/aia2clibano status x y z` diagnoses it. Operator-only `cancel` backs up and clears cooking progress only; explicit `quarantine-residues` moves residue stock/history into a bounded8NBTbackup without output/refund/proof, preserving slots/fuel/cooking counters. The installer never invokes these commands.

233Python/57Node/5237Java/151minimal-Minecraft assertions PASS;285new modeled assertions and14actual-NBT checks. Full Clibano weaving/JEI/UI/Survival/TPS are NOT RUN. Frame IO, generic copied components and universal rollback remain outside this scope.

Stop the game/server, install `nbtlib==2.0.4`, run `python install_runtime.py "C:\CurseForge\AllInOneAdventure2" --dry-run`, then omit the flag. Matching0.4.15JAR/scripts and a full restart are required on both sides. Originals and the old owned JAR are backed up while worlds/progress/foreign quests are preserved.

[Checkpoint](docs/AIA2_0.4.15_CHECKPOINT.uk.md) · [Install](implementation/INSTALL.uk.txt) · [PLAN](docs/AIA2_0.5.0_PLAN.md) · [PROGRESS](docs/AIA2_0.5.0_PROGRESS.md) · [Maps](docs/research/MOD_MECHANICS.md) · [Sources](docs/research/SOURCE_INDEX.md) · [Acceptance](docs/testing/CLIBANO_DEPENDENCIES_ACCEPTANCE.uk.md).
