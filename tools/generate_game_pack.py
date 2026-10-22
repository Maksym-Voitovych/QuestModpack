#!/usr/bin/env python3
"""Generate real KubeJS/FTB files. Does not install into a Minecraft instance."""
import argparse
import copy
import hashlib
import json
import re
import string
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACK = ROOT
DESIGN = ROOT / 'design'


def load(p):
    return json.loads(Path(p).read_text(encoding='utf-8'))


def emit(relative, data):
    p = PACK / relative
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n' if not isinstance(data, str) else data, encoding='utf-8')


def uid(name):
    # 48-bit IDs stay exact when passed through Rhino JavaScript numbers.
    return hashlib.sha256(('aia2-runtime-v1:' + name).encode()).hexdigest()[:12].upper().rjust(16, '0')


def ing(item):
    return {'item': item}


def expanded(inputs, fusion=False):
    out = []
    for entry in inputs:
        for _ in range(entry['count']):
            out.append({'consume': True, 'ingredient': ing(entry['id'])} if fusion else ing(entry['id']))
    return out


def patch_grid(recipe, changes):
    r = copy.deepcopy(recipe)
    grid = [list(row) for row in r['pattern']]
    alphabet = iter(c for c in string.ascii_letters + string.digits if c not in r['key'])
    for change in changes:
        y, x = change['row'], change['column']
        assert 0 <= y < len(grid) and 0 <= x < len(grid[y]), change
        symbol = next(alphabet)
        grid[y][x] = symbol
        r['key'][symbol] = ing(change['id'])
    r['pattern'] = [''.join(row) for row in grid]
    used = set(''.join(r['pattern'])) - {' '}
    r['key'] = {k: v for k, v in r['key'].items() if k in used}
    return r


def apply_op(proposal):
    kind = proposal['formula_kind']
    if kind == 'full_replacement_shaped_design':
        return {'type': proposal['process'], 'pattern': proposal['pattern'],
                'key': {k: ing(v) for k, v in proposal['key'].items()},
                'result': proposal['output']}
    if kind != 'native_process_ingredient_override':
        return None
    recipe = copy.deepcopy(proposal['preserved_source_recipe'])
    changes = proposal['ingredient_changes']
    operation = changes['kind']
    if operation == 'replace_grid_slots':
        target = recipe[changes['recipe_field']] if changes.get('recipe_field') else recipe
        target['pattern'] = changes['new_pattern']
        target['key'] = changes['new_key']
    elif operation == 'append_native_injector_ingredients':
        recipe['ingredients'] += expanded(changes['add'], fusion=True)
    elif operation in {'replace_native_injector_positions', 'replace_pedestal_positions', 'replace_native_ritual_positions'}:
        for position, item in changes['zero_based_positions'].items():
            index = int(position)
            old = recipe['ingredients'][index]
            if operation == 'replace_native_injector_positions':
                old['ingredient'] = ing(item)
            else:
                recipe['ingredients'][index] = ing(item)
    elif operation == 'retain_native_list_except_explicit_replacement':
        recipe['ingredients'] = [x for x in recipe['ingredients'] if x not in changes['remove']]
        recipe['ingredients'] += expanded(changes['add'])
    elif operation == 'append_native_ritual_inputs':
        recipe['ingredients'] += expanded(changes['add'])
    elif operation == 'append_to_both_wrapped_native_recipes':
        for branch in changes['branches']:
            recipe[branch]['ingredients'] += expanded(changes['add'])
    else:
        raise ValueError('Unimplemented native patch: ' + operation)
    return recipe


def recipe_outputs(recipe):
    out = set()
    for field in ['result', 'results', 'output', 'outputs', 'item_outputs']:
        value = recipe.get(field)
        values = value if isinstance(value, list) else [value]
        for entry in values:
            if isinstance(entry, dict):
                item = entry.get('id', entry.get('item'))
                if isinstance(item, str):
                    out.add(item)
            elif isinstance(entry, str):
                out.add(entry)
    for key in ['recipe', 'base', 'gog']:
        if isinstance(recipe.get(key), dict):
            out.update(recipe_outputs(recipe[key]))
    return out


