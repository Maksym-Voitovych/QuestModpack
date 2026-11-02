"""The authored v12 course must actually ship as gated, actionable FTB quests."""
import hashlib
import json
from pathlib import Path
import unittest

from tools import build_rewards_v5 as rewards

ROOT = Path(__file__).resolve().parents[1]


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def uid(logical):
    return hashlib.sha256(('aia2-runtime-v1:'+logical).encode()).hexdigest()[:12].upper().rjust(16, '0')


class CompiledCreateAddonTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = read(ROOT/'content/quests/v12_create_addons_course.json')['quests']
        cls.chapters = [read(path) for path in (ROOT/'config/ftbquests/quests/chapters').glob('*.snbt')]
        cls.quests = [quest for chapter in cls.chapters for quest in chapter['quests']]
        cls.by_id = {quest['id']: quest for quest in cls.quests}

    def test_all_fifteen_authored_goals_compile_once_with_epoch_gate_and_dependencies(self):
        self.assertEqual(len(self.catalog), 15)
        for record in self.catalog:
            ident = uid(record['id'])
            self.assertEqual(sum(q['id'] == ident for q in self.quests), 1, record['id'])
            compiled = self.by_id[ident]
            self.assertIs(compiled['optional'], True)
            self.assertTrue(compiled['hide_until_deps_complete'])
            self.assertEqual(compiled['title'], record['title_uk'])
            self.assertIn({'id': uid(record['id']+':stage'), 'type': 'advancement',
                           'advancement': f"aia2:stages/e{record['epoch']:02d}"}, compiled['tasks'])
            self.assertTrue({uid(parent) for parent in record['after']} <= set(compiled['dependencies']))
            self.assertEqual(len(compiled['tasks']), len(record['tasks'])+1)

    def test_eleven_crafted_outputs_use_ftb_craft_events_instead_of_inventory_detection(self):
        crafted = []
        for record in self.catalog:
            compiled = self.by_id[uid(record['id'])]
            tasks = {task['id']: task for task in compiled['tasks']}
            for index, task in enumerate(record['tasks']):
                if task.get('craft'):
                    actual = tasks[uid(record['id']+':task:'+str(index))]
                    self.assertEqual(actual['type'], 'item')
                    self.assertEqual(actual['item']['id'], task['item'])
                    self.assertIs(actual['only_from_crafting'], True)
                    self.assertIs(actual['consume_items'], False)
                    crafted.append(task['item'])
        self.assertEqual(len(crafted), 11)
        self.assertEqual(len(set(crafted)), 11)

    def test_native_electrum_goal_requires_both_receipt_projection_and_separate_output(self):
        quest = self.by_id[uid('V12_E15_cca_electrum_native')]
        native = [task for task in quest['tasks'] if task.get('advancement') == 'aia2:mechanics/cca_electrum_mixing']
        self.assertEqual(len(native), 1)
        item = next(task for task in quest['tasks'] if task['type'] == 'item')
        self.assertEqual(item['item']['id'], 'immersiveengineering:ingot_electrum')
        self.assertEqual(item['count'], 2)
        self.assertIs(item['consume_items'], False)
        self.assertIs(item['only_from_crafting'], False)
        criterion = read(ROOT/'kubejs/data/aia2/advancement/mechanics/cca_electrum_mixing.json')
        self.assertEqual(criterion, {'criteria': {'native_process': {'trigger': 'minecraft:impossible'}}})

    def test_reward_audit_explicitly_knows_v12_mods_and_has_no_free_machine(self):
        known = {q['id'] for _, q in rewards.catalog_records(ROOT)}
        self.assertTrue({q['id'] for q in self.catalog} <= known)
        report = read(ROOT/'implementation/rewards-v5-audit.json')
        decisions = {decision['quest']: decision for decision in report['decisions']}
        for record in self.catalog:
            decision = decisions[uid(record['id'])]
            self.assertEqual(decision['mod'], record['mod'])
            self.assertEqual(decision['profile'], record['mod'])
            self.assertEqual(decision['source'], 'profile')
            self.assertLessEqual(decision['min_epoch'], record['epoch'])
            self.assertLessEqual(decision['count'], 4)
            self.assertEqual(len(self.by_id[uid(record['id'])]['rewards']), 1)


if __name__ == '__main__':
    unittest.main()
