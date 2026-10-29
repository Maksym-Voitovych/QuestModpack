"""Four source-backed space-engine assemblies and narrowly scoped late-game floors.

The installed export is used to freeze producer closure, not to invent a source
for loot-only items. Normal generation is portable and uses the frozen files.
This does not certify native machine dispatch, flight or TPS in Minecraft.
"""
import copy
import hashlib
import json
from collections import Counter
from pathlib import Path

try:
    from audit_obtainability_v5 import outputs
except ModuleNotFoundError:
    from tools.audit_obtainability_v5 import outputs

ROOT = Path(__file__).resolve().parents[1]
CATALOG = 'content/recipes/v5_ad_astra_core.json'
REPORT = 'implementation/ad-astra-core-balance-v6.json'
PREFIX = 'aia2:v5/ad_astra_core/'
ENGINES = {'ad_astra:steel_engine': 37, 'ad_astra:desh_engine': 37,
           'ad_astra:ostrum_engine': 37, 'ad_astra:calorite_engine': 38}
FLOORS = {'ad_astra:' + name: 38 for name in (
    'raw_calorite', 'raw_calorite_block', 'calorite_block', 'calorite_nugget',
    'calorite_plate', 'calorite_tank', 'calorite_engine', 'calorite_ingot',
    'jet_suit_helmet', 'jet_suit', 'jet_suit_pants', 'jet_suit_boots',
    'gravity_normalizer', 'energizer')}
ADDED = {
    'ad_astra:steel_engine': ['kubejs:aia2_tech_matrix_36', 'kubejs:aia2_arcane_catalyst_36',
                             'ars_nouveau:air_essence', 'mekanism:advanced_control_circuit'],
    'ad_astra:desh_engine': ['kubejs:aia2_tech_matrix_36', 'kubejs:aia2_arcane_catalyst_36',
                            'botania:rune_earth', 'oritech:processing_unit'],
    'ad_astra:ostrum_engine': ['kubejs:aia2_tech_matrix_36', 'kubejs:aia2_arcane_catalyst_36',
                              'botania:rune_fire', 'pneumaticcraft:printed_circuit_board'],
    'ad_astra:calorite_engine': ['kubejs:aia2_tech_matrix_36', 'kubejs:aia2_arcane_catalyst_36',
                                'botania:gaia_ingot', 'mekanism:ultimate_control_circuit'],
}
PATTERN = ['A###B', '#E#CD', '  F  ']


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def canonical(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
                                     separators=(',', ':')).encode()).hexdigest()


def frozen(root, source):
    root = Path(root).resolve()
    relative = Path(source['path'])
    assert not relative.is_absolute() and '..' not in relative.parts, 'Nonportable Ad Astra evidence'
    path = (root / relative).resolve()
    assert path.is_relative_to(root) and path.is_file(), ('Missing Ad Astra evidence', relative)
    raw = path.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == source['sha256'], ('Stale Ad Astra source', relative)
    return raw


def cost(recipe):
    assert recipe['type'] in {'minecraft:crafting_shaped', 'create:mechanical_crafting'}, 'Unsupported engine recipe'
    pattern, keys = recipe['pattern'], recipe['key']
    assert pattern and len({len(row) for row in pattern}) == 1, 'Irregular assembly pattern'
    assert set(keys) == set(''.join(pattern)) - {' '}, 'Unused or missing assembly keys'
    assert all(set(value) in ({'item'}, {'tag'}) for value in keys.values()), 'Unreviewed engine ingredient shape'
    return Counter(json.dumps(keys[char], sort_keys=True) for row in pattern for char in row if char != ' ')


def scan_export(export):
    export = Path(export)
    assert (export / 'recipes').is_dir(), 'Original export required for producer rescan'
    targets = {target: [] for target in sorted(set(ENGINES) | set(FLOORS))}
    manifest = {}
    for path in sorted((export / 'recipes').rglob('*.json')):
        relative = path.relative_to(export / 'recipes').with_suffix('')
        ident = relative.parts[0] + ':' + '/'.join(relative.parts[1:])
        raw = path.read_bytes()
        manifest[ident] = hashlib.sha256(raw).hexdigest()
        for item in set(outputs(json.loads(raw))) & targets.keys():
            targets[item].append(ident)
    return {'recipes_scanned': len(manifest), 'manifest_sha256': canonical(manifest), 'targets': targets}


def quest_references(root):
    """An explicit functional floor must not strand a previously authored goal."""
    references = []
    for path in sorted((Path(root) / 'content/quests').glob('*.json')):
        data = read(path)
        for quest in data if isinstance(data, list) else data.get('quests', []):
            limit = 99 if quest.get('post_completion') else quest['epoch']
            used = {quest.get('icon')}
            for record in quest.get('tasks', []) + quest.get('reward', []):
                used.update((record.get('item'), record.get('block')))
            for item in sorted(used & FLOORS.keys()):
                assert FLOORS[item] <= limit, ('Earlier quest references gated space equipment', quest['id'], item)
                references.append({'quest': quest['id'], 'item': item, 'epoch': quest['epoch']})
    return references


