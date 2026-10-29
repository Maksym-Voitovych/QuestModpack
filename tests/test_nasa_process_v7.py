"""Portable NASA content/generation regressions; no Minecraft dispatch claim."""
import copy
import hashlib
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

from tools import build_nasa_process_v7 as N
from tools import validate_v5 as V


ROOT = Path(__file__).resolve().parents[1]


class NasaProcessTests(unittest.TestCase):
    def setUp(self):
        self.pending = N.read(ROOT / N.PENDING)
        self.catalog = N.read(ROOT / N.QUESTS)
        self.runtime = N.read(ROOT / N.RUNTIME)

    def validate(self, **kwargs):
        return N.validate(ROOT, pending=self.pending, catalog=self.catalog,
                          runtime=self.runtime, **kwargs)

    def fixture(self, root):
        paths = [N.PENDING, N.QUESTS, N.RUNTIME, N.MECHANICS, N.RESEARCH,
                 'content/quests/v5_ad_astra_depth.json']
        paths += [row['evidence'][0]['frozen_path'] for row in self.pending['mechanic_rules']]
        for relative in paths:
            target = root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / relative, target)
        # Test upgrading the published eleven-rule configuration even after the
        # root agent has generated the new rules in the shared checkout.
        document = N.read(root / N.MECHANICS)
        document['rules'] = [row for row in document['rules'] if row['id'] in N.BASELINE_RULE_IDS]
        N.write(root / N.MECHANICS, document)

    @staticmethod
    def snapshot(root):
        return {path.relative_to(root).as_posix(): path.read_bytes()
                for path in root.rglob('*') if path.is_file()}

    def test_four_optional_goals_use_proof_and_separate_possession(self):
        report = self.validate()
        self.assertEqual(report['nasa_manufacturing_quests'], 4)
        self.assertFalse(report['minecraft_dispatch_tested'])
        self.assertEqual([q['epoch'] for q in self.catalog['quests']], [37, 37, 38, 38])
        self.assertEqual(len({q['id'] for q in self.catalog['quests']}), 4)
        self.assertTrue(all(q['required'] is False for q in self.catalog['quests']))
        self.assertEqual([task['type'] for q in self.catalog['quests'] for task in q['tasks']],
                         ['advancement', 'item'] * 4)
        self.assertTrue(all(q['reward'][0]['count'] == 3 for q in self.catalog['quests']))

    def test_catalog_passes_normal_content_validation(self):
        specs = {row['id']: (row['epoch'], row['serializer'], row['output'], set(row['recipeIds']))
                 for row in self.pending['mechanic_rules']}
        registry = {key: set(values) for key, values in
                    N.read(ROOT / 'content/audit/registries.json')['registries'].items()}
        old = N.read(ROOT / 'content/quests/v5_ad_astra_depth.json')['quests']
        with patch.dict(V.MECHANIC_CONTRACT, specs):
            report = V.validate_catalog(self.catalog['quests'], self.runtime, registry,
                old_records=old,
                mechanic_advancements={row['advancement'] for row in self.pending['mechanic_rules']})
        self.assertEqual(report['new_authored_quests'], 4)
        self.assertEqual(report['task_types'], {'advancement': 4, 'item': 4})

    def test_new_objectives_are_distinct_from_published_catalogs(self):
        old = {V.objective_signature(q['tasks']): q['id']
               for path in (ROOT / 'content/quests').glob('*.json')
               if path.name != Path(N.QUESTS).name
               for data in [N.read(path)] for q in (data if isinstance(data, list) else data['quests'])}
        for quest in self.catalog['quests']:
            signature = V.objective_signature(quest['tasks'])
            self.assertNotIn(signature, old)
            old[signature] = quest['id']

    def test_exact_frozen_export_recipes_and_fourteen_slot_cost(self):
        for tier, _, _ in N.TIERS:
            row = self.pending['mechanic_rules'][tier - 1]
            evidence = row['evidence'][0]
            raw = (ROOT / evidence['frozen_path']).read_bytes()
            self.assertEqual(hashlib.sha256(raw).hexdigest(), N.RECIPE_SHA256[tier])
            self.assertEqual(json.loads(raw), evidence['json'])
            self.assertEqual(N.canonical(json.loads(raw)), evidence['canonical_sha256'])
            self.assertEqual(len(evidence['json']['ingredients']), 14)
            self.assertEqual(row['serializer'], 'ad_astra:nasa_workbench')
            self.assertEqual(row['recipeIds'],
                             [f'ad_astra:nasa_workbench/tier_{tier}_rocket_from_nasa_workbench'])
            self.assertTrue(V.verify_evidence(ROOT, {'path': evidence['frozen_path'],
                              'sha256': evidence['source_sha256']}, claimed=True))

    def test_original_export_matches_when_available(self):
        export = Path('/workspace/aia2-reference/export')
        if not export.is_dir():
            self.skipTest('External installed export unavailable')
        for rule in self.pending['mechanic_rules']:
            evidence = rule['evidence'][0]
            self.assertEqual((ROOT / evidence['frozen_path']).read_bytes(),
                             (export / evidence['export_path']).read_bytes())
        for row in self.pending['input_tag_evidence']:
            self.assertEqual(row['source_text'].encode(), (export / row['export_path']).read_bytes())

    def test_all_old_stages_and_research_graph_remain_valid(self):
        current = next(row for row in N.read(ROOT / N.RESEARCH)['mods'] if row['mod_id'] == 'ad_astra')
        stages = {stage['id']: stage for stage in current['stages']}
        self.assertEqual(len(self.pending['preserved_stage_hashes']), 27)
        for ident, digest in self.pending['preserved_stage_hashes'].items():
            self.assertEqual(N.canonical(stages[ident]), digest)
        stages.update({stage['id']: stage for stage in self.pending['stages']})
        self.assertEqual(len(stages), 31)
        self.assertEqual(V.validate_graph({ident: {'dependencies': stage.get('prerequisites', [])}
                                          for ident, stage in stages.items()}), 31)

    def test_existing_future_tag_alternative_does_not_strand_steel_recipe(self):
        tags = N.tag_members(self.pending['input_tag_evidence'])
        steel = tags['ad_astra:steel_blocks']
        self.assertIn('industrialupgrade:blockresource/steel_block', steel)
        self.assertEqual(self.runtime['itemGates']['industrialupgrade:blockresource/steel_block'], 44)
        self.assertEqual(len({item for item in steel if self.runtime['itemGates'][item] <= 37}), 7)
        self.validate()

    def test_apply_preserves_old_rules_and_only_writes_config_and_four_proofs(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            self.fixture(root)
            before = self.snapshot(root)
            document = N.read(root / N.MECHANICS)
            old_rules = copy.deepcopy(document['rules'])
            report = N.apply(root)
            after = self.snapshot(root)
            changed = {path for path in before.keys() | after.keys() if before.get(path) != after.get(path)}
            self.assertEqual(changed, {N.MECHANICS} | {
                f'kubejs/data/aia2/advancement/mechanics/nasa_tier_{tier}_rocket.json'
                for tier, _, _ in N.TIERS})
            generated = N.read(root / N.MECHANICS)
            self.assertEqual(generated['rules'][:11], old_rules)
            self.assertEqual(len(generated['rules']), 15)
            self.assertEqual({key: value for key, value in generated.items() if key != 'rules'},
                             {key: value for key, value in document.items() if key != 'rules'})
            self.assertEqual(report['preserved_mechanic_rules'], 11)
            for tier, _, _ in N.TIERS:
                self.assertEqual(N.read(root / f'kubejs/data/aia2/advancement/mechanics/nasa_tier_{tier}_rocket.json'),
                                 {'criteria': {'native_process': {'trigger': 'minecraft:impossible'}}})

    def test_generation_is_byte_identical_when_repeated(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            self.fixture(root)
            N.apply(root)
            once = self.snapshot(root)
            N.apply(root)
            self.assertEqual(once, self.snapshot(root))

    def test_duplicate_native_rule_is_rejected_before_any_write(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            self.fixture(root)
            document = N.read(root / N.MECHANICS)
            document['rules'].append(copy.deepcopy(document['rules'][0]))
            N.write(root / N.MECHANICS, document)
            before = self.snapshot(root)
            with self.assertRaisesRegex(AssertionError, 'Duplicate mechanic'):
                N.apply(root)
            self.assertEqual(before, self.snapshot(root))

    def test_changed_old_rule_is_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            self.fixture(root)
            document = N.read(root / N.MECHANICS)
            document['rules'][0]['epoch'] = 5
            N.write(root / N.MECHANICS, document)
            with self.assertRaisesRegex(AssertionError, 'Published mechanic rule changed'):
                N.apply(root)

    def test_changed_old_research_stage_is_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            self.fixture(root)
            document = N.read(root / N.RESEARCH)
            next(row for row in document['mods'] if row['mod_id'] == 'ad_astra')['stages'][0]['title_uk'] += '!'
            N.write(root / N.RESEARCH, document)
            with self.assertRaisesRegex(AssertionError, 'Published Ad Astra research stage changed'):
                N.apply(root)

    def test_recipe_whitespace_edit_fails_exact_source_sha(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            self.fixture(root)
            path = root / self.pending['mechanic_rules'][0]['evidence'][0]['frozen_path']
            path.write_bytes(path.read_bytes() + b'\n')
            with self.assertRaisesRegex(AssertionError, 'NASA exact recipe SHA mismatch'):
                N.apply(root)

    def test_wrong_recipe_id_serializer_output_or_epoch_is_rejected(self):
        for field, replacement in [('recipeIds', ['ad_astra:tier_1_rocket']),
                                   ('serializer', 'minecraft:crafting_shaped'),
                                   ('output', 'ad_astra:tier_2_rocket'), ('epoch', 38)]:
            with self.subTest(field=field):
                pending = copy.deepcopy(self.pending)
                pending['mechanic_rules'][0][field] = replacement
                with self.assertRaises(AssertionError):
                    N.validate(ROOT, pending=pending)

    def test_recipe_canonical_evidence_and_source_sha_are_both_checked(self):
        for field, replacement in [('canonical_sha256', '0' * 64), ('source_sha256', '0' * 64),
                                   ('frozen_path', '../outside.json')]:
            with self.subTest(field=field):
                pending = copy.deepcopy(self.pending)
                pending['mechanic_rules'][0]['evidence'][0][field] = replacement
                with self.assertRaises(AssertionError):
                    N.validate(ROOT, pending=pending)

    def test_future_machine_recipe_output_and_direct_input_are_rejected(self):
        cases = [('blockGates', 'ad_astra:nasa_workbench'),
                 ('itemGates', 'ad_astra:tier_1_rocket'),
                 ('itemGates', 'ad_astra:steel_engine'),
                 ('recipeGates', 'ad_astra:nasa_workbench/tier_1_rocket_from_nasa_workbench')]
        for table, ident in cases:
            with self.subTest(table=table, ident=ident):
                runtime = copy.deepcopy(self.runtime)
                runtime[table][ident] = 38
                with self.assertRaisesRegex(AssertionError, 'Future NASA|future-only inputs'):
                    N.validate(ROOT, runtime=runtime)

    def test_future_only_tag_ingredient_is_rejected(self):
        for item in N.tag_members(self.pending['input_tag_evidence'])['ad_astra:steel_blocks']:
            self.runtime['itemGates'][item] = 38
        with self.assertRaisesRegex(AssertionError, 'future-only inputs'):
            self.validate()

    def test_tampered_tag_source_or_resolved_membership_is_rejected(self):
        for field, value in [('source_text', '[]'), ('resolved_item_ids', ['minecraft:diamond_block'])]:
            with self.subTest(field=field):
                pending = copy.deepcopy(self.pending)
                pending['input_tag_evidence'][0][field] = value
                with self.assertRaisesRegex(AssertionError, 'SHA mismatch|membership differs'):
                    N.validate(ROOT, pending=pending)

    def test_coordinated_tag_text_and_hash_edit_cannot_replace_export_evidence(self):
        row = self.pending['input_tag_evidence'][0]
        row['source_text'] = '["minecraft:diamond_block"]'
        row['source_sha256'] = hashlib.sha256(row['source_text'].encode()).hexdigest()
        row['resolved_item_ids'] = ['minecraft:diamond_block']
        with self.assertRaisesRegex(AssertionError, 'Unreviewed NASA exact tag SHA'):
            self.validate()

    def test_future_reward_or_research_prerequisite_is_rejected(self):
        self.runtime['itemGates']['ad_astra:steel_nugget'] = 38
        with self.assertRaisesRegex(AssertionError, 'Future NASA reward'):
            self.validate()
        self.runtime = N.read(ROOT / N.RUNTIME)
        self.pending['stages'][0]['prerequisites'] = ['ad_astra.core.rocket_t4']
        with self.assertRaisesRegex(AssertionError, 'Wrong NASA research dependency'):
            self.validate()

    def test_duplicate_quest_and_stage_ids_are_rejected(self):
        self.catalog['quests'][1]['id'] = self.catalog['quests'][0]['id']
        with self.assertRaisesRegex(AssertionError, 'Exactly four NASA manufacturing quests'):
            self.validate()
        self.catalog = N.read(ROOT / N.QUESTS)
        self.pending['stages'][1]['id'] = self.pending['stages'][0]['id']
        with self.assertRaisesRegex(AssertionError, 'stage ID collision'):
            self.validate()

    def test_inventory_only_goal_mandatory_conversion_and_wrong_dependency_are_rejected(self):
        changes = [('tasks', [self.catalog['quests'][0]['tasks'][1]]),
                   ('required', True), ('after', ['V5_E38_ad_astra_core_rocket_t4'])]
        for field, value in changes:
            with self.subTest(field=field):
                catalog = copy.deepcopy(self.catalog)
                catalog['quests'][0][field] = value
                with self.assertRaises(AssertionError):
                    N.validate(ROOT, catalog=catalog)

    def test_inventory_trigger_or_dispatch_claim_is_rejected(self):
        self.pending['advancement_json'] = {'criteria': {'inventory': {'trigger': 'minecraft:inventory_changed'}}}
        with self.assertRaisesRegex(AssertionError, 'impossible criterion'):
            self.validate()
        self.pending = N.read(ROOT / N.PENDING)
        self.pending['minecraft_dispatch_tested'] = True
        with self.assertRaisesRegex(AssertionError, 'does not certify Minecraft dispatch'):
            self.validate()

    def test_generated_inventory_trigger_is_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            self.fixture(root)
            N.apply(root)
            N.write(root / 'kubejs/data/aia2/advancement/mechanics/nasa_tier_1_rocket.json',
                    {'criteria': {'inventory': {'trigger': 'minecraft:inventory_changed'}}})
            with self.assertRaisesRegex(AssertionError, 'impossible criterion'):
                N.validate(root, compiled=True)


if __name__ == '__main__':
    unittest.main()
