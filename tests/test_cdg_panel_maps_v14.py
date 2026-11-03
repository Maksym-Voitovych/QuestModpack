"""One append-only native panel stage; portable hashes pin the complete 0.4.24 map.

No test shells out to Git or treats source-version matches as optional-binary
execution. Baseline canonical hashes were recorded from published 9067fdf.
"""
import hashlib
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
MOD = 'createdieselgenerators'
STAGE = MOD+'.native_v14.panel_compression'
QUEST = 'V14_E12_cdg_panel_native'
PARENT = 'V13_E12_cdg_mold_lines'
RECIPE = MOD+':compression_molding/sheet_metal_panel'
ADVANCEMENT = 'aia2:mechanics/cdg_panel_compression'
MANIFEST = 'content/research/evidence/cdg_panel_native_v14/manifest.json'
MANIFEST_SHA = 'cd16c2ddb9194d47969e3f037bb68403e7c526dce43f3edc1430104cb0e991dd'
OLD_STAGES_SHA = '75ef62a8828a45f6ba93fd649133f62545f141cc6a41e2d6f4ab9320b7e17a02'
OLD_SOURCES_SHA = '8af365cdba3d9330570f899362b7993dd5aa50a340692887c34ff78e5e2ae136'
OLD_OPTIONAL_SHA = '8fea20762e8231f109b4cfa65a4525ab1ebc65474b3c078c95d20e49be3bf251'
PROTECTED_SHA = '317eeee1bcd96b2697294ecc7a583d038e6eccdf43b2e177de7b1990e85d8a50'
OTHER_MODS_SHA = '3837c4f276c2b97baf435dec2586ccab1cd6377c794740c4f64181b90ba4bc61'


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def sha(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
                                     separators=(',', ':')).encode()).hexdigest()


def uid(logical):
    return hashlib.sha256(('aia2-runtime-v1:'+logical).encode()).hexdigest()[:12].upper().rjust(16, '0')


class CdgPanelMapTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.document = read(ROOT/'content/research/technology_v5.json')
        cls.mod = next(mod for mod in cls.document['mods'] if mod['mod_id'] == MOD)
        cls.catalog = read(ROOT/'content/quests/v14_cdg_panel_native.json')['quests']
        cls.quest = cls.catalog[0]
        cls.stage = next(stage for stage in cls.mod['stages'] if stage['id'] == STAGE)
        cls.manifest = read(ROOT/MANIFEST)

    def test_all_thirty_old_stage_payloads_and_order_remain_exact(self):
        self.assertEqual(len(self.mod['stages']), 31)
        self.assertEqual(sha(self.mod['stages'][:30]), OLD_STAGES_SHA)
        self.assertEqual(self.mod['stages'][30:], [self.stage])
        self.assertEqual(sum(stage['id'] == STAGE for stage in self.mod['stages']), 1)

    def test_all_old_sources_optional_ids_metadata_and_other_mods_are_preserved(self):
        self.assertEqual(len(self.mod['sources']), 234)
        self.assertEqual(sha(self.mod['sources'][:227]), OLD_SOURCES_SHA)
        self.assertEqual(len(self.mod['optional_quest_ids']), 30)
        self.assertEqual(sha(self.mod['optional_quest_ids'][:29]), OLD_OPTIONAL_SHA)
        self.assertEqual(self.mod['optional_quest_ids'][29:], [QUEST])
        protected = {key: value for key, value in self.mod.items()
                     if key not in {'stages', 'sources', 'optional_quest_ids'}}
        self.assertEqual(sha(protected), PROTECTED_SHA)
        self.assertEqual(sha([mod for mod in self.document['mods'] if mod['mod_id'] != MOD]),
                         OTHER_MODS_SHA)

    def test_exact_six_create_source_files_and_manifest_are_portable_and_hash_verified(self):
        self.assertEqual(hashlib.sha256((ROOT/MANIFEST).read_bytes()).hexdigest(), MANIFEST_SHA)
        self.assertEqual(self.manifest['schema'], 1)
        self.assertEqual(self.manifest['mod_id'], 'create')
        self.assertEqual(self.manifest['source_version'], '6.0.10')
        self.assertEqual(self.manifest['source_pin'], 'ac0c444d9828da3453ae8cc65338e8de063286fb')
        self.assertIs(self.manifest['source_version_matches'], True)
        self.assertIs(self.manifest['installed_binary_equivalence_verified'], False)
        self.assertIs(self.manifest['full_client_tested'], False)
        self.assertEqual(len(self.manifest['files']), 6)
        expected = {entry['path']: entry['sha256'] for entry in self.manifest['files']}
        self.assertEqual(len(expected), 6)
        expected[MANIFEST] = MANIFEST_SHA
        appended = self.mod['sources'][227:]
        self.assertEqual(len(appended), 7)
        self.assertEqual({entry['path']: entry['sha256'] for entry in appended}, expected)
        for entry in appended:
            relative = Path(entry['path'])
            self.assertFalse(relative.is_absolute())
            self.assertNotIn('..', relative.parts)
            self.assertTrue((ROOT/relative).resolve().is_relative_to(ROOT.resolve()))
            self.assertEqual(hashlib.sha256((ROOT/relative).read_bytes()).hexdigest(), entry['sha256'])
            self.assertIs(entry['verified'], True)

    def test_native_stage_matches_one_optional_goal_and_known_profile_prerequisite(self):
        self.assertEqual([quest['id'] for quest in self.catalog], [QUEST])
        self.assertEqual(self.quest['research_stage'], STAGE)
        self.assertEqual(self.stage['new_quest_ids'], [QUEST])
        self.assertEqual(self.stage['epoch'], self.quest['epoch'])
        self.assertEqual(self.stage['epoch'], 12)
        self.assertEqual(self.quest['after'], [PARENT])
        self.assertEqual(self.stage['prerequisites'], [MOD+'.molds_v13.lines'])
        self.assertEqual(self.stage['external_quest_prerequisites'], [])
        self.assertFalse(self.stage.get('external_research_prerequisites', []))
        self.assertIs(self.quest['required'], False)
        self.assertEqual(self.stage['proof_scope'], self.quest['proof_scope'])
        self.assertEqual(self.stage['proof_scope'], 'current_owned_basin_successful_native_apply_not_simulation')
        parent = next(stage for stage in self.mod['stages']
                      if stage['id'] == self.stage['prerequisites'][0])
        self.assertEqual(parent['new_quest_ids'], [PARENT])
        self.assertLessEqual(parent['epoch'], self.stage['epoch'])
        self.assertEqual(parent['proof_scope'], 'component_profile_and_product_samples')
        self.assertNotIn('component_predicates', self.stage,
                         'The new native proof must not replace the old inventory predicate')

    def test_native_stage_has_exact_original_recipe_witness_and_available_machines(self):
        self.assertEqual(self.stage['recipe_ids'], [RECIPE])
        self.assertEqual(self.quest['recipe_ids'], [RECIPE])
        self.assertEqual(len(self.stage['recipe_evidence']), 1)
        witness = self.stage['recipe_evidence'][0]
        self.assertEqual(witness['recipe_id'], RECIPE)
        self.assertEqual(witness['type'], MOD+':compression_molding')
        self.assertEqual(witness['path'], 'content/research/evidence/cdg_molds_v13/recipes/'
                         'createdieselgenerators/compression_molding/sheet_metal_panel.json')
        raw = (ROOT/witness['path']).read_bytes()
        self.assertEqual(hashlib.sha256(raw).hexdigest(), witness['sha256'])
        self.assertEqual(witness['sha256'], '9841618670e0a89bea6788df3d213a8acb60849c3c5430b91b89ffa78a138d3b')
        self.assertEqual(json.loads(raw), {
            'type': MOD+':compression_molding', 'ingredients': [{'tag': 'c:plates/iron'}],
            'mold': MOD+':lines', 'results': [{'id': MOD+':sheet_metal_panel', 'count': 4}]})
        self.assertEqual(set(self.stage['machine_ids']), {'create:mechanical_press', 'create:basin'})
        runtime = read(ROOT/'kubejs/config/aia2_runtime.json')
        for item in self.stage['item_ids']:
            self.assertLessEqual(runtime['itemGates'][item], self.stage['epoch'])
        for machine in self.stage['machine_ids']:
            self.assertLessEqual(runtime['blockGates'][machine], self.stage['epoch'])
        self.assertLessEqual(runtime['recipeGates'][RECIPE], self.stage['epoch'])

    def test_compiled_native_goal_is_unique_gated_and_keeps_profile_goal_separate(self):
        all_quests = [quest for path in sorted((ROOT/'config/ftbquests/quests/chapters').glob('*.snbt'))
                      for quest in read(path)['quests']]
        goals = [quest for quest in all_quests if quest['id'] == uid(QUEST)]
        self.assertEqual(len(goals), 1, 'Native panel goal must actually ship exactly once')
        goal = goals[0]
        self.assertEqual(goal['title'], self.quest['title_uk'])
        self.assertIs(goal['optional'], True)
        self.assertIs(goal['hide_until_deps_complete'], True)
        self.assertIn(uid(PARENT), goal['dependencies'])
        self.assertEqual(len(goal['tasks']), 3)
        self.assertIn({'id': uid(QUEST+':stage'), 'type': 'advancement',
                       'advancement': 'aia2:stages/e12'}, goal['tasks'])
        self.assertIn({'id': uid(QUEST+':task:0'), 'type': 'advancement',
                       'advancement': ADVANCEMENT}, goal['tasks'])
        inventory = next(task for task in goal['tasks'] if task['type'] == 'item')
        self.assertEqual(inventory['id'], uid(QUEST+':task:1'))
        self.assertEqual(inventory['item'], {'id': MOD+':sheet_metal_panel', 'count': 1})
        self.assertEqual(inventory['count'], 4)
        self.assertIs(inventory['consume_items'], False)
        self.assertIs(inventory['only_from_crafting'], False)
        self.assertEqual(read(ROOT/'kubejs/data/aia2/advancement/mechanics/cdg_panel_compression.json'),
                         {'criteria': {'native_process': {'trigger': 'minecraft:impossible'}}})


if __name__ == '__main__':
    unittest.main()
