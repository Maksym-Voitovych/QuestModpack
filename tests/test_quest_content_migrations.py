import json
from pathlib import Path
import tempfile
import unittest
from tools.quest_content_migrations import apply, MIGRATIONS


class QuestContentMigrationTest(unittest.TestCase):
    def test_presentation_repair_requires_exact_previous_values(self):
        record={'id':'EXISTING','title_uk':'Стара назва','description_uk':['Старе пояснення'],'icon':'minecraft:stone',
                'tasks':[{'type':'item','item':'minecraft:stone'}],'after':[],'reward':[]}
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);p=root/MIGRATIONS;p.parent.mkdir(parents=True)
            repair={'id':'EXISTING','reason_uk':'Виправлено конкретну ранню ціль на основі точних джерел установленого мода.',
                    'item_targets':[],'presentation_changes':{'title_uk':{'from':'Стара назва','to':'Уточнена назва'}}}
            p.write_text(json.dumps({'schema':1,'quests':[repair]}))
            self.assertEqual(apply([record],root)[0]['title_uk'],'Уточнена назва')
            self.assertEqual(record['title_uk'],'Стара назва')
            repair['presentation_changes']['title_uk']['from']='Інша назва';p.write_text(json.dumps({'schema':1,'quests':[repair]}))
            with self.assertRaisesRegex(AssertionError,'presentation no longer matches'):apply([record],root)

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
