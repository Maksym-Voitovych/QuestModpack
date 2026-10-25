"""Reproduce controller floors in a temporary pack without modifying runtime."""
import copy
from pathlib import Path
import tempfile
import unittest

from tools import build_industrial_controller_gates_v5 as B

ROOT = Path(__file__).resolve().parents[1]


class IndustrialControllerGatesTests(unittest.TestCase):
    def inputs(self):
        return (B.read(ROOT/B.CATALOG), B.read(ROOT/'kubejs/config/aia2_runtime.json'),
                B.read(ROOT/'kubejs/config/aia2_recipes.json'))

    def fixture(self, data, rules, bundle):
        temporary = tempfile.TemporaryDirectory(prefix='aia2-controller-floors-')
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        for relative, value in [(B.CATALOG, data), ('kubejs/config/aia2_runtime.json', rules),
                                ('kubejs/config/aia2_recipes.json', bundle)]:
            B.write(root/relative, value)
        scan = B.read(ROOT/data['producer_scan']['path'])
        sources = data['sources']+[data['producer_scan'], data['published_baseline_catalog']]+scan['sources']
        for source in sources:
            path = root/source['path']
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes((ROOT/source['path']).read_bytes())
        for path in (ROOT/'content/quests').glob('*.json'):
            target = root/'content/quests'/path.name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(path.read_bytes())
        return root

    def test_exact_runtime_ids_frozen_producers_and_full_export_agree(self):
        data, rules, bundle = self.inputs()
        report = B.validate(ROOT, rules, bundle, compiled=False)
        self.assertEqual(report['item_floors'], 30)
        self.assertEqual(report['native_recipe_floors'], 41)
        self.assertEqual(report['custom_recipe_floors'], 5)
        self.assertEqual(report['published_custom_recipes_preserved'], 606)
        self.assertGreater(report['quest_references_checked'], 20)
        export = Path('/workspace/aia2-reference/export/recipes')
        if export.is_dir():
            actual = B.scan_export(export)
            frozen = B.read(ROOT/data['producer_scan']['path'])
            self.assertEqual(actual, {key: frozen[key] for key in actual})
        self.assertIn('oritech:crafting/droneportalt', data['native_recipe_floors'])
        self.assertEqual(B.FLOORS['oritech:laser_arm_block'], 32)
        self.assertNotIn('oritech:atomic_forge_block', B.FLOORS)
        self.assertNotIn('oritech:motor/overchargedcrystal', data['native_recipe_floors'])
        self.assertNotIn('oritech:centrifuge_fluid/siliconwafers', data['native_recipe_floors'])

    def test_apply_only_raises_gates_and_preserves_all_recipe_entries_and_removals(self):
        data, rules, bundle = self.inputs()
        keep_item = 'modern_industrialization:oil_drilling_rig'
        keep_recipe = 'modern_industrialization:oil/oil_drilling_rig_asbl'
        rules['itemGates'][keep_item] = rules['blockGates'][keep_item] = 99
        rules['recipeGates'][keep_recipe] = 99
        rules['recipeGates']['aia2:v4/oritech/crafting/laserarm'] = 99
        expected = copy.deepcopy(rules)
        for section in ('itemGates', 'blockGates'):
            for item, floor in B.FLOORS.items():
                expected[section][item] = max(expected[section][item], floor)
        for ident, floor in dict(data['native_recipe_floors'], **data['custom_recipe_floors']).items():
            expected['recipeGates'][ident] = max(expected['recipeGates'][ident], floor)
        root = self.fixture(data, rules, bundle)
        recipes_path = root/'kubejs/config/aia2_recipes.json'
        recipes_before = recipes_path.read_bytes()
        report = B.apply(root)
        self.assertEqual(B.read(root/'kubejs/config/aia2_runtime.json'), expected)
        self.assertEqual(recipes_path.read_bytes(), recipes_before)
        self.assertEqual(report['native_recipe_json_removed'], 0)
        actual = B.read(recipes_path)
        self.assertEqual(actual, bundle)
        self.assertEqual(next(r for r in actual['add'] if r['id'] == 'aia2:v4/oritech/crafting/laserarm')['epoch'], 25)
        runtime_before = (root/'kubejs/config/aia2_runtime.json').read_bytes()
        B.apply(root)
        self.assertEqual((root/'kubejs/config/aia2_runtime.json').read_bytes(), runtime_before)
        self.assertEqual(recipes_path.read_bytes(), recipes_before)
        self.assertEqual(expected['itemGates']['modern_industrialization:replicator'], 99)
        self.assertEqual(expected['blockGates']['modern_industrialization:replicator'], 99)
        self.assertEqual(expected['recipeGates']['modern_industrialization:electric_age/machine/assembler/replicator'], 99)
        self.assertEqual(expected['itemGates']['oritech:atomic_forge_block'], rules['itemGates']['oritech:atomic_forge_block'])

    def test_lowered_item_block_native_and_custom_gates_fail(self):
        data, rules, bundle = self.inputs()
        root = self.fixture(data, rules, bundle)
        B.apply(root)
        actual = B.read(root/'kubejs/config/aia2_runtime.json')
        cases = [('itemGates', 'modern_industrialization:replicator', 48),
                 ('blockGates', 'oritech:laser_arm_block', 25),
                 ('recipeGates', 'oritech:crafting/droneportalt', 25),
                 ('recipeGates', 'aia2:v4/oritech/crafting/laserarm', 25)]
        for section, ident, epoch in cases:
            with self.subTest(section=section, ident=ident):
                broken = copy.deepcopy(actual)
                broken[section][ident] = epoch
                with self.assertRaisesRegex(AssertionError, 'floor not applied'):
                    B.validate(root, broken, bundle)

    def test_replication_goal_cannot_become_required_or_precompletion(self):
        data, rules, bundle = self.inputs()
        root = self.fixture(data, rules, bundle)
        path = root/data['quest_contract']['catalog']
        original = B.read(path)
        for change in ({'required': True}, {'post_completion': False}):
            quests = copy.deepcopy(original)
            next(q for q in quests['quests'] if q['id'] == 'V5_DEPTH_MI_REPLICATOR').update(change)
            B.write(path, quests)
            with self.assertRaises(AssertionError):
                B.validate(root, rules, bundle, compiled=False)

    def test_existing_early_icon_task_or_reward_would_reject_floor(self):
        data, rules, bundle = self.inputs()
        root = self.fixture(data, rules, bundle)
        path = root/'content/quests/controller_test.json'
        for ref in ({'icon': 'oritech:laser_arm_block'},
                    {'tasks': [{'type': 'observation', 'block': 'oritech:laser_arm_block'}]},
                    {'tasks': [{'type': 'advancement', 'advancement': 'modern_industrialization:nuclear_reactor'}]},
                    {'reward': [{'item': 'oritech:laser_arm_block', 'count': 1}]}):
            quest = {'id': 'early_controller_test', 'epoch': 25, 'icon': 'minecraft:stone', 'tasks': []}
            quest.update(ref)
            B.write(path, {'quests': [quest]})
            with self.assertRaisesRegex(AssertionError, 'Earlier quest'):
                B.validate(root, rules, bundle, compiled=False)

    def test_missing_alternate_changed_snapshot_or_custom_recipe_are_detected(self):
        data, rules, bundle = self.inputs()
        root = self.fixture(data, rules, bundle)
        broken = copy.deepcopy(data)
        del broken['native_recipe_floors']['oritech:crafting/droneportalt']
        B.write(root/B.CATALOG, broken)
        with self.assertRaisesRegex(AssertionError, 'floor incomplete'):
            B.validate(root, rules, bundle, compiled=False)
        B.write(root/B.CATALOG, data)
        changed = copy.deepcopy(bundle)
        next(r for r in changed['add'] if r['id'] == 'aia2:v4/oritech/crafting/laserarm')['epoch'] = 32
        with self.assertRaisesRegex(AssertionError, 'baseline changed'):
            B.validate(root, rules, changed, compiled=False)
        changed = copy.deepcopy(bundle)
        next(r for r in changed['add'] if r['id'] == 'aia2:v5/industrial_core/oritech_reactor_controller')['json']['time'] = 1
        with self.assertRaisesRegex(AssertionError, 'custom recipe changed'):
            B.validate(root, rules, changed, compiled=False)
        scan = B.read(root/data['producer_scan']['path'])
        source = scan['sources'][0]
        (root/source['path']).write_bytes(b'{}')
        with self.assertRaisesRegex(AssertionError, 'Stale controller source'):
            B.validate(root, rules, bundle, compiled=False)


if __name__ == '__main__':
    unittest.main()
