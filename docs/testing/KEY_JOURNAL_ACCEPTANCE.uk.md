# Журнал ключів 0.4.22 — приймання повного інстансу

Статус клієнта: **NOT_RUN**. Цей документ описує перевірку, яку ще потрібно
виконати в повному AIA2 з фактичними optional-модами. Host-тести, перевірка
NBT у development-сервері й успішне складання JAR не замінюють цього запуску.

Контракт і source facts: [KEY_JOURNAL_PRESERVATION.uk.md](../research/KEY_JOURNAL_PRESERVATION.uk.md),
`content/research/evidence/key_journal_v11/manifest.json`,
`companion/src/main/java/ua/aia2/guard/KeyProductionBridge.java`.
Предметні віхи описані в [SPACE_MILESTONES.uk.md](../research/SPACE_MILESTONES.uk.md),
обов’язкові NASA-докази — в [SPACE_REQUIRED_ACCEPTANCE.uk.md](SPACE_REQUIRED_ACCEPTANCE.uk.md).

## Підготовка й установлення

1. Повністю зупинити Minecraft і сервер. Зробити перевірену резервну копію
   інстансу та світу. Створити **окрему одноразову копію інстансу** з власним
   шляхом; усі подальші запуски, NBT-фікстури й навмисні пошкодження виконувати
   тільки там. Не вказувати `C:\CurseForge\AllInOneAdventure2` як ціль тестів.
   Не використовувати Junction на оригінал. Оригінальні світи, журнали,
   installed JAR і player/team data не редагувати.
2. Записати версії Minecraft, NeoForge, Java, KubeJS/Rhino, FTB Quests,
   ProjectE, Create, Mekanism та Ad Astra; SHA-256 matching companion JAR і
   пакета. Окремо зберегти журнали ключів, механік і стан команд зі старої
   тестової копії. Для кожного сценарію нижче брати нову копію одного
   зафіксованого тестового світу, а не продовжувати пошкоджений сценарій.
3. Із кореня розпакованого пакета виконати
   `python install_runtime.py "D:\AIA2-test\instance" --dry-run`.
   Цей шлях — приклад окремої копії. Звірити список операцій: тільки
   `kubejs/`, `config/` та власний companion JAR; світи не повинні входити
   до плану. Порівняти SHA та перелік файлів інстансу до/після dry-run:
   жодних змін або нового `aia2-backups/`.
4. На **окремій копії пакета** замінити bundled companion на старий
   `0.4.21-alpha`, який ще не має `journalProtectionVersion() == 1`, залишивши
   рівно один власний JAR і новий presentation JSON. Запустити dry-run, потім
   звичайний інсталятор у ще одній disposable-копії інстансу. Обидва повинні
   завершитися відмовою `key journal protection capability1` до backup/запису;
   усі файли інстансу мають залишитися побайтово незмінними. Наявності API4
   або потрібної назви JAR недостатньо. Не прибирати marker JSON і не
   підміняти метод заради проходження перевірки.
5. Повернути matching пакет 0.4.22 та застосувати інсталятор до тестової копії.
   Перевірити backup/journal операцій, збереження `config/ftbquests/quests/data.snbt`,
   сторонніх модів та всіх файлів світів до першого запуску. Старий власний
   JAR має бути зарезервований; у `mods/` залишається один активний companion.

## Спостереження за всіма 96 доказами

`/aia2 status` показує загальний стан, але не перелік усіх receipts. Для
ізольованих сценаріїв дозволено додати наведений **тимчасовий read-only probe**
лише до `kubejs/server_scripts/aia2_journal_probe.js` disposable-інстансу.
Він використовує наявний типізований FTB-міст і публічний production-proof
API; не записує receipts, епохи, стадії або FTB completion. Команда доступна
гравцю-оператору. Повний клієнтський запуск цього probe також має статус
NOT_RUN до фактичного виконання.

