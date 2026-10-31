"""Six additive world-action goals for paid Ad Astra station construction.

This catalog never adopts old native station entries, mutates native recipes or
rewrites published task conditions. Runtime proof is owned by Java; these
impossible advancements are only the revocable projection of its team journal.
"""
import copy
import hashlib
import json
from pathlib import Path

try:
    from . import build_station_floors_v8 as floors
except ImportError:
    import build_station_floors_v8 as floors

ROOT = Path(__file__).resolve().parents[1]
QUESTS = 'content/quests/v5_station_construction.json'
CONFIG = 'kubejs/config/aia2_stations.json'
RUNTIME = 'kubejs/config/aia2_runtime.json'
RESEARCH = 'content/research/technology_v5.json'
PROOF_SCOPE = 'current_builder_team_exact_payment_accepted_structure_new_owner_registration_and_native_landing'
ADVANCEMENT = {'criteria': {'native_station': {'trigger': 'minecraft:impossible'}}}
SPECS = (
    ('earth', 37, 'desh_batch', 'desh', 'airlock'),
    ('moon', 37, 'desh_batch', 'desh', 'water_pump'),
    ('mars', 37, 'mars_sensor', 'ostrum', 'oxygen_sensor'),
    ('mercury', 38, 'calorite_metallurgy', 'calorite', 'calorite_plate'),
    ('venus', 38, 'calorite_metallurgy', 'calorite', 'calorite_ingot'),
    ('glacio', 38, 'glacio_fuel', 'calorite', 'cryo_freezer'),
)
# Frozen published0.4.19 stages: additions cannot silently rewrite their payloads.
BASELINE_STAGE_HASHES = {
    "ad_astra.phase.01": "2994a916c615f0566c13e1ff2136f170c830b0507bf8e0125f1df7b8fc5a9625",
    "ad_astra.phase.02": "e123659306a9c2cbd15ac5c06399507103e52decc8a6d6d06210f9fed59f8aa4",
    "ad_astra.phase.03": "2bf6baf06c6c177cdb0e2a8f06124234673fff4eb7f8fdd2157dd810e1be0fe9",
    "ad_astra.phase.04": "5b6ee7e454c123e48744b578a2a9a027f289c820e5f4e9fcd3981fbccd97847b",
    "ad_astra.phase.05": "a04f35edaa3f80252449cb714e56eb7f039eb15b5737991c964a6e3f9b66b4fb",
    "ad_astra.phase.06": "18f24e6c961d7e0de511c6fe82cca8360aa8a07df40708bbdf274393d005d456",
    "ad_astra.phase.07": "f0de23cadc96a3969e3e0636f9ce41b74f2d6885805a9a80cf6a66668eacf06d",
    "ad_astra.core.ground_workshop": "f2420d88332c892537f441fbea184ed1556cef3dee9a1cd85f7ec002b9986046",
    "ad_astra.core.steel_workshop": "c5a53cac71d3afa094b32c3d4005d90a625dd0d3276efba0bf46c2b6fb566c2d",
    "ad_astra.core.steel_engine": "892809f71bc0bf81afa4764019f9b2eaa7b129d2b50e2e315caa3a4ce161a33c",
    "ad_astra.core.fuel_bootstrap": "2e311f2063f4e289eabd14aa90fd72c42d2f63a2490222a837f0fb61c90cfcb5",
    "ad_astra.core.oxygen_bootstrap": "57d4e6b6adb386199a612209082dded7643521819ab5669c2679379439f9dac1",
    "ad_astra.core.flight_suit": "6e23730cbb5a67ab34fda7fdc44295953792af95b5c868d55c7eff223ad43db2",
    "ad_astra.core.rocket_t1": "c6cc85b7519155514e6ba051ff8a8ab8cd191928caa90e09f4c5d0be212391ba",
    "ad_astra.core.earth_orbit": "484363f5bff5f26251921fd24773572e33bec63b93afa22575ce63250d6c8be6",
    "ad_astra.core.desh_batch": "7e4167bdf0b3a73cedff32b0978c5e24cdb14e86b51dab117f195cbcdcf10f72",
    "ad_astra.core.moon_water": "8c716f98b21991dea6ca25df4db0c04b8f3cea65a4c846725cce9cee242ddfba",
    "ad_astra.core.rocket_t2": "389398410bb41a7cd88afa438486153e5b0c273cb83cdb852cd6a8b9022a22cb",
    "ad_astra.core.mars_sensor": "9ba77c1efd45bd5d91932e3a74f9a9af163f99f0446088df47649f0915eb4b25",
    "ad_astra.core.hostile_suit": "60135c9766642e73bc55321c90016e959028bedc551035435082dd07783a8093",
    "ad_astra.core.rocket_t3": "1abf8d74c3a874e375525aa65b1c546c2bdca7b2d13e9433e4f64c36abb91d17",
    "ad_astra.core.calorite_metallurgy": "119eca73161df23630e843c75799ae81ce18c44df1acd1227129fbf2e03ab3f6",
    "ad_astra.core.calorite_engine": "caab0ade3136b54787911641bc8e80a591c6422723f67adf3efaef0f8d2590c5",
    "ad_astra.core.cryo_bootstrap": "99af00a60993a3cc40fbe850ae5777ba28be4e6b62fd9c7ce4992717cb9b94a2",
    "ad_astra.core.rocket_t4": "ec49109c6f83bf1a8d40153b21d0d3f5aa62b936d8135dc8f47d2a0863fbdad3",
    "ad_astra.core.glacio_fuel": "ff374f9026730b9990dadf054715410d4b75807b06e690e1896f3d38d3217884",
    "ad_astra.core.orbital_atlas": "139e8fdc9cb8a7d99a84e1195471996fc1b7e1eddd83c46930ca1799cff55867",
    "ad_astra.manufacturing.rocket_t1": "d77945c70efa0f00e7860bdd4e3517703852e24622da5fc39386dedbbb4c09b1",
    "ad_astra.manufacturing.rocket_t2": "89f24026ebb2b923582e02c7a97f5393fbf3c7de6a0eda3dd4018ca8793983e6",
    "ad_astra.manufacturing.rocket_t3": "51c4a60cff976689359e1a72779f12d79cda43467d7af0eebe612e90a41b283f",
    "ad_astra.manufacturing.rocket_t4": "27d3284a80e1238a960e4b2b23b3f8a6fca5bedf23b4327bd52f9f66af0873a0"
}


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def canonical(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
                                     separators=(',', ':')).encode()).hexdigest()


