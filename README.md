# All in One Adventure 2.0 — AIA2

**0.4.21-alpha — compatible required NASA progression for epochs37–38.**
Minecraft1.21.1 NeoForge / FTB Quests2101.1.36 / KubeJS2101.7.2 / Rhino85.
The full0.5 update remains in progress.

Four existing NASA production goals are now required: T1+T2 for technology
key37, T3+T4 for key38. Their17preparation goals also enter the required
closure. Native key processing and new transition issuance read actual team
receipts independently of FTB completion flags or old key receipts. All six
station construction goals stay optional.

**3381quests/140chapters,627recipes,3117item rewards,390items/models/PNGs,
48epochs and96manufactured keys.** No tasks, types, counts, reward payloads or
IDs were replaced. Four dependency migrations are explicit; other46epochs'
runtime contracts remain unchanged. Existing completed progress and paid legacy
pending transitions are grandfathered. New37/38pending transactions persist
contract1 and recheck NASA evidence after restart.

The existing mechanic journal now rejects corrupt NBT/unreadable files without
replacing history with an empty map. API4, the ProjectE hotfix and station guards
remain. Full original optional binaries/client/JEI/Survival/TPS are not tested.

Stop Minecraft, extract to a separate folder, then run
`python install_runtime.py "C:\CurseForge\AllInOneAdventure2" --dry-run`.
Run again without the flag and restart both sides fully. The installer backs up
changed files and the old owned JAR; it never edits world/player progress.

[Checkpoint](docs/AIA2_0.4.21_CHECKPOINT.uk.md) ·
[Install](implementation/INSTALL.uk.txt) ·
[Acceptance](docs/testing/SPACE_REQUIRED_ACCEPTANCE.uk.md) ·
[PLAN](docs/AIA2_0.5.0_PLAN.md) · [PROGRESS](docs/AIA2_0.5.0_PROGRESS.md).