```javascript
var ProbeKeyGuard = Java.loadClass('ua.aia2.guard.Aia2MachineGuard');
var ProbeFtbBridge = Java.loadClass('ua.aia2.guard.FtbQuestBridge');
var ProbeQuestFile = Java.loadClass('dev.ftb.mods.ftbquests.quest.ServerQuestFile');
ServerEvents.commandRegistry(function (event) {
  var C = event.commands;
  event.register(C.literal('aia2journalprobe')
    .requires(function (source) { return source.hasPermission(2); })
    .executes(function (ctx) {
      var player = ctx.source.getPlayer();
      if (!player) return 0;
      try {
        var data = ProbeFtbBridge.getTeamData(ProbeQuestFile.INSTANCE, player);
        var team = String(data.getTeamId());
        var found = [];
        for (var epoch = 1; epoch <= 48; epoch++) {
          ['tech', 'arcane'].forEach(function (branch) {
            if (ProbeKeyGuard.hasProductionProof(player.server, team, epoch, branch)) {
              found.push(epoch + ':' + branch);
            }
          });
        }
        var text = '[AIA2 journal probe] team=' + team +
          ' canonical=' + found.length + '/96 ' + found.join(',');
        player.tell(text);
        console.info(text);
        return 1;
      } catch (error) {
        var failure = '[AIA2 journal probe] BLOCKED ' + String(error);
        player.tell(failure);
        console.error(failure);
        return 0;
      }
    }));
});
```

Зберегти UUID поточної **FTB-команди** з probe. Він не обов’язково збігається
з UUID гравця. Файл спільного overworld-журналу:
`<корінь тестового світу>/data/aia2_key_production_v1.dat`.
У compressed SavedData NBT власні поля знаходяться всередині compound `data`:
`schema` — INT зі значенням 1; `teams` — COMPOUND;
`teams.<team UUID>` — COMPOUND; кожен proof — BYTE зі значенням 1.
Зберегти зовнішню NBT-обгортку й використовувати NBT
редактор із підтримкою точних типів. Не підміняти весь `.dat` звичайним JSON.

## Сценарії журналу

1. **Відсутній файл, лише читання.** Створити новий disposable-світ. Запустити
   клієнт, перевірити відсутність нових AIA2 Mixin/Rhino помилок, виконати
   `/aia2 status`, `/aia2 sync`, probe, `/reload` і знову probe. Очікується
   `canonical=0/96`, без нового доказу. Чисто закрити світ і перевірити, що
   самі configure/read/reload не створили `aia2_key_production_v1.dat`.
2. **Справжній перший запис.** У Survival завершити потрібні умови гілки й
   виконати реальний нативний рецепт ключа; записати машину, recipe ID,
   списані входи та прийнятий вихід. Probe показує тільки відповідний
   канонічний доказ. Самі `/give`, Creative-одержання та передача ключа від
   іншої команди доказу не створюють. Чисто закрити світ: журнал з’являється
   зі schema INT1. Повністю перезапустити клієнт, повторити probe й перевірити
   збереження доказу та вже завершених епох без повторного списання.
3. **Усі 96, тільки читання.** Лише в зупиненій disposable-копії підготувати
   синтетичний журнал для зафіксованого test-team UUID: усі `1:tech`…`48:tech`
   та `1:arcane`…`48:arcane` як BYTE1, рівно 96. Позначити fixture як
   штучну — вона не є доказом Survival-проходження. Запустити, виконати probe:
   `canonical=96/96`. Виконати `/reload`, дочекатися готовності Machine Guard,
   повторити probe. Чисто завершити й повністю перезапустити клієнт; знову96.
   Після зупинки звірити всі 96 імен і типів NBT. Runtime reset не скорочує
   журнал до 64, не нормалізує імена та не скидає completed/FTB progress.
4. **Історичні alias-рядки.** В іншій зупиненій копії лишити тільки
   `08:tech` і `+8:tech`, обидва BYTE1; `8:tech` відсутній. Probe має показати
   `canonical=0/96`, зокрема не надавати дозвіл 8tech. Після reload і двох
   повних перезапусків обидва сирі імена залишаються буквально тими самими.
   На підготовленій Survival-копії з доступною гілкою 8tech реально виготовити
   її ключ: може додатися окремий `8:tech`; aliases не видаляються й не
   перетворюються. Наявність alias сама по собі не замінює це виробництво.
5. **Межа 96.** У копії з 96 канонічними доказами повторне довірене виробництво
   вже наявного ключа має бути ідемпотентним щодо журналу. Окрема fixture
   з 95 канонічними рядками й одним alias не повинна прийняти 97-й новий рядок
   через реальний ключовий процес. Зберегти помилку capacity і звірити
   збереження всіх попередніх 96 рядків; reset/автоматичного очищення немає.
