"""One explicitly reviewed additive CCA process; preserves fifteen published rules.

This validates the recipe/data protocol. It does not prove optional-mod dispatch.
"""
import copy
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PENDING = 'content/research/create_addons_pending_v12.json'
MECHANICS = 'kubejs/config/aia2_mechanics.json'
QUESTS = 'content/quests/v12_create_addons_course.json'
RULE_ID = 'cca_electrum_mixing'
RECIPE_ID = 'createaddition:mixing/electrum'
RECIPE_PATH = 'content/research/evidence/create_addons_core_v12/cca/recipes/createaddition/mixing/electrum.json'
RECIPE_SHA = 'cc53b40416e04bcc272825e463a8f6dabda639b18cab6197468578ca6d1569ef'
BASELINE_HASHES = {
    "andesite_mixing": "7effe537ef431df1847b9cf6e3680696a8377a0f96dffe254d64600c4fa0f722",
    "brass_mixing": "1f795a8ccb12c24c3e66de8e1a29519b49bb68630736f9e972534640940eb9fe",
    "infused_alloy": "b24cfdcdc1a0366a4d0dc3eefe1945e13f1fdb9ef9dc89f85e951f24fca51b64",
    "reinforced_alloy": "453d9ef71d83d8c5b8492bb4e39e4f56cfcab8ce0259d8970b8700f4641c91cc",
    "roots_living_pickaxe": "844383f55c605f7048d5ddb5f9168f5267da12fb33361b0f8dca51cfa7e59d31",
    "roots_charged_focus": "aaa649884db5a3fa2861ec798dce3f7559f5122dc338457bdcced5f8ae8f0ad9",
    "enderio_energetic_alloy": "9ae1bfa4bb5e656ed5aa3f7571a200a28f1ae5a8b520c36ee5ace0224af53e84",
    "powah_blazing_crystal": "5bcd347e05dc1e6d89d7c0a7723ed09a7eef09fdc448b86f346f9bbc502c30f8",
    "clibano_arcane_dust": "3ddb68f6662bcddb1f453b73f87ad3273f3e13295f1949ed06032bb7a6a4c683",
    "clibano_rune": "fe9d1c6310bd562ad24188467c82b50644599e194b0b280ca004c63ec794f54c",
    "clibano_obsidiansteel": "68102dfc566df1578c1997938002d8562dcc5a15c651ec1447fe4a54d63992f6",
    "nasa_tier_1_rocket": "95a8a5e58dd6dbea3808bf1fc2c6afa8307c0f6c0c363522647448475fd99def",
    "nasa_tier_2_rocket": "6a4b5d9e376dbbb48d5e4352eed2cb60ce620ef9f8e1635ef609882935b2857d",
    "nasa_tier_3_rocket": "f54bfb3c519cfe4dcd98addff22f8c95726f23b73b0d88ef29a1e3be79b3fa13",
    "nasa_tier_4_rocket": "7604bf910f1c31058944f592e13733881eeb1e5e685cbec171e70de2ef65b056"
}
ADVANCEMENT = {'criteria': {'native_process': {'trigger': 'minecraft:impossible'}}}
PROCESS_MAP = 'content/research/processes_v5.json'
PUBLISHED_CONFIG_SHA = 'ea394f6e5cb38050dbc36a71ab1ee3b7fcd0ee0b978bc8e7d827ef6b8d8b6a69'


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def write(path, data):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def canonical(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
                                     separators=(',', ':')).encode()).hexdigest()


def process_references(root, target_sha, compiled=False):
    """Refresh six whole-file references after preserving each published rule.

    This never changes a stage/action identity or accepts an arbitrary stale
    source: only the published15-rule SHA or this exact16-rule composition.
    """
    path = Path(root)/PROCESS_MAP
    if not path.is_file(): return None, 0
    document = read(path); changed = 0
    def visit(value):
        nonlocal changed
        if isinstance(value, dict):
            if value.get('path') == MECHANICS:
                allowed = {target_sha} if compiled else {PUBLISHED_CONFIG_SHA, target_sha}
                assert value.get('sha256') in allowed, 'Unreviewed process-map source contract SHA'
                value['sha256'] = target_sha; changed += 1
            for child in value.values(): visit(child)
        elif isinstance(value, list):
            for child in value: visit(child)
    visit(document)
    assert changed == 6, 'Expected six existing process-map references'
    return document, changed


