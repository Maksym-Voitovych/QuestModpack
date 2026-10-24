"""Finite and creative Mana Tablets share an Item ID and must not share a gate."""
import copy
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from tools.build_variant_balance_v5 import CATALOG, RECIPE, TABLET, ESSENCE, apply, read, validate, is_creative_tablet

ROOT = Path(__file__).resolve().parents[1]


class ComponentVariantBalanceTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = read(ROOT/CATALOG)
        cls.bundle = read(ROOT/'kubejs/config/aia2_recipes.json')
        cls.rules = read(ROOT/'kubejs/config/aia2_runtime.json')

    def check(self, catalog=None, bundle=None, rules=None):
        return validate(ROOT, catalog or self.catalog, bundle or self.bundle, rules or self.rules)

    def test_all_three_component_producers_are_closed_and_normal_two_retained(self):
        result = self.check()
        self.assertEqual(result['source_removals'], 3)
        self.assertEqual(result['preserved_normal_routes'], ['botania:mana_tablet', 'botania:mana_tablet_alt'])
        self.assertEqual(result['baseline_recipes_preserved'], 602)
        broken = copy.deepcopy(self.catalog); broken['remove'].remove('avaritia:botania_mana_tablet')
        with self.assertRaisesRegex(ValueError, 'creative producer remains'): self.check(broken)

    def test_component_flag_not_item_id_defines_creative_tablet(self):
        self.assertFalse(is_creative_tablet({'id': TABLET}))
        self.assertFalse(is_creative_tablet({'id': TABLET, 'components': {'minecraft:custom_data': {'creative': 'true'}}}))
        for flag in (True, 1):
            self.assertTrue(is_creative_tablet({'id': TABLET, 'components': {'minecraft:custom_data': {'creative': flag}}}))
        self.assertFalse(is_creative_tablet({'id': 'minecraft:stone', 'components': {'minecraft:custom_data': {'creative': True}}}))

    def test_output_components_and_no_early_stage_are_enforced(self):
        broken = copy.deepcopy(self.catalog); broken['add'][0]['epoch'] = 48
        with self.assertRaisesRegex(ValueError, 'completed48'): self.check(broken)
        broken = copy.deepcopy(self.catalog); broken['add'][0]['json']['result'].pop('components')
        with self.assertRaisesRegex(ValueError, 'output components'): self.check(broken)
        broken = copy.deepcopy(self.catalog); broken['add'][0]['json']['ingredients'] = [{'item':TABLET}]
        with self.assertRaisesRegex(ValueError, 'Creative Essence'): self.check(broken)

    def test_ordinary_item_gate_and_recipe_cannot_be_blocked(self):
        broken = copy.deepcopy(self.rules); broken['itemGates'][TABLET] = 99
        with self.assertRaisesRegex(ValueError, 'Ordinary tablet item gate'): self.check(rules=broken)
        broken = copy.deepcopy(self.bundle); broken['remove'].append('botania:mana_tablet')
        with self.assertRaisesRegex(ValueError, 'Ordinary tablet recipe'): self.check(bundle=broken)

    def test_source_hash_recipe_preservation_keys_and_unknown_inputs(self):
        broken = copy.deepcopy(self.catalog); broken['route_evidence'][0]['sha256'] = '0'*64
        with self.assertRaisesRegex(ValueError, 'Changed variant source'): self.check(broken)
        broken_bundle = copy.deepcopy(self.bundle); broken_bundle['add'][0]['epoch'] = -1
        with self.assertRaisesRegex(ValueError, 'Existing recipe changed'): self.check(bundle=broken_bundle)
        for item in ('example:missing', self.rules['epochs'][0]['key']):
            broken = copy.deepcopy(self.catalog); broken['add'][0]['json']['ingredients'].append({'item':item})
            with self.assertRaisesRegex(ValueError, 'Unknown variant ingredient|Epoch key'): self.check(broken)

    def test_apply_is_idempotent_and_does_not_touch_other_gates_or_recipes(self):
        with tempfile.TemporaryDirectory() as destination:
            root = Path(destination)
            paths = {CATALOG, 'content/audit/registries.json', 'kubejs/config/aia2_recipes.json', 'kubejs/config/aia2_runtime.json'}
            paths |= {s['path'] for s in self.catalog['route_evidence'] + self.catalog['source_evidence']}
            paths.add(self.catalog['audit_scope']['scan_path'])
            for relative in paths:
                target = root/relative; target.parent.mkdir(parents=True, exist_ok=True); shutil.copy2(ROOT/relative,target)
            (root/'implementation').mkdir()
            before = read(root/'kubejs/config/aia2_runtime.json')
            result = apply(root)
            self.assertEqual(result['minimum_completed_epochs'], 48)
            after = read(root/'kubejs/config/aia2_runtime.json')
            self.assertEqual(before['itemGates'], after['itemGates'])
            self.assertEqual(before['blockGates'], after['blockGates'])
            self.assertEqual(after['recipeGates'][RECIPE], 99)
            bundle = read(root/'kubejs/config/aia2_recipes.json')
            self.assertEqual({r['id']:r for r in bundle['add'] if r['id'] != RECIPE},
                             {r['id']:r for r in self.bundle['add'] if r['id'] != RECIPE})
            first = {p.relative_to(root):p.read_bytes() for p in root.rglob('*') if p.is_file()}
            apply(root)
            self.assertEqual(first,{p.relative_to(root):p.read_bytes() for p in root.rglob('*') if p.is_file()})
