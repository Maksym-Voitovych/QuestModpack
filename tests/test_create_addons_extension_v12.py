"""Explicit additive recipe-proof protocol; no optional Create dispatch claim."""
import copy
import hashlib
import json
from pathlib import Path
import shutil
import tempfile
import unittest

from tools import build_create_addons_v12 as C
from tools import build_nasa_process_v7 as N


ROOT = Path(__file__).resolve().parents[1]
PUBLISHED_IDS = (
    'andesite_mixing', 'brass_mixing', 'infused_alloy', 'reinforced_alloy',
    'roots_living_pickaxe', 'roots_charged_focus', 'enderio_energetic_alloy',
    'powah_blazing_crystal', 'clibano_arcane_dust', 'clibano_rune',
    'clibano_obsidiansteel', 'nasa_tier_1_rocket', 'nasa_tier_2_rocket',
    'nasa_tier_3_rocket', 'nasa_tier_4_rocket',
)
NATIVE_ADVANCEMENT = 'aia2:mechanics/cca_electrum_mixing'
IMPOSSIBLE = {'criteria': {'native_process': {'trigger': 'minecraft:impossible'}}}


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def snapshot(root):
    return {path.relative_to(root).as_posix(): path.read_bytes()
            for path in root.rglob('*') if path.is_file()}


