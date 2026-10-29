"""Four curated NASA completion proofs and additive manufacturing objectives.

Generation uses portable frozen recipe bytes and embedded exported tag evidence.
It does not establish optional-mod weaving or Minecraft dispatch. The Java
witness and the existing server-side projection own those runtime guarantees.
"""
import copy
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
QUESTS = 'content/quests/v5_nasa_manufacturing.json'
PENDING = 'content/research/nasa_process_pending_v7.json'
MECHANICS = 'kubejs/config/aia2_mechanics.json'
RUNTIME = 'kubejs/config/aia2_runtime.json'
RESEARCH = 'content/research/technology_v5.json'
ADVANCEMENT = {'criteria': {'native_process': {'trigger': 'minecraft:impossible'}}}
TIERS = ((1, 37, 'steel'), (2, 37, 'desh'), (3, 38, 'ostrum'), (4, 38, 'calorite'))
BASELINE_RULE_IDS = (
    'andesite_mixing', 'brass_mixing', 'infused_alloy', 'reinforced_alloy',
    'roots_living_pickaxe', 'roots_charged_focus', 'enderio_energetic_alloy',
    'powah_blazing_crystal', 'clibano_arcane_dust', 'clibano_rune', 'clibano_obsidiansteel',
)
RECIPE_SHA256 = {
    1: '65ae3abda2e55391d78f2edc605474a5b7dda5596b96fce2a97f6541960c9bc7',
    2: 'ece9d879bddc3da6d537e5722639b3c721e881368b4d202f80f926f5c372c632',
    3: '5fca2e4a080908552b1c324606aa7f6f5bb391163961d9bb789838eb2771f53c',
    4: '38de0249125fecdd8c96191c7d523b8e1a810fb8d76235698faaa56c36f51e1b',
}
TAG_SHA256 = {
    'ad_astra:steel_blocks': '61f0f81d0e1668b2908e3fdc6335554a9d9bf20489bd1afb1baf6c9a665229da',
    'c:storage_blocks/steel': '2b99c413c20026bf7084a4645fda73cf4df1f7403d7150234b8a16835058571c',
    'ad_astra:desh_blocks': '76fb8331d565a9d42f0b325fc92dacf3fa6798995c6c01720f332fc813648eac',
    'c:storage_blocks/desh': '043ddced2f94f0b17543d79cd6e8df1ef3709b02ba4369f0ffab752c4afb9c5d',
    'ad_astra:ostrum_blocks': 'e9de6ba25dda9066557d5b847723b8d96e0f65f4e49b24fadcc76b0fbf9f0043',
    'c:storage_blocks/ostrum': '701dd79260e9c60733307e8bf4d5225522b5650e39d51fad37cfd20bf9ae4775',
    'ad_astra:calorite_blocks': '08a7f03c64708338533404658363e98fce2701c5785607197c32ab7092b9a541',
    'c:storage_blocks/calorite': 'f154e01babfce89043b42fca989e862ab297102f599b807a8386fa00ed14d52a',
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


def frozen(root, relative, digest):
    root = Path(root).resolve()
    relative = Path(relative)
    assert not relative.is_absolute() and '..' not in relative.parts, 'Nonportable NASA evidence'
    path = (root / relative).resolve()
    assert path.is_relative_to(root) and path.is_file(), 'Missing NASA recipe evidence'
    raw = path.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == digest, 'NASA exact recipe SHA mismatch'
    return json.loads(raw)


def tag_members(evidence):
    """Resolve the frozen export's explicit item tags, retaining optional edges."""
    by_id = {row['tag']: row for row in evidence}
    assert len(by_id) == len(evidence), 'Duplicate NASA input tag evidence'
    assert set(by_id) == set(TAG_SHA256), 'Incomplete NASA input tag evidence'
    active, resolved = set(), {}

    def visit(tag):
        assert tag not in active, 'Cyclic NASA input tag evidence'
        if tag in resolved:
            return resolved[tag]
        active.add(tag)
        row = by_id[tag]
        assert row['export_path'] == 'tags/minecraft/item/' + tag.replace(':', '/') + '.json', 'Changed NASA tag path'
        raw = row['source_text'].encode()
        assert row['source_sha256'] == TAG_SHA256[tag], 'Unreviewed NASA exact tag SHA'
        assert hashlib.sha256(raw).hexdigest() == row['source_sha256'], 'NASA exact tag SHA mismatch'
        values = json.loads(raw)
        assert isinstance(values, list) and values, 'Empty NASA ingredient tag'
        items = set()
        for value in values:
            assert isinstance(value, str) and ':' in value, 'Unreviewed NASA tag value'
            if value.startswith('#'):
                nested = value[1:].removesuffix('?')
                assert nested in by_id, 'Missing nested NASA ingredient tag'
                items.update(visit(nested))
            else:
                assert not value.endswith('?'), 'Unreviewed optional NASA item'
                items.add(value)
        active.remove(tag)
        assert sorted(items) == row['resolved_item_ids'], 'NASA tag membership differs from export'
        resolved[tag] = items
        return items

    for tag in by_id:
        visit(tag)
    return resolved


def validate(root=ROOT, pending=None, catalog=None, runtime=None, compiled=False):
    """Validate source contracts before any generation writes are performed."""
    root = Path(root)
    pending = copy.deepcopy(pending if pending is not None else read(root / PENDING))
    catalog = copy.deepcopy(catalog if catalog is not None else read(root / QUESTS))
    runtime = runtime if runtime is not None else read(root / RUNTIME)
    assert pending['schema'] == catalog['schema'] == 1, 'Unsupported NASA source schema'
    assert pending['mod_id'] == 'ad_astra' and pending['installed_version'] == '1.16.26', 'Unreviewed NASA version'
    assert pending['new_recipes'] == 0 and pending['advancement_json'] == ADVANCEMENT, 'NASA proof must use its impossible criterion'
    assert pending['proof_scope'] == 'current_machine_owner_team_accepted_output_and_exact_14_slot_payment', 'Changed NASA proof scope'
    assert pending['minecraft_dispatch_tested'] is False, 'Source validation does not certify Minecraft dispatch'
    baseline = pending['baseline_mechanic_hashes']
    assert set(baseline) == set(BASELINE_RULE_IDS), 'Published eleven mechanic rules required'
    mechanics = read(root / MECHANICS)
    assert mechanics['schema'] == 1, 'Unsupported mechanics schema'
    rows = mechanics['rules']
    actual = {row['id']: row for row in rows}
    assert len(actual) == len(rows), 'Duplicate mechanic rule ID'
    specs = pending['mechanic_rules']
    own = {row['id']: row for row in specs}
    expected_ids = {f'nasa_tier_{tier}_rocket' for tier, _, _ in TIERS}
    assert len(own) == len(specs) == 4 and set(own) == expected_ids, 'Exactly four NASA mechanic rules required'
    assert set(actual) in (set(baseline), set(baseline) | expected_ids), 'Unreviewed mechanics set'
    assert [row['id'] for row in rows if row['id'] in baseline] == list(BASELINE_RULE_IDS), 'Published mechanic rule order changed'
    for ident, digest in baseline.items():
        assert canonical(actual[ident]) == digest, 'Published mechanic rule changed'
    for ident in set(actual) & expected_ids:
        assert actual[ident] == own[ident], 'Previously generated NASA rule changed'
    if compiled:
        assert set(actual) == set(baseline) | expected_ids, 'NASA rules not generated'

    research = next(row for row in read(root / RESEARCH)['mods'] if row['mod_id'] == 'ad_astra')
    previous = pending['preserved_stage_hashes']
    assert len(previous) == 27, 'Published twenty-seven Ad Astra stages required'
    research_by_id = {row['id']: row for row in research['stages']}
    assert len(research_by_id) == len(research['stages']), 'Duplicate Ad Astra research stage ID'
    for ident, digest in previous.items():
        assert ident in research_by_id and canonical(research_by_id[ident]) == digest, 'Published Ad Astra research stage changed'

    other_quests = {}
    for path in sorted((root / 'content/quests').glob('*.json')):
        if path.name == Path(QUESTS).name:
            continue
        data = read(path)
        for quest in data if isinstance(data, list) else data['quests']:
            assert quest['id'] not in other_quests, 'Duplicate published quest ID'
            other_quests[quest['id']] = quest
    quests = catalog['quests']
    quest_by_id = {quest['id']: quest for quest in quests}
    assert len(quests) == len(quest_by_id) == 4, 'Exactly four NASA manufacturing quests required'
    assert not (set(quest_by_id) & other_quests.keys()), 'NASA quest ID collides with a published quest'
    assert set(pending['optional_quest_ids']) == set(quest_by_id) and len(pending['optional_quest_ids']) == 4, 'Incomplete NASA quest links'
    stages = pending['stages']
    by_stage = {stage['id']: stage for stage in stages}
    assert len(stages) == len(by_stage) == 4 and not (set(by_stage) & previous.keys()), 'NASA research stage ID collision'
    tags = tag_members(pending['input_tag_evidence'])
    input_alternatives = 0
    for tier, epoch, metal in TIERS:
        ident = f'nasa_tier_{tier}_rocket'
        output = f'ad_astra:tier_{tier}_rocket'
        recipe_id = f'ad_astra:nasa_workbench/tier_{tier}_rocket_from_nasa_workbench'
        advancement = 'aia2:mechanics/' + ident
        rule = own[ident]
        assert set(rule) == {'id', 'epoch', 'output', 'serializer', 'recipeIds', 'advancement', 'evidence'}, 'Unreviewed NASA mechanic fields'
        assert type(rule['epoch']) is int and rule['epoch'] == epoch, 'Wrong NASA mechanic epoch'
        assert rule['serializer'] == 'ad_astra:nasa_workbench' and rule['output'] == output, 'Wrong NASA output or serializer'
        assert rule['recipeIds'] == [recipe_id] and rule['advancement'] == advancement, 'Wrong NASA recipe or advancement ID'
        assert len(rule['evidence']) == 1, 'NASA requires exact recipe evidence'
        evidence = rule['evidence'][0]
        relative = 'content/research/evidence/ad_astra_content_v6/export_recipes/nasa_workbench/' + f'tier_{tier}_rocket_from_nasa_workbench.json'
        assert evidence['frozen_path'] == relative and evidence['recipeId'] == recipe_id, 'Wrong NASA recipe provenance'
        assert evidence['export_path'] == 'recipes/' + recipe_id.replace(':', '/') + '.json', 'Wrong NASA export provenance'
        assert evidence['source_sha256'] == RECIPE_SHA256[tier], 'Unreviewed NASA exact recipe SHA'
        recipe = frozen(root, relative, evidence['source_sha256'])
        assert recipe == evidence['json'] and canonical(recipe) == evidence['canonical_sha256'], 'NASA canonical recipe mismatch'
        assert recipe['type'] == rule['serializer'] and recipe['result'] == {'count': 1, 'id': output}, 'NASA recipe output changed'
        expected_ingredients = [
            {'item': 'ad_astra:rocket_nose_cone'},
            *[{'tag': f'ad_astra:{metal}_blocks'}] * 6,
            {'item': 'ad_astra:rocket_fin'}, {'item': f'ad_astra:{metal}_tank'},
            {'item': f'ad_astra:{metal}_tank'}, {'item': 'ad_astra:rocket_fin'},
            {'item': 'ad_astra:rocket_fin'}, {'item': f'ad_astra:{metal}_engine'},
            {'item': 'ad_astra:rocket_fin'},
        ]
        assert recipe['ingredients'] == expected_ingredients, 'NASA exact fourteen-slot inputs changed'
        assert runtime['itemGates'].get(output, 100) <= epoch and runtime['recipeGates'].get(recipe_id, 100) <= epoch, 'Future NASA output or recipe'
        assert runtime['blockGates'].get('ad_astra:nasa_workbench', 100) <= epoch, 'Future NASA machine'
        for ingredient in recipe['ingredients']:
            members = tags[ingredient['tag']] if 'tag' in ingredient else {ingredient['item']}
            available = {item for item in members if runtime['itemGates'].get(item, 100) <= epoch}
            assert available, 'NASA recipe has missing or future-only inputs'
            input_alternatives += len(available)

        qid = f'V7_E{epoch}_nasa_manufacture_t{tier}'
        quest = quest_by_id.get(qid, {})
        assert quest.get('epoch') == epoch and quest.get('required') is False, 'Wrong NASA quest epoch or mandatory flag'
        assert quest.get('mod') == 'ad_astra' and quest.get('icon') == output, 'Wrong NASA quest target'
        parent = f'V5_E{epoch}_ad_astra_core_rocket_t{tier}'
        assert quest.get('after') == [parent] and parent in other_quests and other_quests[parent]['epoch'] <= epoch, 'NASA quest must follow its published rocket objective'
        assert quest['tasks'] == [
            {'type': 'advancement', 'advancement': advancement},
            {'type': 'item', 'item': output, 'count': 1, 'consume': False, 'craft': False},
        ], 'NASA quest must require native proof and separate possession'
        assert len(' '.join(quest.get('description_uk', []))) >= 160 and quest.get('title_uk'), 'Missing substantive NASA manufacturing explanation'
        assert quest.get('proof_scope') == pending['proof_scope'], 'NASA quest misstates proof scope'
        assert quest.get('reward') == [{'item': f'ad_astra:{metal}_nugget', 'count': 3}], 'Unreviewed NASA reward'
        assert runtime['itemGates'].get(quest['reward'][0]['item'], 100) <= epoch, 'Future NASA reward'

        stage_id = f'ad_astra.manufacturing.rocket_t{tier}'
        stage = by_stage.get(stage_id, {})
        assert stage.get('epoch') == epoch and stage.get('prerequisites') == [f'ad_astra.core.rocket_t{tier}'], 'Wrong NASA research dependency'
        assert stage.get('new_quest_ids') == [qid] and quest.get('research_stage') == stage_id, 'Broken NASA research quest link'
        assert stage.get('item_ids') == [output] and stage.get('machine_ids') == ['ad_astra:nasa_workbench'], 'Wrong NASA research target'
        assert stage.get('recipe_evidence') == [{'path': relative, 'sha256': RECIPE_SHA256[tier],
            'recipe_id': recipe_id, 'type': 'ad_astra:nasa_workbench', 'source_kind': 'installed_export_recipe', 'verified': True}], 'Wrong NASA research recipe evidence'
        assert stage.get('proof_scope') == pending['proof_scope'], 'NASA research misstates proof scope'
        if stage_id in research_by_id:
            assert research_by_id[stage_id] == stage, 'Integrated NASA research differs from its source'
        if compiled:
            assert read(root / f'kubejs/data/aia2/advancement/mechanics/{ident}.json') == ADVANCEMENT, 'NASA proof must use its impossible criterion'
    return {'nasa_manufacturing_quests': 4, 'nasa_mechanic_rules': 4,
            'preserved_mechanic_rules': 11, 'preserved_ad_astra_stages': 27,
            'nasa_recipe_input_alternatives': input_alternatives,
            'minecraft_dispatch_tested': False}


def apply(root=ROOT):
    root = Path(root)
    report = validate(root)
    pending = read(root / PENDING)
    document = read(root / MECHANICS)
    own_ids = {row['id'] for row in pending['mechanic_rules']}
    document['rules'] = [row for row in document['rules'] if row['id'] not in own_ids] + pending['mechanic_rules']
    write(root / MECHANICS, document)
    for row in pending['mechanic_rules']:
        write(root / ('kubejs/data/aia2/advancement/mechanics/' + row['id'] + '.json'), ADVANCEMENT)
    validate(root, compiled=True)
    return report


if __name__ == '__main__':
    print(json.dumps(apply(), ensure_ascii=False, indent=2))
