# All in One Adventure 2.0 — AIA2

**0.4.17-alpha — ProjectE startup hotfix.** Minecraft1.21.1 NeoForge,
FTB Quests2101.1.36, KubeJS2101.7.2 / Rhino85. Full0.5 remains in progress.

The tablet redirect now targets released PE1.1.0 `use(...)`. Its previous
`openContainer(...)` selectors came from a later development commit retaining
the same version properties. `require=1`, stage47 and server permissions remain.

The installer checks the critical compiled tablet contract against the instance's
ProjectE JAR before any backup/write. A separate tool can check all ProjectE
method/invocation contracts against supplied artifacts; it does not certify weaving.

**48epochs,96manufactured keys,3371quests/140chapters,627recipes,
390items/models/PNGs are preserved.** Only one Java class changes;201classes
and all1171non-JAR runtime files remain byte-identical.

Real Sponge0.8.7 reproduces the old InvalidInjectionException and applies the
fixed redirect to the exact release-source class compiled with modeled dependencies.
The original ProjectE binary and full client have NOT been tested: artifact delivery
is blocked by HTTP403 and the installed JAR was not supplied. The FTB theme/shape
and Aether logout errors follow the broken mod state; their files are untouched.

Stop Minecraft, extract the package and run
`python install_runtime.py "C:\CurseForge\AllInOneAdventure2" --dry-run`, then omit
the flag. Originals and the old owned JAR are backed up; worlds, player progress
and foreign content are preserved. Restart both sides completely.

[Hotfix report](docs/AIA2_0.4.17_HOTFIX.uk.md) · [Install](implementation/INSTALL.uk.txt) · [Client acceptance](docs/testing/PROJECTE_CLIENT_HOTFIX_ACCEPTANCE.uk.md) · [PLAN](docs/AIA2_0.5.0_PLAN.md) · [PROGRESS](docs/AIA2_0.5.0_PROGRESS.md) · [Previous Ad Astra checkpoint](docs/AIA2_0.4.16_CHECKPOINT.uk.md).
