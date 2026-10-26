"""Five audited EnderIO/Powah machine processes; preserve all 610 published entries.

Portable source/producer snapshots support normal validation. ``scan_export``
independently reproduces the complete 42,064-recipe export inventory and producers.
These static checks do not claim a full Minecraft codec or Survival execution.
"""
import argparse
from collections import Counter
import copy
import hashlib
import json
from pathlib import Path

try:
    from audit_obtainability_v5 import outputs
except ModuleNotFoundError:
    from tools.audit_obtainability_v5 import outputs

ROOT = Path(__file__).resolve().parents[1]
CATALOG = 'content/recipes/v5_enderio_powah_core.json'
REPORT = 'implementation/energy-core-balance-v5-audit.json'
PREFIX = 'aia2:v5/energy_core/'
TARGET_EPOCHS = {
    'enderio:redstone_alloy_ingot': 19,
    'enderio:pulsating_alloy_ingot': 19,
    'enderio:soularium_ingot': 19,
    'powah:steel_energized': 11,
    'powah:ender_core': 11,
}
VERSIONS = {'enderio': '8.2.12-beta', 'powah': '6.2.10'}
SOUL_BLOCKS = ('minecraft:soul_sand', 'minecraft:soul_soil')


def storage_forms():
    """Weights use ninths of an ingot, keeping every conversion integral."""
    forms = {}
    for name in ('redstone_alloy', 'pulsating_alloy', 'soularium', 'energized_steel'):
        ns = 'powah' if name == 'energized_steel' else 'enderio'
        target = 'powah:steel_energized' if ns == 'powah' else f'enderio:{name}_ingot'
        forms[f'{ns}:{name}_block'] = {'target': target, 'units': 81}
        if ns == 'enderio':
            forms[f'{ns}:{name}_nugget'] = {'target': target, 'units': 1}
        for tier in range(1, 10):
            forms[f'allthecompressed:{name}_block_{tier}x'] = {'target': target, 'units': 81*9**tier}
    return forms


STORAGE_FORMS = storage_forms()


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')


def canonical(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
                                    separators=(',', ':')).encode()).hexdigest()


def frozen(root, source):
    root = Path(root).resolve()
    path = Path(source['path'])
    assert not path.is_absolute() and '..' not in path.parts, 'Nonportable energy source'
    target = (root/path).resolve()
    assert target.is_relative_to(root), 'Energy source escapes project'
    raw = target.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == source['sha256'], ('Stale energy source', str(path))
    return raw


def scan_export(export_recipes):
    manifest, producers = [], {item: [] for item in sorted(TARGET_EPOCHS)}
    storage_producers = {item: [] for item in sorted(STORAGE_FORMS)}
    export_recipes = Path(export_recipes)
    for path in sorted(export_recipes.rglob('*.json')):
        raw = path.read_bytes()
        relative = path.relative_to(export_recipes)
        assert len(relative.parts) >= 2, 'Recipe export lacks namespace directory'
        manifest.append([relative.as_posix(), hashlib.sha256(raw).hexdigest()])
        ident = relative.parts[0]+':'+relative.with_suffix('').as_posix().split('/', 1)[1]
        produced = set(outputs(json.loads(raw)))
        for target in produced & TARGET_EPOCHS.keys():
            producers[target].append(ident)
        for target in produced & STORAGE_FORMS.keys():
            storage_producers[target].append(ident)
    return {'recipes_scanned': len(manifest), 'manifest_sha256': canonical(manifest),
            'targets': producers, 'storage_form_producers': storage_producers}


def ingredient_key(entry):
    ingredient = {k: v for k, v in entry.items() if k != 'count'}
    if set(ingredient) == {'item'}:
        return ('item', ingredient['item'])
    if set(ingredient) == {'tag'}:
        if ingredient['tag'] == 'minecraft:soul_fire_base_blocks':
            return ('alternatives', SOUL_BLOCKS)
        return ('tag', ingredient['tag'])
    assert ingredient == {'type': 'neoforge:compound', 'children': [
        {'item': 'minecraft:soul_sand'}, {'item': 'minecraft:soul_soil'}]}, 'Unreviewed ingredient codec'
    return ('alternatives', SOUL_BLOCKS)


