"""Source-backed station floors; no structure placement or optional dispatch claim."""
import copy
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

from tools import build_station_floors_v8 as F


ROOT = Path(__file__).resolve().parents[1]


class StationFloorsTests(unittest.TestCase):
    def setUp(self):
        self.catalog = F.read(ROOT / F.CATALOG)
        self.runtime = F.read(ROOT / F.RUNTIME)

    def fixture(self, root):
        for name in [F.CATALOG, F.RUNTIME]:
            target = root / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / name, target)
        # Test the initial six-floor migration even after the generator is integrated.
        runtime = F.read(root / F.RUNTIME)
        for ident in F.RECIPES:
            runtime['recipeGates'][ident] = 0
        F.write(root / F.RUNTIME, runtime)
        bundle = root / 'kubejs/config/aia2_recipes.json'
        bundle.write_text('{"preserved":"native recipe bundle is outside this module"}\n')
        quests = root / 'config/ftbquests/quests/chapters/foreign.snbt'
        quests.parent.mkdir(parents=True)
        quests.write_text('{id:"ABCDEF0000000001",quests:[]}\n')

    @staticmethod
    def snapshot(root):
        return {path.relative_to(root).as_posix(): path.read_bytes()
                for path in root.rglob('*') if path.is_file()}

    def test_six_exact_native_sources_and_current_dimension_floors(self):
        result = F.validate(ROOT)
        self.assertEqual(result['native_recipe_floors'], 6)
        self.assertEqual(result['frozen_input_tag_sources'], 18)
        self.assertEqual(result['input_item_alternatives'], 27)
        self.assertEqual(result['future_tag_alternatives_retained'], 3)
        self.assertEqual(result['new_recipes'], 0)
        self.assertFalse(result['full_modpack_dispatch_tested'])
        self.assertEqual(set(F.FLOORS.values()), {37, 38})
        for row in self.catalog['recipes']:
            self.assertEqual(row['json']['type'], 'ad_astra:space_station_recipe')
            self.assertEqual(len(row['json']['ingredients']), 4)
            self.assertTrue(all(holder['count'] in {32, 64} for holder in row['json']['ingredients']))
            self.assertEqual(self.runtime['dimensionGates'][row['dimension']], row['stage'])

    def test_apply_only_raises_six_floors_preserving_all_other_bytes_and_data(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            self.fixture(root)
            before_files = self.snapshot(root)
            before = F.read(root / F.RUNTIME)
            report = F.apply(root)
            after_files = self.snapshot(root)
            self.assertEqual(report['changed_recipe_floors'], 6)
            self.assertEqual({name for name in before_files if before_files[name] != after_files[name]}, {F.RUNTIME})
            after = F.read(root / F.RUNTIME)
            self.assertEqual(set(before['recipeGates']), set(after['recipeGates']))
            for ident in F.RECIPES:
                self.assertEqual(after['recipeGates'][ident], F.FLOORS[F.RECIPES[ident]])
            for key in before:
                if key != 'recipeGates':
                    self.assertEqual(before[key], after[key], key)
            for ident in before['recipeGates'].keys() - F.RECIPES.keys():
                self.assertEqual(before['recipeGates'][ident], after['recipeGates'][ident], ident)
            self.assertEqual(before_files.keys(), after_files.keys())
            self.assertTrue(F.validate(root, compiled=True)['native_costs_and_structures_preserved'])

    def test_generation_is_byte_idempotent_and_keeps_stricter_existing_floor(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            self.fixture(root)
            runtime = F.read(root / F.RUNTIME)
            ident = 'ad_astra:space_station/earth_orbit_space_station'
            runtime['recipeGates'][ident] = 44
            F.write(root / F.RUNTIME, runtime)
            report = F.apply(root)
            self.assertEqual(report['changed_recipe_floors'], 5)
            self.assertEqual(F.read(root / F.RUNTIME)['recipeGates'][ident], 44)
            once = self.snapshot(root)
            self.assertEqual(F.apply(root)['changed_recipe_floors'], 0)
            self.assertEqual(once, self.snapshot(root))

    def test_hash_seed_changes_do_not_change_generated_bytes(self):
        with tempfile.TemporaryDirectory() as folder:
            outputs = []
            for seed in [113, 137]:
                root = Path(folder) / str(seed)
                self.fixture(root)
                code = 'from tools.build_station_floors_v8 import apply;apply(__import__("pathlib").Path(__import__("sys").argv[1]))'
                run = subprocess.run([sys.executable, '-c', code, str(root)], cwd=ROOT,
                    env={**os.environ, 'PYTHONHASHSEED': str(seed)}, capture_output=True, text=True)
                self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
                outputs.append((root / F.RUNTIME).read_bytes())
            self.assertEqual(outputs[0], outputs[1])

    def test_original_export_recipe_and_tag_bytes_match_when_available(self):
        export = Path('/workspace/aia2-reference/export')
        if not export.is_dir():
            self.skipTest('External installed export unavailable')
        for row in self.catalog['recipes'] + self.catalog['input_tag_evidence']:
            raw = (export / row['export_path']).read_bytes()
            self.assertEqual(raw, row['source_text'].encode())
            self.assertEqual(hashlib.sha256(raw).hexdigest(), row['source_sha256'])

    def test_missing_changed_or_unknown_destination_floor_is_rejected(self):
        for replacement in [None, 1, 36, 38, 99, True]:
            with self.subTest(replacement=replacement):
                runtime = copy.deepcopy(self.runtime)
                if replacement is None:
                    runtime['dimensionGates'].pop('ad_astra:earth_orbit')
                else:
                    runtime['dimensionGates']['ad_astra:earth_orbit'] = replacement
                with self.assertRaisesRegex(AssertionError, 'dimension floor'):
                    F.validate(ROOT, runtime=runtime)
        catalog = copy.deepcopy(self.catalog)
        catalog['recipes'][0]['dimension'] = 'ad_astra:unknown_orbit'
        with self.assertRaisesRegex(AssertionError, 'floor/dimension'):
            F.validate(ROOT, catalog=catalog)

    def test_incomplete_extra_or_duplicate_recipe_scope_is_rejected(self):
        for mode in ['remove', 'duplicate', 'extra']:
            with self.subTest(mode=mode):
                catalog = copy.deepcopy(self.catalog)
                if mode == 'remove':
                    catalog['recipes'].pop()
                elif mode == 'duplicate':
                    catalog['recipes'].append(copy.deepcopy(catalog['recipes'][0]))
                else:
                    extra = copy.deepcopy(catalog['recipes'][0])
                    extra['recipe_id'] = 'ad_astra:space_station/unknown'
                    catalog['recipes'].append(extra)
                with self.assertRaisesRegex(AssertionError, 'Exactly six'):
                    F.validate(ROOT, catalog=catalog)

    def test_compiled_floor_cannot_be_missing_lower_or_noninteger(self):
        ident = next(iter(F.RECIPES))
        valid = copy.deepcopy(self.runtime)
        for recipe, dimension in F.RECIPES.items():
            valid['recipeGates'][recipe] = F.FLOORS[dimension]
        F.validate(ROOT, runtime=valid, compiled=True)
        for value in [None, 0, 36, -1, 37.5, True, 101]:
            with self.subTest(value=value):
                bad = copy.deepcopy(valid)
                if value is None:
                    bad['recipeGates'].pop(ident)
                else:
                    bad['recipeGates'][ident] = value
                with self.assertRaisesRegex(AssertionError, 'Station recipe floor'):
                    F.validate(ROOT, runtime=bad, compiled=True)

    def test_known_future_tag_alternatives_remain_but_future_only_inputs_fail(self):
        self.assertEqual(F.validate(ROOT)['future_tag_alternatives_retained'], 3)
        bad = copy.deepcopy(self.runtime)
        bad['itemGates']['ad_astra:calorite_ingot'] = 39
        with self.assertRaisesRegex(AssertionError, 'Future-only'):
            F.validate(ROOT, runtime=bad)
        bad = copy.deepcopy(self.runtime)
        bad['itemGates'].pop('oritech:biosteel_ingot')
        with self.assertRaisesRegex(AssertionError, 'Unknown station ingredient'):
            F.validate(ROOT, runtime=bad)

    def test_native_json_text_hash_and_path_tampering_fail(self):
        mutations = [lambda row: row['json'].__setitem__('structure', 'minecraft:empty'),
                     lambda row: row.__setitem__('source_text', row['source_text'] + '\n'),
                     lambda row: row.__setitem__('source_sha256', '0' * 64),
                     lambda row: row.__setitem__('export_path', '../other.json')]
        for mutate in mutations:
            with self.subTest(mutate=mutate):
                bad = copy.deepcopy(self.catalog)
                mutate(bad['recipes'][0])
                with self.assertRaises(AssertionError):
                    F.validate(ROOT, catalog=bad)
        bad = copy.deepcopy(self.catalog)
        row = bad['recipes'][0]
        row['source_text'] = row['source_text'].replace('"count": 64', '"count": 1')
        row['source_sha256'] = hashlib.sha256(row['source_text'].encode()).hexdigest()
        row['json'] = json.loads(row['source_text'])
        with self.assertRaisesRegex(AssertionError, 'Unreviewed station source SHA'):
            F.validate(ROOT, catalog=bad)

    def test_tag_text_membership_scope_and_hash_tampering_fail(self):
        bad = copy.deepcopy(self.catalog)
        bad['input_tag_evidence'][0]['resolved_item_ids'] = ['minecraft:dirt']
        with self.assertRaisesRegex(AssertionError, 'membership differs'):
            F.validate(ROOT, catalog=bad)
        bad = copy.deepcopy(self.catalog)
        bad['input_tag_evidence'].pop()
        with self.assertRaisesRegex(AssertionError, 'Incomplete or duplicate'):
            F.validate(ROOT, catalog=bad)
        bad = copy.deepcopy(self.catalog)
        row = bad['input_tag_evidence'][0]
        row['source_text'] = '["minecraft:dirt"]'
        row['source_sha256'] = hashlib.sha256(row['source_text'].encode()).hexdigest()
        row['resolved_item_ids'] = ['minecraft:dirt']
        with self.assertRaisesRegex(AssertionError, 'Unreviewed station source SHA'):
            F.validate(ROOT, catalog=bad)

    def test_real_holder_count_shape_and_structural_budgets(self):
        original = self.catalog['recipes'][0]['json']
        dimension = original['dimension']
        for count in [0, -1, True, 1.5, 4097]:
            bad = copy.deepcopy(original)
            bad['ingredients'][0]['count'] = count
            with self.assertRaisesRegex(AssertionError, 'Invalid station material count'):
                F.recipe_inputs(bad, dimension)
        for count in [0, 65]:
            bad = copy.deepcopy(original)
            bad['ingredients'] = [copy.deepcopy(original['ingredients'][0]) for _ in range(count)]
            with self.assertRaisesRegex(AssertionError, 'Unbounded station ingredient count'):
                F.recipe_inputs(bad, dimension)
        bad = copy.deepcopy(original)
        bad['ingredients'] = [{'count': 4096, 'ingredient': {'item': 'minecraft:iron_ingot'}}] * 5
        with self.assertRaisesRegex(AssertionError, 'Unbounded station material total'):
            F.recipe_inputs(bad, dimension)
        for ingredient in [{'tag': 'c:ingots/iron', 'count': 4}, [], {'custom': 'anything'}, {'item': None}]:
            bad = copy.deepcopy(original)
            bad['ingredients'][0]['ingredient'] = ingredient
            with self.assertRaisesRegex(AssertionError, 'Unsupported station ingredient'):
                F.recipe_inputs(bad, dimension)
        bad = copy.deepcopy(original)
        bad['type'] = 'ad_astra:space_station'
        with self.assertRaisesRegex(AssertionError, 'serializer'):
            F.recipe_inputs(bad, dimension)
        bad = copy.deepcopy(original)
        bad['structure'] = 'minecraft:unknown'
        with self.assertRaisesRegex(AssertionError, 'structure'):
            F.recipe_inputs(bad, dimension)

    def test_failed_preflight_writes_nothing(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            self.fixture(root)
            bad = F.read(root / F.RUNTIME)
            bad['recipeGates'].pop(next(iter(F.RECIPES)))
            F.write(root / F.RUNTIME, bad)
            before = self.snapshot(root)
            with self.assertRaisesRegex(AssertionError, 'missing or invalid'):
                F.apply(root)
            self.assertEqual(before, self.snapshot(root))

    def test_static_catalog_must_not_claim_dispatch_or_new_recipes(self):
        for field, value in [('full_modpack_dispatch_tested', True), ('new_recipes', 6),
                             ('installed_version', '1.0'), ('serializer', 'invented:recipe')]:
            with self.subTest(field=field):
                bad = copy.deepcopy(self.catalog)
                bad[field] = value
                with self.assertRaises(AssertionError):
                    F.validate(ROOT, catalog=bad)
