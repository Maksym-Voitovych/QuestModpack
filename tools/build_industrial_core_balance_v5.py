"""Four audited MI/Oritech machine processes; preserve published recipes and material costs.

This validates exact source/export contracts. It does not launch either optional
mod or claim that static recipe presence proves complete Survival reachability.
"""
from collections import Counter
import copy
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CATALOG = 'content/recipes/v5_mi_oritech_core.json'
REPORT = 'implementation/industrial-core-balance-v5-audit.json'
PREFIX = 'aia2:v5/industrial_core/'
TARGET_EPOCHS = {
    'modern_industrialization:mv_diesel_generator': 22,
    'modern_industrialization:hv_diesel_generator': 32,
    'oritech:fuel_generator_block': 25,
    'oritech:reactor_controller': 32,
}
VERSIONS = {'modern_industrialization': '2.5.10', 'oritech': '1.2.13'}


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def write(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')


def canonical(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
                                    separators=(',', ':')).encode()).hexdigest()


def frozen(root, source):
    path = Path(source['path'])
    assert not path.is_absolute() and '..' not in path.parts, 'Nonportable industrial source'
    target = (Path(root)/path).resolve()
    assert target.is_relative_to(Path(root).resolve()), 'Industrial source escapes project'
    data = target.read_bytes()
    assert hashlib.sha256(data).hexdigest() == source['sha256'], ('Stale industrial source', str(path))
    return data


def inputs(recipe):
    """Amounts mean stack quantities in MI and repeated units in Oritech."""
    if recipe['type'] == 'modern_industrialization:assembler':
        return recipe['item_inputs']
    assert recipe['type'] == 'oritech:assembler', 'Unsupported industrial serializer'
    return recipe['ingredients']


def cost(entries):
    result = Counter()
    for entry in entries:
        keys = set(entry)-{'amount'}
        assert keys in ({'item'}, {'tag'}), 'Only explicit item/tag inputs reviewed'
        kind = next(iter(keys))
        amount = entry.get('amount', 1)
        assert type(amount) is int and 1 <= amount <= 64, 'Invalid industrial input quantity'
        result[(kind, entry[kind])] += amount
    return result


def crafting_cost(recipe):
    assert recipe['type'] == 'minecraft:crafting_shaped', 'Unreviewed native alternate producer'
    return cost([dict(recipe['key'][symbol]) for row in recipe['pattern']
                 for symbol in row if symbol != ' '])


def output(recipe):
    if recipe['type'] == 'modern_industrialization:assembler':
        assert recipe['item_outputs'] and len(recipe['item_outputs']) == 1
        stack = recipe['item_outputs'][0]
        assert set(stack) == {'item', 'amount'} and stack['amount'] == 1
        return stack['item']
    if recipe['type'] == 'oritech:assembler':
        assert recipe['results'] and len(recipe['results']) == 1
        stack = recipe['results'][0]
        assert set(stack) == {'id', 'count'} and stack['count'] == 1
        return stack['id']
    assert recipe['type'] == 'minecraft:crafting_shaped'
    assert recipe['result'].get('count', 1) == 1
    return recipe['result']['id']


