"""Authored addon course contracts, distinct from native dispatch/client tests.

These checks use portable frozen installed-export recipes and current gate
registries. They do not claim a flow meter, fluid receipt or rolling witness.
"""
import hashlib
import json
import re
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT/'content/quests/v12_create_addons_course.json'
EVIDENCE = ROOT/'content/research/evidence/create_addons_core_v12'
NATIVE_ID = 'V12_E15_cca_electrum_native'


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


class CreateAddonCatalogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.document = read(CATALOG)
        cls.quests = cls.document['quests']
        cls.by_id = {quest['id']: quest for quest in cls.quests}
        cls.runtime = read(ROOT/'kubejs/config/aia2_runtime.json')
        cls.compiled_ids = {quest['id'] for path in (ROOT/'config/ftbquests/quests/chapters').glob('*.snbt')
                            for quest in read(path)['quests']}
        cls.published = {}
        for path in sorted((ROOT/'content/quests').glob('*.json')):
            if path == CATALOG:
                continue
            value = read(path)
            for quest in value if isinstance(value, list) else value['quests']:
                if quest['id'] in cls.published:
                    raise AssertionError('Duplicate published quest '+quest['id'])
                cls.published[quest['id']] = quest

    def test_scope_is_fifteen_additive_optional_goals_with_real_tasks(self):
        self.assertEqual(self.document['schema'], 1)
        self.assertEqual(len(self.quests), len(self.by_id))
        self.assertEqual(len(self.quests), 15)
        self.assertEqual(sum(q['mod'] == 'createaddition' for q in self.quests), 7)
        self.assertEqual(sum(q['mod'] == 'createdieselgenerators' for q in self.quests), 8)
        self.assertFalse(set(self.by_id) & set(self.published))
        for quest in self.quests:
            with self.subTest(quest=quest['id']):
                self.assertIs(quest['required'], False)
                self.assertEqual(quest['category'], 'automation')
                self.assertGreaterEqual(len(quest['tasks']), 2)
                self.assertTrue({t['type'] for t in quest['tasks']} <= {'item', 'observation', 'advancement'})
                self.assertGreaterEqual(len(quest['title_uk']), 20)
                self.assertEqual(len(quest['description_uk']), 3)
                self.assertTrue(all(len(line) >= 100 for line in quest['description_uk']))
                self.assertTrue(quest['research_stage'].startswith(quest['mod']+'.core_v12.'))
                self.assertTrue(quest['after'])

    def test_dependencies_are_known_reachable_and_never_point_to_a_future_epoch(self):
        all_quests = dict(self.published, **self.by_id)
        active, visited = set(), set()

        def visit(ident):
            self.assertNotIn(ident, active, 'New addon dependency cycle')
            if ident in visited:
                return
            active.add(ident)
            quest = all_quests[ident]
            for parent in quest.get('after', []):
                if parent not in all_quests:
                    # Six legacy milestones and key/component anchors are
                    # generated, rather than declared in authored catalogs.
                    match = re.fullmatch(r'E(\d{2})_.+', parent)
                    self.assertIsNotNone(match, 'Unknown dependency '+parent)
                    compiled = hashlib.sha256(('aia2-runtime-v1:'+parent).encode()).hexdigest()[:12].upper().rjust(16, '0')
                    self.assertIn(compiled, self.compiled_ids, 'Missing generated anchor '+parent)
                    all_quests[parent] = {'id': parent, 'epoch': int(match[1]), 'after': []}
                self.assertLessEqual(all_quests[parent]['epoch'], quest['epoch'])
                visit(parent)
            active.remove(ident)
            visited.add(ident)

        for ident in self.by_id:
            visit(ident)
        self.assertTrue(set(self.by_id) <= visited)
        self.assertIn('V12_E12_cdg_seed_oils', self.by_id['V12_E15_cca_biomass_loop']['after'])
        self.assertIn('V12_E11_cca_relay_contacts', self.by_id['V12_E18_cdg_backup_energy']['after'])

    def test_items_icons_observers_and_rewards_have_real_current_epoch_floors(self):
        for quest in self.quests:
            with self.subTest(quest=quest['id']):
                self.assertIn(quest['icon'], self.runtime['itemGates'])
                self.assertLessEqual(self.runtime['itemGates'][quest['icon']], quest['epoch'])
                for task in quest['tasks']:
                    if task['type'] == 'advancement':
                        continue
                    key = 'block' if task['type'] == 'observation' else 'item'
                    registry = self.runtime['blockGates' if key == 'block' else 'itemGates']
                    self.assertIn(task[key], registry)
                    self.assertLessEqual(registry[task[key]], quest['epoch'])
                    if key == 'block':
                        self.assertEqual(task['ticks'], 40)
                    else:
                        self.assertIs(task['consume'], False)
                        self.assertIs(type(task['count']), int)
                        self.assertTrue(1 <= task['count'] <= 10)
                for reward in quest['reward']:
                    self.assertIn(reward['item'], self.runtime['itemGates'])
                    self.assertLessEqual(self.runtime['itemGates'][reward['item']], quest['epoch'])
                    self.assertTrue(1 <= reward['count'] <= 6)
                    self.assertNotIn('epoch_', reward['item'])
                    self.assertNotIn('creative', reward['item'])

    def test_only_exact_vanilla_crafting_outputs_request_crafting_events(self):
        # Independent recipe witnesses: mechanical crafting and machine-only
        # outputs must not accidentally acquire player-crafting predicates.
        witnessed = {
            'createaddition:copper_spool': ('cca', 'createaddition/crafting/copper_spool.json'),
            'createaddition:electrum_spool': ('cca', 'createaddition/crafting/electrum_spool.json'),
            'createaddition:capacitor': ('cca', 'createaddition/crafting/capacitor_1.json'),
            'createaddition:redstone_relay': ('cca', 'createaddition/crafting/redstone_relay.json'),
            'createdieselgenerators:canister': ('cdg', 'createdieselgenerators/crafting/canister.json'),
            'createdieselgenerators:oil_barrel': ('cdg', 'createdieselgenerators/crafting/oil_barrel.json'),
            'createdieselgenerators:basin_lid': ('cdg', 'createdieselgenerators/crafting/basin_lid.json'),
            'createdieselgenerators:bulk_fermenter': ('cdg', 'createdieselgenerators/crafting/bulk_fermenter.json'),
            'createdieselgenerators:engine_piston': ('cdg', 'createdieselgenerators/crafting/engine_piston.json'),
            'createdieselgenerators:engine_silencer': ('cdg', 'createdieselgenerators/crafting/engine_silencer.json'),
            'createdieselgenerators:engine_turbocharger': ('cdg', 'createdieselgenerators/crafting/engine_turbocharger.json'),
        }
        actual = {task['item'] for q in self.quests for task in q['tasks']
                  if task['type'] == 'item' and task['craft']}
        self.assertEqual(actual, set(witnessed))
        for ident, (mod, relative) in witnessed.items():
            recipe = read(EVIDENCE/mod/'recipes'/relative)
            self.assertIn(recipe['type'], {'minecraft:crafting_shaped', 'minecraft:crafting_shapeless'})
            self.assertEqual(recipe['result']['id'], ident)
        for quest in self.quests:
            if any(t.get('craft') for t in quest['tasks']):
                text = ' '.join(quest['description_uk'])
                self.assertIn('після відкриття', text)
                self.assertIn('верстак', text)

    def test_native_electrum_requires_both_durable_provenance_and_current_possession(self):
        quest = self.by_id[NATIVE_ID]
        self.assertEqual(quest['epoch'], 15)
        self.assertEqual(quest['research_stage'], 'createaddition.core_v12.electrum_native')
        self.assertEqual(quest['after'], ['V12_E11_cca_electrum_shapes'])
        self.assertEqual(quest['tasks'], [
            {'type': 'advancement', 'advancement': 'aia2:mechanics/cca_electrum_mixing'},
            {'type': 'item', 'item': 'immersiveengineering:ingot_electrum',
             'count': 2, 'consume': False, 'craft': False},
        ])
        proofs = [(q['id'], t['advancement']) for q in self.quests
                  for t in q['tasks'] if t['type'] == 'advancement']
        self.assertEqual(proofs, [(NATIVE_ID, 'aia2:mechanics/cca_electrum_mixing')])
        text = ' '.join(quest['description_uk'])
        self.assertIn('Creative або /give не створюють', text)
        self.assertIn('не оголошує Blaze Burner єдиним', text)

    def test_reference_samples_do_not_claim_fluid_rolling_or_component_receipts(self):
        allowed_scopes = {'inventory_samples', 'block_observation_and_inventory',
                          'crafting_and_inventory', 'current_machine_owner_team_native_post_consumption'}
        self.assertTrue({q['proof_scope'] for q in self.quests} <= allowed_scopes)
        panel = self.by_id['V12_E12_cdg_panel_tooling']
        self.assertIn('не порівнює компонент mold_type', ' '.join(panel['description_uk']))
        self.assertEqual(next(t for t in panel['tasks'] if t.get('item') == 'createdieselgenerators:mold'),
                         {'type': 'item', 'item': 'createdieselgenerators:mold',
                          'count': 1, 'consume': False, 'craft': False})
        biodiesel = self.by_id['V12_E12_cdg_biodiesel_samples']
        self.assertIn('доказ рідкого виробництва тут не реалізований', ' '.join(biodiesel['description_uk']))
        self.assertFalse(any(t.get('craft') for t in biodiesel['tasks']))
        for ident in ('V12_E11_cca_copper_shapes', 'V12_E11_cca_electrum_shapes'):
            self.assertFalse(any(t.get('craft') for t in self.by_id[ident]['tasks']))

    def test_distillation_stock_respects_controller_batch_and_per_block_cost(self):
        quest = self.by_id['V12_E15_cdg_distillation_samples']
        items = {t['item']: t['count'] for t in quest['tasks'] if t['type'] == 'item'}
        recipe = read(EVIDENCE/'cdg/recipes/createdieselgenerators/crafting/distillation_controller.json')
        self.assertEqual(recipe['result']['count'], 4)
        self.assertEqual(items['createdieselgenerators:distillation_controller'], 4)
        self.assertEqual(items['create:fluid_tank'], 4)
        text = ' '.join(quest['description_uk'])
        self.assertIn('окремий контролер на кожен блок', text)
        self.assertIn('не оголошується комплектом для вежі будь-якого розміру', text)

    def test_new_tasks_do_not_duplicate_an_existing_authored_bundle(self):
        published = {(q['epoch'], json.dumps(q['tasks'], sort_keys=True))
                     for q in self.published.values()}
        for quest in self.quests:
            self.assertNotIn((quest['epoch'], json.dumps(quest['tasks'], sort_keys=True)), published)


if __name__ == '__main__':
    unittest.main()
