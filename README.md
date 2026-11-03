# All in One Adventure 2.0 — AIA2

**0.4.24-alpha — exact CDG Mold profile objectives.**
Minecraft1.21.1 NeoForge / FTB Quests2101.1.36 / KubeJS2101.7.2 / Rhino85.
The full0.5 update remains in progress.

Six optional goals distinguish Lines, Bowl, Chain and Bar components and teach
their compression/casting applications. FTB fuzzy matching requires the full
profile identifier while permitting an extra item name. Generic Mold or another
profile cannot satisfy these predicates; product samples are not production proof.

**3402quests/140chapters/6groups,627recipes,3138item rewards,390items/models/PNGs,
48epochs and96manufactured keys.** All3396old non-coordinate quest payloads
remain identical.20old coordinates moved in one chapter. Old generic Mold tasks,
rewards, dependencies and completed progress are preserved.

Source/compiler/compiled/package/installer checks reject malformed or missing
predicates before deployment. Actual Minecraft tests confirmed that partial
ItemStack decoding can discard a bad component and broaden a filter.43pinned
source/recipe files and a separate native API fact document the boundary.

329actual minimal-server assertions across2JVMs include56new codec/map checks,
using an opt-in IDE-only synthetic component.88actual FTB matcher assertions
use a modeled host. Original CDG/FTB UI, full client, JEI, Survival and TPS are
not tested. API4,16native rules,76Mixins and guard policy classes remain unchanged.

Stop Minecraft, extract separately, then run
`python install_runtime.py "C:\CurseForge\AllInOneAdventure2" --dry-run`.
Run again without the flag and restart both sides fully. Changed files and the
old owned JAR are backed up; worlds and player/team progress are never edited.

[Checkpoint](docs/AIA2_0.4.24_CHECKPOINT.uk.md) ·
[Install](implementation/INSTALL.uk.txt) ·
[Acceptance](docs/testing/CDG_MOLDS_ACCEPTANCE.uk.md) ·
[PLAN](docs/AIA2_0.5.0_PLAN.md) · [PROGRESS](docs/AIA2_0.5.0_PROGRESS.md).
