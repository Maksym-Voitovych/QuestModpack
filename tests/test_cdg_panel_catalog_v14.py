"""One meaningful panel-production goal; no replacement of older profile checks."""
import hashlib
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT/'content/quests/v14_cdg_panel_native.json'
RECIPE = ROOT/('content/research/evidence/cdg_molds_v13/recipes/'
               'createdieselgenerators/compression_molding/sheet_metal_panel.json')
QUEST_ID = 'V14_E12_cdg_panel_native'
ADVANCEMENT = 'aia2:mechanics/cdg_panel_compression'
RECIPE_ID = 'createdieselgenerators:compression_molding/sheet_metal_panel'


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


class CdgPanelCatalogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.document = read(CATALOG)
        cls.quest = cls.document['quests'][0]
        cls.runtime = read(ROOT/'kubejs/config/aia2_runtime.json')
        cls.old = {}
        for path in sorted((ROOT/'content/quests').glob('*.json')):
            if path == CATALOG:
                continue
            value = read(path)
            for quest in value if isinstance(value, list) else value.get('quests', []):
                if quest['id'] in cls.old:
                    raise AssertionError('Duplicate old logical quest ID '+quest['id'])
                cls.old[quest['id']] = quest

    def test_one_new_optional_goal_after_exact_profile_without_key_changes(self):
        self.assertEqual(self.document['schema'], 1)
        self.assertEqual(len(self.document['quests']), 1)
        self.assertEqual(self.quest['id'], QUEST_ID)
        self.assertNotIn(QUEST_ID, self.old)
        self.assertIs(self.quest['required'], False)
        self.assertEqual(self.quest['epoch'], 12)
        self.assertEqual(self.quest['category'], 'automation')
        self.assertEqual(self.quest['mod'], 'createdieselgenerators')
        self.assertEqual(self.quest['after'], ['V13_E12_cdg_mold_lines'])
        self.assertEqual(self.quest['research_stage'], 'createdieselgenerators.native_v14.panel_compression')
        parent = self.old[self.quest['after'][0]]
        self.assertEqual(parent['epoch'], 12)
        self.assertEqual(parent['proof_scope'], 'component_profile_and_product_samples')
        self.assertFalse(any(task['type'] == 'advancement' for task in parent['tasks']))
        self.assertEqual(len(self.runtime['epochs']), 48)
        self.assertEqual(len(self.runtime['dualKeys']), 96)

    def test_native_proof_and_inventory_are_distinct_real_tasks(self):
        self.assertEqual(self.quest['proof_scope'], 'current_owned_basin_successful_native_apply_not_simulation')
        self.assertEqual(self.quest['tasks'], [
            {'type': 'advancement', 'advancement': ADVANCEMENT},
            {'type': 'item', 'item': 'createdieselgenerators:sheet_metal_panel',
             'count': 4, 'consume': False, 'craft': False},
        ])
        self.assertEqual(self.quest['icon'], 'createdieselgenerators:sheet_metal_panel')
        # New proof differs from every old quest even if output item/count coincide.
        for old in self.old.values():
            self.assertNotEqual(old.get('tasks'), self.quest['tasks'])

    def test_exported_recipe_is_exact_cold_lines_process_with_guaranteed_four_panels(self):
        raw = RECIPE.read_bytes()
        self.assertEqual(hashlib.sha256(raw).hexdigest(),
                         '9841618670e0a89bea6788df3d213a8acb60849c3c5430b91b89ffa78a138d3b')
        self.assertEqual(json.loads(raw), {
            'type': 'createdieselgenerators:compression_molding',
            'ingredients': [{'tag': 'c:plates/iron'}],
            'mold': 'createdieselgenerators:lines',
            'results': [{'id': 'createdieselgenerators:sheet_metal_panel', 'count': 4}],
        })
        self.assertEqual(self.quest['recipe_ids'], [RECIPE_ID])

    def test_chosen_producers_materials_outputs_and_reward_do_not_require_future_epoch(self):
        targets = {
            'itemGates': ('create:mechanical_press', 'create:basin', 'createdieselgenerators:mold',
                          'immersiveengineering:plate_iron', 'createdieselgenerators:sheet_metal_panel',
                          'createdieselgenerators:wood_chip'),
            'blockGates': ('create:mechanical_press', 'create:basin'),
            'recipeGates': (RECIPE_ID, 'createdieselgenerators:cutting/lines_mold'),
        }
        for category, identities in targets.items():
            for ident in identities:
                self.assertIn(ident, self.runtime[category])
                self.assertLessEqual(self.runtime[category][ident], self.quest['epoch'])
        self.assertEqual(self.runtime['recipeGates'][RECIPE_ID], 12)
        self.assertNotIn(RECIPE_ID, read(ROOT/'kubejs/config/aia2_recipes.json')['remove'])
        self.assertEqual(self.quest['reward'], [{'item': 'createdieselgenerators:wood_chip', 'count': 4}])
        keys = {epoch['key'] for epoch in self.runtime['epochs']}
        keys.update(key['output'] for key in self.runtime['dualKeys'])
        self.assertNotIn(self.quest['reward'][0]['item'], keys)
        self.assertNotIn(self.quest['reward'][0]['item'], targets['blockGates'])

    def test_ukrainian_explanation_teaches_recipe_profile_owner_and_proof_limits(self):
        self.assertGreater(len(self.quest['title_uk']), 20)
        self.assertEqual(len(self.quest['description_uk']), 3)
        self.assertTrue(all(len(line) >= 200 for line in self.quest['description_uk']))
        text = ' '.join(self.quest['description_uk'])
        for fragment in ('Mechanical Press', 'Basin', 'Lines', 'c:plates/iron',
                         'Нагрівання', 'останній Mold', 'вашої команди', 'епохи12',
                         'витрати матеріалу', 'прийняття виходу', '/give', 'симуляція', 'двох ключів'):
            self.assertIn(fragment, text)


if __name__ == '__main__':
    unittest.main()