def station_rules():
    return [{'id': f'station_{planet}_orbit', 'epoch': epoch,
             'dimension': f'ad_astra:{planet}_orbit',
             'recipeId': f'ad_astra:space_station/{planet}_orbit_space_station',
             'serializer': floors.SERIALIZER,
             'advancement': f'aia2:stations/{planet}_orbit'}
            for planet, epoch, _, _, _ in SPECS]


def validate(root=ROOT, catalog=None, runtime=None, research=None, compiled=False):
    """Check exact sources, fixed identities, prerequisites and era-safe rewards."""
    root = Path(root)
    catalog = copy.deepcopy(catalog if catalog is not None else read(root / QUESTS))
    runtime = runtime if runtime is not None else read(root / RUNTIME)
    research = research if research is not None else read(root / RESEARCH)
    assert catalog.get('schema') == 1, 'Unsupported station goal schema'
    quests = catalog.get('quests', [])
    by_id = {quest['id']: quest for quest in quests}
    expected = {f'V9_E{epoch}_station_{planet}_orbit' for planet, epoch, _, _, _ in SPECS}
    assert len(quests) == len(by_id) == 6 and set(by_id) == expected, 'Exactly six distinct station goals required'
    old_quests = {}
    for path in sorted((root / 'content/quests').glob('*.json')):
        if path.name == Path(QUESTS).name:
            continue
        data = read(path)
        for quest in data if isinstance(data, list) else data['quests']:
            assert quest['id'] not in old_quests, 'Duplicate published quest ID'
            old_quests[quest['id']] = quest
    assert not (expected & old_quests.keys()), 'Station quest ID collides with published quest'
    maps = [row for row in research['mods'] if row['mod_id'] == 'ad_astra']
    assert len(maps) == 1 and maps[0]['installed_version'] == '1.16.26', 'Unreviewed Ad Astra version'
    stages = maps[0]['stages']
    stage_by_id = {row['id']: row for row in stages}
    assert len(stages) == len(stage_by_id), 'Duplicate station research stage ID'
    for ident, digest in BASELINE_STAGE_HASHES.items():
        assert ident in stage_by_id and canonical(stage_by_id[ident]) == digest, 'Published Ad Astra stage changed'
    assert len(BASELINE_STAGE_HASHES) == 31, 'Published thirty-one stages required'
    source_root = 'content/research/evidence/station_guard_v8/sourcefreeze/installed_export/recipes/ad_astra/space_station/'
    for planet, epoch, parent, metal, icon in SPECS:
        qid = f'V9_E{epoch}_station_{planet}_orbit'
        stage_id = f'ad_astra.station.{planet}_orbit'
        advancement = f'aia2:stations/{planet}_orbit'
        dimension = f'ad_astra:{planet}_orbit'
        recipe_id = f'ad_astra:space_station/{planet}_orbit_space_station'
        relative = source_root + f'{planet}_orbit_space_station.json'
        path = root / relative
        assert path.is_file() and hashlib.sha256(path.read_bytes()).hexdigest() == floors.RECIPE_SHA256[recipe_id], 'Station exact recipe SHA mismatch'
        recipe = read(path)
        floors.recipe_inputs(recipe, dimension)
        assert runtime['recipeGates'].get(recipe_id, -1) >= epoch, 'Station recipe before orbit floor'
        assert runtime['dimensionGates'].get(dimension) == epoch, 'Wrong station orbit floor'
        quest = by_id[qid]
        assert type(quest.get('epoch')) is int and quest['epoch'] == epoch and quest.get('required') is False, 'Station goal must be optional at its native era'
        assert quest.get('mod') == 'ad_astra' and quest.get('category') == 'technology', 'Wrong station branch'
        assert quest.get('icon') == f'ad_astra:{icon}', 'Wrong station icon'
        assert quest.get('proof_scope') == PROOF_SCOPE, 'Changed station proof scope'
        assert quest.get('tasks') == [
            {'type': 'advancement', 'advancement': advancement},
            {'type': 'dimension', 'dimension': dimension}], 'Station goal needs native proof and separate orbit visit'
        parent_id = f'V5_E{epoch}_ad_astra_core_{parent}'
        assert quest.get('after') == [parent_id] and parent_id in old_quests, 'Wrong station preparation prerequisite'
        assert old_quests[parent_id]['epoch'] <= epoch, 'Future station prerequisite'
        assert quest.get('reward') == [{'item': 'ad_astra:desh_nugget' if epoch == 37 else 'ad_astra:cheese', 'count': 4}], 'Unreviewed station reward'
        assert type(quest['reward'][0]['count']) is int, 'Station reward count must be an integer'
        for item in (quest['icon'], quest['reward'][0]['item']):
            assert runtime['itemGates'].get(item, 100) <= epoch, 'Missing or future station icon/reward'
        assert quest.get('title_uk') and len(' '.join(quest.get('description_uk', []))) >= 600, 'Missing substantive station explanation'
        stage = stage_by_id.get(stage_id, {})
        assert stage.get('epoch') == epoch and stage.get('prerequisites') == [f'ad_astra.core.{parent}'], 'Wrong station map prerequisite'
        assert stage.get('new_quest_ids') == [qid] and quest.get('research_stage') == stage_id, 'Broken station research goal link'
        assert stage.get('proof_scope') == PROOF_SCOPE, 'Research must describe real station proof'
        assert stage.get('item_ids') == [quest['icon']] and stage.get('machine_ids') == [], 'Station action must not invent a machine'
        assert stage.get('recipe_evidence') == [{'path': relative, 'sha256': floors.RECIPE_SHA256[recipe_id],
            'recipe_id': recipe_id, 'type': floors.SERIALIZER, 'source_kind': 'installed_export_recipe', 'verified': True}], 'Wrong station recipe provenance'
        assert qid in maps[0]['optional_quest_ids'], 'Missing optional station map link'
        if compiled:
            assert read(root / f'kubejs/data/aia2/advancement/stations/{planet}_orbit.json') == ADVANCEMENT, 'Station proof must use its impossible criterion'
            chapter_path = root / 'config/ftbquests/quests/chapters/aia2_branch_technology_ad_astra.snbt'
            if chapter_path.is_file():
                uid = hashlib.sha256(('aia2-runtime-v1:' + qid).encode()).hexdigest()[:12].upper().rjust(16, '0')
                goals = [q for q in read(chapter_path)['quests'] if q['id'] == uid]
                assert len(goals) == 1, 'Missing compiled station goal'
                rewards = goals[0].get('rewards', [])
                assert len(rewards) == 1 and rewards[0]['type'] == 'item' and \
                    rewards[0]['item'] == {'id': quest['reward'][0]['item'], 'count': 1} and \
                    rewards[0]['count'] == quest['reward'][0]['count'], 'Compiled station reward differs from its catalog'
    if compiled:
        config = read(root / CONFIG)
        assert config == {'schema': 1, 'rules': station_rules()}, 'Generated station world-action rules differ'
        assert type(config['schema']) is int and all(type(row['epoch']) is int for row in config['rules']), 'Station rule integers must be exact'
    return {'approved_advancements': sorted(rule['advancement'] for rule in station_rules()),
            'station_production_quests': 6, 'station_world_action_rules': 6,
            'station_advancements': 6, 'preserved_ad_astra_stages': 31,
            'new_recipes': 0, 'changed_published_tasks': 0,
            'minecraft_dispatch_tested': False}


def apply(root=ROOT):
    root = Path(root)
    report = validate(root)
    write(root / CONFIG, {'schema': 1, 'rules': station_rules()})
    for planet, _, _, _, _ in SPECS:
        write(root / f'kubejs/data/aia2/advancement/stations/{planet}_orbit.json', ADVANCEMENT)
    validate(root, compiled=True)
    return report


if __name__ == '__main__':
    print(json.dumps(apply(), ensure_ascii=False, indent=2))