def cost(entries, sized=True):
    """EnderIO FLAT_CODEC carries count; Powah Ingredients each consume one unit."""
    result = Counter()
    for entry in entries:
        if not sized:
            assert 'count' not in entry and 'amount' not in entry, 'Unit Ingredient has no stack quantity'
        amount = entry.get('count', 1)
        assert type(amount) is int and 1 <= amount <= 64, 'Invalid energy ingredient quantity'
        result[ingredient_key(entry)] += amount
    return result


def inputs(recipe):
    if recipe['type'] == 'enderio:alloy_smelting':
        return recipe['inputs']
    assert recipe['type'] in {'powah:energizing', 'oritech:foundry'}, 'Unsupported energy producer serializer'
    return recipe['ingredients']


def output_stack(recipe):
    if recipe['type'] == 'enderio:alloy_smelting':
        return recipe['output']
    if recipe['type'] == 'oritech:foundry':
        assert len(recipe['results']) == 1
        return recipe['results'][0]
    return recipe['result']


def quest_craft_references(root):
    refs = []
    for path in sorted((Path(root)/'content/quests').glob('*.json')):
        data = read(path)
        for quest in data if isinstance(data, list) else data.get('quests', []):
            for task in quest.get('tasks', []):
                if task.get('craft') is True and task.get('item') in TARGET_EPOCHS:
                    refs.append([quest['id'], task['item']])
    return refs


def validate_storage_closure(root, catalog, scan, bundle):
    """Close indirect primary producers while proving every storage route lossless."""
    closure = catalog['storage_closure']
    assert closure['forms'] == STORAGE_FORMS, 'Incomplete energy storage family scope'
    assert set(scan['storage_form_producers']) == set(STORAGE_FORMS), 'Incomplete storage producer scan'
    scope = set(STORAGE_FORMS) | TARGET_EPOCHS.keys()
    assert not scan['existing_custom_storage_form_producers']
    assert not [r['id'] for r in bundle['add'] if r['id'] in catalog['baseline_recipe_hashes'] and
                set(outputs(r['json'])) & scope], 'Published custom storage producer exists'
    found = {rid for ids in scan['storage_form_producers'].values() for rid in ids}
    removed, preserved = set(closure['remove_recipe_ids']), set(closure['preserve_recipe_ids'])
    assert not removed & preserved and removed | preserved == found, 'Incomplete storage producer classification'
    assert removed == {f'allthecompressed:energizing/energized_steel_block/x{tier}' for tier in range(5)}, \
        'Unreviewed indirect primary removal scope'
    native = {s['recipe_id']: json.loads(frozen(root, s)) for s in closure['sources']}
    assert len(native) == len(closure['sources']) and set(native) == found, 'Storage source completeness differs'
    weights = {item: (row['target'], row['units']) for item, row in STORAGE_FORMS.items()}
    weights.update({item: (item, 9) for item in TARGET_EPOCHS if item != 'powah:ender_core'})
    steel = next(r['json'] for r in catalog['recipes'] if r['target'] == 'powah:steel_energized')
    for rid, recipe in native.items():
        result = output_stack(recipe); item = result['id']
        assert item in STORAGE_FORMS and rid in scan['storage_form_producers'][item]
        if rid in removed:
            tier = int(rid.rsplit('x', 1)[1]); multiplier = 9**(tier+1)
            expected = ([{'tag': 'c:storage_blocks/iron'}, {'tag': 'c:storage_blocks/gold'}] if tier == 0 else
                        [{'item': f'allthecompressed:iron_block_{tier}x'}, {'item': f'allthecompressed:gold_block_{tier}x'}])
            assert recipe['type'] == 'powah:energizing' and recipe['ingredients'] == expected
            assert result['count'] == 2 and STORAGE_FORMS[item] == {'target': 'powah:steel_energized', 'units': 9*multiplier}
            assert recipe['energy'] == 10000*multiplier
            assert steel['energy']*multiplier >= recipe['energy']*1.5, 'Compressed native energy weakened'
        else:
            if recipe['type'] == 'minecraft:crafting_shaped':
                entries = [recipe['key'][symbol] for row in recipe['pattern'] for symbol in row if symbol != ' ']
            else:
                assert recipe['type'] == 'minecraft:crafting_shapeless', 'Unreviewed storage family primary producer'
                entries = recipe['ingredients']
            assert entries and all(set(entry) == {'item'} and entry['item'] in weights for entry in entries)
            family, weight = weights[item]
            assert all(weights[entry['item']][0] == family for entry in entries), 'Cross-family storage conversion'
            assert sum(weights[entry['item']][1] for entry in entries) == weight*result.get('count', 1), \
                'Storage conversion creates material'
    assert len(removed) == 5 and len(preserved) == 79
    return removed, preserved


