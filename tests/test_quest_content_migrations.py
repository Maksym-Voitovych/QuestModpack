import json
from pathlib import Path
import tempfile
import unittest
from tools.quest_content_migrations import apply, MIGRATIONS


class QuestContentMigrationTest(unittest.TestCase):
    def test_item_repair_keeps_identity_order_and_authored_source(self):
        records = [{'id':'V5_EXISTING','epoch':15,'description_uk':['Потрібна example:unused_book.'],
                    'tasks':[{'type':'item','item':'example:unused_book','count':1,'craft':False}],
                    'after':['E15_M1'],'reward':[{'item':'example:dust','count':2}]}]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); path = root/MIGRATIONS; path.parent.mkdir(parents=True)
            migration = {'id':'V5_EXISTING','reason_uk':'Підтверджено, що початкова книга з нульовою місткістю не має способу отримання.',
                         'item_targets':[{'task_index':0,'from':'example:unused_book','to':'example:copper_book'}],
                         'description_note_uk':'Використовуйте доступну мідну книгу.'}
            path.write_text(json.dumps({'schema':1,'quests':[migration]}))
            result = apply(records, root)
            self.assertEqual(result[0]['id'], records[0]['id'])
            self.assertEqual(result[0]['after'], records[0]['after'])
            self.assertEqual(result[0]['reward'], records[0]['reward'])
            self.assertEqual(result[0]['tasks'][0]['item'], 'example:copper_book')
            self.assertEqual(records[0]['tasks'][0]['item'], 'example:unused_book')
            self.assertIn('example:copper_book', result[0]['description_uk'][0])
            migration['item_targets'][0]['from'] = 'example:wrong_source'
            path.write_text(json.dumps({'schema':1,'quests':[migration]}))
            with self.assertRaisesRegex(AssertionError,'no longer matches'): apply(records,root)
