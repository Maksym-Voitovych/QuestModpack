"""Apply audited MI/Oritech controller floors without editing any recipe entry.

Native producer completeness was checked against the user's 42,064-recipe
export. Frozen relevant recipes make normal builds portable; scan_export can
independently reproduce the full-export check when that export is available.
"""
import hashlib
import json
from pathlib import Path

try:
    from audit_obtainability_v5 import outputs
except ModuleNotFoundError:
    from tools.audit_obtainability_v5 import outputs

ROOT = Path(__file__).resolve().parents[1]
CATALOG = 'content/audit/v5-industrial-controller-floors.json'
REPORT = 'implementation/industrial-controller-gates-v5-audit.json'
FLOORS = {
    'modern_industrialization:replicator': 99,
    'modern_industrialization:oil_drilling_rig': 22,
    'modern_industrialization:distillation_tower': 32,
    'modern_industrialization:heat_exchanger': 32,
    'modern_industrialization:large_diesel_generator': 35,
    'modern_industrialization:large_steam_turbine': 35,
    'modern_industrialization:nuclear_reactor': 35,
    'modern_industrialization:large_steam_boiler': 13,
    'modern_industrialization:large_tank': 13,
    'modern_industrialization:fusion_reactor': 44,
    'modern_industrialization:plasma_turbine': 44,
    'oritech:laser_arm_block': 32,
    'oritech:reactor_controller': 32,
    'oritech:reactor_energy_port': 32,
    'oritech:reactor_absorber_port': 32,
    'oritech:reactor_redstone_port': 32,
    'oritech:reactor_fuel_port': 32,
    'oritech:reactor_rod': 32,
    'oritech:reactor_double_rod': 32,
    'oritech:reactor_quad_rod': 32,
    'oritech:reactor_heat_pipe': 32,
    'oritech:reactor_vent': 32,
    'oritech:reactor_condenser': 32,
    'oritech:drone_port_block': 39,
    'oritech:accelerator_controller': 44,
    'oritech:accelerator_ring': 44,
    'oritech:accelerator_motor': 44,
    'oritech:accelerator_sensor': 44,
    'oritech:particle_collector_block': 44,
    'oritech:deep_drill_block': 44,
}
VERSIONS = {'modern_industrialization': '2.5.10', 'oritech': '1.2.13'}


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')


