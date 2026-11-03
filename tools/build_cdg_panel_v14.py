"""One reviewed CDG completion proof, additive to sixteen immutable rules.

Validates the recipe/data contract, not original optional-mod Mixin dispatch.
"""
import copy
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PENDING = 'content/research/cdg_panel_pending_v14.json'
MECHANICS = 'kubejs/config/aia2_mechanics.json'
PROCESS_MAP = 'content/research/processes_v5.json'
QUESTS = 'content/quests/v14_cdg_panel_native.json'
QUEST_ID = 'V14_E12_cdg_panel_native'
RULE_ID = 'cdg_panel_compression'
RECIPE_ID = 'createdieselgenerators:compression_molding/sheet_metal_panel'
RECIPE_PATH = 'content/research/evidence/cdg_molds_v13/recipes/createdieselgenerators/compression_molding/sheet_metal_panel.json'
RECIPE_SHA = '9841618670e0a89bea6788df3d213a8acb60849c3c5430b91b89ffa78a138d3b'
PUBLISHED_CONFIG_SHA = 'd545e76ff996ee728b6401f8e457472f633ddb4ede679b959bca2e3f92994317'
ADVANCEMENT = {'criteria': {'native_process': {'trigger': 'minecraft:impossible'}}}
BASELINE_HASHES = {'andesite_mixing': '7effe537ef431df1847b9cf6e3680696a8377a0f96dffe254d64600c4fa0f722', 'brass_mixing': '1f795a8ccb12c24c3e66de8e1a29519b49bb68630736f9e972534640940eb9fe', 'infused_alloy': 'b24cfdcdc1a0366a4d0dc3eefe1945e13f1fdb9ef9dc89f85e951f24fca51b64', 'reinforced_alloy': '453d9ef71d83d8c5b8492bb4e39e4f56cfcab8ce0259d8970b8700f4641c91cc', 'roots_living_pickaxe': '844383f55c605f7048d5ddb5f9168f5267da12fb33361b0f8dca51cfa7e59d31', 'roots_charged_focus': 'aaa649884db5a3fa2861ec798dce3f7559f5122dc338457bdcced5f8ae8f0ad9', 'enderio_energetic_alloy': '9ae1bfa4bb5e656ed5aa3f7571a200a28f1ae5a8b520c36ee5ace0224af53e84', 'powah_blazing_crystal': '5bcd347e05dc1e6d89d7c0a7723ed09a7eef09fdc448b86f346f9bbc502c30f8', 'clibano_arcane_dust': '3ddb68f6662bcddb1f453b73f87ad3273f3e13295f1949ed06032bb7a6a4c683', 'clibano_rune': 'fe9d1c6310bd562ad24188467c82b50644599e194b0b280ca004c63ec794f54c', 'clibano_obsidiansteel': '68102dfc566df1578c1997938002d8562dcc5a15c651ec1447fe4a54d63992f6', 'nasa_tier_1_rocket': '95a8a5e58dd6dbea3808bf1fc2c6afa8307c0f6c0c363522647448475fd99def', 'nasa_tier_2_rocket': '6a4b5d9e376dbbb48d5e4352eed2cb60ce620ef9f8e1635ef609882935b2857d', 'nasa_tier_3_rocket': 'f54bfb3c519cfe4dcd98addff22f8c95726f23b73b0d88ef29a1e3be79b3fa13', 'nasa_tier_4_rocket': '7604bf910f1c31058944f592e13733881eeb1e5e685cbec171e70de2ef65b056', 'cca_electrum_mixing': '47e1cb3781a651d5af23d93c504dd2626751cfea62bd98c2f340b4b99af582ef'}
BASELINE_METADATA = {'schema': 1, 'proof_semantics': 'Successful native post-input-consumption completion, current machine owner FTB team; possession/crafting GUI/simulation do not count.'}
PRODUCERS = {
    'itemGates': {'create:basin': 4, 'create:mechanical_press': 4, 'create:mechanical_saw': 4,
                  'createdieselgenerators:mold': 12, 'createdieselgenerators:sheet_metal_panel': 12,
                  'immersiveengineering:plate_iron': 8},
    'blockGates': {'create:basin': 4, 'create:mechanical_press': 4, 'create:mechanical_saw': 4},
    'recipeGates': {RECIPE_ID: 12, 'createdieselgenerators:cutting/lines_mold': 12},
}
PROOF_SCOPE = 'current_owned_basin_successful_native_apply_not_simulation'


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def write(path, value):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def canonical(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
                                     separators=(',', ':')).encode()).hexdigest()