def bootstrap_component_proof(catalog, actual, rules):
    """The initial rocket cannot depend on components made from its first planet."""
    expected = {'kubejs:aia2_tech_matrix_36': 'aia2:components/e36/tech_matrix',
                'kubejs:aia2_arcane_catalyst_36': 'aia2:components/e36/arcane_catalyst'}
    assert {row['item']: row['recipe_id'] for row in catalog['bootstrap_component_sources']} == expected, 'Incomplete pre-Moon component proof'
    graph = {}
    for row in catalog['bootstrap_component_sources']:
        recipe = actual[row['recipe_id']]
        assert recipe['epoch'] == 36 and row['item'] in set(outputs(recipe['json'])), 'Wrong pre-Moon component producer'
        ingredients = recipe['json']['ingredients']
        assert all(set(value) == {'item'} for value in ingredients), 'Unreviewed pre-Moon component ingredient'
        items = sorted({value['item'] for value in ingredients})
        assert items == row['ingredient_item_ids'], 'Changed pre-Moon component ancestry'
        assert all(not item.startswith('ad_astra:') and rules['itemGates'].get(item, 100) <= 36 for item in items), 'Future or cyclic pre-Moon component'
        graph[row['item']] = [item for item in items if item in expected]
    visited, active = set(), set()
    def visit(item):
        assert item not in active, 'Cyclic pre-Moon component'
        if item in visited:
            return
        active.add(item)
        for parent in graph[item]:
            visit(parent)
        active.remove(item)
        visited.add(item)
    for item in expected:
        visit(item)
    return len(visited)


def validate(root, catalog, bundle, rules, compiled=False):
    root = Path(root)
    assert catalog['schema'] == 1 and catalog['installed_versions'] == {'ad_astra': '1.16.26', 'create': '6.0.10'}, 'Ad Astra version contract changed'
    assert catalog['item_floors'] == FLOORS, 'Unreviewed functional floor scope'
    assert set(catalog['baseline_item_floors']) == set(FLOORS), 'Missing baseline item floor evidence'
    matching_blocks = set(FLOORS) & rules['blockGates'].keys()
    assert set(catalog['block_floors']) == matching_blocks and all(v == 38 for v in catalog['block_floors'].values()), 'Unreviewed block floor scope'
    assert {record['target'] for record in catalog['recipes']} == set(ENGINES) and len(catalog['recipes']) == 4, 'Engine closure changed'
    actual = {entry['id']: entry for entry in bundle['add']}
    assert len(actual) == len(bundle['add']), 'Duplicate custom recipe ID'
    assert len(catalog['baseline_recipe_hashes']) == 623, 'Published623 baseline required'
    for ident, digest in catalog['baseline_recipe_hashes'].items():
        assert ident in actual and canonical(actual[ident]) == digest, ('Published custom recipe changed', ident)
    pre_moon_components = bootstrap_component_proof(catalog, actual, rules)
    for evidence in catalog['format_sources']:
        source = frozen(root, evidence).decode()
        assert 'Codec.BOOL.fieldOf("accept_mirrored")' in source, 'Changed Create mechanical codec'
        assert 'RecipeSerializer.SHAPED_RECIPE.codec()' in source, 'Changed Create shape parser'
    scan = catalog['producer_scan']
    assert scan['recipes_scanned'] == 42064 and len(scan['manifest_sha256']) == 64, 'Incomplete full-export inventory'
    assert set(scan['targets']) == set(ENGINES) | set(FLOORS), 'Incomplete producer target set'
    derived = {target: [] for target in scan['targets']}
    native_floors = {}
    for source in catalog['producer_sources']:
        recipe = json.loads(frozen(root, source))
        assert recipe['type'] == source['type'], 'Changed native producer serializer'
        hits = set(outputs(recipe)) & derived.keys()
        assert hits, 'Irrelevant producer evidence'
        ident = source['recipe_id']
        for item in hits:
            derived[item].append(ident)
        floor_hits = hits & FLOORS.keys()
        if floor_hits:
            native_floors[ident] = max(FLOORS[item] for item in floor_hits)
    assert {target: sorted(ids) for target, ids in derived.items()} == scan['targets'], 'Native alternate producer closure changed'
    assert catalog['native_recipe_floors'] == native_floors, 'Incomplete native producer floors'
    for record in catalog['recipes']:
        target = record['target']
        epoch = ENGINES[target]
        assert record['id'] == PREFIX + target.split(':')[1] and record['epoch'] == epoch, 'Wrong engine epoch or ID'
        original = json.loads(frozen(root, record['source']))
        assert original['type'] == 'minecraft:crafting_shaped' and original['result'] == {'id': target, 'count': 1}, 'Unexpected native engine producer'
        recipe = record['json']
        assert recipe['type'] == 'create:mechanical_crafting' and recipe.get('accept_mirrored') is False, 'Wrong assembly serializer or mirror policy'
        assert recipe['pattern'] == PATTERN and recipe['result'] == {'id': target, 'count': 1}, 'Unreviewed engine shape/output'
        assert record['added_item_ids'] == ADDED[target], 'Future or unreviewed assembly additions'
        expected = cost(original) + Counter(json.dumps({'item': item}, sort_keys=True) for item in ADDED[target])
        assert cost(recipe) == expected and sum(cost(original).values()) == 7, 'Native materials or reviewed cross-mod units changed'
        assert all(item in rules['itemGates'] and rules['itemGates'][item] <= epoch and item not in ENGINES for item in ADDED[target]), 'Future or cyclic assembly inputs'
        assert not any('matrix_37' in item or 'catalyst_37' in item or '_key_' in item for item in ADDED[target]), 'Initial rocket requires post-Moon component or epoch key'
        assert rules['itemGates']['create:mechanical_crafter'] <= epoch, 'Future assembly machine'
        assert rules['itemGates'].get(target, 100) <= epoch, 'Future engine target'
        assert record['remove_recipe_ids'] == scan['targets'][target] == [record['source']['recipe_id']], 'Incomplete or unreviewed engine producer removal'
        if compiled:
            assert actual.get(record['id']) == {key: copy.deepcopy(record[key]) for key in ('id', 'epoch', 'target', 'category', 'json')}, 'Engine assembly not compiled'
            assert rules['recipeGates'].get(record['id']) == epoch, 'Engine recipe floor not applied'
            assert set(record['remove_recipe_ids']) <= set(bundle['remove']), 'Native easy engine path still active'
    references = quest_references(root)
    # Existing custom recipes that make a scoped late item also need its output floor.
    custom_floors = {}
    for ident, record in actual.items():
        hits = set(outputs(record['json'])) & FLOORS.keys()
        if hits:
            custom_floors[ident] = max(record['epoch'], *(FLOORS[item] for item in hits))
    if compiled:
        for item, floor in FLOORS.items():
            assert rules['itemGates'][item] >= floor, ('Functional item floor not applied', item)
        for block, floor in catalog['block_floors'].items():
            assert rules['blockGates'][block] >= floor, ('Functional block floor not applied', block)
        for ident, floor in dict(native_floors, **custom_floors).items():
            assert rules['recipeGates'].get(ident, 0) >= floor, ('Space producer floor not applied', ident)
    return {'status': 'passed', 'new_recipes': 4, 'native_engine_producers_replaced': 4,
            'native_material_units_per_engine': 7, 'added_cross_mod_units_per_engine': 4,
            'published_custom_recipes_preserved': 623, 'pre_moon_components_verified': pre_moon_components, 'item_floors': len(FLOORS),
            'item_floors_raised_from_baseline': sum(catalog['baseline_item_floors'][item] < floor for item, floor in FLOORS.items()),
            'block_floors': len(catalog['block_floors']),
            'native_recipe_floors': len(native_floors), 'custom_recipe_floors': len(custom_floors),
            'quest_references_checked': len(references), 'full_export_recipes_scanned': scan['recipes_scanned'],
            'decorative_calorite_scope': 'unchanged', 'full_pack_execution': False}


