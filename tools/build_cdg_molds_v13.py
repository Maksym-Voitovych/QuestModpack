"""Validate six additive profile goals against pinned CDG/FTB contracts."""
import hashlib
import json
from pathlib import Path
try:
    from item_task_components_v13 import predicate, item_stack, MOLD_COMPONENT, MOLD_PROFILES
except ImportError:
    from tools.item_task_components_v13 import predicate, item_stack, MOLD_COMPONENT, MOLD_PROFILES

ROOT = Path(__file__).resolve().parents[1]
CATALOG = 'content/quests/v13_cdg_molds.json'
MANIFEST = 'content/research/evidence/cdg_molds_v13/manifest.json'
CONTRACT = 'content/research/evidence/cdg_molds_v13/contracts/component-contract.json'
NATIVE_FACT = 'content/research/evidence/cdg_mold_codec_native_v13/minecraft-codec-facts.json'
MANIFEST_SHA = '774c1b1edafb868a640bed5572d8e80bbd15c7ba8d195d1e4bb836cf6583479b'
NATIVE_SHA = '4111c58195731e8d133c680a692dfb96d4938fd96ceb8f46a786f9d8e88be757'
PUBLISHED_STAGE_SHA = '1967df3aef6dedcb758165352435d7b85046c990958c169a823e5be9a3fd214f'
OTHER_MODS_SHA = '3837c4f276c2b97baf435dec2586ccab1cd6377c794740c4f64181b90ba4bc61'
SPECS = {
    'V13_E12_cdg_mold_lines': (12, 'lines'),
    'V13_E12_cdg_mold_bowl': (12, 'bowl'),
    'V13_E12_cdg_mold_chain': (12, 'chain'),
    'V13_E15_cdg_mold_bar': (15, 'bar'),
    'V13_E15_cdg_mold_heated_lines': (15, 'lines'),
    'V13_E18_cdg_mold_duroplast': (18, 'bar'),
}


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def canonical(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def uid(value):
    return hashlib.sha256(('aia2-runtime-v1:'+value).encode()).hexdigest()[:12].upper().rjust(16, '0')


def exact_file(root, relative, digest):
    path = Path(relative)
    assert not path.is_absolute() and '..' not in path.parts, 'Nonportable Mold evidence'
    target = (root/path).resolve()
    assert target.is_relative_to(root.resolve()) and target.is_file(), 'Missing portable Mold evidence'
    raw = target.read_bytes(); assert hashlib.sha256(raw).hexdigest() == digest, 'Stale Mold source SHA'
    return raw


def validate(root=ROOT, compiled=False):
    root = Path(root)
    manifest = json.loads(exact_file(root, MANIFEST, MANIFEST_SHA))
    assert len(manifest['files']) == 43 and manifest['source_version_matches'] is True, 'Unreviewed Mold source set'
    assert manifest['installed_binary_equivalence_verified'] is False and manifest['full_client_tested'] is False, 'Source evidence cannot certify original binaries'
    recipes = {}
    for row in manifest['files']:
        raw = exact_file(root, row['path'], row['sha256'])
        if row.get('source_kind') == 'installed_export_recipe':
            recipe = json.loads(raw)
            assert recipe['type'] == row['type'], 'Mold recipe serializer changed'
            recipes[row['recipe_id']] = recipe
    contract = read(root/CONTRACT)
    assert contract['component'] == MOLD_COMPONENT and set(contract['profiles']) == MOLD_PROFILES, 'Changed Mold component/profile registry'
    assert contract['persistent_codec'] == 'ResourceLocation.CODEC' and contract['ftbquests']['matching_modes'] == ['none', 'fuzzy', 'strict'], 'Unreviewed Mold/FTB codec'
    exact_file(root, NATIVE_FACT, NATIVE_SHA)
    catalog = read(root/CATALOG); quests = catalog['quests']
    assert catalog['schema'] == 1 and len(quests) == len(SPECS) and {q['id'] for q in quests} == set(SPECS), 'Expected six additive Mold goals'
    runtime = read(root/'kubejs/config/aia2_runtime.json')
    removed = set(read(root/'kubejs/config/aia2_recipes.json')['remove'])
    maps = read(root/'content/research/technology_v5.json')['mods']
    cdg = next(mod for mod in maps if mod['mod_id'] == 'createdieselgenerators')
    assert canonical(cdg['stages'][:24]) == PUBLISHED_STAGE_SHA and len(cdg['stages']) == 30, 'Published CDG stages changed'
    assert canonical([mod for mod in maps if mod['mod_id'] != 'createdieselgenerators']) == OTHER_MODS_SHA, 'Unrelated mod map changed'
    stages = {stage['id']: stage for stage in cdg['stages'][24:]}
    compiled_quests = {}
    if compiled:
        for path in sorted((root/'config/ftbquests/quests/chapters').glob('*.snbt')):
            for quest in read(path)['quests']:
                assert quest['id'] not in compiled_quests, 'Duplicate compiled quest ID'
                compiled_quests[quest['id']] = quest
    for quest in quests:
        epoch, profile = SPECS[quest['id']]
        assert quest['epoch'] == epoch and quest['required'] is False and quest['mod'] == 'createdieselgenerators', 'Wrong Mold goal era/branch'
        assert quest['proof_scope'] == 'component_profile_and_product_samples', 'Mold presence is not native manufacturing'
        assert not any(task['type'] == 'advancement' for task in quest['tasks']), 'Mold samples cannot fabricate a production receipt'
        filters = [(index, task) for index, task in enumerate(quest['tasks']) if predicate(task) is not None]
        assert len(filters) == 1, 'Each Mold goal requires one exact profile'
        index, task = filters[0]
        assert task['components'][MOLD_COMPONENT] == 'createdieselgenerators:'+profile and task['count'] == 1, 'Wrong Mold profile/count'
        for recipe_id in quest['recipe_ids']:
            assert recipe_id in recipes and recipe_id not in removed and runtime['recipeGates'][recipe_id] <= epoch, 'Missing, removed or future Mold producer'
        stage = stages[quest['research_stage']]
        assert stage['new_quest_ids'] == [quest['id']] and stage['epoch'] == epoch, 'Mold research goal link changed'
        if compiled:
            actual = compiled_quests[uid(quest['id'])]
            matches = [t for t in actual['tasks'] if t['id'] == uid(quest['id']+':task:'+str(index))]
            assert len(matches) == 1, 'Profile task was not compiled exactly once'
            result = matches[0]
            assert result['item'] == item_stack(task) and result.get('match_components') == 'fuzzy', 'Compiled Mold predicate lost components/matching mode'
            assert actual['optional'] is True and actual['hide_until_deps_complete'] is True, 'Mold goals must stay optional and gated'
    return {'status': 'passed', 'new_goals': 6, 'component_profiles': 4, 'source_files': 43,
            'old_cdg_stages_preserved': 24, 'cdg_stages': 30, 'new_recipes_items_textures': 0,
            'profile_proof': 'fuzzy component presence and separate samples; not native manufacturing',
            'native_codec_scope': 'Actual MC synthetic component; original CDG/FTB UI NOT_RUN',
            'full_client': 'NOT_RUN'}


def apply(root=ROOT):
    return validate(root, compiled=True)


if __name__ == '__main__':
    print(json.dumps(validate(compiled=True), ensure_ascii=False, indent=2))
