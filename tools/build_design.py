#!/usr/bin/env python3
"""Build and validate the Ukrainian progression specification; never installs it.

Usage: python3 tools/build_design.py --export-root /path/to/export
The input export is data only. No Minecraft, KubeJS, or quest code is executed.
"""
import argparse
import copy
import csv
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DESIGN = ROOT / 'design'


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def write_json(path, data):
    Path(path).write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def native_input_ids(value, registered_items):
    """Direct item inputs only; tag expansion and runtime-generated inputs need review."""
    if isinstance(value, dict):
        for key, child in value.items():
            if key in {'result', 'results', 'output', 'outputs', 'item_outputs'}:
                continue
            if key in {'item', 'id'} and isinstance(child, str) and child in registered_items:
                yield child
            else:
                yield from native_input_ids(child, registered_items)
    elif isinstance(value, list):
        for child in value:
            yield from native_input_ids(child, registered_items)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--export-root', type=Path, required=True)
    args = parser.parse_args()
    items = read(args.export_root / 'registries/item.json')
    blocks = read(args.export_root / 'registries/block.json')
    actual_mods = read(args.export_root / 'mods.json')
    catalog = read(DESIGN / 'mod-catalog.json')
    mods = catalog['mods'] if isinstance(catalog, dict) else catalog
    epochs = read(DESIGN / 'epochs-01-24.json') + read(DESIGN / 'epochs-25-48.json')
    epochs.sort(key=lambda e: e['number'])
    for component in read(DESIGN / 'component-unlocks.json'):
        epoch = next(e for e in epochs if e['number'] == component['epoch'])
        if component['id'] not in {u['id'] for u in epoch['unlocks']}:
            epoch['unlocks'].append({'id': component['id'], 'purpose_uk': component['purpose_uk'] + ' ' + component['reason_uk']})
    failures = []
    warnings = []
    checked_ids = set()

    def require(condition, message):
        if not condition:
            failures.append(message)

    def check_item(item_id, context):
        checked_ids.add(item_id)
        require(item_id in items, f'{context}: absent native item {item_id}')

    require([e['number'] for e in epochs] == list(range(1, 49)), 'Epoch numbers must be exactly 1..48')
    require(sorted(m.get('id', m.get('index')) for m in mods) == list(range(1, 294)), 'Catalog must cover exactly original mod numbers 1..293')
    explicit_unlocks = {}
    for epoch in epochs:
        for unlock in epoch['unlocks']:
            item_id = unlock['id']
            check_item(item_id, f"epoch {epoch['number']} unlock")
            explicit_unlocks[item_id] = min(epoch['number'], explicit_unlocks.get(item_id, 99))

    for epoch in epochs:
        n = epoch['number']
        key = epoch['key']
        expected_key = f'kubejs:aia2_epoch_key_{n:02d}'
        require(key['id'] == expected_key, f'Key ID mismatch epoch {n}')
        require(key['id'] not in items, f'Planned key unexpectedly exists in export: {key["id"]}')
        require(len(epoch['milestones']) == 6, f'Epoch {n} needs six pre-key milestones')
        require(len(epoch['optional_quests']) == 2, f'Epoch {n} needs two optional quests')
        require(key['requires_all_milestones'] is True, f'Epoch {n} key needs all milestones')
        require(key['consumes_previous_key'] == (n > 1), f'Epoch {n} previous-key consumption mismatch')
        require(key['pattern'] == ['TMT', 'RPR', 'SMS'], f'Epoch {n} unexpected key pattern')
        ingredients = key['ingredients']
        require(set(ingredients) == set('TMRSP'), f'Epoch {n} key ingredient symbols mismatch')
        prior = f'kubejs:aia2_epoch_key_{n-1:02d}' if n > 1 else 'minecraft:crafting_table'
        require(ingredients['P']['id'] == prior, f'Epoch {n} wrong predecessor')
        require(ingredients['P']['count'] == 1, f'Epoch {n} predecessor count must be one')
        for symbol in 'TMRS':
            entry = ingredients[symbol]
            check_item(entry['id'], f'epoch {n} key symbol {symbol}')
            require(entry['count'] == 2, f'Epoch {n} key {symbol} needs two unit slots')
            require('epoch_key_' not in entry['id'], f'Epoch {n}: keys cannot fill ordinary ingredient slots')
            later = explicit_unlocks.get(entry['id'])
            require(later is None or later <= n, f'Epoch {n} key uses {entry["id"]} explicitly unlocked only at {later}')
        require(len({ingredients[s]['id'] for s in 'TMRS'}) == 4, f'Epoch {n}: four ingredient roles must be distinct')
        seen = set()
        for index, milestone in enumerate(epoch['milestones'], start=1):
            expected_id = f'E{n:02d}_M{index}'
            require(milestone['id'] == expected_id, f'Epoch {n}: expected milestone {expected_id}')
            require(bool(milestone.get('objective_uk')), f'{expected_id}: empty objective')
            require(bool(milestone.get('evidence_uk')), f'{expected_id}: no acceptance evidence')
            for dependency in milestone['after']:
                require(dependency in seen, f'{expected_id}: missing or future dependency {dependency}')
            seen.add(milestone['id'])
        epoch['open_stage'] = f'aia2_epoch_{n:02d}'
        epoch['ready_key_stage'] = f'aia2_ready_key_{n:02d}'
        epoch['completion_stage'] = f'aia2_done_{n:02d}'
        epoch['previous_completion_required'] = f'aia2_done_{n-1:02d}' if n > 1 else None
        epoch['final_quest'] = {
            'id': f'E{n:02d}_KEY',
            'item': key['id'],
            'consume': False,
            'depends_on': [m['id'] for m in epoch['milestones']],
            'requires_legal_craft_provenance': True,
            'opens_epoch': n + 1 if n < 48 else None,
        }

    op_data = read(DESIGN / 'op-candidates.json')
    candidates = op_data['candidates']
    op_epochs = {c['target_id']: c['unlock_epoch'] for c in candidates}
    for candidate in candidates:
        target = candidate['target_id']
        n = candidate['unlock_epoch']
        check_item(target, 'OP target')
        require(1 <= n <= 48, f'OP target {target}: invalid epoch')
        planned = explicit_unlocks.get(target)
        require(planned is None or planned == n, f'OP target {target}: recipe gate {n} differs from explicit epoch {planned}')
        for source_id in candidate.get('source_recipe_ids', []):
            namespace, path = source_id.split(':', 1)
            require((args.export_root / 'recipes' / namespace / (path + '.json')).is_file(), f'OP target {target}: missing source recipe {source_id}')
        proposal = candidate.get('proposed_new_recipe') or {}
        for ingredient in proposal.get('ingredients', []):
            item_id = ingredient['id']
            check_item(item_id, f'OP target {target}')
            require('epoch_key_' not in item_id, f'OP target {target}: physical keys forbidden')
            available = explicit_unlocks.get(item_id)
            require(available is None or available <= n, f'OP target {target} at {n}: future input {item_id} at {available}')
            other_target_epoch = op_epochs.get(item_id)
            require(other_target_epoch is None or other_target_epoch <= n, f'OP target {target}: future OP ingredient {item_id}')
        template = proposal.get('preserved_source_recipe')
        if template and proposal.get('formula_kind') == 'native_process_ingredient_override':
            effective = copy.deepcopy(template)
            patch = proposal.get('ingredient_changes', {})
            if patch.get('new_pattern') and patch.get('new_key'):
                effective['pattern'] = patch['new_pattern']
                effective['key'] = patch['new_key']
            for item_id in native_input_ids(effective, items):
                checked_ids.add(item_id)
                available = explicit_unlocks.get(item_id)
                require(available is None or available <= n, f'OP target {target} at {n}: retained native input {item_id} at {available}')
    for epoch in epochs:
        integration = epoch.get('integration_recipe')
        if integration:
            integration = integration if isinstance(integration, list) else [integration]
            for recipe in integration:
                target = recipe['target_id']
                check_item(target, f'epoch {epoch["number"]} integration')
                for ingredient in recipe.get('additional_inputs', []):
                    item_id = ingredient['id']
                    check_item(item_id, f'epoch {epoch["number"]} integration')
                    require('epoch_key_' not in item_id, f'Epoch {epoch["number"]}: key in normal integration recipe')
                    available = explicit_unlocks.get(item_id)
                    require(available is None or available <= epoch['number'], f'Epoch {epoch["number"]} integration: future ingredient {item_id} at {available}')
                source_id = recipe.get('preserve_source_recipe_id') or recipe.get('source_recipe_id')
                if source_id:
                    namespace, path = source_id.split(':', 1)
                    require((args.export_root / 'recipes' / namespace / (path + '.json')).is_file(), f'Integration missing source recipe {source_id}')
                recipe['stage'] = epoch['open_stage']
                full_recipe = recipe.get('proposed_native_recipe')
                if full_recipe:
                    source = read(args.export_root / 'recipes' / namespace / (path + '.json'))
                    require(full_recipe.get('type') == source.get('type'), f'Integration {target}: native serializer changed')
                    require(full_recipe.get('result') == source.get('result'), f'Integration {target}: native output changed')
                    if 'pattern' in full_recipe:
                        symbols = Counter(''.join(full_recipe['pattern']).replace(' ', ''))
                        require(set(symbols) == set(full_recipe['key']), f'Integration {target}: grid key mismatch')
                        if full_recipe['type'] != 'create:mechanical_crafting':
                            require(len(full_recipe['pattern']) <= 3 and max(map(len, full_recipe['pattern'])) <= 3, f'Integration {target}: exceeds 3x3 crafting')
                    elif 'ingredients' in full_recipe:
                        require(len(full_recipe['ingredients']) <= 9, f'Integration {target}: exceeds shapeless slot count')
        for bridge in epoch.get('required_recipe_overrides', []):
            check_item(bridge['output']['id'], f'Epoch {epoch["number"]} bootstrap output')
            for ingredient in bridge['ingredients']:
                check_item(ingredient['id'], f'Epoch {epoch["number"]} bootstrap input')
                require('epoch_key_' not in ingredient['id'], f'Epoch {epoch["number"]}: key in bootstrap recipe')
            if 'pattern' in bridge:
                expected = Counter({i['id']: i['count'] for i in bridge['ingredients']})
                actual = Counter(bridge['pattern_key'][s] for row in bridge['pattern'] for s in row if s != ' ')
                require(expected == actual, f'Epoch {epoch["number"]}: bootstrap grid quantities differ')

    warnings.append('Static validation does not prove Minecraft loading, stage enforcement, quest event hooks, or complete native recipe reachability.')
    warnings.append('Only representative unlocks are assigned individually. Namespace entry epochs are floors, not permission to unlock every item in a mod.')
    report = {
        'status': 'failed' if failures else 'passed_static_specification_checks',
        'epochs': len(epochs),
        'original_mod_entries': len(mods),
        'required_milestones': sum(len(e['milestones']) for e in epochs),
        'required_final_key_quests': len(epochs),
        'optional_quests': sum(len(e['optional_quests']) for e in epochs),
        'verified_distinct_existing_item_ids': len(checked_ids),
        'op_recipe_families': len(candidates),
        'epoch_integration_recipe_specs': sum(bool(e.get('integration_recipe')) for e in epochs),
        'bootstrap_recipe_specs': sum(len(e.get('required_recipe_overrides', [])) for e in epochs),
        'key_successor_edges': max(0, len(epochs) - 1),
        'failures': failures,
        'warnings': warnings,
        'not_run': ['Minecraft server/client', 'Game Stages addons', 'FTB Quests import', 'KubeJS recipe reload', 'multiplayer bypass tests', 'energy and timing playtests'],
    }
    write_json(DESIGN / 'validation-report.json', report)
    if failures:
        print(json.dumps(report, ensure_ascii=False, indent=2))
        raise SystemExit(1)

    progression = {
        'schema_version': 1,
        'kind': 'design_specification_not_runtime_configuration',
        'language': 'uk-UA',
        'key_items_are_planned_not_registered': True,
        'stage_authority': 'team_progress_ledger; Game Stages is a synchronized projection',
        'epochs': epochs,
    }
    write_json(DESIGN / 'progression.json', progression)
    write_json(DESIGN / 'key-recipes.json', [{
        'epoch': e['number'],
        'recipe_specification_only': True,
        'output': {'id': e['key']['id'], 'count': 1},
        **e['key'],
        'previous_key_is_only_allowed_recipe_consumer': True,
        'proof_required': e['ready_key_stage'],
    } for e in epochs])

    # Full registry coverage, without pretending a namespace floor is a reviewed item gate.
    namespace_floors = {}
    claimed_namespaces = set()
    for mod in mods:
        first = mod.get('first_epoch')
        for namespace in mod.get('mod_ids', []):
            claimed_namespaces.add(namespace)
            if isinstance(first, int):
                namespace_floors[namespace] = min(first, namespace_floors.get(namespace, 99))
    namespace_floors['minecraft'] = 1
    for kind, registry in [('item', items), ('block', blocks)]:
        destination = DESIGN / f'{kind}-stage-inventory.csv'
        with destination.open('w', encoding='utf-8-sig', newline='') as stream:
            writer = csv.writer(stream)
            writer.writerow(['id', 'mod_entry_epoch_floor', 'individually_planned_epoch', 'review_status', 'java_class'])
            for item_id, java_class in sorted(registry.items()):
                namespace = item_id.split(':', 1)[0]
                exact = explicit_unlocks.get(item_id)
                floor = namespace_floors.get(namespace, '')
                status = 'explicit_in_epoch_plan' if exact else ('namespace_floor_only_requires_tier_review' if floor != '' else 'unassigned_requires_audit')
                if namespace == 'funmod':
                    status = 'quarantined_until_behavior_audit'
                writer.writerow([item_id, floor, exact or '', status, java_class])

    extras = [m for m in actual_mods if m['id'] not in claimed_namespaces]
    write_json(DESIGN / 'export-mods-not-matched-to-user-list.json', extras)
    write_catalog_markdown(mods)
    write_epoch_book(epochs)
    print(json.dumps(report, ensure_ascii=False, indent=2))


