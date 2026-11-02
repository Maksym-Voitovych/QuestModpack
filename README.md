# All in One Adventure 2.0 — AIA2

**0.4.22-alpha — preserved key receipts and accurate space milestones.**
Minecraft1.21.1 NeoForge / FTB Quests2101.1.36 / KubeJS2101.7.2 / Rhino85.
The full0.5 update remains in progress.

The key-production journal now preserves an existing unreadable file instead
of replacing its history with an empty journal. Strict NBT validation, matching
read/write limits and a deployment capability check protect all96receipts.
Historical noncanonical spellings remain literal and grant no new authority.

**3381quests/140chapters,627recipes,3117item rewards,390items/models/PNGs,
48epochs and96manufactured keys.** No tasks, types, counts, reward payloads or
IDs were replaced. Only the titles and descriptions of12existing milestones
in epochs37–38 changed: they explain inventory presence versus consumed resource
submissions. Dependencies, rewards, coordinates and completed progress remain
unchanged. The four required NASA production goals and six optional station
construction goals retain their previous contracts.

API4, the ProjectE hotfix, mechanic/station guards and paid legacy transition
compatibility remain. Automatic, modeled and minimal-server results are recorded
separately; full original optional binaries/client/JEI/Survival/TPS are not tested.

Stop Minecraft, extract to a separate folder, then run
`python install_runtime.py "C:\CurseForge\AllInOneAdventure2" --dry-run`.
Run again without the flag and restart both sides fully. The installer backs up
changed files and the old owned JAR; it never edits world/player progress.

[Checkpoint](docs/AIA2_0.4.22_CHECKPOINT.uk.md) ·
[Install](implementation/INSTALL.uk.txt) ·
[Acceptance](docs/testing/KEY_JOURNAL_ACCEPTANCE.uk.md) ·
[PLAN](docs/AIA2_0.5.0_PLAN.md) · [PROGRESS](docs/AIA2_0.5.0_PROGRESS.md).