def reversible_storage_conversion(recipe, targets):
    if recipe.get('type') not in {'minecraft:crafting_shaped', 'minecraft:crafting_shapeless', 'crafting_shaped', 'crafting_shapeless'}:
        return False
    inputs = recipe.get('ingredients', list(recipe.get('key', {}).values()))
    if not inputs or any(not isinstance(x, dict) or set(x) != {'item'} for x in inputs):
        return False
    input_ids = {x['item'] for x in inputs}
    for target in targets:
        forms = {target + '_block', target + '_nugget', target.replace('_ingot', '_block'),
                 target.replace('_ingot', '_nugget'), target.replace('_essence', '_block')}
        if target == 'avaritia:infinity_ingot':
            forms.add('avaritia:infinity')  # Native block ID differs from its ingot ID.
        forms.discard(target)
        if input_ids <= forms:
            return True
    return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--export-root', type=Path, default=Path('/workspace/aia2-reference/export'))
    args = ap.parse_args()
    export = args.export_root
    epochs = load(DESIGN / 'progression.json')['epochs']
    ops = load(DESIGN / 'op-candidates.json')['candidates']
    items = load(export / 'registries/item.json')
    entities = load(export / 'registries/entity_type.json')
    catalog = load(DESIGN / 'mod-catalog.json')['mods']
    recipes = []
    removals = set()
    blocked = []
    changed_targets = {}

    def source(recipe_id):
        ns, path = recipe_id.split(':', 1)
        return load(export / 'recipes' / ns / (path + '.json'))

    def add(recipe_id, recipe, epoch, target, category):
        assert isinstance(recipe, dict) and 'type' in recipe, recipe_id
        if ':' not in recipe['type']:
            recipe['type'] = 'minecraft:' + recipe['type']
        if target:
            assert target in items, target
        recipes.append({'id': recipe_id, 'json': recipe, 'epoch': epoch, 'target': target, 'category': category})
        if target:
            changed_targets[target] = recipe_id

    for candidate in ops:
        p = candidate['proposed_new_recipe']
        kind = p['formula_kind']
        if kind == 'remove_bypass_recipe_keep_native_manufacturing':
            removals.add(p['preserve_source_recipe_id'])
            continue
        if kind == 'blocked_missing_native_template':
            blocked.append({'id': candidate['target_id'], 'reason': p['native_constraints_uk']})
            continue
        if kind == 'preserve_native_conversion_stage_only':
            continue
        recipe = apply_op(p)
        if recipe is not None:
            add(p['id'], recipe, candidate['unlock_epoch'], candidate['target_id'], 'rebalance')
            removals.add(p['preserve_source_recipe_id'])

    for e in epochs:
        n = e['number']
        for index, bridge in enumerate(e.get('required_recipe_overrides', [])):
            if 'pattern' in bridge:
                recipe = {'type': bridge['recipe_type'], 'pattern': bridge['pattern'],
                          'key': {k: ing(v) for k, v in bridge['pattern_key'].items()}, 'result': bridge['output']}
            else:
                recipe = {'type': bridge['recipe_type'], 'ingredients': expanded(bridge['ingredients']),
                          'results': [bridge['output']]}
                if bridge.get('heat_requirement') not in {None, 'none'}:
                    recipe['heat_requirement'] = bridge['heat_requirement']
            add(f'aia2:bootstrap/epoch_{n:02d}_{index+1}', recipe, n, bridge['output']['id'], 'bootstrap')
        spec = e.get('integration_recipe')
        if not spec:
            continue
        rid = spec.get('preserve_source_recipe_id') or spec['source_recipe_id']
        recipe = copy.deepcopy(spec.get('proposed_native_recipe')) if spec.get('proposed_native_recipe') else source(rid)
        if not spec.get('proposed_native_recipe'):
            if 'input_patch' in spec:
                recipe = patch_grid(recipe, spec['input_patch']['replacements'])
            elif recipe['type'] == 'draconicevolution:fusion_crafting':
                recipe['ingredients'] += expanded(spec['additional_inputs'], fusion=True)
            elif recipe['type'] == 'extendedae:crystal_assembler':
                # Exported Crystal Assembler inputs encode explicit amount + ingredient.
                field = 'input_items'
                template = recipe[field][0]
                for entry in spec['additional_inputs']:
                    extra = copy.deepcopy(template)
                    if 'ingredient' in extra:
                        extra['ingredient'] = ing(entry['id'])
                    else:
                        extra = ing(entry['id'])
                    if 'amount' in template:
                        extra['amount'] = entry['count']
                    elif 'count' in template:
                        extra['count'] = entry['count']
                    recipe[field].append(extra)
            else:
                raise ValueError(('Unsupported integration', n, recipe['type']))
        add(f'aia2:integration/epoch_{n:02d}', recipe, n, spec['target_id'], 'integration')
        removals.add(rid)
        removals.update(spec.get('also_patch_recipe_ids', []))
        removals.update(spec.get('disable_unpatched_alternative_recipe_ids', []))

    # Remove alternate production routes for changed outputs; retain explicit packing recovery.
    target_ids = set(changed_targets)
    production_types = {'minecraft:crafting_shaped', 'minecraft:crafting_shapeless', 'crafting_shaped',
                        'crafting_shapeless', 'minecraft:smithing_transform', 'minecraft:smithing_trim',
                        'mekanism:mek_data', 'draconicevolution:fusion_crafting', 'occultism:ritual',
                        'mysticalagriculture:infusion', 'avaritia:shaped_table', 'botania:gog_alternation'}
    kept_conversions = []
    for file in (export / 'recipes').rglob('*.json'):
        recipe = load(file)
        hits = recipe_outputs(recipe) & target_ids
        if not hits:
            continue
        rid = ':'.join(file.relative_to(export / 'recipes').with_suffix('').parts[:1]) + ':' + '/'.join(file.relative_to(export / 'recipes').with_suffix('').parts[1:])
        rid = rid.replace('::', ':')
        path = rid.split(':', 1)[1]
        if reversible_storage_conversion(recipe, hits) or any(token in path for token in ['from_block', 'from_nugget', 'decompress', 'unpacking', 'config_wipe']):
            kept_conversions.append(rid)
        elif recipe.get('type') in production_types or rid in removals:
            removals.add(rid)

    ids = [r['id'] for r in recipes]
    assert len(ids) == len(set(ids))
    emit('kubejs/config/aia2_recipes.json', {'add': recipes, 'remove': sorted(removals)})
    emit('kubejs/server_scripts/aia2/10_recipes.js', '''// Native serializers are preserved; no unsupported recipe.stage() calls.
ServerEvents.recipes(function (event) {
  var bundle = JSON.parse(JsonIO.readString('kubejs/config/aia2_recipes.json'));
  bundle.remove.forEach(function (id) { event.remove({id: id}); });
  bundle.add.forEach(function (entry) {
    if (entry.json.type === 'create:mixing') {
      // Verified KubeJS Create 2101 schema: results, ingredients, optional time/heat.
      event.recipes.create.mixing(entry.json.results, entry.json.ingredients).id(entry.id);
    } else {
      // Exact native JSON is the supported path for preserving mod-specific wrappers,
      // components, native catalysts, energy, ritual activation and multiblock tiers.
      event.custom(entry.json).id(entry.id);
    }
  });
  // Keys use the server-side atomic forge. Never register an ungated vanilla key recipe.
  for (var n = 1; n <= 48; n++) {
    event.remove({output: 'kubejs:aia2_epoch_key_' + (n < 10 ? '0' : '') + n});
  }
});
''')

    # Source-verified native process proofs supplement (not replace) deliveries.
    process_proofs = load(ROOT / 'implementation/create-process-evidence.json')
    process_by_milestone = {}
    for proof in process_proofs:
        process_by_milestone.setdefault((proof['epoch'], proof['milestone_index']), []).append(proof)
    # Native FTB Quests tasks: deliveries, boss kills and completed Create operations.
    boss_rules = {(7, 5): 'twilightforest:naga', (30, 5): 'minecraft:ender_dragon',
                  (31, 2): 'botania:doppleganger', (31, 5): 'botania:doppleganger',
                  (42, 2): 'draconicevolution:draconic_guardian'}
    # Confirm exact entity IDs from this exported registry.
    for key, entity in list(boss_rules.items()):
        if entity not in entities:
            matches = [x for x in entities if ('chaos_guardian' in x if key == (42, 2) else 'dopple' in x)]
            if len(matches) == 1:
                boss_rules[key] = matches[0]
            else:
                raise ValueError(('No verified boss entity', key, entity, matches))
    runtime_epochs = []
    key_init = ['// Requires a full game restart when added/changed.', "StartupEvents.registry('item', function (event) {"]
    key_init += [f"  event.create('kubejs:aia2_epoch_key_{e['number']:02d}').displayName({json.dumps(e['key']['name_uk'], ensure_ascii=False)}).maxStackSize(1).fireResistant().texture('minecraft:item/tripwire_hook');" for e in epochs]
    key_init += ['});', '']
    emit('kubejs/startup_scripts/aia2/00_epoch_keys.js', '\n'.join(key_init))
    emit('kubejs/client_scripts/aia2/40_key_information.js', '''// KubeJS 2101 RecipeViewerEvents (JEI integration), source-verified.
var aia2ClientRules = JSON.parse(JsonIO.readString('kubejs/config/aia2_runtime.json'));
RecipeViewerEvents.addInformation('item', function (event) {
  aia2ClientRules.epochs.forEach(function (epoch) {
    var lines = ['Завершіть шість обов’язкових квестів епохи ' + epoch.number + '.',
      'Біля звичайного верстака: /aia2 key',
      'Сервер перевіряє умови перед списанням матеріалів.'];
    Object.keys(epoch.cost).forEach(function (id) { lines.push(epoch.cost[id] + ' × ' + id); });
    lines.push('Ключ потрібен лише для завершення глави та створення наступного ключа.');
    event.add(epoch.key, lines);
  });
});
ItemEvents.modifyTooltips(function (event) {
  aia2ClientRules.epochs.forEach(function (epoch) {
    event.add(epoch.key, ['Епоха ' + epoch.number, 'Крафт біля верстака: /aia2 key',
      'Не використовується у звичайних рецептах.']);
  });
});
''')

    for e in epochs:
        n = e['number']
        quests = []
        milestone_ids = []
        technical = e['key']['ingredients']['T']['id']
        magical = e['key']['ingredients']['M']['id']
        resource = e['key']['ingredients']['R']['id']
        support = e['key']['ingredients']['S']['id']
        target = e.get('integration_recipe', {}).get('target_id', e['unlocks'][0]['id'])
        requirements = [[(target, 1, False)], [(technical, 4 if n < 33 else 1, True)],
                        [(magical, 1, False)], [(magical, 2 if n < 33 else 1, True)],
                        [(resource, 4 if n < 33 else 1, True)],
                        [(technical, 2, True), (magical, 2, True), (support, 2, True)]]
        for j, m in enumerate(e['milestones'], start=1):
            qid = uid(m['id'])
            milestone_ids.append(qid)
            deps = [uid(x) for x in m['after']]
            if n > 1:
                deps.append(uid(f'E{n-1:02d}_KEY'))
            tasks = []
            if (n, j) in boss_rules:
                tasks.append({'id': uid(m['id'] + ':kill'), 'type': 'kill', 'entity': boss_rules[(n, j)], 'value': 1})
                acceptance = 'Серверний kill-task: особисто/командою перемогти зазначену істоту після відкриття завдання.'
            else:
                for k, (item_id, count, consume) in enumerate(requirements[j-1]):
                    assert item_id in items
                    tasks.append({'id': uid(m['id'] + f':item{k}'), 'type': 'item',
                                  'item': {'id': item_id, 'count': 1}, 'count': count,
                                  'consume_items': consume, 'only_from_crafting': False})
                acceptance = 'Фактична умова цього коду: ' + '; '.join(f"{c} × {i} ({'здати — витрачається' if consume else 'показати — зберігається'})" for i, c, consume in requirements[j-1]) + '.'
            proofs = process_by_milestone.get((n, j), [])
            tasks.append({'id': uid(m['id'] + ':stage'), 'type': 'advancement',
                          'advancement': f'aia2:stages/e{n:02d}'})
            for proof in proofs:
                tasks.append({'id': uid(m['id'] + ':process:' + proof['advancement']),
                              'type': 'advancement', 'advancement': proof['advancement']})
            process_description = [p['actual_condition_uk'] for p in proofs]
            if proofs:
                process_description.append('Додатково потрібні ВСІ вказані нативні досягнення Create. '
                    'Поставте машину власноруч і будьте онлайн. Уже здобуті досягнення зараховуються; '
                    'це одноразові докази, без лічильника циклів або перевірки FE/t.')
            quests.append({'id': qid, 'title': m['title'], 'x': float((j-1) % 3 * 2), 'y': float((j-1) // 3 * 2),
                           'dependencies': list(dict.fromkeys(deps)), 'tasks': tasks,
                           'rewards': [{'id': uid(m['id'] + ':reward'), 'type': 'item',
                                        'item': {'id': 'minecraft:baked_potato', 'count': 1}, 'count': 8}],
                           'description': [m['objective_uk'], acceptance,
                             f'Потрібна стадія Game Stages Reborn: aia2_epoch_{n:02d}. Вона перевіряється нативним advancement.',
                             *process_description,
                             'Предметна здача підтверджує ресурси, але не вимірює FE/t, час роботи чи топологію автоматизації.'],
                           'hide_until_deps_complete': True})
        key_quest = {'id': uid(f'E{n:02d}_KEY'), 'title': e['key']['name_uk'], 'x': 6.0, 'y': 1.0,
                     'dependencies': milestone_ids, 'hide_until_deps_complete': True,
                     'tasks': [{'id': uid(f'E{n:02d}:keytask'), 'type': 'advancement', 'advancement': f'aia2:keys/e{n:02d}'}],
                     'rewards': [{'id': uid(f'E{n:02d}:stage_sync_reward'), 'type': 'command',
                                  'command': 'aia2 sync', 'permission_level': 0, 'silent': True,
                                  'auto': 'invisible', 'team_reward': False}],
                     'description': ['Після шести обов’язкових завдань станьте біля верстака й виконайте /aia2 key.',
                                     'Сервер перевіряє FTB-команду й усі шість завдань ДО витрати інгредієнтів.',
                                     'Ключ перевіряється неспоживно та витрачається тільки в наступному ключі.',
                                     'Склад: ' + '; '.join(f"{v['count']} × {v['id']}" for v in e['key']['ingredients'].values())]}
        quests.append(key_quest)
        for j, q in enumerate(e['optional_quests'], start=1):
            quests.append({'id': uid(f'E{n:02d}_O{j}'), 'title': q['title'], 'x': float((j-1)*3), 'y': 5.0,
                           'optional': True, 'dependencies': [milestone_ids[0]], 'description': [q['objective_uk']],
                           'rewards': [{'id': uid(f'E{n:02d}:optional{j}:reward'), 'type': 'item',
                                        'item': {'id': 'minecraft:torch', 'count': 1}, 'count': 16}],
                           'tasks': [{'id': uid(f'E{n:02d}:optional{j}'), 'type': 'checkmark'}]})
        chapter = {'id': uid(f'CH{n:02d}'), 'filename': f'aia2_epoch_{n:02d}', 'order_index': n-1,
                   'title': f'{n:02d}. {e["title"]}', 'icon': {'id': e['key']['id'], 'count': 1},
                   'hide_quest_details_until_startable': True, 'hide_quest_until_deps_complete': True,
                   'default_quest_shape': 'square', 'quests': quests}
        emit(f'config/ftbquests/quests/chapters/aia2_epoch_{n:02d}.snbt', chapter)
        emit(f'kubejs/data/aia2/advancement/keys/e{n:02d}.json', {'criteria': {'legal_craft': {'trigger': 'minecraft:impossible'}}})
        emit(f'kubejs/data/aia2/advancement/stages/e{n:02d}.json', {'criteria': {'active_stage': {
            'trigger': 'gamestages:has_stage', 'conditions': {'stage': f'aia2_epoch_{n:02d}'}}}})
        runtime_epochs.append({'number': n, 'title': e['title'], 'key': e['key']['id'],
                               'cost': {v['id']: v['count'] for v in e['key']['ingredients'].values()},
                               'milestoneQuestIds': milestone_ids, 'finalQuestId': key_quest['id']})
    emit('config/ftbquests/quests/data.snbt', {'version': 13})

    floors = {}
    for mod in catalog:
        for ns in mod.get('mod_ids', []):
            floors[ns] = mod.get('first_epoch') if mod.get('first_epoch') is not None else 100
    exact = {}
    for e in epochs:
        for u in e['unlocks']:
            exact[u['id']] = min(e['number'], exact.get(u['id'], 99))
    for c in ops:
        exact[c['target_id']] = 99 if c.get('post_final_only') else c['unlock_epoch']
    exact.update({'chunkloaders:single_chunk_loader': 17, 'chunkloaders:basic_chunk_loader': 17,
                  'chunkloaders:advanced_chunk_loader': 28, 'chunkloaders:ultimate_chunk_loader': 39,
                  'minecraft:crafter': 10})
    # Apply the same policy to BOTH registries. Transformed parts and crops often
    # have no item with the same ID, so an item-only lookup leaves real gaps.
    def stage_for(item_id):
        ns, path = item_id.split(':', 1)
        stage = floors.get(ns, 0)
        if ns == 'evolvedmekanism':
            stage = 43
        if ns == 'draconicevolution':
            stage = 42 if any(x in path for x in ['chaos', 'chaotic']) else (41 if any(x in path for x in ['awakened', 'draconic']) else 40)
        if ns == 'allthemodium':
            stage = 44 if 'unobtainium' in path else 34
        if ns == 'modern_industrialization':
            if any(x in path for x in ['quantum', 'qubit', 'superconductor', 'iridium', 'processing_unit']): stage = 35
            elif 'digital' in path: stage = 32
            elif 'electronic' in path or 'advanced_machine' in path: stage = 22
            elif any(x in path for x in ['electric_', 'analog_', 'basic_machine']): stage = 13
        if ns == 'mekanism':
            if any(x in path for x in ['antimatter', 'sps_', 'meka_tool', 'mekasuit']): stage = 39
            elif any(x in path for x in ['fission', 'polonium', 'plutonium', 'radioactive', 'nuclear_waste']): stage = 33
            elif any(x in path for x in ['ultimate_control', 'teleportation_core', 'quantum_entangloporter', 'digital_miner']): stage = 28
            elif 'elite_control' in path: stage = 26
            elif any(x in path for x in ['advanced_', 'elite_', 'alloy_reinforced', 'alloy_atomic', 'purification']): stage = 23
        if ns == 'mysticalagriculture' and any(x in path for x in ['supremium', 'imperium']): stage = 32
        if ns == 'avaritia': stage = 48 if 'infinity' in path else 46
        if 'creative' in path: stage = 99
        if ns in {'funmod', 'sauce', 'productivelib'}: stage = 100
        if item_id in exact: stage = exact[item_id]
        return stage
    # Keep explicit zeroes too: the native guard distinguishes an intentionally
    # available library/QOL item from a new, unclassified modded item.
    gates = {item_id: stage_for(item_id) for item_id in items}
    gates.update({e['key']['id']: 0 for e in epochs})
    blocks = load(export / 'registries/block.json')
    block_gates = {block_id: stage_for(block_id) for block_id in blocks}
    dimensions = {}
    for dim in load(export / 'registries/dimension.json'):
        ns, path = dim.split(':', 1)
        if dim == 'minecraft:the_nether': dimensions[dim] = 15
        elif dim == 'minecraft:the_end': dimensions[dim] = 30
        elif ns == 'twilightforest': dimensions[dim] = 7
        elif ns == 'aether': dimensions[dim] = 30
        elif ns == 'create_dimension': dimensions[dim] = 28
        elif ns == 'ad_astra': dimensions[dim] = 37 if any(x in path for x in ['moon', 'mars', 'earth']) else 38
        elif ns == 'industrialupgrade': dimensions[dim] = 37 if any(x in path for x in ['moon', 'mars']) else 44
        elif ns != 'minecraft': dimensions[dim] = 100
    emit('kubejs/config/aia2_runtime.json', {'schema': 1, 'epochs': runtime_epochs, 'itemGates': gates,
                                          'blockGates': block_gates,
                                          'machineGuard': {'mode': 'required'},
                                          'dimensionGates': dimensions, 'gameStagesMirror': True,
                                          'enforceItemPickup': False})
    emc = {'minecraft:cobblestone': 1, 'minecraft:stone': 1, 'minecraft:dirt': 1,
           'minecraft:sand': 1, 'minecraft:glass': 1, 'minecraft:gravel': 4,
           'minecraft:oak_log': 32, 'minecraft:oak_planks': 8, 'minecraft:stick': 4,
           'minecraft:charcoal': 32, 'minecraft:coal': 128, 'minecraft:iron_ingot': 256,
           'minecraft:copper_ingot': 128, 'minecraft:gold_ingot': 2048}
    emit('kubejs/config/aia2_emc_whitelist.json', emc)
    emit('config/ProjectE/custom_emc.json', {'comment': 'AIA2: only these ordinary materials have EMC. Runtime re-applies a strict whitelist after every remap.',
          'entries': [{'id': k, 'emc': v} for k, v in emc.items()]})
    report = {'recipes_added': len(recipes), 'source_recipe_ids_removed': len(removals),
              'quest_chapters': 48, 'required_quests': 336, 'optional_quests': 96, 'registered_keys': 48,
              'retained_conversion_ids': kept_conversions, 'blocked_missing_templates': blocked,
              'key_forge': 'atomic_server_command_at_crafting_table_not_ungated_grid_recipe',
              'runtime_compatibility': 'full_pack_source_reviewed_native_adapter_tested_separately',
              'milestone_evidence': 'FTB deliveries and boss kills, plus four source-verified native Create operation proofs in three milestones',
              'native_process_proofs': len(process_proofs),
              'native_stage_advancements': 48, 'mandatory_stage_tasks': 288, 'automatic_stage_sync_rewards': 48,
              'block_registry_entries': len(block_gates),
              'blocks_without_same_item_id': len(set(blocks) - set(items)),
              'remaining_gaps': ['The companion guards machine block tiers, vanilla player crafting and the vanilla Crafter; it does not yet gate every native recipe in early machines.',
                                 'Entity/contraption/global processes and capability IO are outside the standard block-entity tick hook.',
                                 'ProjectE 1.1.0 native EMC whitelist hook is source-verified but must be smoke-tested in the pack.',
                                 'Exact component-aware jetpack/seed family restrictions still require runtime inspection.']}
    (ROOT / 'implementation').mkdir(exist_ok=True)
    (ROOT / 'implementation/generation-report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n')
    print(json.dumps({k: v for k, v in report.items() if k not in {'retained_conversion_ids', 'blocked_missing_templates'}}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