def validate_sources(root, catalog):
    texts = {}
    for source in catalog['sources']:
        raw = frozen(root, source)
        texts[Path(source['path']).name] = raw.decode()
    pins = json.loads(texts['source_pins.json'])
    assert pins['enderio']['installed_version'] == VERSIONS['enderio']
    assert pins['enderio']['commit'] == '9d35cace6895f451b4478a8608ff0fa0506530a5'
    assert 'v8.2.12-beta' in pins['enderio']['tag_points_to_commit'], 'EnderIO exact version unresolved'
    assert pins['powah']['installed_version'] == VERSIONS['powah'] and pins['powah'].get('version_match') is True, \
        'Powah exact 6.2.10 release build provenance required'
    installed = json.loads(texts['installed-metadata.json'])
    assert all(installed[mod]['version'] == version for mod, version in VERSIONS.items())
    alloy = texts['AlloySmeltingRecipe.java']
    for token in ('SizedIngredient.FLAT_CODEC.listOf().fieldOf("inputs")',
                  'ItemStack.CODEC.fieldOf("output")', 'Codec.INT.fieldOf("energy")',
                  'Codec.FLOAT.fieldOf("experience")', 'optionalFieldOf("is_smelting", false)'):
        assert token in alloy, ('Unreviewed EnderIO codec', token)
    assert '.inputSlot(3, this::acceptSlotInput)' in texts['AlloySmelterBlockEntity.java']
    assert 'stack.shrink(input.count())' in texts['AlloySmelterBlockEntity.java']
    assert '"alloy_smelting", AlloySmeltingRecipe.Serializer::new' in texts['EIORecipes.java']
    # Powah exact-source contract is kept in the pin manifest so the vendored
    # source filenames and codec/capacity excerpts remain explicit and portable.
    contract = pins['powah']['contracts']
    assert contract['input_capacity'] == 6 and contract['unit_ingredients'] is True
    assert contract['output_capacity'] == 1 and contract['serializer'] == 'powah:energizing'
    for row in contract['source_tokens']:
        assert row['token'] in texts[row['file']], ('Unreviewed Powah source contract', row)
    return pins


