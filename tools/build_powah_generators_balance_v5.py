"""Three bounded Nitro generator upgrades, preserving all published615 recipe records.

The exact Create6.0.10 mechanical codec and Powah6.2.10 costs are source-checked.
A complete export scan freezes every output producer. This is static validation,
not optional-mod dispatch or a measurement of generator FE performance.
"""
import argparse
from collections import Counter
import copy
import json
from pathlib import Path

try:
    from build_energy_core_balance_v5 import canonical, frozen, read, write
    from audit_obtainability_v5 import outputs
except ModuleNotFoundError:
    from tools.build_energy_core_balance_v5 import canonical, frozen, read, write
    from tools.audit_obtainability_v5 import outputs

ROOT = Path(__file__).resolve().parents[1]
CATALOG = 'content/recipes/v5_powah_generators.json'
REPORT = 'implementation/powah-generators-balance-v5-audit.json'
PREFIX = 'aia2:v5/powah_generators/'
TARGETS = {'powah:furnator_nitro', 'powah:thermo_generator_nitro', 'powah:solar_panel_nitro'}
VERSIONS = {'powah': '6.2.10', 'create': '6.0.10'}


def scan_export(export_recipes):
    """Scan output positions, including recipe/effect wrappers; inputs are not producers."""
    import hashlib
    export_recipes = Path(export_recipes)
    manifest, producers = [], {item: [] for item in sorted(TARGETS)}
    for path in sorted(export_recipes.rglob('*.json')):
        raw = path.read_bytes(); relative = path.relative_to(export_recipes)
        assert len(relative.parts) >= 2, 'Export namespace required'
        manifest.append([relative.as_posix(), hashlib.sha256(raw).hexdigest()])
        ident = relative.parts[0] + ':' + relative.with_suffix('').as_posix().split('/', 1)[1]
        for target in set(outputs(json.loads(raw))) & TARGETS:
            producers[target].append(ident)
    return {'recipes_scanned': len(manifest), 'manifest_sha256': canonical(manifest), 'targets': producers}


def cost(recipe):
    """Every shaped cell consumes one exact item; no hidden count/tag/component codec."""
    assert recipe['type'] in {'minecraft:crafting_shaped', 'create:mechanical_crafting'}, 'Unsupported Nitro codec'
    pattern, keys = recipe['pattern'], recipe['key']
    assert type(pattern) is list and pattern and all(type(row) is str for row in pattern), 'Invalid shaped pattern'
    width = len(pattern[0])
    assert 1 <= width <= 9 and 1 <= len(pattern) <= 9 and all(len(row) == width for row in pattern), 'Invalid mechanical dimensions'
    used = {symbol for row in pattern for symbol in row if symbol != ' '}
    assert used == set(keys) and all(len(symbol) == 1 and symbol != ' ' for symbol in keys), 'Missing/unused shaped key'
    for value in keys.values():
        assert set(value) == {'item'} and type(value['item']) is str, 'Only exact unit item ingredients reviewed'
    return Counter(keys[symbol]['item'] for row in pattern for symbol in row if symbol != ' ')


def result(recipe):
    stack = recipe['result']
    assert set(stack) == {'id', 'count'} and type(stack['count']) is int and stack['count'] == 1, 'Nitro output quantity changed'
    return stack['id']


def craft_conflicts(root):
    conflicts = []
    for path in (Path(root)/'content/quests').glob('*.json'):
        data = read(path)
        for quest in data if type(data) is list else data.get('quests', []):
            for task in quest.get('tasks', []):
                if task.get('type') == 'item' and task.get('item') in TARGETS and task.get('craft') is True:
                    conflicts.append(quest['id'])
    return conflicts


