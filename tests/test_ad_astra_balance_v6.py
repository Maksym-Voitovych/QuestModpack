"""Source-backed engine costs, closed native producer scope and late functional floors."""
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

from tools import build_ad_astra_core_v6 as balance

ROOT = Path(__file__).resolve().parents[1]


class AdAstraBalanceTests(unittest.TestCase):
    def setUp(self):
        self.catalog = balance.read(ROOT / balance.CATALOG)
        self.bundle = balance.read(ROOT / 'kubejs/config/aia2_recipes.json')
        self.rules = balance.read(ROOT / 'kubejs/config/aia2_runtime.json')

    def fixture(self, target):
        needed = {balance.CATALOG, 'kubejs/config/aia2_recipes.json', 'kubejs/config/aia2_runtime.json'}
        needed.update(row['path'] for row in self.catalog['producer_sources'] + self.catalog['format_sources'])
        needed.update(p.relative_to(ROOT).as_posix() for p in (ROOT / 'content/quests').glob('*.json'))
        for name in sorted(needed):
            path = target / name
            path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / name, path)

    def test_frozen_native_costs_and_complete_scoped_floor_contract(self):
        report = balance.validate(ROOT, self.catalog, self.bundle, self.rules)
        self.assertEqual(report['published_custom_recipes_preserved'], 623)
        self.assertEqual(report['new_recipes'], 4)
        self.assertEqual(report['pre_moon_components_verified'], 2)
        self.assertEqual(report['native_recipe_floors'], 28)
        self.assertEqual(report['item_floors'], 14)
        self.assertEqual(report['item_floors_raised_from_baseline'], 12)
        self.assertEqual(report['block_floors'], 4)
        self.assertGreater(report['quest_references_checked'], 0)
        self.assertEqual({row['epoch'] for row in self.catalog['recipes']}, {37, 38})
        self.assertNotIn('ad_astra:calorite_panel', self.catalog['item_floors'])
        for row in self.catalog['recipes']:
            original = json.loads(balance.frozen(ROOT, row['source']))
            self.assertEqual(sum(balance.cost(original).values()), 7)
            self.assertEqual(sum(balance.cost(row['json']).values()), 11)
            self.assertEqual(row['json']['type'], 'create:mechanical_crafting')
            self.assertFalse(row['json']['accept_mirrored'])
            self.assertEqual(row['added_item_ids'][:2], ['kubejs:aia2_tech_matrix_36', 'kubejs:aia2_arcane_catalyst_36'])
            self.assertEqual(row['remove_recipe_ids'], [row['source']['recipe_id']])
        self.assertEqual(self.catalog['native_recipe_floors']['create:pressing/calorite_ingot'], 38)
        self.assertEqual(self.catalog['native_recipe_floors']['immersiveengineering:crafting/plate_calorite_hammering'], 38)
        self.assertEqual(self.catalog['native_recipe_floors']['modern_industrialization:compressor/calorite_ingot_to_plate'], 38)

    def test_invalid_cost_mirror_scope_future_cycle_and_producer_closure_rejected(self):
        bad = copy.deepcopy(self.catalog)
        bad['recipes'][0]['json']['pattern'][2] = '     '
        with self.assertRaisesRegex(AssertionError, 'shape'):
            balance.validate(ROOT, bad, self.bundle, self.rules)
        bad = copy.deepcopy(self.catalog)
        bad['recipes'][0]['json']['key']['#'] = {'item': 'minecraft:dirt'}
        with self.assertRaisesRegex(AssertionError, 'Native materials'):
            balance.validate(ROOT, bad, self.bundle, self.rules)
        bad = copy.deepcopy(self.catalog)
        bad['recipes'][0]['json']['accept_mirrored'] = True
        with self.assertRaisesRegex(AssertionError, 'mirror'):
            balance.validate(ROOT, bad, self.bundle, self.rules)
        bad = copy.deepcopy(self.catalog)
        bad['recipes'][0]['added_item_ids'][0] = 'kubejs:aia2_tech_matrix_37'
        bad['recipes'][0]['json']['key']['A'] = {'item': 'kubejs:aia2_tech_matrix_37'}
        with self.assertRaisesRegex(AssertionError, 'unreviewed'):
            balance.validate(ROOT, bad, self.bundle, self.rules)
        bad = copy.deepcopy(self.catalog)
        bad['recipes'][0]['added_item_ids'][0] = 'ad_astra:steel_engine'
        bad['recipes'][0]['json']['key']['A'] = {'item': 'ad_astra:steel_engine'}
        with self.assertRaisesRegex(AssertionError, 'unreviewed'):
            balance.validate(ROOT, bad, self.bundle, self.rules)
        future = copy.deepcopy(self.rules)
        future['itemGates']['pneumaticcraft:printed_circuit_board'] = 39
        with self.assertRaisesRegex(AssertionError, 'Future or cyclic'):
            balance.validate(ROOT, self.catalog, self.bundle, future)
        future = copy.deepcopy(self.rules)
        future['itemGates']['mekanismgenerators:hohlraum'] = 39
        with self.assertRaisesRegex(AssertionError, 'Future or cyclic pre-Moon component'):
            balance.validate(ROOT, self.catalog, self.bundle, future)
        bad = copy.deepcopy(self.catalog)
        bad['recipes'][0]['remove_recipe_ids'] = []
        with self.assertRaisesRegex(AssertionError, 'producer removal'):
            balance.validate(ROOT, bad, self.bundle, self.rules)
        bad = copy.deepcopy(self.catalog)
        bad['native_recipe_floors'].pop('create:pressing/calorite_ingot')
        with self.assertRaisesRegex(AssertionError, 'producer floors'):
            balance.validate(ROOT, bad, self.bundle, self.rules)
        bad = copy.deepcopy(self.catalog)
        bad['item_floors']['ad_astra:calorite_panel'] = 38
        with self.assertRaisesRegex(AssertionError, 'functional floor scope'):
            balance.validate(ROOT, bad, self.bundle, self.rules)
        changed = copy.deepcopy(self.bundle)
        changed['add'][0]['json']['type'] = 'unreviewed:change'
        with self.assertRaisesRegex(AssertionError, 'Published custom recipe changed'):
            balance.validate(ROOT, self.catalog, changed, self.rules)

    def test_apply_preserves_published_formulas_and_is_byte_idempotent(self):
        with tempfile.TemporaryDirectory(prefix='aia2-space-balance-') as temporary:
            target = Path(temporary)
            self.fixture(target)
            before = {r['id']: r for r in self.bundle['add'] if not r['id'].startswith(balance.PREFIX)}
            report = balance.apply(target)
            self.assertEqual(report['new_recipes'], 4)
            compiled = balance.read(target / 'kubejs/config/aia2_recipes.json')
            byid = {r['id']: r for r in compiled['add']}
            self.assertTrue(all(byid[k] == v for k, v in before.items()))
            self.assertTrue(set(self.bundle['remove']) <= set(compiled['remove']))
            self.assertEqual(len(compiled['add']), len(before) + 4)
            rules = balance.read(target / 'kubejs/config/aia2_runtime.json')
            self.assertTrue(all(rules['itemGates'][item] == 38 for item in balance.FLOORS))
            self.assertEqual(rules['itemGates']['ad_astra:calorite_panel'], self.rules['itemGates']['ad_astra:calorite_panel'])
            self.assertEqual(rules['recipeGates']['ad_astra:jet_suit'], 38)
            self.assertEqual(rules['recipeGates']['aia2:v4/ad_astra/energizer'], 38)
            self.assertEqual(rules['recipeGates'][balance.PREFIX + 'calorite_engine'], 38)
            first = {p.relative_to(target).as_posix(): p.read_bytes() for p in target.rglob('*') if p.is_file()}
            balance.apply(target)
            self.assertEqual(first, {p.relative_to(target).as_posix(): p.read_bytes() for p in target.rglob('*') if p.is_file()})
            broken = copy.deepcopy(rules)
            broken['recipeGates']['create:pressing/calorite_ingot'] = 37
            with self.assertRaisesRegex(AssertionError, 'producer floor'):
                balance.validate(target, self.catalog, compiled, broken, True)
            source = target / self.catalog['producer_sources'][0]['path']
            source.write_text('{}')
            with self.assertRaisesRegex(AssertionError, 'Stale Ad Astra source'):
                balance.apply(target)

    def test_earlier_quest_reference_is_rejected_before_runtime_writes(self):
        with tempfile.TemporaryDirectory(prefix='aia2-space-floor-') as temporary:
            target = Path(temporary)
            self.fixture(target)
            bad = {'schema': 1, 'quests': [{'id': 'test_early_gravity', 'epoch': 37,
                    'icon': 'ad_astra:gravity_normalizer', 'tasks': [], 'reward': []}]}
            balance.write(target / 'content/quests/early.json', bad)
            before = (target / 'kubejs/config/aia2_runtime.json').read_bytes()
            with self.assertRaisesRegex(AssertionError, 'Earlier quest references gated space equipment'):
                balance.apply(target)
            self.assertEqual(before, (target / 'kubejs/config/aia2_runtime.json').read_bytes())
            self.assertFalse((target / balance.REPORT).exists())

    def test_different_python_hash_seeds_produce_identical_runtime(self):
        manifests = []
        for seed in ('131', '149'):
            with tempfile.TemporaryDirectory(prefix='aia2-space-seed-') as temporary:
                target = Path(temporary)
                self.fixture(target)
                env = os.environ.copy()
                env['PYTHONHASHSEED'] = seed
                script = 'from tools.build_ad_astra_core_v6 import apply; apply(__import__("pathlib").Path(__import__("sys").argv[1]))'
                run = subprocess.run([sys.executable, '-c', script, str(target)], cwd=ROOT, env=env, capture_output=True, text=True)
                self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
                manifests.append({name: hashlib.sha256((target / name).read_bytes()).hexdigest() for name in
                                  ['kubejs/config/aia2_recipes.json', 'kubejs/config/aia2_runtime.json', balance.REPORT]})
        self.assertEqual(*manifests)

    def test_full_export_closure_reproduces_when_external_export_available(self):
        export = Path('/workspace/aia2-reference/export')
        if not export.is_dir():
            self.skipTest('External installed export unavailable')
        self.assertEqual(balance.scan_export(export), self.catalog['producer_scan'])