def apply(root=ROOT):
    root = Path(root)
    catalog = read(root / CATALOG)
    bundle = read(root / 'kubejs/config/aia2_recipes.json')
    rules = read(root / 'kubejs/config/aia2_runtime.json')
    validate(root, catalog, bundle, rules)
    owned = {record['id'] for record in catalog['recipes']}
    bundle['add'] = [record for record in bundle['add'] if record['id'] not in owned] + [
        {key: copy.deepcopy(record[key]) for key in ('id', 'epoch', 'target', 'category', 'json')}
        for record in catalog['recipes']]
    bundle['remove'] = sorted(set(bundle['remove']) | {rid for record in catalog['recipes'] for rid in record['remove_recipe_ids']})
    for item, floor in sorted(FLOORS.items()):
        assert item in rules['itemGates'], ('Unregistered space item', item)
        rules['itemGates'][item] = max(rules['itemGates'][item], floor)
    for block, floor in sorted(catalog['block_floors'].items()):
        rules['blockGates'][block] = max(rules['blockGates'][block], floor)
    for ident, floor in sorted(catalog['native_recipe_floors'].items()):
        rules['recipeGates'][ident] = max(rules['recipeGates'].get(ident, 0), floor)
    for record in bundle['add']:
        ident = record['id']
        if ident in owned:
            rules['recipeGates'][ident] = record['epoch']
        hits = set(outputs(record['json'])) & FLOORS.keys()
        if hits:
            rules['recipeGates'][ident] = max(rules['recipeGates'].get(ident, 0), record['epoch'], *(FLOORS[item] for item in hits))
    report = validate(root, catalog, bundle, rules, compiled=True)
    write(root / 'kubejs/config/aia2_recipes.json', bundle)
    write(root / 'kubejs/config/aia2_runtime.json', rules)
    write(root / REPORT, report)
    return report


if __name__ == '__main__':
    print(json.dumps(apply(), ensure_ascii=False, indent=2))
