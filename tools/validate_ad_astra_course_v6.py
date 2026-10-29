"""Ad Astra course invariants backed by frozen installed recipes.

Inventory and looking at a block are not production proofs. Native advancement
tasks, when present, are validated separately by validate_native_advancements_v5.
This validator does not certify the optional mod's event dispatch in Minecraft.
"""
import copy
import hashlib
import json
from collections import Counter
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
COURSE = 'content/quests/v5_ad_astra_depth.json'
FINDINGS = 'content/audit/v6-ad-astra-content-findings.json'
CONTENT_SOURCES = 'content/research/evidence/ad_astra_content_v6/manifest.json'


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def frozen(root, record):
    relative = Path(record['path'])
    assert not relative.is_absolute() and '..' not in relative.parts, 'Nonportable course source'
    path = (root / relative).resolve()
    assert path.is_relative_to(root.resolve()) and path.is_file(), 'Missing course source'
    raw = path.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == record['sha256'], 'Changed course source'
    data = json.loads(raw)
    assert data['type'] == record['type'], 'Changed source recipe serializer'
    return data


def recipe_output(recipe):
    result = recipe.get('result', {})
    return result.get('id') if isinstance(result, dict) else result


def validate(root=ROOT, course=None, rules=None):
    root = Path(root)
    course = copy.deepcopy(course if course is not None else read(root / COURSE))
    rules = rules if rules is not None else read(root / 'kubejs/config/aia2_runtime.json')
    findings = read(root / FINDINGS)
    assert findings['installed_version'] == '1.16.26', 'Unreviewed course version'
    sources = findings['sources'] + read(root / CONTENT_SOURCES)['sources']
    recipes = {row['recipe_id']: frozen(root, row) for row in sources}
    native_craftable = {recipe_output(recipe) for recipe in recipes.values()
                        if recipe['type'] in {'minecraft:crafting_shaped', 'minecraft:crafting_shapeless'}}
    for slot in ('helmet', 'suit', 'pants', 'boots'):
        ident = 'ad_astra:netherite_space_' + slot
        recipe = recipes[ident]
        assert recipe['type'] == 'minecraft:crafting_shaped' and recipe_output(recipe) == ident, 'Space suit is not reviewed player crafting'
    # Recipes justify the order: an initial loader can use Earth inputs;
    # water automation needs Moon metal; the sensor needs Mars metal.
    for name in ('water_pump', 'oxygen_distributor'):
        assert {'tag': 'ad_astra:desh_plates'} in recipes['ad_astra:' + name]['key'].values(), 'Changed Moon oxygen dependency'
    assert {'tag': 'ad_astra:ostrum_plates'} in recipes['ad_astra:oxygen_sensor']['key'].values(), 'Changed Mars sensor dependency'
    assert {'tag': 'ad_astra:desh_plates'} not in recipes['ad_astra:oxygen_loader']['key'].values(), 'Initial loader unexpectedly requires Moon metal'
    for suffix, amount, duration in [('blocks', 9, 800), ('ingots', 1, 100)]:
        recipe = recipes['ad_astra:compressing/desh_plate_from_compressing_desh_' + suffix]
        assert recipe['result'] == {'count': amount, 'id': 'ad_astra:desh_plate'} and recipe['cookingtime'] == duration, 'Changed Desh batch semantics'
    for tier, metal in enumerate(('steel', 'desh', 'ostrum', 'calorite'), 1):
        recipe = recipes[f'ad_astra:nasa_workbench/tier_{tier}_rocket_from_nasa_workbench']
        ingredients = Counter(json.dumps(value, sort_keys=True) for value in recipe['ingredients'])
        expected = Counter({json.dumps({'tag': f'ad_astra:{metal}_blocks'}, sort_keys=True): 6,
                            json.dumps({'item': f'ad_astra:{metal}_tank'}, sort_keys=True): 2,
                            json.dumps({'item': f'ad_astra:{metal}_engine'}, sort_keys=True): 1,
                            json.dumps({'item': 'ad_astra:rocket_fin'}, sort_keys=True): 4,
                            json.dumps({'item': 'ad_astra:rocket_nose_cone'}, sort_keys=True): 1})
        assert ingredients == expected and recipe_output(recipe) == f'ad_astra:tier_{tier}_rocket', 'Changed NASA rocket bill'
    quests = course['quests']
    assert len(quests) == 20, 'Reviewed course contains twenty goals'
    local = {quest['id']: quest for quest in quests}
    assert len(local) == len(quests), 'Duplicate course quest ID'
    assert len({quest['title_uk'] for quest in quests}) == len(quests), 'Duplicate course title'
    all_authored = {}
    for path in sorted((root / 'content/quests').glob('*.json')):
        data = read(path)
        for quest in data if isinstance(data, list) else data.get('quests', []):
            all_authored[quest['id']] = quest
    all_authored.update(local)
    assert local['V5_E37_ad_astra_core_ground_workshop']['after'] == [], 'Ground workshop must precede rocket-gated legacy M1'
    for quest in quests:
        assert quest['epoch'] in (37, 38) and quest['mod'] == 'ad_astra' and not quest['required'], 'Unreviewed mandatory or epoch scope'
        assert quest['tasks'] and len(quest['description_uk']) >= 2, 'Empty course goal'
        assert re.search('[А-Яа-яІіЇїЄєҐґ]', quest['title_uk']), 'Missing Ukrainian title'
        for parent in quest['after']:
            if parent in all_authored:
                parent_epoch = all_authored[parent]['epoch']
            else:
                match = re.fullmatch(r'E(\d{2})_(?:M[1-6]|KEY)', parent)
                assert match, ('Missing course dependency', parent)
                parent_epoch = int(match.group(1))
            assert parent_epoch <= quest['epoch'], 'Course depends on a future epoch'
        for task in quest['tasks']:
            kind = task['type']
            if kind == 'item':
                ident = task['item']
                assert ident in rules['itemGates'] and rules['itemGates'][ident] <= quest['epoch'], 'Future or missing course item'
                if task.get('craft'):
                    assert ident in native_craftable, ('Machine output cannot use player-crafting task', ident)
            elif kind == 'observation':
                ident = task['block']
                assert ident in rules['blockGates'] and rules['blockGates'][ident] <= quest['epoch'], 'Future or missing observation block'
                assert task['ticks'] >= 20, 'Unreviewed zero-duration observation'
            elif kind == 'dimension':
                ident = task['dimension']
                assert ident in rules['dimensionGates'] and rules['dimensionGates'][ident] <= quest['epoch'], 'Future or missing route dimension'
            else:
                assert kind == 'advancement', 'Unsupported course task'
        for reward in quest.get('reward', []):
            assert reward['item'] in rules['itemGates'] and rules['itemGates'][reward['item']] <= quest['epoch'], 'Future or missing course reward'
            assert reward['count'] > 0, 'Empty reward'
    visiting, visited = set(), set()
    def visit(ident):
        assert ident not in visiting, 'Course dependency cycle'
        if ident in visited or ident not in all_authored:
            return
        visiting.add(ident)
        for parent in all_authored[ident].get('after', []):
            visit(parent)
        visiting.remove(ident)
        visited.add(ident)
    for ident in local:
        visit(ident)
    # These are source-motivated relative-order contracts, not visual positions.
    def ancestor(start, expected):
        pending, seen = [start], set()
        while pending:
            ident = pending.pop()
            if ident == expected:
                return True
            if ident in seen:
                continue
            seen.add(ident)
            pending.extend(all_authored.get(ident, {}).get('after', []))
        return False
    stem = 'V5_E37_ad_astra_core_'
    assert ancestor(stem + 'rocket_t1', stem + 'oxygen_bootstrap'), 'First flight lacks oxygen preparation'
    assert ancestor(stem + 'moon_water', stem + 'desh_batch'), 'Moon water automation precedes Desh'
    assert ancestor(stem + 'mars_sensor', stem + 'rocket_t2'), 'Ostrum sensor precedes Mars transport'
    cryo = local['V5_E38_ad_astra_core_cryo_bootstrap']
    assert not ancestor(cryo['id'], 'V5_E38_ad_astra_core_glacio_fuel'), 'Pre-Glacio cryogenic bootstrap cycle'
    assert any(task.get('item') == 'minecraft:blue_ice' for task in cryo['tasks']), 'Missing Earth cryogenic bootstrap input'
    assert not any(task.get('item') == 'ad_astra:ice_shard' for task in cryo['tasks']), 'First Glacio flight requires Glacio-only sample'
    return {'quests': len(quests), 'epochs': sorted({quest['epoch'] for quest in quests}),
            'frozen_recipe_sources': len(sources), 'tasks': dict(Counter(task['type'] for quest in quests for task in quest['tasks'])),
            'craft_tasks': sum(bool(task.get('craft')) for quest in quests for task in quest['tasks']),
            'quest_graph_nodes_reviewed': len(visited), 'cycle_errors': 0,
            'native_dispatch_fullpack_test': 'NOT_RUN'}


if __name__ == '__main__':
    print(json.dumps(validate(), ensure_ascii=False, indent=2))
