"""Source/runtime/FTB requirement overlays; no full-modpack dispatch claim."""
import copy
import json
from pathlib import Path
import shutil
import tempfile
import unittest

from tools import build_required_space_v10 as S
from tools import quest_content_migrations as M

ROOT = Path(__file__).resolve().parents[1]


class RequiredSpaceTests(unittest.TestCase):
    def setUp(self):
        self.migration = S.read(ROOT / S.MIGRATION)
        self.runtime = S.read(ROOT / S.RUNTIME)

    def fixture(self, root, compiled=False):
        shutil.copytree(ROOT / 'content/quests', root / 'content/quests')
        paths = [S.MIGRATION, S.OVERLAYS, S.RUNTIME, S.nasa.MECHANICS,
                 S.nasa.PENDING, S.nasa.RESEARCH, self.migration['ftb_progress_evidence']['path']]
        pending = S.read(ROOT / S.nasa.PENDING)
        paths += [entry['frozen_path'] for rule in pending['mechanic_rules'] for entry in rule['evidence']]
        for relative in paths:
            target = root / relative; target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / relative, target)
        if compiled:
            shutil.copytree(ROOT / 'config/ftbquests/quests/chapters',
                            root / 'config/ftbquests/quests/chapters')
            for planet in ('earth', 'moon', 'mars', 'mercury', 'venus', 'glacio'):
                relative = f'kubejs/data/aia2/advancement/stations/{planet}_orbit.json'
                target = root / relative; target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(ROOT / relative, target)
            for tier in range(1, 5):
                relative = f'kubejs/data/aia2/advancement/mechanics/nasa_tier_{tier}_rocket.json'
                target = root / relative; target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(ROOT / relative, target)

    def validate(self):
        return S.validate(ROOT, migration=self.migration, runtime=self.runtime)

    def compiled_fixture(self, root):
        self.fixture(root, compiled=True)
        chapters = {path: S.read(path) for path in (root / 'config/ftbquests/quests/chapters').glob('*.snbt')}
        quests = {q['id']: q for chapter in chapters.values() for q in chapter['quests']}
        runtime = S.read(root / S.RUNTIME)
        for row in self.migration['quests']:
            actual = quests[row['compiled_id']]
            expected = copy.deepcopy(row['old_compiled_payload'])
            expected['optional'] = False
            expected['description'].append(row['description_note_uk'])
            expected.update({k: actual[k] for k in ('x', 'y') if k in actual})
            actual.clear(); actual.update(expected)
            epoch = runtime['epochs'][row['epoch'] - 1]
            if row['compiled_id'] not in epoch['branchQuestIds']['tech']:
                epoch['branchQuestIds']['tech'].append(row['compiled_id'])
            trial = quests[S.uid(f"E{row['epoch']:02d}_EXPANSION_TRIAL")]
            if row['compiled_id'] not in trial['dependencies']:
                trial['dependencies'].append(row['compiled_id'])
        for ident in self.migration['promoted_compiled_quest_ids']:
            quests[ident]['optional'] = False
        for path, chapter in chapters.items():
            path.write_text(json.dumps(chapter, ensure_ascii=False))
        (root / S.RUNTIME).write_text(json.dumps(runtime, ensure_ascii=False))
        S.apply(root)
        return chapters, quests

    def test_four_existing_goals_use_source_verified_native_proofs(self):
        report = self.validate()
        self.assertEqual(report['migrated_existing_nasa_goals'], 4)
        self.assertEqual(report['promoted_required_prerequisite_closure'], 21)
        self.assertEqual(report['replaced_tasks'], 0)
        self.assertEqual(report['new_quests'], 0)
        self.assertEqual(report['new_recipes'], 0)
        self.assertGreater(report['nasa_recipe_input_alternatives'], 14)
        self.assertEqual(report['native_dispatch_fullpack'], 'NOT_RUN')

    def test_authored_catalog_and_tasks_are_preserved_by_requirement_overlay(self):
        records = []
        for path in sorted((ROOT / 'content/quests').glob('*.json')):
            data = S.read(path); records.extend(data if isinstance(data, list) else data['quests'])
        by_id = {q['id']: q for q in records}
        effective = {q['id']: q for q in M.apply(records, ROOT)}
        for row in self.migration['quests']:
            old, new = by_id[row['quest_id']], effective[row['quest_id']]
            self.assertFalse(old['required']); self.assertTrue(new['required'])
            self.assertEqual(new['tasks'], old['tasks'])
            self.assertEqual(new['after'], old['after'])
            self.assertEqual(new['reward'], old['reward'])
            self.assertEqual(new['description_uk'], old['description_uk'] + [row['description_note_uk']])

    def test_wrong_epoch_proof_mapping_and_future_rules_are_rejected(self):
        self.migration['branch_action_proofs']['37']['tech'] = ['nasa_tier_3_rocket']
        with self.assertRaisesRegex(AssertionError, 'proof mapping'):
            self.validate()
        self.migration = S.read(ROOT / S.MIGRATION)
        self.runtime['recipeGates']['ad_astra:nasa_workbench/tier_1_rocket_from_nasa_workbench'] = 38
        with self.assertRaisesRegex(AssertionError, 'Future NASA output or recipe'):
            self.validate()

    def test_cannot_add_station_proofs_to_required_contract(self):
        self.migration['branch_action_proofs']['37']['tech'].append('station_earth_orbit')
        with self.assertRaisesRegex(AssertionError, 'proof mapping'):
            self.validate()

    def test_cannot_turn_source_validation_into_dispatch_or_new_content_claim(self):
        for field, value in [('new_quests', 1), ('new_recipes', 1), ('native_dispatch_tested', True)]:
            with self.subTest(field=field):
                old = self.migration[field]; self.migration[field] = value
                with self.assertRaises(AssertionError): self.validate()
                self.migration[field] = old

    def test_paid_pending_and_completed_progress_policy_is_fixed(self):
        for field in ('old_without_pendingActionContract', 'new_space_pendingActionContract', 'completed_epochs_and_recovery'):
            with self.subTest(field=field):
                old = self.migration['pending_policy'][field]
                self.migration['pending_policy'][field] = 'reset'
                with self.assertRaisesRegex(AssertionError, 'pending compatibility'): self.validate()
                self.migration['pending_policy'][field] = old

    def test_other_forty_six_epochs_cannot_receive_space_contract(self):
        self.runtime['epochs'][0]['branchActionProofs'] = copy.deepcopy(S.EXPECTED[37])
        with self.assertRaisesRegex(AssertionError, 'other forty-six'): self.validate()

    def test_wrong_runtime_branch_or_missing_receipt_is_rejected(self):
        self.runtime['epochs'][36]['branchActionProofs'] = {'tech': [], 'arcane': ['nasa_tier_1_rocket']}
        with self.assertRaisesRegex(AssertionError, 'runtime mapping'): self.validate()

    def test_published_raw_catalog_and_stable_ids_are_frozen(self):
        self.migration['raw_catalog_sha256'] = '0' * 64
        with self.assertRaisesRegex(AssertionError, 'raw NASA catalog'): self.validate()
        self.migration = S.read(ROOT / S.MIGRATION)
        self.migration['quests'][0]['compiled_id'] = '0000000000000001'
        with self.assertRaisesRegex(AssertionError, 'compiled NASA ID'): self.validate()

    def test_duplicate_missing_or_changed_goal_is_rejected(self):
        for mutation in ('duplicate', 'missing', 'changed'):
            with self.subTest(mutation=mutation):
                doc = copy.deepcopy(self.migration)
                if mutation == 'duplicate': doc['quests'][1] = copy.deepcopy(doc['quests'][0])
                elif mutation == 'missing': doc['quests'].pop()
                else: doc['quests'][0]['raw_quest_sha256'] = '0' * 64
                with self.assertRaises(AssertionError): S.validate(ROOT, migration=doc)

    def test_apply_writes_only_two_epoch_fields_and_is_idempotent(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); self.fixture(root)
            before = {p.relative_to(root).as_posix(): p.read_bytes() for p in root.rglob('*') if p.is_file()}
            old = S.read(root / S.RUNTIME)
            for epoch in old['epochs']: epoch.pop('branchActionProofs', None)
            (root / S.RUNTIME).write_text(json.dumps(old))
            before[S.RUNTIME] = (root / S.RUNTIME).read_bytes()
            S.apply(root)
            once = {p.relative_to(root).as_posix(): p.read_bytes() for p in root.rglob('*') if p.is_file()}
            S.apply(root)
            twice = {p.relative_to(root).as_posix(): p.read_bytes() for p in root.rglob('*') if p.is_file()}
            self.assertEqual(once, twice)
            for path, data in before.items():
                if path != S.RUNTIME: self.assertEqual(once[path], data, path)
            expected = copy.deepcopy(old)
            for epoch in expected['epochs']:
                if epoch['number'] in S.EXPECTED: epoch['branchActionProofs'] = S.EXPECTED[epoch['number']]
            self.assertEqual(S.read(root / S.RUNTIME), expected)

    def test_missing_or_altered_requirement_overlay_rejected_before_any_write(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); self.fixture(root)
            overlays = S.read(root / S.OVERLAYS)
            own = next(row for row in overlays['quests'] if row.get('source_audit') == S.MIGRATION)
            own['requirement_change']['to'] = False
            (root / S.OVERLAYS).write_text(json.dumps(overlays))
            before = (root / S.RUNTIME).read_bytes()
            with self.assertRaisesRegex(AssertionError, 'false-to-true'):
                S.apply(root)
            self.assertEqual((root / S.RUNTIME).read_bytes(), before)

    def test_effective_compiled_requirements_preserve_payloads_and_station_optionality(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); self.compiled_fixture(root)
            report = S.validate(root, compiled=True)
            self.assertEqual(report['migrated_existing_nasa_goals'], 4)
            self.assertEqual(report['station_goals_still_optional'], 6)

    def test_replacing_old_task_type_or_id_is_rejected(self):
        for mutation in ('type', 'id', 'reward'):
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as directory:
                root = Path(directory); chapters, quests = self.compiled_fixture(root)
                qid = self.migration['quests'][0]['compiled_id']; quest = quests[qid]
                if mutation == 'type': quest['tasks'][0] = {'id': quest['tasks'][0]['id'], 'type': 'checkmark'}
                elif mutation == 'id': quest['tasks'][0]['id'] = '0000000000000001'
                else: quest['rewards'][0]['count'] = 64
                for path, chapter in chapters.items():
                    if any(q['id'] == qid for q in chapter['quests']): path.write_text(json.dumps(chapter))
                with self.assertRaisesRegex(AssertionError, 'changed a task, ID, reward or dependency'):
                    S.validate(root, compiled=True)

    def test_station_cannot_become_required_through_this_overlay(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); chapters, quests = self.compiled_fixture(root)
            qid = S.uid('V9_E37_station_earth_orbit'); quests[qid]['optional'] = False
            for path, chapter in chapters.items():
                if any(q['id'] == qid for q in chapter['quests']): path.write_text(json.dumps(chapter))
            with self.assertRaisesRegex(AssertionError, 'Station construction must remain optional'):
                S.validate(root, compiled=True)

    def test_new_required_ancestor_cycle_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); chapters, quests = self.compiled_fixture(root)
            qid = S.uid('V5_E37_ad_astra_core_ground_workshop')
            quests[qid]['dependencies'].append(self.migration['quests'][0]['compiled_id'])
            for path, chapter in chapters.items():
                if any(q['id'] == qid for q in chapter['quests']): path.write_text(json.dumps(chapter))
            with self.assertRaisesRegex(AssertionError, 'dependency cycle'):
                S.validate(root, compiled=True)

    def test_changed_progress_evidence_is_rejected_before_runtime_write(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); self.fixture(root)
            path = root / self.migration['ftb_progress_evidence']['path']
            path.write_bytes(path.read_bytes() + b'\n')
            before = (root / S.RUNTIME).read_bytes()
            with self.assertRaisesRegex(AssertionError, 'Changed FTB migration evidence'):
                S.apply(root)
            self.assertEqual((root / S.RUNTIME).read_bytes(), before)

    def test_later_course_required_goal_is_linked_to_its_own_terminal_trial(self):
        ident = S.uid('V5_E37_ad_astra_core_mars_sensor')
        t37, t38 = (S.uid(f'E{n}_EXPANSION_TRIAL') for n in (37, 38))
        quests = {ident: {'id': ident, 'dependencies': [], 'tasks': [{'id': 'unchanged'}]},
                  t37: {'id': t37, 'dependencies': []}, t38: {'id': t38, 'dependencies': [ident]}}
        records = [{'id': 'V5_E37_ad_astra_core_mars_sensor', 'epoch': 37}]
        self.assertEqual(S.link_current_promoted(quests, records, ROOT), [37])
        self.assertEqual(quests[t37]['dependencies'], [ident])
        self.assertEqual(quests[t38]['dependencies'], [ident])
        self.assertEqual(quests[ident]['tasks'], [{'id': 'unchanged'}])
        self.assertEqual(S.link_current_promoted(quests, records, ROOT), [])

    def test_trial_link_update_preserves_unrelated_legacy_quest_representation(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); chapters, quests = self.compiled_fixture(root)
            qid = S.uid('E37_M6')
            self.assertNotIn('optional', quests[qid])
            quests[qid]['optional'] = False
            for path, chapter in chapters.items():
                if any(q['id'] == qid for q in chapter['quests']): path.write_text(json.dumps(chapter))
            with self.assertRaisesRegex(AssertionError, 'Unrelated legacy space quest changed'):
                S.validate(root, compiled=True)


if __name__ == '__main__':
    unittest.main()