def canonical(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def frozen(root, source):
    root = Path(root).resolve()
    path = Path(source['path'])
    assert not path.is_absolute() and '..' not in path.parts, 'Nonportable controller source'
    target = (root/path).resolve()
    assert target.is_relative_to(root), 'Controller source escapes project'
    raw = target.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == source['sha256'], ('Stale controller source', str(path))
    return raw


def scan_export(export_recipes):
    """Reproduce the frozen inventory hash and every semantic target producer."""
    export_recipes = Path(export_recipes)
    manifest, producers = [], {item: [] for item in sorted(FLOORS)}
    for path in sorted(export_recipes.rglob('*.json')):
        raw = path.read_bytes()
        relative = path.relative_to(export_recipes)
        manifest.append([relative.as_posix(), hashlib.sha256(raw).hexdigest()])
        recipe = json.loads(raw)
        ident = relative.parts[0]+':'+relative.with_suffix('').as_posix().split('/', 1)[1]
        for target in set(outputs(recipe)) & FLOORS.keys():
            producers[target].append(ident)
    return {'recipes_scanned': len(manifest), 'manifest_sha256': canonical(manifest), 'targets': producers}


def quest_references(root, catalog):
    """Reject a floor that would strand any existing task, reward or icon."""
    references, goals = 0, {}
    for path in sorted((Path(root)/'content/quests').glob('*.json')):
        data = read(path)
        for quest in data if isinstance(data, list) else data.get('quests', []):
            goals[quest['id']] = quest
            limit = 99 if quest.get('post_completion') else quest['epoch']
            used = {quest.get('icon')}
            for entry in quest.get('tasks', []) + quest.get('reward', []):
                used.update((entry.get('item'), entry.get('block')))
                advancement = entry.get('advancement', '')
                if advancement in FLOORS:
                    used.add(advancement)
                if advancement.startswith('aia2:mi/'):
                    used.add('modern_industrialization:'+advancement.removeprefix('aia2:mi/'))
            for item in used & FLOORS.keys():
                references += 1
                assert FLOORS[item] <= limit, ('Earlier quest references gated controller', quest['id'], item)
    contract = catalog['quest_contract']
    goal = goals.get(contract['replicator_goal'])
    assert goal and goal['epoch'] == 48 and goal.get('post_completion') is True and not goal.get('required'), \
        'Replicator goal must remain optional after final completion'
    assert any(t.get('block') == 'modern_industrialization:replicator' for t in goal['tasks']), \
        'Replicator setup task missing'
    return references


def validate(root, rules, bundle=None, compiled=True):
    root = Path(root)
    data = read(root/CATALOG)
    if bundle is None:
        bundle = read(root/'kubejs/config/aia2_recipes.json')
    assert data['schema'] == 1 and data['installed_versions'] == VERSIONS, 'Controller version contract changed'
    assert data['item_block_floors'] == FLOORS, 'Unreviewed controller floor scope'
    for source in data['sources']:
        frozen(root, source)
    scan = json.loads(frozen(root, data['producer_scan']))
    assert scan['recipes_scanned'] == 42064 and set(scan['targets']) == set(FLOORS), 'Incomplete controller producer scan'
    assert len(scan['manifest_sha256']) == 64, 'Missing full-export inventory hash'
    derived, producers = {}, {item: [] for item in FLOORS}
    for source in scan['sources']:
        recipe = json.loads(frozen(root, source))
        hits = set(outputs(recipe)) & FLOORS.keys()
        assert hits and recipe['type'] == source['type'], 'Irrelevant controller producer source'
        ident = source['recipe_id']
        assert ident not in derived, 'Duplicate native controller producer'
        derived[ident] = max(FLOORS[item] for item in hits)
        for item in hits:
            producers[item].append(ident)
    assert all(producers.values()), 'Controller has no confirmed native producer'
    assert {item: sorted(ids) for item, ids in producers.items()} == scan['targets'], 'Native controller alternate missing'
    assert len(derived) == scan['native_producer_recipes'] == 41, 'Native controller producer scope changed'
    assert data['native_recipe_floors'] == derived, 'Native controller floor incomplete'

    core = json.loads(frozen(root, data['published_baseline_catalog']))
    baseline = core['baseline_recipe_hashes']
    actual = {entry['id']: entry for entry in bundle['add']}
    assert len(actual) == len(bundle['add']), 'Duplicate custom recipe ID'
    assert len(baseline) == 606, 'Published606 baseline required'
    for ident, digest in baseline.items():
        assert ident in actual and canonical(actual[ident]) == digest, ('Published industrial baseline changed', ident)
    custom = {}
    for entry in bundle['add']:
        hits = set(outputs(entry['json'])) & FLOORS.keys()
        if hits:
            custom[entry['id']] = max(entry['epoch'], *(FLOORS[item] for item in hits))
    for entry in core['recipes']:
        ident = entry['id']
        assert ident in actual and actual[ident] == {key: entry[key] for key in ('id', 'epoch', 'target', 'category', 'json')}, \
            ('New industrial custom recipe changed', ident)
        custom[ident] = max(custom.get(ident, 0), entry['epoch'])
    assert custom == data['custom_recipe_floors'] and len(custom) == 5, 'Custom controller floor incomplete'
    for section in ('itemGates', 'blockGates'):
        for item, floor in FLOORS.items():
            assert item in rules[section], ('Unregistered controller', section, item)
            if compiled:
                assert rules[section][item] >= floor, ('Controller floor not applied', section, item)
    for ident, floor in dict(derived, **custom).items():
        assert ident in rules['recipeGates'], ('Unregistered controller producer', ident)
        if compiled:
            assert rules['recipeGates'][ident] >= floor, ('Controller producer floor not applied', ident)
    references = quest_references(root, data)
    return {'status': 'passed', 'item_floors': len(FLOORS), 'block_floors': len(FLOORS),
            'native_recipe_floors': len(derived), 'custom_recipe_floors': len(custom),
            'published_custom_recipes_preserved': 606, 'new_custom_recipes_preserved': 4,
            'quest_references_checked': references, 'full_export_recipes_scanned': 42064,
            'replicator_post_completion_floor': 99, 'native_recipe_json_removed': 0,
            'full_pack_execution': False}


def apply(root=ROOT):
    root = Path(root)
    data = read(root/CATALOG)
    rules = read(root/'kubejs/config/aia2_runtime.json')
    bundle = read(root/'kubejs/config/aia2_recipes.json')
    validate(root, rules, bundle, compiled=False)
    for section in ('itemGates', 'blockGates'):
        for item, floor in sorted(FLOORS.items()):
            rules[section][item] = max(rules[section][item], floor)
    for ident, floor in sorted(dict(data['native_recipe_floors'], **data['custom_recipe_floors']).items()):
        rules['recipeGates'][ident] = max(rules['recipeGates'][ident], floor)
    report = validate(root, rules, bundle)
    write(root/'kubejs/config/aia2_runtime.json', rules)
    write(root/REPORT, report)
    return report


if __name__ == '__main__':
    print(json.dumps(apply(), ensure_ascii=False, indent=2))
