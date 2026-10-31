"""Portable station action content checks; these do not run optional mods."""
import copy
import hashlib
from pathlib import Path
import shutil
import tempfile
import unittest

from tools import build_station_proofs_v9 as S
from tools import validate_v5 as V

ROOT = Path(__file__).resolve().parents[1]


class StationContentTests(unittest.TestCase):
    def setUp(self):
        self.catalog = S.read(ROOT / S.QUESTS)
        self.runtime = S.read(ROOT / S.RUNTIME)
        self.research = S.read(ROOT / S.RESEARCH)

    def validate(self, **kwargs):
        return S.validate(ROOT, catalog=self.catalog, runtime=self.runtime,
                          research=self.research, **kwargs)

    def fixture(self, root):
        for directory in ('content/quests',
                          'content/research/evidence/station_guard_v8/sourcefreeze/installed_export/recipes/ad_astra/space_station'):
            shutil.copytree(ROOT / directory, root / directory)
        for relative in (S.RUNTIME, S.RESEARCH, 'kubejs/config/aia2_mechanics.json'):
            target = root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / relative, target)

    @staticmethod
    def snapshot(root):
        return {p.relative_to(root).as_posix(): p.read_bytes()
                for p in root.rglob('*') if p.is_file()}

    def test_six_optional_real_build_actions_have_native_proof_and_visit(self):
        report = self.validate()
        self.assertEqual(report['station_production_quests'], 6)
        self.assertEqual(report['preserved_ad_astra_stages'], 31)
        self.assertFalse(report['minecraft_dispatch_tested'])
        self.assertEqual([q['epoch'] for q in self.catalog['quests']], [37, 37, 37, 38, 38, 38])
        self.assertTrue(all(q['required'] is False for q in self.catalog['quests']))
        self.assertEqual([t['type'] for q in self.catalog['quests'] for t in q['tasks']],
                         ['advancement', 'dimension'] * 6)

    def test_normal_catalog_validation_accepts_actual_registered_orbits_and_rewards(self):
        registries = {key: set(values) for key, values in
                      S.read(ROOT / 'content/audit/registries.json')['registries'].items()}
        old = S.read(ROOT / 'content/quests/v5_ad_astra_depth.json')['quests']
        report = V.validate_catalog(self.catalog['quests'], self.runtime, registries,
                                   old_records=old,
                                   native_action_advancements={r['advancement'] for r in S.station_rules()})
        self.assertEqual(report['task_types'], {'advancement': 6, 'dimension': 6})

    def test_objectives_are_distinct_from_every_published_goal(self):
        old = {V.objective_signature(q['tasks'])
               for path in (ROOT / 'content/quests').glob('*.json')
               if path.name != Path(S.QUESTS).name
               for data in [S.read(path)]
               for q in (data if isinstance(data, list) else data['quests'])}
        for quest in self.catalog['quests']:
            signature = V.objective_signature(quest['tasks'])
            self.assertNotIn(signature, old)
            old.add(signature)

    def test_real_native_recipe_costs_are_not_replaced_by_generic_equal_batches(self):
        amounts = []
        for rule in S.station_rules():
            planet = rule['id'].removeprefix('station_').removesuffix('_orbit')
            path = ROOT / ('content/research/evidence/station_guard_v8/sourcefreeze/installed_export/recipes/ad_astra/space_station/' + planet + '_orbit_space_station.json')
            amounts.append([h['count'] for h in S.read(path)['ingredients']])
        self.assertEqual(amounts, [[64, 32, 32, 32], [64, 32, 32, 32], [32, 64, 32, 32],
                                  [64, 64, 32, 32], [64, 64, 32, 32], [32, 32, 32, 32]])

    def test_generator_is_deterministic_and_preserves_runtime_recipes_old_mechanics_and_research(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.fixture(root)
            before = self.snapshot(root)
            report = S.apply(root)
            once = self.snapshot(root)
            S.apply(root)
            self.assertEqual(once, self.snapshot(root))
            for path, raw in before.items():
                self.assertEqual(once[path], raw, path)
            new = set(once) - set(before)
            self.assertEqual(len(new), 7)
            self.assertIn(S.CONFIG, new)
            self.assertEqual(report['new_recipes'], 0)
            self.assertEqual(report['changed_published_tasks'], 0)
            for planet, *_ in S.SPECS:
                self.assertEqual(S.read(root / f'kubejs/data/aia2/advancement/stations/{planet}_orbit.json'),
                                 S.ADVANCEMENT)

    def test_duplicate_or_reused_quest_id_is_rejected(self):
        self.catalog['quests'][1]['id'] = self.catalog['quests'][0]['id']
        with self.assertRaisesRegex(AssertionError, 'Exactly six distinct'):
            self.validate()

    def test_missing_native_proof_cannot_be_replaced_by_orbit_visit_or_item(self):
        for replacement in (
            [{'type': 'dimension', 'dimension': 'ad_astra:earth_orbit'}],
            [{'type': 'item', 'item': 'ad_astra:airlock', 'count': 1}],
            [{'type': 'advancement', 'advancement': 'minecraft:story/root'},
             {'type': 'dimension', 'dimension': 'ad_astra:earth_orbit'}],
        ):
            with self.subTest(replacement=replacement):
                catalog = copy.deepcopy(self.catalog)
                catalog['quests'][0]['tasks'] = replacement
                with self.assertRaisesRegex(AssertionError, 'native proof'):
                    S.validate(ROOT, catalog=catalog)

    def test_mismatched_orbit_proof_is_rejected(self):
        self.catalog['quests'][0]['tasks'][0]['advancement'] = 'aia2:stations/moon_orbit'
        with self.assertRaisesRegex(AssertionError, 'native proof'):
            self.validate()

    def test_proof_scope_must_not_claim_inventory_or_old_station_adoption(self):
        self.catalog['quests'][0]['proof_scope'] = 'old_station_adoption'
        with self.assertRaisesRegex(AssertionError, 'proof scope'):
            self.validate()

    def test_future_reward_or_free_machine_or_key_is_rejected(self):
        for item in ('ad_astra:nasa_workbench', 'kubejs:epoch_48_key', 'minecraft:diamond'):
            with self.subTest(item=item):
                catalog = copy.deepcopy(self.catalog)
                catalog['quests'][0]['reward'] = [{'item': item, 'count': 3}]
                with self.assertRaisesRegex(AssertionError, 'Unreviewed station reward'):
                    S.validate(ROOT, catalog=catalog)
        self.runtime['itemGates']['ad_astra:desh_nugget'] = 38
        with self.assertRaisesRegex(AssertionError, 'future station icon/reward'):
            self.validate()

    def test_premature_recipe_or_destination_floor_is_rejected(self):
        for key, ident in (('recipeGates', 'ad_astra:space_station/earth_orbit_space_station'),
                           ('dimensionGates', 'ad_astra:earth_orbit')):
            with self.subTest(key=key):
                runtime = copy.deepcopy(self.runtime)
                runtime[key][ident] = 36
                with self.assertRaisesRegex(AssertionError, 'floor'):
                    S.validate(ROOT, runtime=runtime)

    def test_published_research_stage_change_is_rejected(self):
        mod = next(m for m in self.research['mods'] if m['mod_id'] == 'ad_astra')
        mod['stages'][0]['mechanic_uk'] += ' змінено'
        with self.assertRaisesRegex(AssertionError, 'Published Ad Astra stage changed'):
            self.validate()

    def test_new_research_cannot_invent_machine_or_future_prerequisite(self):
        for field, value in (('machine_ids', ['ad_astra:station_builder']),
                             ('prerequisites', ['ad_astra.station.glacio_orbit'])):
            with self.subTest(field=field):
                research = copy.deepcopy(self.research)
                mod = next(m for m in research['mods'] if m['mod_id'] == 'ad_astra')
                mod['stages'][-6][field] = value
                with self.assertRaises(AssertionError):
                    S.validate(ROOT, research=research)

    def test_changed_frozen_recipe_is_rejected_before_any_generation_write(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.fixture(root)
            path = root / 'content/research/evidence/station_guard_v8/sourcefreeze/installed_export/recipes/ad_astra/space_station/earth_orbit_space_station.json'
            path.write_text(path.read_text() + '\n')
            before = self.snapshot(root)
            with self.assertRaisesRegex(AssertionError, 'exact recipe SHA mismatch'):
                S.apply(root)
            self.assertEqual(self.snapshot(root), before)

    def test_impossible_criterion_cannot_be_changed_to_inventory_or_location(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.fixture(root)
            S.apply(root)
            S.write(root / 'kubejs/data/aia2/advancement/stations/earth_orbit.json',
                    {'criteria': {'native_station': {'trigger': 'minecraft:changed_dimension'}}})
            with self.assertRaisesRegex(AssertionError, 'impossible criterion'):
                S.validate(root, compiled=True)

    def test_compiled_rewards_match_the_reviewed_profile_and_catalog(self):
        relative = 'config/ftbquests/quests/chapters/aia2_branch_technology_ad_astra.snbt'
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.fixture(root)
            target = root / relative
            target.parent.mkdir(parents=True)
            shutil.copyfile(ROOT / relative, target)
            S.apply(root)
            compiled = S.read(target)
            qid = self.catalog['quests'][0]['id']
            uid = hashlib.sha256(('aia2-runtime-v1:' + qid).encode()).hexdigest()[:12].upper().rjust(16, '0')
            goal = next(q for q in compiled['quests'] if q['id'] == uid)
            goal['rewards'][0]['count'] = 64
            S.write(target, compiled)
            with self.assertRaisesRegex(AssertionError, 'Compiled station reward differs'):
                S.validate(root, compiled=True)

    def test_wrong_generated_rule_recipe_or_epoch_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.fixture(root)
            S.apply(root)
            config = S.read(root / S.CONFIG)
            config['rules'][0]['epoch'] = 1
            S.write(root / S.CONFIG, config)
            with self.assertRaisesRegex(AssertionError, 'world-action rules differ'):
                S.validate(root, compiled=True)


if __name__ == '__main__':
    unittest.main()