def uid(value):
    return hashlib.sha256(('aia2-runtime-v1:'+value).encode()).hexdigest()[:12].upper().rjust(16, '0')


def extension_rule(root=ROOT):
    """Independent identity validation; safe for earlier generators to call."""
    root = Path(root); pending = read(root/PENDING)
    assert pending.get('schema') == 1 and pending.get('baseline') == '9067fdf71fe1da045e5e1038afe8de140a01b1c9', 'Unreviewed panel baseline'
    assert pending.get('scope') == 'one_explicit_additive_cdg_compression_contract_preserving_sixteen_published_rules', 'Unreviewed panel scope'
    assert pending.get('published_mechanic_hashes') == BASELINE_HASHES, 'Published sixteen mechanic hashes changed'
    assert pending.get('published_config_sha256') == PUBLISHED_CONFIG_SHA and pending.get('published_metadata') == BASELINE_METADATA, 'Published mechanics metadata changed'
    assert pending.get('proof_scope') == PROOF_SCOPE and pending.get('quest_id') == QUEST_ID, 'Changed panel proof scope/quest'
    assert pending.get('new_recipes') == 0 and pending.get('native_create_dispatch_tested') is False, 'Panel extension cannot invent recipes or certify dispatch'
    assert pending.get('advancement_json') == ADVANCEMENT and pending.get('producer_requirements') == PRODUCERS, 'Unreviewed panel advancement/producer route'
    raw = (root/RECIPE_PATH).read_bytes()
    assert hashlib.sha256(raw).hexdigest() == RECIPE_SHA, 'Frozen panel recipe changed'
    recipe = json.loads(raw)
    assert recipe == {'type': 'createdieselgenerators:compression_molding',
                      'ingredients': [{'tag': 'c:plates/iron'}], 'mold': 'createdieselgenerators:lines',
                      'results': [{'id': 'createdieselgenerators:sheet_metal_panel', 'count': 4}]}, 'Wrong native panel recipe/profile/output'
    expected = {'id': RULE_ID, 'epoch': 12, 'output': 'createdieselgenerators:sheet_metal_panel',
                'serializer': 'createdieselgenerators:compression_molding', 'recipeIds': [RECIPE_ID],
                'advancement': 'aia2:mechanics/'+RULE_ID,
                'evidence': [{'source_kind': 'installed_export_recipe', 'recipeId': RECIPE_ID,
                              'export_path': 'recipes/createdieselgenerators/compression_molding/sheet_metal_panel.json',
                              'frozen_path': RECIPE_PATH, 'source_sha256': RECIPE_SHA,
                              'canonical_sha256': canonical(recipe), 'json': recipe}]}
    assert pending.get('extension_rule') == expected, 'Unreviewed panel rule identity/evidence'
    return copy.deepcopy(expected)


def validate_mechanic_rules(root=ROOT, compiled=False):
    root = Path(root); own = extension_rule(root)
    document = read(root/MECHANICS)
    assert {k: v for k, v in document.items() if k != 'rules'} == BASELINE_METADATA, 'Published mechanics header changed'
    rows = document['rules']; by_id = {row['id']: row for row in rows}
    assert len(rows) == len(by_id), 'Duplicate mechanic rule ID'
    actual = set(by_id); baseline = set(BASELINE_HASHES)
    allowed = [baseline | {RULE_ID}] if compiled else [baseline, baseline | {RULE_ID}]
    assert actual in allowed, 'Unreviewed explicit panel extension set'
    for ident, digest in BASELINE_HASHES.items():
        assert canonical(by_id[ident]) == digest, 'Published mechanic rule changed'
    assert [row['id'] for row in rows if row['id'] in baseline] == list(BASELINE_HASHES), 'Published sixteen mechanic order changed'
    if RULE_ID in by_id: assert by_id[RULE_ID] == own, 'Generated panel rule changed'
    if compiled: assert [row['id'] for row in rows] == [*BASELINE_HASHES, RULE_ID], 'Final seventeen mechanic order changed'
    return own


def planned_config(root=ROOT):
    root = Path(root); document = read(root/MECHANICS)
    by_id = {row['id']: row for row in document['rules']}
    document['rules'] = [by_id[ident] for ident in BASELINE_HASHES] + [extension_rule(root)]
    digest = hashlib.sha256((json.dumps(document, ensure_ascii=False, indent=2)+'\n').encode()).hexdigest()
    return document, digest