class CreateAddonExtensionTests(unittest.TestCase):
    def fixture(self, root, nasa=False):
        for relative in (C.PENDING, C.RECIPE_PATH, 'kubejs/config/aia2_runtime.json'):
            target = root/relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT/relative, target)
        # Filtering immutable published IDs makes this fixture independent of
        # whether the concurrent authoring checkout has generated rule16 yet.
        document = read(ROOT/C.MECHANICS)
        by_id = {rule['id']: rule for rule in document['rules']}
        document['rules'] = [copy.deepcopy(by_id[ident]) for ident in PUBLISHED_IDS]
        write(root/C.MECHANICS, document)
        quest = {
            'id': 'V12_E15_cca_electrum_native', 'epoch': 15,
            'required': False, 'mod': 'createaddition',
            'tasks': [
                {'type': 'advancement', 'advancement': NATIVE_ADVANCEMENT},
                {'type': 'item', 'item': 'immersiveengineering:ingot_electrum',
                 'count': 2, 'consume': False, 'craft': False},
            ],
        }
        write(root/C.QUESTS, {'schema': 1, 'quests': [quest]})
        if nasa:
            paths = [N.PENDING, N.QUESTS, N.RESEARCH,
                     'content/quests/v5_ad_astra_depth.json']
            pending = read(ROOT/N.PENDING)
            paths += [source['frozen_path'] for rule in pending['mechanic_rules']
                      for source in rule['evidence']]
            for relative in paths:
                target = root/relative
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(ROOT/relative, target)

    def assert_refuses_without_writes(self, root, pattern=None):
        before = snapshot(root)
        with self.assertRaises(AssertionError) as error:
            C.apply(root)
        if pattern:
            self.assertIn(pattern, str(error.exception))
        self.assertEqual(snapshot(root), before)

    def test_fifteen_published_rules_and_exact_unified_heated_recipe_are_frozen(self):
        pending = read(ROOT/C.PENDING)
        self.assertEqual(tuple(pending['published_mechanic_hashes']), PUBLISHED_IDS)
        self.assertEqual(tuple(C.BASELINE_HASHES), PUBLISHED_IDS)
        by_id = {rule['id']: rule for rule in read(ROOT/C.MECHANICS)['rules']}
        for ident in PUBLISHED_IDS:
            raw = json.dumps(by_id[ident], ensure_ascii=False, sort_keys=True,
                             separators=(',', ':')).encode()
            self.assertEqual(hashlib.sha256(raw).hexdigest(), pending['published_mechanic_hashes'][ident])
        raw = (ROOT/C.RECIPE_PATH).read_bytes()
        self.assertEqual(hashlib.sha256(raw).hexdigest(),
                         'cc53b40416e04bcc272825e463a8f6dabda639b18cab6197468578ca6d1569ef')
        recipe = json.loads(raw)
        self.assertEqual(recipe['type'], 'create:mixing')
        self.assertEqual(recipe['heat_requirement'], 'heated')
        self.assertEqual(recipe['ingredients'], [{'tag': 'c:ingots/gold'}, {'tag': 'c:ingots/silver'}])
        self.assertEqual(recipe['results'], [{'id': 'immersiveengineering:ingot_electrum', 'count': 2}])

    def test_apply_adds_exactly_one_rule_and_impossible_projection_without_rewriting_history(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); self.fixture(root)
            before = read(root/C.MECHANICS)
            report = C.apply(root)
            after = read(root/C.MECHANICS)
            self.assertEqual(after['schema'], 1)
            self.assertEqual(after['rules'][:15], before['rules'])
            self.assertEqual(len(after['rules']), 16)
            own = after['rules'][15]
            self.assertEqual((own['id'], own['epoch'], own['serializer'], own['output']),
                             ('cca_electrum_mixing', 15, 'create:mixing', 'immersiveengineering:ingot_electrum'))
            self.assertEqual(own['recipeIds'], ['createaddition:mixing/electrum'])
            self.assertEqual(own['advancement'], NATIVE_ADVANCEMENT)
            self.assertEqual(read(root/'kubejs/data/aia2/advancement/mechanics/cca_electrum_mixing.json'), IMPOSSIBLE)
            self.assertEqual(report['new_native_rules'], 1)
            self.assertEqual(report['published_rules_preserved'], 15)
            self.assertEqual(report['new_recipes'], 0)
            self.assertFalse(report['native_create_dispatch_tested'])
            self.assertEqual(C.validate(root, compiled=True)['status'], 'passed')

    def test_apply_is_byte_idempotent_and_cannot_create_world_or_receipt_files(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); self.fixture(root)
            before = snapshot(root)
            C.apply(root); once = snapshot(root)
            C.apply(root)
            self.assertEqual(snapshot(root), once)
            self.assertEqual(set(once)-set(before),
                             {'kubejs/data/aia2/advancement/mechanics/cca_electrum_mixing.json'})
            self.assertFalse(any(path.startswith(('saves/', 'world/', 'playerdata/')) for path in once))

    def test_whole_file_process_references_refresh_only_after_fifteen_rule_preservation(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); self.fixture(root)
            original = read(ROOT/C.PROCESS_MAP)
            def legacy(value):
                if isinstance(value, dict):
                    if value.get('path') == C.MECHANICS:
                        value['sha256'] = C.PUBLISHED_CONFIG_SHA
                    for child in value.values(): legacy(child)
                elif isinstance(value, list):
                    for child in value: legacy(child)
            legacy(original); write(root/C.PROCESS_MAP, original)
            self.assertEqual(C.apply(root)['preserved_process_map_references_refreshed'], 6)
            after = read(root/C.PROCESS_MAP)
            self.assertNotEqual(original, after)
            # Only source-file SHA fields change, never existing process tasks/stages.
            legacy(after); self.assertEqual(after, original)
            once = snapshot(root); C.apply(root); self.assertEqual(snapshot(root), once)

    def test_unreviewed_process_reference_fails_before_config_or_advancement_writes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); self.fixture(root)
            document = read(ROOT/C.PROCESS_MAP)
            document['mods'][0]['sources'][0]['sha256'] = '0'*64
            write(root/C.PROCESS_MAP, document)
            self.assert_refuses_without_writes(root, 'Unreviewed process-map source contract SHA')

    def test_every_published_rule_is_protected_before_any_write(self):
        for ident in PUBLISHED_IDS:
            with self.subTest(rule=ident), tempfile.TemporaryDirectory() as directory:
                root = Path(directory); self.fixture(root)
                document = read(root/C.MECHANICS)
                next(rule for rule in document['rules'] if rule['id'] == ident)['epoch'] = 1
                write(root/C.MECHANICS, document)
                self.assert_refuses_without_writes(root, 'Published mechanic rule changed')

    def test_unknown_rule_duplicate_rule_and_changed_published_order_are_refused(self):
        for mutation in ('unknown', 'duplicate', 'order', 'missing'):
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as directory:
                root = Path(directory); self.fixture(root)
                document = read(root/C.MECHANICS)
                if mutation == 'unknown':
                    extra = copy.deepcopy(document['rules'][0]); extra['id'] = 'invented_process'
                    document['rules'].append(extra)
                elif mutation == 'duplicate': document['rules'].append(copy.deepcopy(document['rules'][0]))
                elif mutation == 'order': document['rules'][0], document['rules'][1] = document['rules'][1], document['rules'][0]
                else: document['rules'].pop()
                write(root/C.MECHANICS, document)
                self.assert_refuses_without_writes(root)

    def test_a_16th_rule_must_match_the_explicit_reviewed_extension(self):
        for field, value in (
                ('epoch', 14), ('output', 'minecraft:gold_ingot'),
                ('serializer', 'create:compacting'), ('recipeIds', ['createaddition:invented']),
                ('advancement', 'minecraft:story/smelt_iron')):
            with self.subTest(field=field), tempfile.TemporaryDirectory() as directory:
                root = Path(directory); self.fixture(root)
                own = copy.deepcopy(read(root/C.PENDING)['extension_rule']); own[field] = value
                document = read(root/C.MECHANICS); document['rules'].append(own)
                write(root/C.MECHANICS, document)
                self.assert_refuses_without_writes(root, 'Generated electrum rule changed')

    def test_pending_metadata_cannot_rewrite_published_hashes_or_claim_dispatch(self):
        for mutation in ('published_hash', 'epoch', 'recipe', 'dispatch', 'schema', 'advancement'):
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as directory:
                root = Path(directory); self.fixture(root)
                pending = read(root/C.PENDING)
                if mutation == 'published_hash': pending['published_mechanic_hashes']['andesite_mixing'] = '0'*64
                elif mutation == 'epoch': pending['extension_rule']['epoch'] = 11
                elif mutation == 'recipe': pending['extension_rule']['recipeIds'].append('create:mixing/andesite_alloy')
                elif mutation == 'dispatch': pending['native_create_dispatch_tested'] = True
                elif mutation == 'schema': pending['schema'] = 2
                else: pending['advancement_json'] = {'criteria': {'native_process': {'trigger': 'minecraft:inventory_changed'}}}
                write(root/C.PENDING, pending)
                self.assert_refuses_without_writes(root)

    def test_changed_recipe_heat_or_output_and_corrupt_source_are_refused_before_write(self):
        for mutation in ('heat', 'output', 'corrupt'):
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as directory:
                root = Path(directory); self.fixture(root)
                path = root/C.RECIPE_PATH
                if mutation == 'corrupt': path.write_text('{')
                else:
                    recipe = read(path)
                    if mutation == 'heat': recipe['heat_requirement'] = 'superheated'
                    else: recipe['results'][0]['count'] = 200
                    write(path, recipe)
                self.assert_refuses_without_writes(root, 'Frozen exact electrum recipe changed')

    def test_future_or_missing_chosen_producer_gate_cannot_pass_route_check(self):
        for category, target in (
                ('blockGates', 'create:blaze_burner'),
                ('itemGates', 'immersiveengineering:ingot_silver'),
                ('recipeGates', 'createaddition:mixing/electrum')):
            with self.subTest(category=category), tempfile.TemporaryDirectory() as directory:
                root = Path(directory); self.fixture(root)
                path = root/'kubejs/config/aia2_runtime.json'; runtime = read(path)
                runtime[category][target] = 16
                write(path, runtime)
                self.assert_refuses_without_writes(root, 'Future or changed chosen electrum producer route')
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); self.fixture(root)
            path = root/'kubejs/config/aia2_runtime.json'; runtime = read(path)
            runtime['recipeGates'].pop('createaddition:mixing/electrum')
            write(path, runtime)
            self.assert_refuses_without_writes(root, 'Future or changed chosen electrum producer route')

    def test_native_proof_and_two_retained_ingots_are_independent_mandatory_conditions(self):
        for mutation in ('missing_proof', 'inventory_trigger', 'one_ingot', 'consumed', 'craft_only', 'future', 'required', 'duplicate'):
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as directory:
                root = Path(directory); self.fixture(root)
                catalog = read(root/C.QUESTS); quest = catalog['quests'][0]
                if mutation == 'missing_proof': quest['tasks'].pop(0)
                elif mutation == 'inventory_trigger': quest['tasks'][0]['advancement'] = 'minecraft:story/smelt_iron'
                elif mutation == 'one_ingot': quest['tasks'][1]['count'] = 1
                elif mutation == 'consumed': quest['tasks'][1]['consume'] = True
                elif mutation == 'craft_only': quest['tasks'][1]['craft'] = True
                elif mutation == 'future': quest['epoch'] = 16
                elif mutation == 'required': quest['required'] = True
                else: catalog['quests'].append(copy.deepcopy(quest))
                write(root/C.QUESTS, catalog)
                self.assert_refuses_without_writes(root)

    def test_compiled_inventory_trigger_or_absent_advancement_cannot_replace_native_proof(self):
        for mutation in ('inventory', 'missing'):
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as directory:
                root = Path(directory); self.fixture(root); C.apply(root)
                path = root/'kubejs/data/aia2/advancement/mechanics/cca_electrum_mixing.json'
                if mutation == 'missing': path.unlink()
                else: write(path, {'criteria': {'native_process': {'trigger': 'minecraft:inventory_changed'}}})
                with self.assertRaises((AssertionError, FileNotFoundError)):
                    C.validate(root, compiled=True)

    def test_nasa_regeneration_accepts_only_explicit_extension_and_preserves_both_contracts(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); self.fixture(root, nasa=True)
            published = copy.deepcopy(read(root/C.MECHANICS)['rules'])
            C.apply(root)
            own = copy.deepcopy(read(root/C.MECHANICS)['rules'][-1])
            report = N.apply(root)
            self.assertEqual(report['nasa_mechanic_rules'], 4)
            self.assertEqual(next(rule for rule in read(root/C.MECHANICS)['rules'] if rule['id'] == 'cca_electrum_mixing'), own)
            C.apply(root)
            self.assertEqual(read(root/C.MECHANICS)['rules'], [*published, own])
            once = snapshot(root); N.apply(root); C.apply(root)
            self.assertEqual(snapshot(root), once)
            (root/C.PENDING).unlink()
            with self.assertRaisesRegex(AssertionError, 'Unreviewed mechanics set'):
                N.validate(root)


if __name__ == '__main__':
    unittest.main()