def validate(root, catalog, bundle, rules, compiled=False, export_recipes=None):
    root = Path(root)
    assert catalog['schema'] == 1 and catalog['installed_versions'] == VERSIONS, 'Energy version contract changed'
    assert len(catalog['recipes']) == 5 and {r['target'] for r in catalog['recipes']} == set(TARGET_EPOCHS), \
        'Energy target scope changed'
    baseline = catalog['baseline_recipe_hashes']
    assert len(baseline) == 610, 'Published610 baseline required'
    actual = {r['id']: r for r in bundle['add']}
    assert len(actual) == len(bundle['add']), 'Duplicate custom recipe ID'
    for ident, digest in baseline.items():
        assert ident in actual and canonical(actual[ident]) == digest, ('Published energy baseline changed', ident)
    assert not [r['id'] for r in bundle['add'] if r['id'] in baseline and
                set(outputs(r['json'])) & TARGET_EPOCHS.keys()], 'Target already has a published custom producer'
    assert not quest_craft_references(root), 'Machine output cannot require quest craft:true'
    validate_sources(root, catalog)
    scan = json.loads(frozen(root, catalog['producer_scan']))
    assert scan['recipes_scanned'] == 42064 and set(scan['targets']) == set(TARGET_EPOCHS), 'Incomplete energy producer scan'
    assert scan['custom_baseline_entries'] == 610 and not scan['existing_custom_target_producers']
    if export_recipes is not None:
        expected = {key: scan[key] for key in ('recipes_scanned', 'manifest_sha256', 'targets', 'storage_form_producers')}
        assert scan_export(export_recipes) == expected, 'Full export producer inventory drifted'
    tags = catalog['tag_evidence']
    for tag, evidence in tags.items():
        assert json.loads(frozen(root, evidence['source'])) == evidence['members'] and evidence['members'], \
            ('Invalid energy tag evidence', tag)
    assert tuple(sorted(tags['minecraft:soul_fire_base_blocks']['members'])) == SOUL_BLOCKS, \
        'Soul sand/soil alternatives changed'
    assert catalog['item_block_floors'] == catalog['native_recipe_floors'] == {}, 'Unexpected energy floor mutation'
    indirect_removed, storage_preserved = validate_storage_closure(root, catalog, scan, bundle)
    removed, preserved, seen, serializers = set(), set(), set(), Counter()
    contracts = catalog['preserved_producer_contracts']
    for spec in catalog['recipes']:
        ident, target, epoch, recipe = spec['id'], spec['target'], spec['epoch'], spec['json']
        assert ident.startswith(PREFIX) and ident not in seen and ident not in baseline
        seen.add(ident)
        assert epoch == TARGET_EPOCHS[target] and len(spec['purpose_uk'].strip()) >= 30
        result = output_stack(recipe)
        assert set(result) == {'id', 'count'} and result['id'] == target
        assert type(result['count']) is int and result['count'] in {1, 2}, 'Invalid energy output quantity'
        replaced, kept = set(spec['remove_recipe_ids']), set(spec['preserve_recipe_ids'])
        assert not replaced & kept and replaced | kept == set(scan['targets'][target]), 'Incomplete native producer classification'
        assert not (removed | preserved) & (replaced | kept), 'Duplicate native producer classification'
        assert rules['itemGates'][target] <= epoch
        machine = spec['producer_machine']
        assert machine in rules['blockGates'] and rules['blockGates'][machine] <= epoch, 'Future producer machine'
        assert spec['producer_machine_epoch'] <= epoch
        kind = recipe['type']; serializers[kind] += 1
        entries = inputs(recipe)
        if kind == 'enderio:alloy_smelting':
            assert machine == 'enderio:alloy_smelter' and spec['input_slot_capacity'] == 3
            assert set(recipe) == {'type', 'energy', 'experience', 'inputs', 'output'}, 'Unsupported EnderIO fields'
            assert len(entries) == 3 and recipe['experience'] == 0.3 and type(recipe['energy']) is int
            current_cost = cost(entries)
        else:
            assert kind == 'powah:energizing' and machine == 'powah:energizing_orb'
            assert set(recipe) == {'type', 'energy', 'ingredients', 'result'}, 'Unsupported Powah fields'
            assert spec['input_slot_capacity'] == 6 and 1 <= len(entries) <= 6
            assert type(recipe['energy']) is int and recipe['energy'] > 0
            current_cost = cost(entries, sized=False)
        assert spec['output_slot_capacity'] == 1
        assert current_cost[('item', spec['magic_input'])] >= 1 and spec['magic_input'].startswith(('botania:', 'occultism:'))
        for (input_kind, item), amount in current_cost.items():
            if input_kind == 'tag':
                assert item in tags, ('Missing energy input tag snapshot', item)
                members = [x for x in tags[item]['members'] if not x.startswith('#')]
                assert members and not set(members) & TARGET_EPOCHS.keys(), 'Machine bootstrap through tag'
                assert any(x in rules['itemGates'] and rules['itemGates'][x] <= epoch for x in members), \
                    ('No attainable energy tag member', item)
            else:
                members = item if input_kind == 'alternatives' else [item]
                for member in members:
                    assert member in rules['itemGates'] and rules['itemGates'][member] <= epoch, ('Future/unknown energy input', member)
                    assert member not in TARGET_EPOCHS and not member.startswith('kubejs:'), 'Machine bootstrap/key dependency'
        native = {s['recipe_id']: json.loads(frozen(root, s)) for s in spec['sources']}
        assert len(native) == len(spec['sources']) and set(native) == replaced | kept, 'Native source completeness differs'
        for rid, original in native.items():
            assert target in set(outputs(original)), ('Source is not a target producer', rid)
            if rid in replaced:
                assert original['type'] in {'enderio:alloy_smelting', 'oritech:foundry', 'powah:energizing'}, \
                    'Only confirmed cheap native primary processes may be removed'
                assert output_stack(original) == result, 'Native output count changed'
                old_cost = cost(inputs(original), sized=original['type'] == 'enderio:alloy_smelting')
                assert all(current_cost[key] >= amount for key, amount in old_cost.items()), 'Native material cost weakened'
                if 'energy' in original:
                    assert recipe['energy'] >= original['energy'] * 1.5, 'Native machine energy weakened'
            else:
                contract = contracts[rid]
                assert original['type'] in {'minecraft:crafting_shaped', 'minecraft:crafting_shapeless', 'crafting_shaped'}
                if contract['kind'] == 'later_renewable_essence':
                    assert rid.startswith('mysticalagriculture:essence/')
                    assert epoch < contract['input_epoch'] <= rules['itemGates'][contract['input']] <= 48, 'Renewable producer is not later'
                    assert set(original['key']) == {'E'} and original['key']['E'] == {'item': contract['input']}
                else:
                    assert contract['kind'] == 'lossless_storage_conversion'
                    item = contract['input']
                    assert item.rsplit('_', 1)[0] == target.rsplit('_', 1)[0] or \
                        (target == 'powah:steel_energized' and item == 'powah:energized_steel_block'), 'Unrelated storage conversion'
                    if original['type'] == 'minecraft:crafting_shaped':
                        assert original['pattern'] == ['NNN']*3 and original['key'] == {'N': {'item': item}}
                        assert item.endswith('_nugget') and output_stack(original)['count'] == 1
                    else:
                        assert original['ingredients'] == [{'item': item}] and item.endswith('_block')
                        assert output_stack(original)['count'] == 9
        removed.update(replaced); preserved.update(kept)
        if compiled:
            expected = {key: copy.deepcopy(spec[key]) for key in ('id', 'epoch', 'target', 'category', 'json')}
            assert actual.get(ident) == expected, 'Compiled energy recipe differs'
            assert rules['recipeGates'][ident] == epoch, 'Energy recipe floor differs'
    assert len(removed) == 8 and len(preserved) == 11 and set(contracts) == preserved
    assert not (removed | preserved) & set(baseline)
    removed.update(indirect_removed); preserved.update(storage_preserved)
    assert len(removed) == 13 and len(preserved) == 90
    assert not preserved & set(bundle['remove']), 'Preserved storage/renewable producer was removed'
    if compiled:
        assert removed <= set(bundle['remove']), 'Native cheaper route remains active'
    return {'status': 'passed', 'recipes': len(seen), 'native_producers_replaced': len(removed),
            'native_producers_preserved': len(preserved), 'serializers': dict(serializers),
            'storage_forms_checked': len(STORAGE_FORMS), 'storage_conversions_preserved': 86,
            'later_renewable_producers_preserved': 4,
            'published_custom_recipes_preserved': 610, 'native_material_costs_preserved': True,
            'quest_craft_true_conflicts': 0, 'full_export_recipes_scanned': 42064,
            'full_export_verified_this_run': export_recipes is not None, 'full_pack_execution': False}


