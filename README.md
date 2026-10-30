# All in One Adventure 2.0 — AIA2

**0.4.19-alpha — Ad Astra station payment and placement checkpoint.**
Minecraft1.21.1 NeoForge / FTB Quests2101.1.36 / KubeJS2101.7.2 / Rhino85.
Full0.5 remains in progress; original optional binaries and the complete client
have not been tested.

Station construction now uses a packet scope, live owner-team/destination checks,
and bounded global payment allocation. Split stacks pay the full requirement;
overlapping ingredients cannot spend one unit twice. All non-air primary writes
must be accepted and retained before registration/teleport continues. Native
partial effects are preserved on failure; no rollback/refund is fabricated.

**48epochs,96manufactured keys,3375quests/140chapters,627recipes,
3111item rewards,390items/models/PNGs are preserved.** No new quests, recipes,
rewards, items or textures in this guard block. Only six native station recipe
floors rise to their orbit's37/38 stage. Old station SavedData, NASA proofs,
ProjectE hotfix and API4 remain.

The installer checks six optional NASA/station Mixin contracts against an available
Ad Astra JAR before backup/write; ProjectE tablet preflight remains. The supported
station template has one palette, no entities/blockNBT and bounded dimensions.
Custom definitions outside this contract are rejected before payment. Ordinary
unscoped structure placement keeps native behavior.

Stop Minecraft and extract the package to a separate folder. Run
`python install_runtime.py "C:\CurseForge\AllInOneAdventure2" --dry-run`, then
omit the flag. Originals/old owned JAR are backed up. Restart both sides fully.

[Checkpoint](docs/AIA2_0.4.19_CHECKPOINT.uk.md) ·
[Install](implementation/INSTALL.uk.txt) ·
[Station acceptance](docs/testing/STATION_CONSTRUCTION_ACCEPTANCE.uk.md) ·
[PLAN](docs/AIA2_0.5.0_PLAN.md) · [PROGRESS](docs/AIA2_0.5.0_PROGRESS.md).