def validate(root, catalog, bundle, rules, compiled=False, export_recipes=None):
    root = Path(root)
    assert catalog['schema'] == 1 and catalog['installed_versions'] == VERSIONS, 'Nitro installed version contract changed'
    assert len(catalog['recipes']) == 3 and {r['target'] for r in catalog['recipes']} == TARGETS, 'Nitro target scope changed'
    baseline = catalog['baseline_recipe_hashes']
    assert len(baseline) == 615, 'Published615 recipe baseline required'
    actual = {row['id']: row for row in bundle['add']}
    assert len(actual) == len(bundle['add']), 'Duplicate custom recipe ID'
    for ident, digest in baseline.items():
        assert ident in actual and canonical(actual[ident]) == digest, ('Published Nitro baseline changed', ident)
    assert not [r['id'] for r in bundle['add'] if not r['id'].startswith(PREFIX) and set(outputs(r['json'])) & TARGETS], 'Unreviewed custom Nitro producer'
    texts = {Path(source['path']).name: frozen(root, source).decode() for source in catalog['sources']}
    assert 'ShapedRecipePattern.setCraftingSize(9, 9)' in texts['AllRecipeTypes.java'], 'Mechanical maximum size unverified'
    assert 'RecipeSerializer.SHAPED_RECIPE.codec()' in texts['MechanicalCraftingRecipe.java']
    assert 'Codec.BOOL.fieldOf("accept_mirrored")' in texts['MechanicalCraftingRecipe.java']
    assert 'if (!(input instanceof MechanicalCraftingInput))' in texts['MechanicalCraftingRecipe.java']
    assert 'getRecipeFor(getType(), inv, world)' in texts['AllRecipeTypes.java'], 'Mechanical lookup path changed'
    assert 'POWAH_VERSION' in texts['build.gradle'] and 'github.event.release.tag_name' in texts['release.yml']
    scan = json.loads(frozen(root, catalog['producer_scan']))
    assert scan['recipes_scanned'] == 42064 and set(scan['targets']) == TARGETS and not scan['existing_custom_target_producers'], 'Nitro producer inventory incomplete'
    assert scan['storage_or_conversion_forms'] == [], 'Unreviewed Nitro storage form'
    if export_recipes is not None:
        reproduced = scan_export(export_recipes)
        assert all(scan[key] == value for key, value in reproduced.items()), 'Full Nitro producer inventory differs'
    registry = json.loads(frozen(root, catalog['registry_evidence']))
    assert registry['registry_entries'] == 27964 and len(registry['source_sha256']) == 64, 'Registry selection provenance required'
    assert not craft_conflicts(root), 'Mechanical Nitro output cannot require vanilla craft:true quest'
    seen, removed = set(), set()
    for spec in catalog['recipes']:
        ident, target, recipe, epoch = spec['id'], spec['target'], spec['json'], spec['epoch']
        assert ident == PREFIX + target.split(':', 1)[1] and ident not in seen, 'Invalid/duplicate Nitro recipe ID'
        seen.add(ident)
        assert epoch == 36 and spec['producer'] == 'create:mechanical_crafter', 'Nitro epoch/producer contract changed'
        assert spec['category'] == 'integration' and spec['recipe_shape'] == [5, 3]
        assert set(recipe) == {'type', 'category', 'key', 'pattern', 'result', 'accept_mirrored'}, 'Unreviewed mechanical recipe fields'
        assert recipe['type'] == 'create:mechanical_crafting' and recipe['category'] == 'misc' and recipe['accept_mirrored'] is False
        assert result(recipe) == target and len(recipe['pattern']) == 3 and all(len(row) == 5 for row in recipe['pattern']), 'Nitro shape/result changed'
        current_cost = cost(recipe)
        assert rules['itemGates'].get(target) == epoch and rules['blockGates'].get(target) == epoch, 'Nitro generator floor changed'
        assert rules['blockGates'].get(spec['producer'], 100) <= epoch, 'Future mechanical producer'
        assert spec['magic_input'].startswith('botania:') and spec['tech_input'].split(':')[0] in {'mekanism', 'ae2', 'actuallyadditions'}, 'Missing magic/technology integration'
        assert spec['magic_input'] != spec['tech_input']
        for item in current_cost:
            assert item in registry['items'] and item in rules['itemGates'] and rules['itemGates'][item] <= epoch, ('Future/unknown Nitro input', item)
            assert item not in TARGETS and not item.startswith('kubejs:'), 'Nitro bootstrap/key dependency'
        source_ids = set(spec['remove_recipe_ids'])
        assert len(source_ids) == len(spec['remove_recipe_ids']) and source_ids == set(scan['targets'][target]), 'Incomplete Nitro source removal'
        native = {source['recipe_id']: json.loads(frozen(root, source)) for source in spec['sources']}
        assert set(native) == source_ids and len(native) == len(spec['sources']), 'Missing native Nitro recipe evidence'
        for rid, original in native.items():
            assert rid == 'powah:crafting/' + target.split(':', 1)[1]
            assert original['type'] == 'minecraft:crafting_shaped' and result(original) == target
            native_cost = cost(original)
            assert sum(native_cost.values()) == 9, 'Unreviewed native Nitro material budget'
            expected = native_cost + Counter([spec['magic_input'], spec['tech_input']])
            assert current_cost == expected, 'Native Nitro material cost changed or unjustified grind added'
            assert any(item.startswith('powah:') and item.endswith('_spirited') for item in native_cost), 'Previous-tier generator missing'
        assert not source_ids & set(baseline), 'Published recipe deletion attempted'
        removed.update(source_ids)
        if compiled:
            expected = {key: copy.deepcopy(spec[key]) for key in ('id', 'epoch', 'target', 'category', 'json')}
            assert actual.get(ident) == expected, 'Compiled Nitro row differs'
            assert rules['recipeGates'].get(ident) == epoch, 'Compiled Nitro recipe gate differs'
    if compiled:
        assert removed <= set(bundle['remove']), 'Cheap native Nitro route remains'
    return {'status': 'passed', 'recipes': 3, 'serializers': {'create:mechanical_crafting': 3},
            'native_producers_replaced': len(removed), 'native_material_units_per_recipe': 9,
            'added_cross_mod_units_per_recipe': 2, 'published_custom_recipes_preserved': 615,
            'full_export_recipes_scanned': 42064, 'full_export_verified_this_run': export_recipes is not None,
            'storage_conversion_routes_found': 0, 'quest_craft_true_conflicts': 0,
            'full_pack_execution': False, 'generator_fe_performance_tested': False}


