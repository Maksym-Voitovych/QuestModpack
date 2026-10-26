"""Reproduce exact machine replacements in temporary roots; never modify runtime."""
import copy
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from tools import build_energy_core_balance_v5 as B

ROOT = Path(__file__).resolve().parents[1]
EXPORT = Path('/workspace/aia2-reference/export/recipes')


class EnergyCoreBalanceTests(unittest.TestCase):
    def inputs(self):
        return (B.read(ROOT/B.CATALOG), B.read(ROOT/'kubejs/config/aia2_recipes.json'),
                B.read(ROOT/'kubejs/config/aia2_runtime.json'))

    def fixture(self, catalog, bundle, rules):
        temporary = tempfile.TemporaryDirectory(prefix='aia2-energy-core-')
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        for rel, data in [(B.CATALOG, catalog), ('kubejs/config/aia2_recipes.json', bundle),
                          ('kubejs/config/aia2_runtime.json', rules)]:
            B.write(root/rel, data)
        sources = catalog['sources']+[catalog['producer_scan']]+catalog['storage_closure']['sources']+[
            source for spec in catalog['recipes'] for source in spec['sources']]+[
            row['source'] for row in catalog['tag_evidence'].values()]
        for source in sources:
            path = root/source['path']; path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes((ROOT/source['path']).read_bytes())
        for path in (ROOT/'content/quests').glob('*.json'):
            output = root/path.relative_to(ROOT); output.parent.mkdir(parents=True, exist_ok=True)
            output.write_bytes(path.read_bytes())
        return root

    def test_exact_sources_capacities_native_materials_and_later_routes(self):
        catalog, bundle, rules = self.inputs()
        report = B.validate(ROOT, catalog, bundle, rules)
        self.assertEqual(report['published_custom_recipes_preserved'], 610)
        self.assertEqual(report['native_producers_replaced'], 13)
        self.assertEqual(report['native_producers_preserved'], 90)
        self.assertEqual(report['storage_conversions_preserved'], 86)
        self.assertEqual(report['serializers'], {'enderio:alloy_smelting': 3, 'powah:energizing': 2})
        for spec in catalog['recipes']:
            self.assertLessEqual(len(B.inputs(spec['json'])), spec['input_slot_capacity'])
            self.assertFalse(spec['json'].get('is_smelting', False))
            self.assertNotIn(spec['magic_input'], B.TARGET_EPOCHS)
        soularium = next(r for r in catalog['recipes'] if r['target'] == 'enderio:soularium_ingot')
        self.assertEqual(B.cost(B.inputs(soularium['json']))[('alternatives', B.SOUL_BLOCKS)], 1)
        self.assertEqual(B.cost(B.inputs(soularium['json']))[('tag', 'c:ingots/gold')], 1)
        self.assertEqual(B.cost(B.inputs(soularium['json']))[('item', 'occultism:otherworld_ashes')], 1)
        self.assertEqual(sum(r['kind'] == 'later_renewable_essence' for r in catalog['preserved_producer_contracts'].values()), 4)
        self.assertEqual(sum(r['kind'] == 'lossless_storage_conversion' for r in catalog['preserved_producer_contracts'].values()), 7)

    def test_invalid_machine_slots_quantities_native_cost_and_energy_fail(self):
        catalog, bundle, rules = self.inputs()
        changes = [
            (0, lambda j: j['inputs'].append({'item': 'minecraft:stone', 'count': 1}), None),
            (0, lambda j: j['inputs'][0].update(count=0), 'quantity'),
            (0, lambda j: j.update(energy=1), 'energy weakened'),
            (0, lambda j: j['inputs'][0].update(tag='c:ingots/gold'), 'material cost weakened'),
            (1, lambda j: j['output'].update(count=1), 'output count changed'),
            (0, lambda j: j['output'].update(count=True), 'output quantity'),
            (3, lambda j: j['ingredients'][0].update(count=2), 'no stack quantity'),
            (3, lambda j: j.update(ingredients=j['ingredients']*3), None),
            (3, lambda j: j.update(energy=1.5), None),
        ]
        for index, edit, message in changes:
            with self.subTest(index=index, message=message):
                changed = copy.deepcopy(catalog); edit(changed['recipes'][index]['json'])
                if message:
                    with self.assertRaisesRegex(AssertionError, message): B.validate(ROOT, changed, bundle, rules)
                else:
                    with self.assertRaises(AssertionError): B.validate(ROOT, changed, bundle, rules)

    def test_future_inputs_bootstrap_and_unreviewed_codec_fail(self):
        catalog, bundle, rules = self.inputs()
        for item, message in [('missing:invented_part', 'Future/unknown'),
                              ('enderio:redstone_alloy_ingot', 'bootstrap/key'),
                              ('botania:elementium_ingot', 'Future/unknown')]:
            changed = copy.deepcopy(catalog)
            changed['recipes'][0]['json']['inputs'][0] = {'item': item, 'count': 1}
            with self.assertRaisesRegex(AssertionError, message): B.validate(ROOT, changed, bundle, rules)
        changed = copy.deepcopy(catalog)
        changed['recipes'][0]['json']['inputs'][0] = {'fluid': 'minecraft:water', 'count': 1}
        with self.assertRaisesRegex(AssertionError, 'ingredient codec'): B.validate(ROOT, changed, bundle, rules)
        changed = copy.deepcopy(rules); changed['blockGates']['enderio:alloy_smelter'] = 20
        with self.assertRaisesRegex(AssertionError, 'Future producer'): B.validate(ROOT, catalog, bundle, changed)

    def test_every_published_record_and_metadata_are_preserved(self):
        catalog, bundle, rules = self.inputs()
        for field, value in [('category', 'changed'), ('epoch', 0), ('target', 'minecraft:air')]:
            changed = copy.deepcopy(bundle)
            next(r for r in changed['add'] if r['id'] in catalog['baseline_recipe_hashes'])[field] = value
            with self.assertRaisesRegex(AssertionError, 'baseline changed'): B.validate(ROOT, catalog, changed, rules)
        changed = copy.deepcopy(bundle)
        changed['add'] = [r for r in changed['add'] if r['id'] != next(iter(catalog['baseline_recipe_hashes']))]
        with self.assertRaisesRegex(AssertionError, 'baseline changed'): B.validate(ROOT, catalog, changed, rules)
        # Even a falsely repinned baseline cannot introduce a second producer.
        changed = copy.deepcopy(bundle); edited = changed['add'][0]
        edited['json'] = {'type': 'minecraft:crafting_shapeless', 'ingredients': [{'item': 'minecraft:dirt'}],
                          'result': {'id': 'powah:ender_core', 'count': 1}}
        changed_catalog = copy.deepcopy(catalog); changed_catalog['baseline_recipe_hashes'][edited['id']] = B.canonical(edited)
        with self.assertRaisesRegex(AssertionError, 'published custom producer'):
            B.validate(ROOT, changed_catalog, changed, rules)

    def test_quest_craft_conflicts_and_source_drift_fail(self):
        catalog, bundle, rules = self.inputs(); root = self.fixture(catalog, bundle, rules)
        B.write(root/'content/quests/energy_conflict.json', {'quests': [{'id': 'conflict', 'tasks': [
            {'type': 'item', 'item': 'powah:ender_core', 'craft': True}]}]})
        with self.assertRaisesRegex(AssertionError, 'craft:true'): B.validate(root, catalog, bundle, rules)
        B.write(root/'content/quests/energy_conflict.json', {'quests': []})
        source = root/catalog['sources'][0]['path']; source.write_bytes(source.read_bytes()+b'\n')
        with self.assertRaisesRegex(AssertionError, 'Stale energy source'): B.validate(root, catalog, bundle, rules)
        changed = copy.deepcopy(catalog); changed['sources'][0]['path'] = '../outside'
        with self.assertRaisesRegex(AssertionError, 'Nonportable'): B.validate(ROOT, changed, bundle, rules)

    def test_native_producer_completeness_and_preservation_fail_closed(self):
        catalog, bundle, rules = self.inputs()
        changed = copy.deepcopy(catalog); changed['recipes'][0]['remove_recipe_ids'].pop()
        with self.assertRaisesRegex(AssertionError, 'Incomplete native producer classification'):
            B.validate(ROOT, changed, bundle, rules)
        changed = copy.deepcopy(bundle); changed['remove'].append(next(iter(catalog['preserved_producer_contracts'])))
        with self.assertRaisesRegex(AssertionError, 'Preserved storage/renewable'): B.validate(ROOT, catalog, changed, rules)
        root = self.fixture(catalog, bundle, rules); B.apply(root)
        actual = B.read(root/'kubejs/config/aia2_recipes.json'); updated = B.read(root/'kubejs/config/aia2_runtime.json')
        actual['remove'].remove('oritech:foundry/alloy/compat/enderio/redstonealloy')
        with self.assertRaisesRegex(AssertionError, 'cheaper route remains'): B.validate(root, catalog, actual, updated, compiled=True)
        actual['remove'].append('oritech:foundry/alloy/compat/enderio/redstonealloy')
        actual['remove'].remove('allthecompressed:energizing/energized_steel_block/x0')
        with self.assertRaisesRegex(AssertionError, 'cheaper route remains'): B.validate(root, catalog, actual, updated, compiled=True)
        changed = copy.deepcopy(catalog); changed['storage_closure']['preserve_recipe_ids'].pop()
        with self.assertRaisesRegex(AssertionError, 'Incomplete storage producer classification'):
            B.validate(ROOT, changed, bundle, rules)

    def test_scan_uses_outputs_and_wrappers_instead_of_input_mentions(self):
        with tempfile.TemporaryDirectory(prefix='aia2-energy-scan-') as directory:
            root = Path(directory)
            B.write(root/'example/input.json', {'type': 'example:process',
                'ingredients': [{'item': 'powah:ender_core'}], 'result': {'id': 'minecraft:stone'}})
            B.write(root/'example/wrapper.json', {'recipe': {'output': {'id': 'powah:ender_core'}}})
            B.write(root/'example/effect.json', {'effectConfig': {'result': {'id': 'enderio:soularium_ingot'}}})
            scan = B.scan_export(root)
            self.assertEqual(scan['recipes_scanned'], 3)
            self.assertEqual(scan['targets']['powah:ender_core'], ['example:wrapper'])
            self.assertEqual(scan['targets']['enderio:soularium_ingot'], ['example:effect'])

    @unittest.skipUnless(EXPORT.is_dir(), 'Original full export is optional for portable builds')
    def test_full_export_manifest_and_all_native_producers_reproduce(self):
        catalog, bundle, rules = self.inputs()
        report = B.validate(ROOT, catalog, bundle, rules, export_recipes=EXPORT)
        self.assertTrue(report['full_export_verified_this_run'])

    def test_apply_is_idempotent_hash_seed_independent_and_only_adds_owned_rows(self):
        catalog, bundle, rules = self.inputs(); root = self.fixture(catalog, bundle, rules)
        B.apply(root)
        paths = ['kubejs/config/aia2_recipes.json', 'kubejs/config/aia2_runtime.json', B.REPORT]
        first = {rel: (root/rel).read_bytes() for rel in paths}; B.apply(root)
        self.assertEqual(first, {rel: (root/rel).read_bytes() for rel in paths})
        actual = B.read(root/paths[0]); updated = B.read(root/paths[1])
        self.assertEqual({r['id']: r for r in actual['add'] if not r['id'].startswith(B.PREFIX)},
                         {r['id']: r for r in bundle['add'] if not r['id'].startswith(B.PREFIX)})
        self.assertEqual(len([r for r in actual['add'] if r['id'].startswith(B.PREFIX)]), 5)
        for key in rules.keys()-{'recipeGates'}: self.assertEqual(updated[key], rules[key])
        results = []
        for seed in ['13', '41']:
            B.write(root/paths[0], bundle); B.write(root/paths[1], rules)
            env = os.environ.copy(); env.update(PYTHONHASHSEED=seed, PYTHONPATH=str(ROOT))
            command = [sys.executable, '-c', 'from tools.build_energy_core_balance_v5 import apply; import sys; apply(sys.argv[1])', str(root)]
            result = subprocess.run(command, env=env, text=True, capture_output=True)
            self.assertEqual(result.returncode, 0, result.stdout+result.stderr)
            results.append({rel: (root/rel).read_bytes() for rel in paths})
        self.assertEqual(results[0], results[1])