def planned_config(root):
    document = read(Path(root)/MECHANICS); by_id = {row['id']: row for row in document['rules']}
    document['rules'] = [by_id[ident] for ident in BASELINE_HASHES] + [extension_rule(root)]
    digest = hashlib.sha256((json.dumps(document, ensure_ascii=False, indent=2)+'\n').encode()).hexdigest()
    return document, digest


def extension_rule(root=ROOT):
    root = Path(root); pending = read(root/PENDING)
    assert pending.get('schema') == 1 and pending.get('baseline') == '0ca0c5b028da51753057e5a7e4ff079a46a43ae3', 'Unreviewed Create extension baseline'
    assert pending.get('published_mechanic_hashes') == BASELINE_HASHES, 'Published fifteen mechanic hashes changed'
    assert pending.get('new_recipes') == 0 and pending.get('native_create_dispatch_tested') is False, 'Extension cannot invent recipes or certify dispatch'
    assert pending.get('scope') == 'one_explicit_additive_create_mixing_contract_preserving_fifteen_published_rules', 'Unreviewed Create extension scope'
    assert pending.get('proof_scope') == 'current_owned_basin_successful_native_apply_not_simulation', 'Changed Basin proof scope'
    assert pending.get('quest_id') == 'V12_E15_cca_electrum_native' and pending.get('advancement_json') == ADVANCEMENT, 'Wrong native quest/advancement contract'
    raw = (root/RECIPE_PATH).read_bytes()
    assert hashlib.sha256(raw).hexdigest() == RECIPE_SHA, 'Frozen exact electrum recipe changed'
    recipe = json.loads(raw)
    expected = {'id': RULE_ID, 'epoch': 15, 'output': 'immersiveengineering:ingot_electrum',
                'serializer': 'create:mixing', 'recipeIds': [RECIPE_ID],
                'advancement': 'aia2:mechanics/'+RULE_ID,
                'evidence': [{'source_kind': 'installed_export_recipe', 'recipeId': RECIPE_ID,
                              'export_path': 'recipes/createaddition/mixing/electrum.json',
                              'frozen_path': RECIPE_PATH, 'source_sha256': RECIPE_SHA,
                              'canonical_sha256': canonical(recipe), 'json': recipe}]}
    assert pending.get('extension_rule') == expected, 'Unreviewed electrum rule identity/evidence'
    assert recipe.get('type') == 'create:mixing' and recipe.get('heat_requirement') == 'heated', 'Wrong electrum serializer/heat'
    assert recipe.get('ingredients') == [{'tag': 'c:ingots/gold'}, {'tag': 'c:ingots/silver'}], 'Wrong electrum inputs'
    assert recipe.get('results') == [{'count': 2, 'id': 'immersiveengineering:ingot_electrum'}], 'Wrong unified electrum output'
    return copy.deepcopy(expected)


def validate_mechanic_rules(root=ROOT, allow_legacy=True):
    """Used before NASA regeneration too; extension permission is never arbitrary."""
    root = Path(root); own = extension_rule(root)
    document = read(root/MECHANICS)
    assert document.get('schema') == 1 and isinstance(document.get('rules'), list), 'Unsupported mechanics schema'
    rows = document['rules']; by_id = {row['id']: row for row in rows}
    assert len(rows) == len(by_id), 'Duplicate mechanic rule ID'
    base_ids = set(BASELINE_HASHES); actual = set(by_id)
    # The eleven-rule state exists only inside the independently tested NASA upgrade fixture.
    base_eleven = list(BASELINE_HASHES)[:11]
    allowed = [base_ids, base_ids | {RULE_ID}]
    if allow_legacy: allowed.append(set(base_eleven))
    assert actual in allowed, 'Unreviewed explicit mechanic extension set'
    for ident in actual & base_ids:
        assert canonical(by_id[ident]) == BASELINE_HASHES[ident], 'Published mechanic rule changed'
    assert [row['id'] for row in rows if row['id'] in base_ids] == [ident for ident in BASELINE_HASHES if ident in actual], 'Published mechanic rule order changed'
    if RULE_ID in by_id: assert by_id[RULE_ID] == own, 'Generated electrum rule changed'
    if not allow_legacy: assert actual == base_ids | {RULE_ID}, 'Electrum extension not generated'
    return own


