# 0.4.22-alpha — збереження журналу ключів і точні космічні віхи

База: `35a4d5d` /0.4.21-alpha. Це окремий checkpoint; повний0.5 ще не готовий.

У дванадцяти старих віхах епох37–38 змінено лише українські назви та описи.
Вони прямо розрізняють показ предмета й здачу з витратою. Наявність ракети,
зливка чи магічного трофея не оголошується доказом польоту, автоматизації
або справжньої збірки NASA. Чотири окремі required NASA goals, шість optional
station goals та всі правила переходів попереднього checkpoint збережені.

3381квест/140глав/6груп,627рецептів,3117item rewards,390предметів/моделей/PNG,
48епох і96виробничих ключів. Нових квестів/рецептів/нагород/предметів/текстур0.
ID, task payloads/types/counts, rewards, dependencies, optional flags, icons
і координати всіх3381цілей незмінні;3369повних payloads незмінні повністю.
7runtimeconfigs/782assets/627recipeentries збережені byte-for-byte.

Підтверджено першопричину ризику журналу ключів: vanilla DimensionDataStorage
може поглинути IO/load exception й повернути null; computeIfAbsent потім
встановлює порожній SavedData. Наступний dirty-save міг замінити історію.
KeyProductionBridge тепер читає journal ліниво, суворо перевіряє schema1/NBT
і залишає blocked sentinel для наявного нечитаного файла. Такий файл не
перезаписується; читання proof і нові записи блокуються з повідомленням.

Ліміти читання/запису узгоджені:16384команди/96proofs накоманду. Усі96
канонічних ключів round-trip без зміни. Старі parse-valid aliases08/+8
зберігаються буквально й не стають новими канонічними proof. Повторний
реальний proof ідемпотентний; читання/reload не додає доказів. API4 та
наявні world-save names/schema1 збережені; installer не мігрує TeamData.

Matching JAR має compiled journalProtectionVersion1. Пакувальник та installer
перевіряють його до backup/write. Це захист від випадкового старого JAR,
а не заміна поведінкових тестів.76mixins і їхня конфігурація незмінні.

Перевірки PASS:393Python/0fail/0skip,79Node,5237Java;273actual minimalMC
assertions у2JVM/650ticks.231actual-key journal modeled assertions,424key/action
modeled checks; старий computeIfAbsent FAIL у негативному контролі. Seed191
rebuild1183non-JAR runtimefiles byte-identical, central14JSsyntax/SNBT/ID/DAG/
requiredclosure/presentation PASS. Повний клієнт цими числами не засвідчено.

Точні звіти:
- implementation/space-milestones-preservation-v11.json — міграція12текстів;
- implementation/key-journal-jar-v11.json — compiledJAR та збереження класів;
- implementation/key-journal-verification-v11.json — остаточні QA/межі;
- implementation/key-journal-package-install-v11.json — перевірка пакета.

Межі доказів: modeled IO/hook tests, actual common Minecraft NBT/SavedData
і дві JVM перевіряються окремо. У minimal-server fixture лише8tech створюється
реальним commonкрафтом;37tech — явно синтетичний proof для restart. Повний
original optional binary/client/JEI/Survival/TPS NOT_RUN. Відсутній original
ProjectE binary має BLOCKED ABI report; hotfix не оголошується retested.

Зупиніть гру, розпакуйте пакет окремо, виконайте installer --dry-run, потім
без прапорця й повністю перезапустіть обидві сторони. Installer резервує
змінені оригінали/старий власний JAR, не редагує світи/журнали/прогрес.
При помилці journal не видаляйте його: збережіть оригінал і перевіряйте
відновлення з backup лише на окремій копії світу.

Джерела: docs/research/KEY_JOURNAL_PRESERVATION.uk.md та
docs/research/SPACE_MILESTONES.uk.md. Ручне приймання повного інстансу:
docs/testing/KEY_JOURNAL_ACCEPTANCE.uk.md.

Наступний змістовний блок —34partialкарти/рештаrequired48ліній. NASA/station
докази, перехід37/38, назви дванадцяти віх та key journal не повторювати.