def validate(root, catalog, bundle, rules, compiled=False):
    root = Path(root)
    assert catalog['schema'] == 1 and catalog['installed_versions'] == VERSIONS, 'Industrial version contract changed'
    assert len(catalog['recipes']) == 4 and {r['target'] for r in catalog['recipes']} == set(TARGET_EPOCHS), 'Industrial target scope changed'
    assert len(catalog['baseline_recipe_hashes']) == 606, 'Published606 baseline required'
    actual = {r['id']: r for r in bundle['add']}
    assert len(actual) == len(bundle['add']), 'Duplicate custom recipe ID'
    for ident, digest in catalog['baseline_recipe_hashes'].items():
        assert ident in actual and canonical(actual[ident]) == digest, ('Published industrial baseline changed', ident)
    for source in catalog['sources']:
        frozen(root, source)
    scan = json.loads(frozen(root, catalog['producer_scan']))
    assert scan['recipes_scanned'] == 42064 and set(scan['targets']) == set(TARGET_EPOCHS), 'Incomplete producer scan'
    assert not scan['existing_custom_target_producers'], 'Target already has a published custom producer'
    tags = catalog['tag_evidence']
    for tag, evidence in tags.items():
        assert json.loads(frozen(root, evidence['source'])) == evidence['members'] and evidence['members'], ('Invalid tag evidence', tag)
    source_text = {Path(s['path']).name: frozen(root, s).decode() for s in catalog['sources']}
    assert 'MIMachineRecipeTypes.ASSEMBLER, 9, 3, 2, 0' in source_text['SingleBlockCraftingMachines.java']
    assert 'new InventorySlotAssignment(0, 4, 4, 1)' in source_text['AssemblerBlockEntity.java']
    assert 'Ingredient.CODEC_NONEMPTY.listOf().fieldOf("ingredients")' in source_text['OritechRecipeType.java']
    assert 'ItemStack.CODEC.listOf().fieldOf("results")' in source_text['OritechRecipeType.java']
    assert 'ExtraCodecs.POSITIVE_INT.fieldOf("eu")' in source_text['MachineRecipe.java']
    assert 'Ingredient.MAP_CODEC_NONEMPTY.forGetter(ItemInput::ingredient)' in source_text['MachineRecipe.java']
    assert catalog['item_block_floors'] == {'oritech:reactor_controller': 32}
    removed, seen = set(), set()
    serializers = Counter()
    for spec in catalog['recipes']:
        ident, target, epoch, recipe = spec['id'], spec['target'], spec['epoch'], spec['json']
        assert ident.startswith(PREFIX) and ident not in seen and ident not in catalog['baseline_recipe_hashes']
        seen.add(ident)
        assert epoch == TARGET_EPOCHS[target] and len(spec['purpose_uk'].strip()) >= 30
        assert output(recipe) == target and set(spec['remove_recipe_ids']) == set(scan['targets'][target])
        assert not spec['preserve_recipe_ids'], 'Unexpected producer-preservation exception'
        assert rules['itemGates'][target] <= epoch and rules['blockGates'][target] <= epoch
        machine = spec['producer_machine']
        assert machine in rules['blockGates'] and rules['blockGates'][machine] <= epoch
        assert spec['producer_machine_epoch'] <= epoch
        kind = recipe['type']; serializers[kind] += 1
        entries = inputs(recipe); current_cost = cost(entries)
        if kind == 'modern_industrialization:assembler':
            assert machine == 'modern_industrialization:assembler' and spec['input_slot_capacity'] == 9
            assert 1 <= len(entries) <= 9 and spec['output_slot_capacity'] == 3
            assert set(recipe) == {'type', 'eu', 'duration', 'item_inputs', 'item_outputs'}
            assert recipe['eu'] == 8 and type(recipe['duration']) is int and 200 <= recipe['duration'] <= 600
        else:
            assert machine == 'oritech:assembler_block' and spec['input_slot_capacity'] == 4
            assert 1 <= len(entries) <= 4 and spec['output_slot_capacity'] == 1
            assert all('amount' not in i for i in entries), 'Oritech Ingredient codec has no stack amount'
            assert set(recipe) == {'type', 'time', 'ingredients', 'results'} and recipe['time'] == 192
        for (input_kind, item), amount in current_cost.items():
            if input_kind == 'tag':
                assert item in tags, ('Missing input tag snapshot', item)
                gates = [rules['itemGates'][member] for member in tags[item]['members'] if member in rules['itemGates']]
                assert gates and min(gates) <= epoch, ('No attainable input tag member', item)
                assert not set(tags[item]['members']) & set(TARGET_EPOCHS), 'Machine bootstrap loop through tag'
            else:
                assert item in rules['itemGates'] and rules['itemGates'][item] <= epoch, ('Future/unknown input', item)
                assert item not in TARGET_EPOCHS and not (item.startswith('kubejs:') and 'key' in item), 'Machine bootstrap/key dependency'
        native = {}
        for source in spec['sources']:
            native[source['recipe_id']] = json.loads(frozen(root, source))
        assert set(native) == set(spec['remove_recipe_ids']) and not removed & set(native), 'Native removal scope differs'
        for original in native.values():
            assert output(original) == target
            old_cost = crafting_cost(original) if original['type'] == 'minecraft:crafting_shaped' else cost(inputs(original))
            assert all(current_cost[key] >= amount for key, amount in old_cost.items()), 'Native material cost weakened'
        removed.update(native)
        if compiled:
            assert actual.get(ident) == {key:copy.deepcopy(spec[key]) for key in ('id','epoch','target','category','json')}
            assert rules['recipeGates'][ident] == epoch, 'Industrial recipe floor differs'
    assert len(removed) == 6 and not removed & set(catalog['baseline_recipe_hashes'])
    if compiled:
        assert removed <= set(bundle['remove']), 'Native cheaper route remains active'
        for item, floor in catalog['item_block_floors'].items():
            assert rules['itemGates'][item] == rules['blockGates'][item] == floor, 'Controller floor not applied'
        for rid, floor in catalog['native_recipe_floors'].items():
            assert floor <= rules['recipeGates'][rid] <= 48, 'Controller native recipe floor not applied'
    return {'status':'passed', 'recipes':len(seen), 'native_producers_replaced':len(removed),
            'serializers':dict(serializers), 'published_custom_recipes_preserved':606,
            'native_material_costs_preserved':True, 'controller_item_block_floor':32,
            'full_export_recipes_scanned':42064, 'full_pack_execution':False}


def apply(root=ROOT):
    root = Path(root); catalog = read(root/CATALOG)
    bundle = read(root/'kubejs/config/aia2_recipes.json'); rules = read(root/'kubejs/config/aia2_runtime.json')
    validate(root,catalog,bundle,rules)
    owned = {r['id'] for r in catalog['recipes']}
    bundle['add'] = [r for r in bundle['add'] if r['id'] not in owned] + [
        {key:copy.deepcopy(r[key]) for key in ('id','epoch','target','category','json')} for r in catalog['recipes']]
    removals = {rid for row in catalog['recipes'] for rid in row['remove_recipe_ids']}
    bundle['remove'] = sorted(set(bundle['remove']) | removals)
    bundle['aia2_v5_industrial_core_source_removals'] = sorted(removals)
    for row in sorted(catalog['recipes'],key=lambda row:row['id']):
        rules['recipeGates'][row['id']] = row['epoch']
    for item,floor in sorted(catalog['item_block_floors'].items()):
        rules['itemGates'][item] = max(rules['itemGates'][item],floor)
        rules['blockGates'][item] = max(rules['blockGates'][item],floor)
    for rid,floor in sorted(catalog['native_recipe_floors'].items()):
        assert rid in rules['recipeGates'], ('Unregistered native controller recipe',rid)
        rules['recipeGates'][rid] = max(rules['recipeGates'][rid],floor)
    report = validate(root,catalog,bundle,rules,compiled=True)
    write(root/'kubejs/config/aia2_recipes.json',bundle); write(root/'kubejs/config/aia2_runtime.json',rules)
    write(root/REPORT,report)
    return report
