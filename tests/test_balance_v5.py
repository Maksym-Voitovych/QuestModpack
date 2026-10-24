"""Portable regression tests for v5 native alternatives and postgame costs."""
import copy
import json
from pathlib import Path
import shutil
import tempfile
import unittest
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.build_balance_v5 import CATALOG, ESSENCE, PREFIX, apply, read, validate


class BalanceV5Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = read(ROOT/CATALOG)
        cls.bundle = read(ROOT/'kubejs/config/aia2_recipes.json')
        cls.rules = read(ROOT/'kubejs/config/aia2_runtime.json')

    def check_catalog(self, catalog=None, bundle=None, rules=None):
        return validate(ROOT, catalog or self.catalog, bundle or self.bundle, rules or self.rules)

    def test_source_backed_catalog_and_acyclic_component_graph(self):
        result = self.check_catalog()
        self.assertEqual(result['recipes'], 33)
        self.assertEqual(result['post_completion_recipes'], 25)
        self.assertTrue(result['explicit_graph_acyclic'])
        self.assertEqual(result['baseline_recipes_preserved'], 569)

    def test_all_three_native_pool_routes_are_closed(self):
        routes = self.catalog['alternative_audit']['botania:creative_pool']['routes']
        self.assertEqual(len(routes), 3)
        self.assertTrue(all(r['id'] in self.catalog['remove'] for r in routes))
        broken = copy.deepcopy(self.catalog)
        broken['remove'].remove('botania:cre/creative_pool_extreme')
        with self.assertRaisesRegex(ValueError, 'alternate|active'):
            self.check_catalog(broken)

    def test_corrupt_frozen_native_source_is_rejected(self):
        broken = copy.deepcopy(self.catalog)
        broken['evidence'][0]['sources'][0]['json']['totalEnergy'] = 1
        with self.assertRaisesRegex(ValueError, 'Source hash changed'):
            self.check_catalog(broken)

    def test_pre_v5_json_is_preserved_not_only_id(self):
        broken = copy.deepcopy(self.bundle)
        first = next(r for r in broken['add'] if not r['id'].startswith(PREFIX))
        first['epoch'] = 1 if first['epoch'] != 1 else 2
        with self.assertRaisesRegex(ValueError, 'Baseline recipe changed'):
            self.check_catalog(bundle=broken)

    def test_stage99_is_explicit_post_completion(self):
        broken = copy.deepcopy(self.catalog)
        broken['add'][0]['post_completion'] = False
        with self.assertRaisesRegex(ValueError, 'stage semantics'):
            self.check_catalog(broken)

    def test_native_fusion_codec_requires_catalyst_and_consumption_flag(self):
        broken = copy.deepcopy(self.catalog)
        recipe = next(r['json'] for r in broken['add'] if r['target']==ESSENCE)
        recipe.pop('catalyst')
        with self.assertRaisesRegex(ValueError, 'native fusion inputs'):
            self.check_catalog(broken)
        broken = copy.deepcopy(self.catalog)
        recipe = next(r['json'] for r in broken['add'] if r['target']==ESSENCE)
        recipe['ingredients'][0]['consume'] = 'true'
        with self.assertRaisesRegex(ValueError, 'native fusion ingredient'):
            self.check_catalog(broken)

    def test_native_pressure_chamber_requires_flat_counted_inputs(self):
        broken = copy.deepcopy(self.catalog)
        recipe = next(r['json'] for r in broken['add'] if r['target']=='pneumaticcraft:creative_compressor')
        ingredient = recipe['inputs'][0].pop('item')
        recipe['inputs'][0]['ingredient'] = {'item':ingredient}
        with self.assertRaisesRegex(ValueError, 'pressure-chamber inputs'):
            self.check_catalog(broken)

    def test_native_postgame_energy_and_mana_are_positive_integers(self):
        for target, field, value, message in [
            (ESSENCE, 'totalEnergy', True, 'Fusion energy'),
            ('powah:energy_cell_creative', 'energy', 0, 'energizing energy'),
            ('botania:creative_pool', 'mana', -1, 'Native output/process changed|terra-plate'),
        ]:
            broken = copy.deepcopy(self.catalog)
            recipe = next(r['json'] for r in broken['add'] if r['target']==target)
            recipe[field] = value
            with self.assertRaisesRegex(ValueError, message):
                self.check_catalog(broken)

    def test_no_future_creative_ingredient_in_early_infinity_tool(self):
        broken = copy.deepcopy(self.catalog)
        recipe = next(r for r in broken['add'] if r['target']=='industrialforegoing:infinity_drill')
        recipe['json']['input'][0] = {'item': ESSENCE}
        with self.assertRaisesRegex(ValueError, 'Future ingredient'):
            self.check_catalog(broken)

    def test_native_infinity_tool_stays_empty_and_uncharged(self):
        broken = copy.deepcopy(self.catalog)
        recipe = next(r for r in broken['add'] if r['target']=='industrialforegoing:infinity_drill')
        recipe['json']['output']['components']['industrialforegoing:infinity_item_power'] = 1000000
        with self.assertRaisesRegex(ValueError, 'Native output/process changed'):
            self.check_catalog(broken)

    def test_free_conversion_cannot_be_removed(self):
        broken = copy.deepcopy(self.catalog)
        broken['remove'].append('evolvedmekanism:block_alloys/creative/from_block')
        with self.assertRaisesRegex(ValueError, 'Free conversion removed'):
            self.check_catalog(broken)

    def test_creative_essence_cannot_bootstrap_itself(self):
        broken = copy.deepcopy(self.catalog)
        recipe = next(r for r in broken['add'] if r['target']==ESSENCE)
        recipe['json']['ingredients'][0]['ingredient'] = {'item':ESSENCE}
        with self.assertRaisesRegex(ValueError, 'cycle|bootstraps'):
            self.check_catalog(broken)

    def test_forge_routes_are_real_block_rituals_not_fake_recipes(self):
        routes = self.catalog['native_ritual_audit']
        self.assertEqual([r['required_forge_tier'] for r in routes], [1,2,3,4])
        self.assertTrue(all(r['registry']=='forbidden_arcanus:hephaestus_forge/ritual' for r in routes))
        self.assertTrue(all(r['source_version']=='2.6.1' and r['result_item_empty'] for r in routes))
        self.assertFalse(any('upgrade_tier_' in r for r in self.catalog['remove']))

    def test_apply_is_idempotent_without_touching_real_runtime(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            for relative in [CATALOG, 'content/audit/registries.json',
                             'kubejs/config/aia2_recipes.json', 'kubejs/config/aia2_runtime.json',
                             self.catalog['native_source_evidence']['file'],
                             self.catalog['native_codec_evidence']['file']]:
                dst=root/relative
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(ROOT/relative, dst)
            (root/'implementation').mkdir()
            apply(root)
            first = (root/'kubejs/config/aia2_recipes.json').read_bytes()
            report = apply(root)
            self.assertEqual(first, (root/'kubejs/config/aia2_recipes.json').read_bytes())
            self.assertEqual(report['forge_gate_floors'], [15,21,21,21,31])
            bundle = read(root/'kubejs/config/aia2_recipes.json')
            self.assertEqual(len(bundle['add']), len([r for r in self.bundle['add'] if not r['id'].startswith(PREFIX)]) + len(self.catalog['add']))
            rules=read(root/'kubejs/config/aia2_runtime.json')
            self.assertEqual(rules['itemGates']['forbidden_arcanus:hephaestus_forge_tier_3'],21)
            self.assertEqual(rules['blockGates']['forbidden_arcanus:hephaestus_forge_tier_4'],21)
            self.assertEqual(rules['itemGates']['industrialforegoing:infinity_nuke'],30)


if __name__ == '__main__':
    unittest.main()