6. **Неоднозначні або пошкоджені дані.** Для кожного випадку нижче зробити
   окрему копію, зупинити гру, змінити лише тестовий журнал і зафіксувати
   SHA-256 його вже пошкоджених байтів до запуску:

   | Окрема fixture | Очікувана відмова |
   | --- | --- |
   | Нечитабельний або обрізаний compressed `.dat` | Помилка IO не стає порожнім дозволеним журналом |
   | Немає `schema`, schema STRING `"1"`, schema INT2 | Непідтверджена схема закриває журнал |
   | `teams` чи запис команди має інший NBT-тип | Неправильна структура закриває журнал |
   | Proof INT1, BYTE0 або BYTE2 | Лише BYTE1 є коректним записаним доказом |
   | `0:tech`, `49:tech`, `8:unknown` | Неприпустима епоха/гілка закриває журнал |
   | Понад 96 рядків у команді | Пошкоджений надмірний запис не обрізається |

   У кожній fixture перевірити probe, `/aia2 sync` і новий key process на
   завчасно підготовленій гілці; жодного нового proof/переходу. Зберегти
   повідомлення `Invalid AIA2 key production journal` або
   `Unreadable AIA2 key production journal` та відмову читання/запису.
   Сам напис «Machine Guard активний» не є достатньою перевіркою журналу.
   Дочекатися звичайного збереження світу, чисто завершити гру й порівняти SHA:
   пошкоджений файл має лишитися побайтово незмінним. Повторити після повного
   restart та спроби реального виробництва: нова порожня структура не повинна
   перезаписати старі байти. При зупиненій грі відновити **перевірений backup**
   у тестовій копії; після запуску повертаються тільки її попередні докази.
7. **Команди й перехід.** Використати двох гравців у різних FTB-командах.
   Доказ A не з’являється у B після передачі предмета, зміни команди або
   reload. Новий фінальний перехід потребує обох реальних key receipts,
   обох обов’язкових гілок та фіналу. Окремо виконати сценарії NASA 37/38
   і старого оплаченого pending із SPACE_REQUIRED_ACCEPTANCE. Завершені
   старі епохи не скидаються; пошкодження журналу не видає нових прав.

## Дванадцять назв і предметних умов у клієнті

Відкрити епохи 37/38 в окремій підготовленій тестовій команді. Звірити всі
12 назв і три абзаци опису з presentation JSON; українські символи та іконки
мають відображатися правильно, координати й залежності зберігаються.
Для кожної віхи перевірити її реальну умову:

| Віхи | Дія у FTB Quests |
| --- | --- |
| E37_M1, E37_M3; E38_M1, E38_M3 | Показати відповідно 1 T1 rocket, 1 Gaia Spirit; 1 T3 rocket, 1 Wilden Tribute. Предмет залишається |
| E37_M2, E37_M4, E37_M5 | Здати по 1 desh ingot, Gaia Spirit, ostrum ingot; кожен витрачається |
| E38_M2, E38_M4, E38_M5 | Здати по 1 calorite ingot, Wilden Tribute, ostrum ingot; кожен витрачається |
| E37_M6 | Здати по 2 desh ingot, Gaia Spirit і MI Processing Unit; усі витрачаються |
| E38_M6 | Здати по 2 calorite ingot, Wilden Tribute і Powah Nitro Crystal; усі витрачаються |

Не виставляти `only_from_crafting` і не чекати від цих старих предметних
tasks доказу NASA-процесу, польоту, кисню чи FE. Перевірити часткові лічильники
внесків на копії попереднього світу: оновлення лише тексту не обнуляє їх,
старі completion timestamps та вже отримані нагороди. Отримання предмета
може закрити саме предметний task, але не має створювати key receipt або
обходити окремі виробничі цілі NASA й фінальні вимоги.

## Що записати у звіт

Для кожного пункту: `PASS`, `FAIL` або `NOT_RUN`, версії/SHA, точна fixture,
до/після NBT та SHA, список native proofs, completed/pending команди,
скриншоти FTB і відповідні рядки логів. Окремо зазначити рівень перевірки:
source/host, development Minecraft server чи повний клієнтський інстанс.
Зберегти TPS/MSPT спостереження без заяви про продуктивність, якщо її не
вимірювали. Після тестів прибрати лише власний probe з disposable-копії;
тестові світи, навмисно змінені журнали та логи не переносити у звичайний
інстанс і не додавати до Git.
