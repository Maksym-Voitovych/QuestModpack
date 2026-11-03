"""Authored profile-aware goals use real recipes, without claiming native production."""
import hashlib
import json
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT/'content/quests/v13_cdg_molds.json'
RECIPES = ROOT/'content/research/evidence/create_addons_core_v12/cdg/recipes/createdieselgenerators'
PROFILES = {'createdieselgenerators:'+name for name in ('lines', 'bowl', 'chain', 'bar')}
EPOCHS = {'lines':12, 'bowl':12, 'chain':12, 'bar':15, 'heated_lines':15, 'duroplast':18}


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def signature(tasks):
    return tuple(sorted((task['type'], task.get('item', task.get('block', '')),
                         json.dumps(task.get('components', {}), sort_keys=True),
                         task.get('match_components'), task.get('consume', False), task.get('craft', False))
                        for task in tasks))


class CdgMoldCatalogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.document = read(CATALOG)
        cls.quests = cls.document['quests']
        cls.by_id = {quest['id']: quest for quest in cls.quests}
        cls.runtime = read(ROOT/'kubejs/config/aia2_runtime.json')
        cls.compiled = {quest['id'] for path in (ROOT/'config/ftbquests/quests/chapters').glob('*.snbt')
                        for quest in read(path)['quests']}
        cls.published = {}
        for path in sorted((ROOT/'content/quests').glob('*.json')):
            if path == CATALOG:
                continue
            value = read(path)
            for quest in value if isinstance(value, list) else value.get('quests', []):
                if quest['id'] in cls.published:
                    raise AssertionError('Duplicate old logical quest ID '+quest['id'])
                cls.published[quest['id']] = quest

    def test_six_additive_parallel_profiles_have_meaningful_distinct_applications(self):
        self.assertEqual(self.document['schema'], 1)
        self.assertEqual(len(self.quests), len(self.by_id))
        self.assertEqual(len(self.quests), 6)
        self.assertFalse(set(self.by_id) & set(self.published))
        for slug, epoch in EPOCHS.items():
            quest = self.by_id[f'V13_E{epoch:02d}_cdg_mold_{slug}']
            self.assertEqual(quest['epoch'], epoch)
            self.assertIs(quest['required'], False)
            self.assertEqual(quest['category'], 'automation')
            self.assertEqual(quest['mod'], 'createdieselgenerators')
            self.assertEqual(quest['research_stage'], 'createdieselgenerators.molds_v13.'+slug)
            self.assertEqual(quest['proof_scope'], 'component_profile_and_product_samples')
            self.assertGreaterEqual(len(quest['tasks']), 4)
            self.assertEqual(len(quest['description_uk']), 3)
            self.assertTrue(all(len(line) >= 150 for line in quest['description_uk']))
        parent = ['V12_E12_cdg_panel_tooling']
        for slug, epoch in [('lines',12), ('bowl',12), ('chain',12), ('bar',15)]:
            self.assertEqual(self.by_id[f'V13_E{epoch}_cdg_mold_{slug}']['after'], parent)
        self.assertEqual(self.by_id['V13_E15_cdg_mold_heated_lines']['after'], ['V13_E12_cdg_mold_lines'])
        self.assertEqual(self.by_id['V13_E18_cdg_mold_duroplast']['after'],
                         ['V13_E15_cdg_mold_bar','V5_DEPTH_IMMERSIVEENGINEERING_REFINERY'])

    def test_every_goal_requires_one_exact_resource_location_profile_without_consuming_tool(self):
        observed = []
        for quest in self.quests:
            molds = [task for task in quest['tasks'] if task.get('item') == 'createdieselgenerators:mold']
            self.assertEqual(len(molds), 1)
            task = molds[0]
            self.assertEqual(set(task['components']), {'createdieselgenerators:mold_type'})
            value = task['components']['createdieselgenerators:mold_type']
            self.assertIn(value, PROFILES)
            self.assertEqual(task['match_components'], 'fuzzy')
            self.assertEqual(task['count'], 1)
            self.assertIs(task['consume'], False)
            self.assertIs(task['craft'], False)
            observed.append(value)
        self.assertEqual(set(observed), PROFILES)
        self.assertEqual(observed.count('createdieselgenerators:lines'), 2)
        self.assertEqual(observed.count('createdieselgenerators:bar'), 2)

    def test_profiles_are_real_component_bearing_saw_outputs_not_invented_item_ids(self):
        for name in ('lines','bowl','chain','bar'):
            recipe = read(RECIPES/f'cutting/{name}_mold.json')
            self.assertEqual(recipe['type'], 'create:cutting')
            self.assertEqual(recipe['ingredients'], [{'tag':'c:plates/iron'}])
            self.assertEqual(recipe['results'], [{'id':'createdieselgenerators:mold',
                'components':{'createdieselgenerators:mold_type':'createdieselgenerators:'+name}}])

    def test_component_presence_does_not_pretend_to_be_crafting_or_native_process_proof(self):
        for quest in self.quests:
            self.assertTrue({task['type'] for task in quest['tasks']} <= {'item','observation'})
            for task in quest['tasks']:
                if task['type'] == 'item':
                    self.assertIs(task['craft'], False)
                    self.assertIs(task['consume'], False)
        for ident in ('V13_E15_cdg_mold_bar','V13_E18_cdg_mold_duroplast'):
            blocks = {task['block'] for task in self.by_id[ident]['tasks'] if task['type'] == 'observation'}
            self.assertIn('create:spout', blocks)
            self.assertNotIn('create:mechanical_press', blocks, 'Bar casting is not pressure molding')

    def test_cold_and_heated_compression_products_match_actual_recipe_materials(self):
        cases = {
            'sheet_metal_panel':('lines','createdieselgenerators:sheet_metal_panel',4),
            'bowl':('bowl','minecraft:bowl',1), 'bucket':('bowl','minecraft:bucket',1),
            'chain':('chain','minecraft:chain',1), 'minecart_coupling':('chain','create:minecart_coupling',1),
            'blaze_rod':('lines','minecraft:blaze_rod',1),
        }
        for recipe_name, (profile, product, count) in cases.items():
            recipe = read(RECIPES/f'compression_molding/{recipe_name}.json')
            self.assertEqual(recipe['type'], 'createdieselgenerators:compression_molding')
            self.assertEqual(recipe['mold'], 'createdieselgenerators:'+profile)
            self.assertEqual(recipe['results'][0]['id'], product)
            self.assertEqual(recipe['results'][0].get('count',1), count)
        hot = read(RECIPES/'compression_molding/blaze_rod.json')
        self.assertEqual(hot['heat_requirement'], 'heated')
        self.assertEqual(hot['ingredients'], [{'item':'minecraft:blaze_powder'}]*4)
        self.assertEqual(read(RECIPES/'compression_molding/chain.json')['ingredients'], [{'tag':'c:nuggets/iron'}]*6)
        self.assertEqual(read(RECIPES/'compression_molding/bowl.json')['ingredients'], [{'item':'createdieselgenerators:wood_chip'}]*4)

    def test_bar_uses_real_fluid_casting_recipes_with_two_hundred_fifty_mb(self):
        for relative, output in [('casting/chocolate_bar.json','create:bar_of_chocolate'),
                                 ('compat/immersiveengineering/duroplast_sheet.json','immersiveengineering:plate_duroplast')]:
            recipe = read(RECIPES/relative)
            self.assertEqual(recipe['type'], 'createdieselgenerators:casting')
            self.assertEqual(recipe['mold'], 'createdieselgenerators:bar')
            self.assertEqual(recipe['ingredients'][0]['amount'], 250)
            self.assertEqual(recipe['results'][0]['id'], output)

    def test_all_targets_rewards_and_chosen_recipe_gates_are_available(self):
        keys = {epoch['key'] for epoch in self.runtime['epochs']} | {key['output'] for key in self.runtime['dualKeys']}
        for quest in self.quests:
            self.assertIn(quest['icon'], self.runtime['itemGates'])
            self.assertLessEqual(self.runtime['itemGates'][quest['icon']], quest['epoch'])
            for task in quest['tasks']:
                gates = self.runtime['blockGates'] if task['type'] == 'observation' else self.runtime['itemGates']
                target = task.get('block', task.get('item'))
                self.assertIn(target, gates)
                self.assertLessEqual(gates[target], quest['epoch'])
            for ident in quest['recipe_ids']:
                self.assertIn(ident, self.runtime['recipeGates'])
                self.assertLessEqual(self.runtime['recipeGates'][ident], quest['epoch'])
            self.assertEqual(quest['reward'], [{'item':'createdieselgenerators:wood_chip','count':4}])
            self.assertNotIn(quest['reward'][0]['item'], keys)

    def test_all_dependencies_are_known_reachable_and_never_future(self):
        all_quests = dict(self.published, **self.by_id)
        visited, visiting = set(), set()
        def visit(ident):
            self.assertNotIn(ident, visiting, 'Dependency cycle')
            if ident in visited:
                return
            visiting.add(ident)
            quest = all_quests[ident]
            for parent in quest.get('after', []):
                if parent not in all_quests:
                    match = re.fullmatch(r'E(\d{2})_.+', parent)
                    self.assertIsNotNone(match, 'Unknown dependency '+parent)
                    compiled = hashlib.sha256(('aia2-runtime-v1:'+parent).encode()).hexdigest()[:12].upper().rjust(16,'0')
                    self.assertIn(compiled, self.compiled)
                    all_quests[parent] = {'id':parent,'epoch':int(match[1]),'after':[]}
                self.assertLessEqual(all_quests[parent]['epoch'], quest['epoch'])
                visit(parent)
            visiting.remove(ident);visited.add(ident)
        for ident in self.by_id:
            visit(ident)

    def test_profiles_and_products_are_not_quantity_only_duplicates(self):
        old = {signature(quest['tasks']) for quest in self.published.values()}
        for quest in self.quests:
            current = signature(quest['tasks'])
            self.assertNotIn(current, old)
            old.add(current)


if __name__ == '__main__':
    unittest.main()
