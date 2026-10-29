# ProjectE0.4.17 — реальний клієнтський retest

Ці сценарії ще **NOT RUN**. Isolated Sponge/source fixture і мінімальний
NeoForge сервер не є повним клієнтом з установленим ProjectE1.1.0.

1. Закрийте гру/сервер. Оновіть репозиторій або розпакуйте hotfix. Виконайте
   `python install_runtime.py "C:\CurseForge\AllInOneAdventure2" --dry-run`.
   Перевірка Tablet ABI має завершитися до будь-якої зміни файлів.
2. Встановіть без прапорця; збережіть створений backup. У `mods/` має бути
   один активний `aia2-machine-guard-0.4.17-alpha.jar`. Інші моди не замінюйте.
3. Запустіть саме Minecraft1.21.1 / NeoForge21.1.264 / ProjectE1.1.0 /
   FTB Quests2101.1.36 із попереднього тесту. Перевірте відсутність
   `InvalidInjectionException`, broken mod state та незавершеного resource reload.
4. Дочекайтеся головного меню й відкрийте тестову копію світу. Перевірте
   `/aia2 status`,140глав, українські тексти, theme/shapes та іконки FTB.
   Підтвердіть відсутність повторного `skyroot_log` NPE при нормальному виході.
5. У ранній команді імпортована Tablet не повинна відкривати трансмутацію.
   На фактично відкритій45епосі перевірте фізичний Table, на47 — ручну Tablet,
   обидві руки, зміну команди/стадії при відкритому меню, click/quickmove та EMC.
   Curios-shortcut пізнішої unreleased-гілки тут не є вимогою.
6. Звірте key/manufacturing receipts, FTB completion, knowledge/EMC і прогрес
   після restart. Хотфікс не повинен видавати ключі, очищати знання або скидати світ.

Незалежна read-only перевірка повного ProjectE contract набору:

```text
python tools/check_optional_mixin_targets_v6.py --guard mods/aia2-machine-guard-0.4.17-alpha.jar --target-jar "C:\CurseForge\AllInOneAdventure2\mods\ProjectE-1.21.1-PE1.1.0.jar" --report projecte-abi.json
```

Tool перевіряє21ProjectE-targeting Mixins; інсталятор — критичний Tablet redirect.
Звіт із JAR SHA і version дає бінарні докази, але не підтверджує весь клієнт.
Якщо повториться crash, аналізувати перший fatal нового latest.log разом із
crash-report; не видаляти FTB чи Aether data для приховування наступних помилок.
