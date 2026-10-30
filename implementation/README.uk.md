# Стан реалізації AIA2

Основна інструкція: [README.uk.md](../README.uk.md). Встановлення:
[INSTALL.uk.txt](INSTALL.uk.txt), [резервування й відкат](INSTALLER-SAFETY.uk.md).

Поточний checkpoint 0.4.19-alpha містить 48 епох, 3375 квестів (3279 без 96
старих ручних цілей), 140 глав, шість груп, 627 нативних рецептів, 48 серверних формул
фінального гравіювання, 390 власних предметів, моделей і PNG. Результати
завершеного запуску перевірок і контрольні суми беріть зі
[звіту релізу](release-report.json).

- Machine Guard, Java/Rhino UUID та ProjectE: [guard-v4-audit.json](guard-v4-audit.json).
- Дві обов'язкові гілки та 96 виробничих ключів: [механіка й міграція](../design/progression-v4.md), [dual-key-report.json](dual-key-report.json).
- Нові рецепти 22 просторів імен: [recipes-v4-audit.json](recipes-v4-audit.json), [каталог](../content/recipes/v4_expansion.json).
- Авторські курси й автоматизація: [quests-v4-audit.json](quests-v4-audit.json), [каталог](../content/quests/v4_mod_depth.json).
- Усі епохи, компоненти й підсумкові кількості: [expansion-report.json](expansion-report.json).
- Ресурси: [resource-report.json](resource-report.json), [96 нових ключів](resource-dual-report.json), [огляд](dual-keys-preview.png).
- Нативний JAR і серверні перевірки: [companion/verification-report.json](../companion/verification-report.json).
- SNBT, ID та граф: [validation-report.json](validation-report.json), [content-validation-report.json](content-validation-report.json).
- Виробнича доступність: [прогресія](../content/audit/progression-audit.json), [джерела предметів](../content/audit/quest-obtainability.json), [пізні епохи](../content/audit/late-obtainability.json).
- Межі інтеграції: [обходи](bypass-audit.json), [адаптери](native-adapter-review.json), [Robit і brewing](compatibility-adapters-report.json).
- [Відомі обмеження й ручні тести](KNOWN_LIMITATIONS.uk.txt), [зміни](CHANGELOG.uk.md).

`generation-report.json`, `phase-02-report.json`, `stabilization-report.json`
та попередні секції нативного звіту містять історичні результати. Вони не
замінюють поточний release-report. Справжній Rhino, мінімальний нативний
сервер і повна Minecraft-збірка є різними рівнями перевірки. Повний
Windows-інстанс, додаткові модові перехоплення, клієнтські ресурси й TPS
залишаються приймальними перевірками у грі.

Поточний NASA-підблок: [checkpoint](../docs/AIA2_0.4.18_CHECKPOINT.uk.md),
[перевірки](nasa-production-verification-v7.json). Повний0.5 ще не завершено.

Station payment/placement: [checkpoint](../docs/AIA2_0.4.19_CHECKPOINT.uk.md),
[перевірки](station-verification-v8.json); нових квестів/рецептів/предметів0.