def validate(root=ROOT, compiled=False):
    root = Path(root); own = validate_mechanic_rules(root, allow_legacy=not compiled)
    assert set(BASELINE_HASHES) <= {row['id'] for row in read(root/MECHANICS)['rules']}, 'NASA upgrade must generate all fifteen published rules before Create extension'
    pending = read(root/PENDING); runtime = read(root/'kubejs/config/aia2_runtime.json')
    for category, values in pending['producer_requirements'].items():
        assert category in {'itemGates', 'blockGates', 'recipeGates'}, 'Unknown producer gate category'
        for ident, floor in values.items():
            assert runtime[category].get(ident) == floor and floor <= own['epoch'], 'Future or changed chosen electrum producer route'
    assert pending['producer_requirements'] == {
        'itemGates': {'create:blaze_burner': 15, 'create:mechanical_mixer': 4, 'create:basin': 4, 'immersiveengineering:ingot_silver': 8, 'minecraft:gold_ingot': 0},
        'blockGates': {'create:blaze_burner': 15, 'create:mechanical_mixer': 4, 'create:basin': 4},
        'recipeGates': {RECIPE_ID: 8}}, 'Unreviewed chosen producer route'
    catalog = read(root/QUESTS)['quests']; matches = [q for q in catalog if q['id'] == pending['quest_id']]
    assert len(matches) == 1, 'Missing unique electrum manufacturing quest'
    quest = matches[0]
    assert quest['epoch'] == 15 and quest.get('required') is False and quest['mod'] == 'createaddition', 'Wrong electrum course epoch/branch'
    assert any(t == {'type': 'advancement', 'advancement': own['advancement']} for t in quest['tasks']), 'Native manufacturing cannot be replaced by inventory'
    assert any(t['type'] == 'item' and t['item'] == own['output'] and t.get('count') == 2 and not t.get('consume') and not t.get('craft') for t in quest['tasks']), 'Separate electrum output presence required'
    if compiled:
        assert read(root/f"kubejs/data/aia2/advancement/mechanics/{RULE_ID}.json") == ADVANCEMENT, 'Native proof requires only impossible trigger'
        assert [row['id'] for row in read(root/MECHANICS)['rules']] == [*BASELINE_HASHES, RULE_ID], 'Final sixteen rule order changed'
    _, desired_sha = planned_config(root)
    _, references = process_references(root, desired_sha, compiled=compiled)
    return {'status': 'passed', 'new_native_rules': 1, 'published_rules_preserved': 15,
            'mechanic_rules': 16, 'native_goal_epoch': 15, 'new_recipes': 0,
            'preserved_process_map_references_refreshed': references,
            'native_create_dispatch_tested': False,
            'heat_scope': 'Chosen Create Burner15; CDG12 alternate heat documented, not excluded'}


def apply(root=ROOT):
    root = Path(root); report = validate(root)
    document, digest = planned_config(root)
    processes, _ = process_references(root, digest)
    write(root/MECHANICS, document)
    write(root/f'kubejs/data/aia2/advancement/mechanics/{RULE_ID}.json', ADVANCEMENT)
    if processes is not None: write(root/PROCESS_MAP, processes)
    validate(root, compiled=True)
    return report


if __name__ == '__main__':
    print(json.dumps(apply(), ensure_ascii=False, indent=2))
