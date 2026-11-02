"""Frozen presentation migration: item evidence is not machine/flight evidence."""
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from tools import build_space_milestones_v11 as S

ROOT = Path(__file__).resolve().parents[1]

# Independent assertions about the published tasks, rather than trusting a new
# title or the migration's own actual_items summary as evidence of completion.
ITEMS = {
    'E37_M1': [('ad_astra:tier_1_rocket', 1, False)],
    'E37_M2': [('ad_astra:desh_ingot', 1, True)],
    'E37_M3': [('botania:life_essence', 1, False)],
    'E37_M4': [('botania:life_essence', 1, True)],
    'E37_M5': [('ad_astra:ostrum_ingot', 1, True)],
    'E37_M6': [('ad_astra:desh_ingot', 2, True), ('botania:life_essence', 2, True),
               ('modern_industrialization:processing_unit', 2, True)],
    'E38_M1': [('ad_astra:tier_3_rocket', 1, False)],
    'E38_M2': [('ad_astra:calorite_ingot', 1, True)],
    'E38_M3': [('ars_nouveau:wilden_tribute', 1, False)],
    'E38_M4': [('ars_nouveau:wilden_tribute', 1, True)],
    'E38_M5': [('ad_astra:ostrum_ingot', 1, True)],
    'E38_M6': [('ad_astra:calorite_ingot', 2, True), ('ars_nouveau:wilden_tribute', 2, True),
               ('powah:crystal_nitro', 2, True)],
}
TITLES = {
    'E37_M1': 'Ракета T1 у розпорядженні',
    'E37_M2': 'Зразок дешу для місячного маршруту',
    'E37_M3': 'Магічний резерв: Дух Ґаї',
    'E37_M4': 'Внесок Духа Ґаї',
    'E37_M5': 'Острамний внесок експедиції',
    'E37_M6': 'Комплект узгодження експедиції',
    'E38_M1': 'Ракета T3 у розпорядженні',
    'E38_M2': 'Калоритовий внесок',
    'E38_M3': 'Трофей Вайлдена для оснастки',
    'E38_M4': 'Магічний внесок Вайлдена',
    'E38_M5': 'Острамний внесок нового ступеня',
    'E38_M6': 'Комплект міжмодової оснастки',
}
BASELINE_HASHES = {
    'E37_M1': 'fdfa70b3de749f0f60755044e3af2acb03b027aa3fc71e4e72186bfc1d1f093b',
    'E37_M2': '8c77f30fb878033b430bdf412931026dc048f44e69b250a482ea677edaa27bf7',
    'E37_M3': '057b26af3db1dd91dd86e074637cba93cf6a8de50597a6a9ccb68a470e9f81ce',
    'E37_M4': '2e466267ba9a75ff023f64be0343bab82097ca6110114c0e050b5c3efabf9a13',
    'E37_M5': 'cd06799db1d6cc5aa19e3542da8d9369d4114ad4e1e5eec2303af894f4074f97',
    'E37_M6': '44b5e5e1960e4ad52a5c7a6f37a32c4726ffefa5d457d6b8ea6c8f5f8b7f53ad',
    'E38_M1': '322f922ae1c69238512602fa121172742a48a26046978d587051d6bc45fe961c',
    'E38_M2': 'c81403a18f268f485220eb450b9a4e28d98f8e14b74956849c11ac31ae8d6ec4',
    'E38_M3': 'de1088142f510ae7efaf874a1010c7f4bb21b8ee30cf47bd35ce99d990cedae1',
    'E38_M4': 'c6547d70b1958b45eef15547eb899f5b560a4882ac18cc5ba9b102db95cf0ad3',
    'E38_M5': 'dd43af6b228e4cb994124aada8873d77bfcb494cef9da692f8e9ae2666314d06',
    'E38_M6': '6b459d424c372072c1ec79a2a0889e097c276082cf54620c9f73b928e8947c1f',
}


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def snapshot(root):
    return {p.relative_to(root).as_posix(): p.read_bytes() for p in root.rglob('*') if p.is_file()}