def apply(root=ROOT):
    root = Path(root); catalog = read(root/CATALOG)
    bundle, rules = read(root/'kubejs/config/aia2_recipes.json'), read(root/'kubejs/config/aia2_runtime.json')
    validate(root, catalog, bundle, rules)
    owned = {row['id'] for row in catalog['recipes']}
    bundle['add'] = [row for row in bundle['add'] if row['id'] not in owned] + [
        {key: copy.deepcopy(row[key]) for key in ('id', 'epoch', 'target', 'category', 'json')} for row in catalog['recipes']]
    removed = sorted({rid for row in catalog['recipes'] for rid in row['remove_recipe_ids']})
    bundle['remove'] = sorted(set(bundle['remove']) | set(removed))
    bundle['aia2_v5_powah_generator_source_removals'] = removed
    for row in sorted(catalog['recipes'], key=lambda row: row['id']): rules['recipeGates'][row['id']] = row['epoch']
    report = validate(root, catalog, bundle, rules, compiled=True)
    write(root/'kubejs/config/aia2_recipes.json', bundle); write(root/'kubejs/config/aia2_runtime.json', rules); write(root/REPORT, report)
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['apply', 'validate'])
    parser.add_argument('--root', type=Path, default=ROOT)
    parser.add_argument('--compiled', action='store_true')
    parser.add_argument('--export-recipes', type=Path)
    args = parser.parse_args()
    report = apply(args.root) if args.command == 'apply' else validate(args.root, read(args.root/CATALOG),
        read(args.root/'kubejs/config/aia2_recipes.json'), read(args.root/'kubejs/config/aia2_runtime.json'),
        compiled=args.compiled, export_recipes=args.export_recipes)
    print(json.dumps(report, ensure_ascii=False, indent=2))
