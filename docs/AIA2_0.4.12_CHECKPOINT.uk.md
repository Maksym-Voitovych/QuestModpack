# AIA2 0.4.12-alpha — Forbidden Forge і досліджені ритуали

Проміжний завершений підблок до0.5; повний великий план ще IN_PROGRESS.
База: `80051c098189a3859cc898cd371510d4d41c46c3`, резервна копія перед змінами:
`/workspace/aia2-backups/before-forbidden-ritual-20261027T185709Z/checkpoint-80051c0.tar.gz`.

48епох,96виробничих ключів, **3346квестів/140глав/6груп**,
623нативні custom-рецепти,390предметів/моделей/PNG. Нових рецептів,
предметів і текстур у цьому блоці0. Існуючі рецепти та переходи не замінено.

## Зміни

Додано16optional-цілей Forbidden Arcanus з16тематичними нагородами:
ресурси/есенції, побудова Forge, сімп'єдесталів для Ferrognetic Mixture,
upgrade tier2–5, Eternal Stella, підготовка Clibano. Scopedcore-карта має
24етапи;8попередніх stage ID/refs збережено.26scopedcoremaps і35partial,
61мод/63записи. Це не означає повної реалізації всіх здібностей26модів.

Шість нових критеріїв перевіряють реальний native `ritual_completed` із
точним `recipe_id`. Загалом105nativeaction-цілей;8командних виробничих
правил/11recipeIDs і96ключових виробничих доказів незмінні. Native тригер
потребує online-ініціатора у вимірі кузні й передує world effect/output.

Forge захищено трьома точковими mixins і типізованими Java helpers:

- prepayment-перевірки actual controller, synchronized live team, нинішнього
  ritual registry, tier, main/pedestal stacks, physical enhancer components
  і поточних cached enhancer holders;
- `Optional.map` scope з try/finally охоплює справжню native lambda;
  доказ оплати створюється лише після exact `EssencesStorage.reduce` RETURN,
  з перевіркою identity сховища та native cost object;
- перед tick/finish/fail перевіряються оплата, SHA повного DIRECT_CODEC
  визначення, повний склад входів і допустимий результат. Тотожний новий
  holder можна переприв'язати; змінений/видалений ритуал призупиняється;
- raw active NBT/receipt читається до native load і зберігається навіть
  при codec failure. Legacy/corrupt не отримують вигаданої оплати;
- input slots5–8 перевіряються до перетворення трубних предметів на есенції;
  ключі заборонені як копійований вихід і ритуальний/essence input;
- `/aia2forge status x y z` пояснює pause; операторське `cancel` поблизу
  власної кузні явно зберігає bounded8backup й залишає фізичні предмети.
  Автоматичного cancel/refund немає.

Усі3330попередніх quest/task/reward/dependency payloads збережено, крім
однієї обґрунтованої icon-only міграції старого Forge-квесту з block-only
tier1 на реальний Mundabitur Dust. Усі623recipeentries незмінні.
Координати змінилися лише в Forbiddenглаві:1147→1152перетини при16нових
цілях,0накладань/зворотних/вертикальних/надто довгих ліній.
[Порівняння](../implementation/forbidden-core-preservation-v5.json).

## Перевірки й межі

212Python/55Node/5237Java і JDK21build PASS;297новихmodelassertions.
Мінімальний MC0.4.12:111assertions/2JVM/650ticks.13JS syntaxfiles PASS;
1169runtimeфайлів byte-identical післяPYTHONHASHSEED97rebuild. ZIP CRC і
повний SHAmanifest, actualextractedCLI dry-run0writes та syntheticupgrade
0.4.11→0.4.12 з backupJAR і збереженням opaque прогрес-маркерів PASS.
Детальні результати доступних suites, JAR і пакетних перевірок записано в
[release-report](../implementation/release-report.json) і журнал PROGRESS.
Модельований host виконує справжні helpers/handlers/GuardPolicy; мінімальний
Minecraft окремо перевіряє справжній NBT, UUID і compressed binary roundtrip.
Жоден із них не є підтвердженням optional Forbidden weaving у повному модпаку.

Clibano internal-main ownership/cached production, Obelisk, пасивні здібності,
сторонні ritual result types, generic copied components і transitive registry
graph ще потребують окремого аудиту. DIRECT_CODEC fingerprint фіксує саме
визначення ритуалу, а не всі залежні tag/registry файли. Native midpoint RNG
й світові ефекти не відкочуються. Legacy active ritual зберігається paused:
можна повернутися до старої копії для завершення або явно скасувати на тестовій
копії; нова версія не приписує йому непідтверджену оплату.

JEI/UI, Survival, TPS і повний optional dispatch — **NOT RUN**.
[Приймальні сценарії](testing/FORBIDDEN_RITUAL_ACCEPTANCE.uk.md).

Наступна конкретна дія: Forge transitive-definition review і Clibano actual
main-controller ownership/production guard за exact2.6.1source, потім35partial
карт/невивчені моди та старі обов'язкові лінії48епох. Roots unfinished ritual
restart, DraconicCI633 і6IFfluidgaps лишаються відкритими. Новий балансний
рецепт додавати тільки після підтвердження цього реального ланцюга.

Установлення із закритою грою: `python install_runtime.py
"C:\CurseForge\AllInOneAdventure2" --dry-run`, потім без прапорця, із
`nbtlib==2.0.4`. Matching JAR0.4.12/скрипти потрібні на обох сторонах;
повний перезапуск обов'язковий. Інсталятор резервує оригінали й старий
власний JAR, зберігаючи світи, прогрес та сторонні квести.
