# 0.4.17-alpha — ProjectE startup hotfix

База: `b428e08` / 0.4.16-alpha. Це окремий hotfix розробки0.5;
повний реліз0.5 не завершено. Реальний Windows-інстанс не змінювався.

## Причина

Наш `ProjectETabletSourceMixin` вимагав два `openContainer(...)`, яких немає
в релізному ProjectE1.1.0. Попередній аудит використав пізніший commit
`f432b0c66837759fb0731c9144dc53176b949c5d`, який додав цей API, залишивши
`projecte_version=1.1.0`. Самого збігу version properties було недостатньо.

Релізний commit `6aea247f7056eea1521db3f0c73d656857b75423` має назву
`ProjectE-1.21.1-PE1.1.0`; у ньому `Player.openMenu(...)` викликається
безпосередньо в `TransmutationTablet.use(Level,Player,InteractionHand)`.
Redirect перенесено на цей точний JVM descriptor. `require=1`, stage47,
серверний permission helper та source-floor меню збережені; Mixin не вимкнено.
`No refMap loaded` не пояснює відсутні методи: цей target використовує `remap=false`.

Звірено всі24ProjectE mixins:21 спрямовано на20класів ProjectE,3 — Minecraft.
Окрім Tablet, інших відсутніх source methods/call-site назв не знайдено.
Для36active research sources додано release counterparts:35еквівалентних,
1змінений Tablet,0відсутніх. Історичні файли не видалено; provenance виправлено.
CurioItemCapability присутній у release; його passive/attribute guards збережені.

## Відтворення та перевірки

- Справжній Sponge `0.16.4+mixin.0.8.7`, як у логах, відтворив
  `InvalidInjectionException` старих selectors на класі, скомпільованому з
  exact release source. Залежності Minecraft/ProjectE в цьому host модельовані.
- Той самий transformer застосував виправлений redirect: один виклик helper,
  один guarded call у `use`, жодного початкового unchecked `Player.openMenu` там.
- Classfile checker читає compiled annotations, method descriptors і INVOKE
  owner/name/descriptor/ordinal. Неправильні return/callee signatures відхиляються;
  без target artifact повертається `BLOCKED`, не `PASS`. Slices/довільні трансформери
  та весь pipeline він не моделює.
- Installer preflight читає встановлений `ProjectE*.jar`, якщо він є, і звіряє
  критичний Tablet contract до backup/write. Негативний тест старого redirect
  зберігає world marker й не створює backup/kubejs; позитивний dry-run теж не пише.
- CI спочатку збирає companion, щоб отримати справжні Sponge/ASM залежності,
  а потім запускає regression; історичний source fixture працює без Git history.
- Пройдено263Python/57Node тестів,5237Java policy assertions, JDK21build,
 151minimal-Minecraft assertions у2JVM/650ticks і targeted10 після portable-fixture
  уточнення. Оригінальний ProjectE в мінімальному сервері відсутній.

**Точний binary/full-client test не виконано.** Завантаження офіційного JAR
блокує HTTP403 навіть після повторного дозволеного запиту; JAR інстансу не надано.
Це явно зафіксовано в `implementation/projecte-hotfix-binary-abi-v6.json`.
Source compilation і справжній transformer на fixture не є доказом успішного
запуску всього модпаку. Потрібен [клієнтський retest](testing/PROJECTE_CLIENT_HOTFIX_ACCEPTANCE.uk.md).

## FTB Quests та Aether

У наданому latest.log перший fatal — ProjectE Mixin (рядок1122).
Після construction failure й broken mod state (1460–1462) відсутні нормальні
mod resource packs. ThemeLoader (1528) бачить порожні ресурси, а
QuestShape.reload (1531+) викликає `iterator().next()` на порожній мапі.
У exact FTB2101.1.36 source тема та10shape backgrounds наявні.
Зміна quest SNBT чи створення fallback-theme тут не усуває первинну помилку.

`aether:skyroot_log` стає unbound під час аварійного logout/disconnect:
`emergencySaveAndCrash → ClientHooks.firePlayerLogout → AetherClient → ToolHooks`.
Це вже після зірваної ініціалізації реєстрів. Логи не доводять незалежної
первинної несправності Aether; після hotfix потрібен новий client log.
FTB/Aether конфіги, світи й прогрес не змінювалися. Сирі логи й приватні
ідентифікатори не комітяться; збережено sanitized audit і4FTB SHA-джерела.

## Збереження та встановлення

3371квест/140глав,627рецептів,96ключів,390предметів/моделей/PNG без змін.
1171non-JAR runtime-файл byte-identical;201із202Java classes незмінні.
71Mixins і всі permission/manufacturing/SavedData guards збережені.
Нових quests/recipes/rewards/items/textures:0.

Закрийте Minecraft, розпакуйте пакет і запустіть інсталятор із `--dry-run`,
потім без прапорця. Він резервує оригінали й старий власний JAR, не видаляє
світи/прогрес/сторонні квести та моди. Full restart потрібен на обох сторонах.
Окремі звіти: `projecte-hotfix-jar-v6.json`, `projecte-hotfix-preservation-v6.json`,
`projecte-hotfix-verification-v6.json`, `projecte-hotfix-package-install-v6.json`.

Після стабілізації повернутися до NASA accepted-output/payment witness і
station split-stack payment/accepted placement adapter. Решта плану0.5,
34partial-карти та required лінії48епох залишаються в роботі.