def process_references(root, target_sha, compiled=False):
    root = Path(root); path = root/PROCESS_MAP
    if not path.is_file(): return None, 0
    document = read(path); changed = 0
    def visit(value):
        nonlocal changed
        if isinstance(value, dict):
            if value.get('path') == MECHANICS:
                allowed = {target_sha} if compiled else {PUBLISHED_CONFIG_SHA, target_sha}
                assert value.get('sha256') in allowed, 'Unreviewed panel process-map source contract SHA'
                value['sha256'] = target_sha; changed += 1
            for child in value.values(): visit(child)
        elif isinstance(value, list):
            for child in value: visit(child)
    visit(document)
    assert changed == 6, 'Expected six existing process-map references'
    return document, changed


def validate(root=ROOT, compiled=False):
    root = Path(root); own = validate_mechanic_rules(root, compiled=compiled)
    runtime = read(root/'kubejs/config/aia2_runtime.json')
    for category, entries in PRODUCERS.items():
        for ident, epoch in entries.items():
            assert runtime[category].get(ident) == epoch and epoch <= own['epoch'], 'Future or changed panel producer route'
    assert RECIPE_ID not in read(root/'kubejs/config/aia2_recipes.json')['remove'], 'Panel recipe was removed'
    catalog = read(root/QUESTS)
    assert catalog.get('schema') == 1 and len(catalog['quests']) == 1, 'Expected one additive panel objective'
    quest = catalog['quests'][0]
    assert quest.get('id') == QUEST_ID and quest.get('epoch') == 12 and quest.get('required') is False and quest.get('mod') == 'createdieselgenerators', 'Wrong panel quest identity/era'
    assert quest.get('after') == ['V13_E12_cdg_mold_lines'] and quest.get('proof_scope') == PROOF_SCOPE, 'Wrong panel quest prerequisite/scope'
    assert quest.get('tasks') == [
        {'type': 'advancement', 'advancement': own['advancement']},
        {'type': 'item', 'item': own['output'], 'count': 4, 'consume': False, 'craft': False},
    ], 'Panel manufacturing must require native proof and separate output presence'
    assert quest['tasks'][1].get('consume') is False and quest['tasks'][1].get('craft') is False, 'Panel output inventory flags must be Boolean false'
    if compiled:
        assert read(root/f'kubejs/data/aia2/advancement/mechanics/{RULE_ID}.json') == ADVANCEMENT, 'Panel proof requires only impossible trigger'
        candidates = [q for path in (root/'config/ftbquests/quests/chapters').glob('*.snbt')
                      for q in read(path)['quests'] if q['id'] == uid(QUEST_ID)]
        assert len(candidates) == 1, 'Panel objective not compiled exactly once'
        actual = candidates[0]
        assert actual.get('optional') is True and actual.get('hide_until_deps_complete') is True, 'Panel goal must stay optional and gated'
        assert uid('V13_E12_cdg_mold_lines') in actual.get('dependencies', []), 'Compiled panel dependency lost'
        tasks = actual['tasks']
        assert len(tasks) == 3 and tasks[0] == {'id': uid(QUEST_ID+':task:0'), 'type': 'advancement', 'advancement': own['advancement']}, 'Compiled panel native proof lost'
        assert tasks[1].get('type') == 'item' and tasks[1].get('item') == {'id': own['output'], 'count': 1} and tasks[1].get('count') == 4 and tasks[1].get('consume_items') is False and tasks[1].get('only_from_crafting') is False, 'Compiled panel output sample changed'
        assert tasks[1].get('id') == uid(QUEST_ID+':task:1') and tasks[2] == {'id': uid(QUEST_ID+':stage'), 'type': 'advancement', 'advancement': 'aia2:stages/e12'}, 'Compiled panel task/stage identity changed'
    _, target_sha = planned_config(root)
    _, references = process_references(root, target_sha, compiled=compiled)
    return {'status': 'passed', 'new_native_rules': 1, 'published_rules_preserved': 16,
            'mechanic_rules': 17, 'native_goal_epoch': 12, 'new_recipes': 0,
            'preserved_process_map_references_refreshed': references,
            'native_create_dispatch_tested': False}


def apply(root=ROOT):
    root = Path(root); report = validate(root)
    document, digest = planned_config(root)
    processes, _ = process_references(root, digest)
    # All source/contracts are validated before any generated output is written.
    write(root/MECHANICS, document)
    write(root/f'kubejs/data/aia2/advancement/mechanics/{RULE_ID}.json', ADVANCEMENT)
    if processes is not None: write(root/PROCESS_MAP, processes)
    # Compiled quest checks happen in the central post-generation validator.
    validate_mechanic_rules(root, compiled=True)
    return report


if __name__ == '__main__':
    print(json.dumps(apply(), ensure_ascii=False, indent=2))
