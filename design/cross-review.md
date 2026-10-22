# Підсумкова перехресна перевірка прогресії

Перевірено специфікацію 48 епох, 61 OP/gateway-пропозицію, компонентні пороги та вибрані нативні рецепти/loot tables експорту. Це перевірка даних і залежностей; сервер, JAR та Game Stages інтеграцію не запускали.

## Результат статичної перевірки

У 61 пропозиції немає фізичних ключів епох як звичайних інгредієнтів, прямих циклів між новими формулами цільових OP-предметів або залежностей нових явних інгредієнтів від пізнішого явного порога. Ця перевірка охоплює `unlocks` і `component-unlocks.json`; вона не доводить всю транзитивну мережу 42 064 нативних рецептів.

Підрахунки shaped-patterns перевіряються за їхніми символами. Infusion використовує центр і 8 п’єдесталів, fusion — native catalyst/injectors/energy, Avaritia — власний tier і розмір сітки. Ці різні схеми не можна перевіряти як універсальний 3×3 крафт.

## Виправлені суперечності

- Con­denser Mk1 відкривається45; AdvancedAE quantum crafter39, разом із відповідною епохою.
- Foliot miner28 зберігає ритуал і Iesnium pickaxe. Marid master перенесено32→39: його нативний рецепт справді потребує marid essence, bound-marid book і craft-marid pentacle.
- Ручний Iesnium відкрито24 до обов’язкової есенції африта25. Перший метал не залежить від miner, який сам потребує цього металу.
- Draconic, Occultism, Mystical infusion, Orechid й Avaritia зберігають native процеси/структури. Використано підтверджений `avaritia:shaped_table` із `tier`; не вигаданий serializer. Native sources і точні зміни комірок/позицій включені у пропозиції.
- Extreme table46 зберігає 7×7, tier3 і попередній стіл; усі **4** недоступні `reinforced_deepslate` замінено на `unobtainium_block`, а одиничний світовий `dragon_egg` — на відновлюваний через повторного дракона `dragon_heart`. Catalyst більше не вимагає bedrock. Ці зміни усувають залежність від post-final Infinity pickaxe та монополію першої команди.
- Збережено batch-виходи single chunk loader×9 та Powah Nitro reactor×4. Ціну chunk loading застосовано до виробництва basic loader, а не його оборотного поділу.
- Native copy-components і конфігураційні wrapper-рецепти розглядаються окремо; розпакування блоків/самородків не названо безкоштовним виробництвом.
- Есенції африта25 та маріда39 підтверджуються справжнім summon→kill→loot. JEI display stack у summon recipe не є виданою есенцією.
- Сингулярності46–47 мають конкретні component variants і кількості, а не порожній generic item.

## Узгоджені рішення балансу

Базові EMC collectors/relays — епоха47 з білим списком звичайних матеріалів; вони не відкривають EMC для ключів, доказів, нових руд і контрольних компонентів. Це остаточна політика, що замінює ранню пропозицію відкласти всю родину до postgame.

Конкретна Infinity chestplate дозволена до ключа48 як фінальний виробничий доказ: усі обов’язкові боси вже пройдені до42, а у48 немає нового обов’язкового бою. Infinity pickaxe і creative controls залишаються після `done_48`, зокрема через bedrock/mining bypass. `post_final_only` не дорівнює простому `open_48`.

## Доказ ручного Iesnium bootstrap

Експорт містить безциклові передумови без Iesnium-інгредієнта:

1. `occultism:crafting/spirit_attuned_pickaxe_head`: 3 spirit-attuned gems → head.
2. `occultism:ritual/craft_infused_pickaxe`: bound-djinni book, 2 дерев’яні палиці, head, 2 silver; pentacle `craft_djinni`, duration150. У рецепті немає Iesnium.
3. `occultism:ritual/craft_infused_lenses`: lenses, 2 silver, gold; bound-foliot/craft-foliot, duration60. Разом із lens frame/leather це дає otherworld goggles.
4. `occultism:blocks/iesnium_ore_natural` loot table: `uncovered=false` дає netherrack; `uncovered=true` — raw_iesnium або ore за Silk Touch.
5. `occultism:smelting/iesnium_ingot_from_raw` / `...from_ore`: 1 raw/ore → 1 ingot,200 ticks; blasting100 ticks. Відповідні теги підтверджують raw/ore IDs.

Експорт не містить виконуваного коду `IesniumOreNaturalBlock`, worldgen-налаштувань і runtime-перевірки конкретного uncover trigger. Намір маршруту — природний видобуток із легальними Otherworld perception/infused pickaxe після Nether15; точні умови розкриття та геологію треба перевірити на реальному інстансі. Не приписувати цю перевірку вже виконаній.

## Що залишається для реалізації

Два предметні ребаланси свідомо не видані за готові рецепти: tier/component-bearing Iron Jetpacks і Eternal Stella, для яких немає повного native template у експорті. Вони залишаються необов’язковими й не блокують жоден із 48 ключів; до перевірки їх не можна вводити через generic 3×3 shortcut.

Залишаються інтеграційні вимоги: точні актуальні Game Stages аддони/API, власник машин/fake players, підтверджені типи FTB Quests tasks, production/kill provenance, dimension/loot/EMC enforcement, міграція наявних `aia2_*` доказів та вимірювання економіки/часу. Це блокери заяви про **працюючу серверну реалізацію**, а не невиконаний етап складання цієї дизайн-специфікації. Для нового незвіреного контенту лишається явний карантин; він не є автоматичним дозволом всього namespace.