class SpaceMilestoneTests(unittest.TestCase):
    def setUp(self):
        self.document = read(ROOT / S.SOURCE)

    def fixture(self, root):
        """Use frozen published payloads, independent of concurrent generation."""
        write(root / S.SOURCE, self.document)
        chapters = {}
        for index, row in enumerate(self.document['quests']):
            chapter = chapters.setdefault(row['chapter'], {
                'id': 'KEEP_CHAPTER_' + str(row['epoch']), 'title': 'Наявна глава',
                'custom_chapter_metadata': {'preserve': True},
                'quests': [{'id': 'FOREIGN_' + str(row['epoch']), 'title': 'Інша віха',
                            'tasks': [{'id': 'FOREIGN_TASK', 'type': 'checkmark'}],
                            'foreign_field': ['leave', 'untouched']}],
            })
            quest = copy.deepcopy(row['old_payload'])
            quest.update(x=index * 2.75 - 9, y=(index % 3) * 3.5)
            chapter['quests'].append(quest)
        for relative, chapter in chapters.items():
            write(root / relative, chapter)
        return chapters

    def quest(self, root, logical):
        row = next(row for row in self.document['quests'] if row['logical_id'] == logical)
        path = root / row['chapter']; chapter = read(path)
        quest = next(quest for quest in chapter['quests'] if quest['id'] == row['quest_id'])
        return path, chapter, quest

    def assert_refuses_without_writes(self, root, message=None):
        before = snapshot(root)
        with self.assertRaises(AssertionError) as error:
            S.apply(root)
        if message:
            self.assertIn(message, str(error.exception))
        self.assertEqual(snapshot(root), before)

    def test_published_payload_hashes_and_twelve_item_contracts_are_frozen(self):
        rows = S.source_rows(ROOT)
        self.assertEqual(len(rows), 12)
        self.assertEqual({row['logical_id'] for row in rows}, set(ITEMS))
        for row in rows:
            with self.subTest(logical=row['logical_id']):
                raw = json.dumps(row['old_payload'], ensure_ascii=False, sort_keys=True,
                                 separators=(',', ':')).encode('utf-8')
                digest = hashlib.sha256(raw).hexdigest()
                self.assertEqual(digest, BASELINE_HASHES[row['logical_id']])
                self.assertEqual(row['old_payload_sha256'], digest)
                item_tasks = [task for task in row['old_payload']['tasks'] if task['type'] == 'item']
                actual = [(task['item']['id'], task.get('count', 1), task.get('consume_items', False))
                          for task in item_tasks]
                self.assertEqual(actual, ITEMS[row['logical_id']])
                self.assertTrue(all(not task.get('only_from_crafting', False) for task in item_tasks))
                self.assertEqual(row['scope'], 'resource_submission' if all(t[2] for t in actual)
                                 else 'inventory_presence')

    def test_approved_ukrainian_texts_explain_actual_submission_or_presence(self):
        for row in S.source_rows(ROOT):
            with self.subTest(logical=row['logical_id']):
                text = row['new_presentation']
                self.assertEqual(text['title'], TITLES[row['logical_id']])
                first = text['description'][0]
                if all(consume for _, _, consume in ITEMS[row['logical_id']]):
                    self.assertTrue(first.startswith('Здайте '))
                    self.assertIn('витрача', first)
                else:
                    self.assertTrue(first.startswith('Покажіть '))
                    self.assertRegex(first, r'залишається|зберігається')
                quantity = r'\b(?:один|одну|одного)\b' if ITEMS[row['logical_id']][0][1] == 1 else r'\bдва\b'
                self.assertRegex(first, quantity)
                self.assertEqual(set(text), {'title', 'description'})
                self.assertEqual(len(text['description']), 3)
        row37 = next(row for row in self.document['quests'] if row['logical_id'] == 'E37_M6')
        self.assertIn('два зливки дешу, два Духи Ґаї', row37['new_presentation']['description'][0])
        self.assertIn('два Processing Unit', row37['new_presentation']['description'][0])
        row38 = next(row for row in self.document['quests'] if row['logical_id'] == 'E38_M6')
        self.assertIn('два калоритові зливки, два Wilden Tribute та два Nitro Crystal',
                      row38['new_presentation']['description'][0])

    def test_apply_only_repairs_presentation_and_preserves_all_saved_fields(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); before = self.fixture(root)
            report = S.apply(root)
            self.assertEqual(report['chapter_files_written'], 2)
            self.assertFalse(report['full_pack_run'])
            for counter in ('new_quests', 'new_recipes', 'new_items', 'changed_task_payloads',
                            'changed_reward_payloads', 'changed_dependencies_optional_icons_coordinates'):
                self.assertEqual(report[counter], 0)
            by_id = {row['quest_id']: row for row in self.document['quests']}
            for relative, old_chapter in before.items():
                new_chapter = read(root / relative)
                self.assertEqual({key: value for key, value in old_chapter.items() if key != 'quests'},
                                 {key: value for key, value in new_chapter.items() if key != 'quests'})
                self.assertEqual(len(new_chapter['quests']), len(old_chapter['quests']))
                for old, new in zip(old_chapter['quests'], new_chapter['quests']):
                    if old['id'] not in by_id:
                        self.assertEqual(new, old)
                        continue
                    self.assertEqual({key: value for key, value in new.items() if key not in ('title', 'description')},
                                     {key: value for key, value in old.items() if key not in ('title', 'description')})
                    self.assertEqual(new['title'], by_id[old['id']]['new_presentation']['title'])
                    self.assertEqual(new['description'], by_id[old['id']]['new_presentation']['description'])

    def test_apply_is_byte_idempotent_and_compiled_validation_rejects_old_text(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); self.fixture(root)
            with self.assertRaisesRegex(AssertionError, 'historical misleading presentation'):
                S.validate(root, compiled=True)
            S.apply(root); once = snapshot(root)
            report = S.apply(root)
            self.assertEqual(report['chapter_files_written'], 0)
            self.assertEqual(snapshot(root), once)
            self.assertEqual(S.validate(root, compiled=True)['status'], 'passed')

    def test_late_target_failure_is_validated_before_earlier_chapter_write(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); self.fixture(root)
            path, chapter, quest = self.quest(root, 'E38_M6')
            next(task for task in quest['tasks'] if task['type'] == 'item')['count'] = 200
            write(path, chapter)
            self.assert_refuses_without_writes(root, 'Protected milestone fields changed')

    def test_protected_payload_changes_are_refused(self):
        for field in ('tasks', 'rewards', 'dependencies', 'optional', 'icon', 'unsupported_field'):
            with self.subTest(field=field), tempfile.TemporaryDirectory() as directory:
                root = Path(directory); self.fixture(root)
                path, chapter, quest = self.quest(root, 'E37_M6')
                if field == 'tasks': quest['tasks'][0]['id'] = 'NEW_TASK_ID'
                elif field == 'rewards': quest['rewards'].append({'id': 'NEW_REWARD', 'type': 'xp', 'xp': 100})
                elif field == 'dependencies': quest['dependencies'].append('UNREVIEWED_DEPENDENCY')
                elif field == 'optional': quest['optional'] = not quest.get('optional', False)
                elif field == 'icon': quest['icon'] = {'id': 'minecraft:dirt'}
                else: quest[field] = True
                write(path, chapter)
                self.assert_refuses_without_writes(root, 'Protected milestone fields changed')

    def test_mixed_old_and_new_title_description_are_refused(self):
        for field in ('title', 'description'):
            with self.subTest(field=field), tempfile.TemporaryDirectory() as directory:
                root = Path(directory); self.fixture(root)
                row = self.document['quests'][-1]
                path, chapter, quest = self.quest(root, row['logical_id'])
                quest[field] = copy.deepcopy(row['new_presentation'][field])
                write(path, chapter)
                self.assert_refuses_without_writes(root, 'old or approved new text')

    def test_missing_duplicate_or_wrong_compiled_chapter_refuses_before_writes(self):
        for mutation in ('missing', 'duplicate', 'wrong_chapter'):
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as directory:
                root = Path(directory); self.fixture(root)
                path, chapter, quest = self.quest(root, 'E38_M6')
                if mutation == 'duplicate':
                    chapter['quests'].append(copy.deepcopy(quest))
                else:
                    chapter['quests'].remove(quest)
                    if mutation == 'wrong_chapter':
                        other = root / self.document['quests'][0]['chapter']
                        other_chapter = read(other); other_chapter['quests'].append(quest)
                        write(other, other_chapter)
                write(path, chapter)
                self.assert_refuses_without_writes(root)

    def test_source_cannot_redefine_baseline_even_with_recomputed_hash(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); self.fixture(root)
            document = read(root / S.SOURCE)
            row = document['quests'][-1]; row['old_payload']['rewards'] = []
            row['old_payload_sha256'] = S.canonical(row['old_payload'])
            write(root / S.SOURCE, document)
            self.assert_refuses_without_writes(root, 'Published milestone baseline changed')

    def test_unreviewed_source_identities_scopes_and_fields_are_refused(self):
        for mutation in ('chapter', 'quest_id', 'duplicate', 'missing', 'unsupported_presentation',
                         'item_count', 'item_consumption', 'scope', 'native_dispatch', 'new_quest'):
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as directory:
                root = Path(directory); self.fixture(root)
                document = read(root / S.SOURCE); row = document['quests'][-1]
                if mutation == 'chapter': row['chapter'] = 'config/ftbquests/quests/chapters/aia2_epoch_37.snbt'
                elif mutation == 'quest_id': row['quest_id'] = '0000000000000001'
                elif mutation == 'duplicate': document['quests'][-1] = copy.deepcopy(document['quests'][0])
                elif mutation == 'missing': document['quests'].pop()
                elif mutation == 'unsupported_presentation': row['new_presentation']['optional'] = True
                elif mutation == 'item_count': row['actual_items'][0]['count'] = 1
                elif mutation == 'item_consumption': row['actual_items'][0]['consume_items'] = False
                elif mutation == 'scope': row['scope'] = 'nasa_manufacturing'
                elif mutation == 'native_dispatch': document['native_dispatch_tested'] = True
                else: document['new_quests'] = 1
                write(root / S.SOURCE, document)
                self.assert_refuses_without_writes(root)

    def test_presentation_helper_composes_frozen_legacy_m6_contract_without_mutation(self):
        migration = read(ROOT / 'content/audit/v10-space-required-migration.json')
        row = next(row for row in self.document['quests'] if row['logical_id'] == 'E37_M6')
        legacy = next(quest for quest in migration['legacy_passthrough_payloads'] if quest['id'] == row['quest_id'])
        self.assertEqual(legacy, row['old_payload'])
        original = copy.deepcopy(legacy); legacy.update(x=9.25, y=-7.5)
        expected = S.expected_presentation(legacy['id'], legacy, ROOT)
        self.assertEqual({key: value for key, value in expected.items() if key not in ('title', 'description')},
                         {key: value for key, value in legacy.items() if key not in ('title', 'description')})
        self.assertEqual(expected['title'], TITLES['E37_M6'])
        self.assertEqual(legacy, dict(original, x=9.25, y=-7.5))
        expected['tasks'][0]['id'] = 'MUTATED_RETURN'
        self.assertEqual(legacy['tasks'], original['tasks'])

    def test_unknown_quest_is_an_unchanged_deep_copy(self):
        payload = {'id': 'OTHER', 'tasks': [{'type': 'item', 'item': {'id': 'minecraft:stone'}}]}
        result = S.expected_presentation('OTHER', payload, ROOT)
        self.assertEqual(result, payload)
        result['tasks'][0]['item']['id'] = 'minecraft:dirt'
        self.assertEqual(payload['tasks'][0]['item']['id'], 'minecraft:stone')


if __name__ == '__main__':
    unittest.main()