def write_catalog_markdown(mods):
    lines = [
        '# Розподіл усіх 293 модів', '',
        'Номер відповідає списку користувача. Епоха 0 означає інфраструктуру, доступну від початку. Перша епоха моду не відкриває автоматично всі його предмети й рецепти. Невідомі можливості залишаються на аудиті.', '',
        '| № | Мод / файл | Перша епоха | Наступні рівні | Роль і обмеження |',
        '|---:|---|---:|---|---|',
    ]
    for mod in sorted(mods, key=lambda x: x['id']):
        later = ', '.join(map(str, mod.get('later_epochs', []))) or '—'
        notes = mod.get('notes_uk', '').replace('|', '/')
        uncertainty = mod.get('uncertainty', [])
        if uncertainty:
            notes += ' **Перевірити:** ' + '; '.join(map(str, uncertainty))
        lines.append(f"| {mod['id']} | **{mod['name']}**<br>`{mod['filename']}` | {mod.get('first_epoch', 'аудит')} | {later} | {notes} |")
    (DESIGN / 'mod-allocation.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')


def write_epoch_book(epochs):
    lines = [
        '# Книга 48 епох All in One Adventure 2.0', '',
        'Специфікація, а не готовий імпорт FTB Quests. У кожній епосі шість обов’язкових віх, фінальний неспоживний квест на ключ і два необов’язкових завдання. Нативні ID в переліках предметів та складових ключів звірені з експортом. Ключі `kubejs:aia2_epoch_key_XX` є новими запланованими предметами.', '',
        'Стадія зберігає право доступу після витрачання попереднього ключа. Крафт ключа вимагає доказів поточної епохи; підібраний чужий ключ не замінює ці докази. Див. [правила балансу](balance-policy.md) та [схему блокувань](gating-review.md).', '',
        '## Загальна послідовність', '',
        '| Епоха | Тема | Основні моди |', '|---:|---|---|',
    ]
    for e in epochs:
        lines.append(f"| {e['number']:02d} | {e['title']} | {', '.join(e['main_mods'])} |")
    for e in epochs:
        n = e['number']
        lines += ['', f"## Епоха {n:02d}. {e['title']}", '', e['theme'], '',
                  f"Вхід: `{e['open_stage']}`. Умова фінального крафту: `{e['ready_key_stage']}`. Завершення: `{e['completion_stage']}`.", '',
                  '### Предмети та механізми', '']
        for unlock in e['unlocks']:
            lines.append(f"- `{unlock['id']}` — {unlock['purpose_uk']}")
        lines += ['', '### Обов’язковий ланцюжок', '']
        for m in e['milestones']:
            after = ', '.join(m['after']) or 'відкриття епохи'
            lines.append(f"- **{m['id']} — {m['title']}**. {m['objective_uk']} Доказ: {m['evidence_uk']} Залежить від: {after}.")
        lines += [f"- **E{n:02d}_KEY — {e['key']['name_uk']}**. Після всіх шести віх законно скрафтити `{e['key']['id']}`. Квест перевіряє ключ без споживання; переданий ключ не дає обходу. " + ('Відкриває наступну епоху.' if n < 48 else 'Фіксує остаточну перемогу; наступної обов’язкової епохи немає.'), '',
                  '### Фінальний крафт', '',
                  'Сітка: `TMT / RPR / SMS`; вихід — один ключ. Кожне повторення символу — один предмет в окремому слоті.', '',
                  '| Позначення | Складова | Разом одиниць |', '|---|---|---:|']
        for symbol in 'TMRSP':
            ingredient = e['key']['ingredients'][symbol]
            lines.append(f"| {symbol} | `{ingredient['id']}` | {ingredient['count']} |")
        lines += ['', '### Межі епохи', ''] + ['- ' + text for text in e['limits_uk']]
        overrides = e.get('required_recipe_overrides', [])
        if overrides:
            lines += ['', '### Необхідні зміни для досяжності', '', 'Ці зміни — вимоги реалізації; без них нативні рецепти можуть блокувати вказаний порядок.', '', '```json', json.dumps(overrides, ensure_ascii=False, indent=2), '```']
        integration = e.get('integration_recipe')
        if integration:
            lines += ['', '### Рецепт взаємодії магії й техніки', '', 'Нативний процес та його вимоги зберігаються. Нижче — специфікація зміни складових, а не готовий JSON рецепта гри.', '', '```json', json.dumps(integration, ensure_ascii=False, indent=2), '```']
        for field, title in [('singularity_targets', 'Цільові сингулярності'), ('required_component_products', 'Обов’язкові проміжні продукти')]:
            if e.get(field):
                lines += ['', '### ' + title, '', '```json', json.dumps(e[field], ensure_ascii=False, indent=2), '```']
        lines += ['', '### Додаткові завдання', '']
        for q in e['optional_quests']:
            lines.append(f"- **{q['title']}**. {q['objective_uk']}")
    (DESIGN / 'epochs-book.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