def apply(root=ROOT):
    root = Path(root); catalog = read(root/CATALOG)
    bundle = read(root/'kubejs/config/aia2_recipes.json'); rules = read(root/'kubejs/config/aia2_runtime.json')
    validate(root, catalog, bundle, rules)
    owned = {r['id'] for r in catalog['recipes']}
    bundle['add'] = [r for r in bundle['add'] if r['id'] not in owned] + [
        {key: copy.deepcopy(r[key]) for key in ('id', 'epoch', 'target', 'category', 'json')} for r in catalog['recipes']]
    removals = {rid for row in catalog['recipes'] for rid in row['remove_recipe_ids']}
    removals.update(catalog['storage_closure']['remove_recipe_ids'])
    bundle['remove'] = sorted(set(bundle['remove']) | removals)
    bundle['aia2_v5_energy_core_source_removals'] = sorted(removals)
    for row in sorted(catalog['recipes'], key=lambda row: row['id']):
        rules['recipeGates'][row['id']] = row['epoch']
    report = validate(root, catalog, bundle, rules, compiled=True)
    write(root/'kubejs/config/aia2_recipes.json', bundle); write(root/'kubejs/config/aia2_runtime.json', rules)
    write(root/REPORT, report)
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['apply', 'validate'])
    parser.add_argument('--root', type=Path, default=ROOT)
    parser.add_argument('--export-recipes', type=Path)
    parser.add_argument('--compiled', action='store_true', help='Also require generated rows, gates and source removals')
    args = parser.parse_args()
    if args.command == 'apply':
        report = apply(args.root)
    else:
        report = validate(args.root, read(args.root/CATALOG), read(args.root/'kubejs/config/aia2_recipes.json'),
                          read(args.root/'kubejs/config/aia2_runtime.json'), compiled=args.compiled,
                          export_recipes=args.export_recipes)
    print(json.dumps(report, ensure_ascii=False, indent=2))
