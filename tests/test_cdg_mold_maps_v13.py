"""Append-only Mold research maps, with a portable 0.4.23 preservation contract.

These checks concern source/quest/map data; optional mod dispatch, profile
rendering, ItemStack CODEC behavior and FTB UI require their separate tests.
"""
import hashlib
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
MOD = 'createdieselgenerators'
PREFIX = 'content/research/evidence/cdg_molds_v13/'
OTHER_MODS_SHA = '3837c4f276c2b97baf435dec2586ccab1cd6377c794740c4f64181b90ba4bc61'
OLD_STAGES_SHA = '1967df3aef6dedcb758165352435d7b85046c990958c169a823e5be9a3fd214f'
OLD_FIELDS_SHA = 'd495e57c1ab5bb53985c2e68e94c11e50cb060ba53671a8bd4d313ff919c1eb0'
OLD_SOURCES_SHA = '8038fc9f84919290ed2b3d776c563fa47c790c13b0b852212b9b53e76c15d534'
OLD_V12_CATALOG_SHA = '2d5befc8e81823a8b97a7f6abb7284f99242141666ec58849051f1e28c50be54'
SPECS = {
    'V13_E12_cdg_mold_lines': ('lines', 12, 'lines'),
    'V13_E12_cdg_mold_bowl': ('bowl', 12, 'bowl'),
    'V13_E12_cdg_mold_chain': ('chain', 12, 'chain'),
    'V13_E15_cdg_mold_bar': ('bar', 15, 'bar'),
    'V13_E15_cdg_mold_heated_lines': ('heated_lines', 15, 'lines'),
    'V13_E18_cdg_mold_duroplast': ('duroplast', 18, 'bar'),
}
APPROVED_V14_STAGE = 'createdieselgenerators.native_v14.panel_compression'
APPROVED_V14_QUEST = 'V14_E12_cdg_panel_native'
# Historical v13 checks exclude only seven reviewed additions, not every path
# under a prefix. The v14 tests independently pin the complete old projection.
APPROVED_V14_SOURCES = frozenset({
    'content/research/evidence/cdg_panel_native_v14/create/LICENSE.md',
    'content/research/evidence/cdg_panel_native_v14/create/gradle.properties',
    'content/research/evidence/cdg_panel_native_v14/create/src/main/java/com/simibubi/create/content/processing/recipe/ProcessingRecipeParams.java',
    'content/research/evidence/cdg_panel_native_v14/create/src/main/java/com/simibubi/create/content/processing/recipe/ProcessingOutput.java',
    'content/research/evidence/cdg_panel_native_v14/create/src/main/java/com/simibubi/create/content/processing/recipe/ProcessingRecipe.java',
    'content/research/evidence/cdg_panel_native_v14/create/src/main/java/com/simibubi/create/content/kinetics/mixer/CompactingRecipe.java',
    'content/research/evidence/cdg_panel_native_v14/manifest.json',
})


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def sha(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
                                     separators=(',', ':')).encode()).hexdigest()


def links(mod):
    return {qid: stage for stage in mod['stages']
            for qid in stage.get('existing_quest_ids', []) + stage.get('new_quest_ids', [])}


def v13_stages(mod):
    return [stage for stage in mod['stages'] if stage['id'] != APPROVED_V14_STAGE]


def v13_sources(mod):
    return [source for source in mod['sources'] if source['path'] not in APPROVED_V14_SOURCES]


def v13_optional_quests(mod):
    return [qid for qid in mod['optional_quest_ids'] if qid != APPROVED_V14_QUEST]


class CdgMoldMapTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.document = read(ROOT/'content/research/technology_v5.json')
        cls.mod = next(mod for mod in cls.document['mods'] if mod['mod_id'] == MOD)
        cls.audit = read(ROOT/'content/audit/v13-cdg-mold-map-preservation.json')
        cls.catalog = read(ROOT/'content/quests/v13_cdg_molds.json')['quests']
        cls.quests = {q['id']: q for q in cls.catalog}
        cls.stage_map = {stage['id']: stage for stage in cls.mod['stages']}
        cls.manifest = read(ROOT/(PREFIX+'manifest.json'))

    def test_all_other_mod_records_and_protected_cdg_metadata_match_published_checkpoint(self):
        self.assertEqual(sha([mod for mod in self.document['mods'] if mod['mod_id'] != MOD]), OTHER_MODS_SHA)
        mutable = {'stages', 'sources', 'optional_quest_ids', 'coverage_v13', 'quest_dependency_contract_v13'}
        protected = {key: value for key, value in self.mod.items() if key not in mutable}
        self.assertEqual(sha(protected), OLD_FIELDS_SHA)
        self.assertEqual(self.audit['other_mod_records_sha256'], OTHER_MODS_SHA)
        self.assertEqual(self.audit['old_mod_protected_fields_sha256'], OLD_FIELDS_SHA)
        self.assertEqual(self.audit['baseline'], '2a0dcdd541a904a4627fb4823e1631b0f5e7bba4')

    def test_all_twenty_four_published_stage_payloads_and_order_are_unchanged(self):
        old = self.mod['stages'][:24]
        self.assertEqual(sha(old), OLD_STAGES_SHA)
        self.assertEqual([stage['id'] for stage in old], self.audit['old_stage_order'])
        self.assertEqual({stage['id']: sha(stage) for stage in old}, self.audit['old_stage_hashes'])
        self.assertEqual(self.audit['old_stage_count'], 24)

    def test_exact_six_new_stages_and_links_append_without_unknown_goals(self):
        expected = {qid: MOD+'.molds_v13.'+spec[0] for qid, spec in SPECS.items()}
        self.assertEqual(set(self.quests), set(expected))
        self.assertEqual(self.audit['new_quest_stage_pairs'], expected)
        self.assertEqual(len(v13_stages(self.mod)), 30)
        appended = v13_stages(self.mod)[24:]
        self.assertEqual({stage['id'] for stage in appended}, set(expected.values()))
        self.assertEqual(sum(len(s.get('existing_quest_ids', [])) + len(s.get('new_quest_ids', []))
                             for s in appended), 6)
        for qid, identity in expected.items():
            self.assertEqual(self.quests[qid]['research_stage'], identity)
            self.assertEqual(self.stage_map[identity]['new_quest_ids'], [qid])
            self.assertEqual(self.stage_map[identity]['epoch'], SPECS[qid][1])
            self.assertNotIn('existing_quest_ids', self.stage_map[identity])
        self.assertEqual(v13_optional_quests(self.mod), self.audit['old_optional_quest_ids'] + list(SPECS))

    def test_old_source_prefix_and_exact_forty_four_new_source_paths_are_hash_verified(self):
        self.assertEqual(sha(v13_sources(self.mod)[:183]), OLD_SOURCES_SHA)
        self.assertEqual(self.audit['old_sources_sha256'], OLD_SOURCES_SHA)
        self.assertEqual(len(self.manifest['files']), 43)
        expected = {entry['path']: entry['sha256'] for entry in self.manifest['files']}
        manifest_path = PREFIX+'manifest.json'
        expected[manifest_path] = hashlib.sha256((ROOT/manifest_path).read_bytes()).hexdigest()
        appended = v13_sources(self.mod)[183:]
        self.assertEqual(len(appended), 44)
        self.assertEqual(len({entry['path'] for entry in appended}), 44)
        self.assertEqual({entry['path']: entry['sha256'] for entry in appended}, expected)
        self.assertEqual(self.audit['approved_appended_source_hashes'], expected)
        for entry in appended:
            path = Path(entry['path'])
            self.assertFalse(path.is_absolute())
            self.assertNotIn('..', path.parts)
            self.assertTrue((ROOT/path).resolve().is_relative_to(ROOT.resolve()))
            self.assertEqual(hashlib.sha256((ROOT/path).read_bytes()).hexdigest(), entry['sha256'])
            self.assertIs(entry['verified'], True)

    def test_map_recipe_witnesses_match_each_goal_and_frozen_installed_recipe_bytes(self):
        recipes = {entry['recipe_id']: entry for entry in self.manifest['files'] if entry.get('recipe_id')}
        self.assertEqual(len(recipes), 15)
        for quest in self.catalog:
            stage = self.stage_map[quest['research_stage']]
            self.assertEqual(stage['recipe_ids'], quest['recipe_ids'])
            self.assertEqual([row['recipe_id'] for row in stage['recipe_evidence']], quest['recipe_ids'])
            for row in stage['recipe_evidence']:
                self.assertEqual(row['path'], recipes[row['recipe_id']]['path'])
                raw = (ROOT/row['path']).read_bytes()
                self.assertEqual(hashlib.sha256(raw).hexdigest(), row['sha256'])
                self.assertEqual(row['sha256'], recipes[row['recipe_id']]['sha256'])
                self.assertEqual(json.loads(raw)['type'], row['type'])
        bar = self.stage_map[MOD+'.molds_v13.bar']
        resin = self.stage_map[MOD+'.molds_v13.duroplast']
        self.assertIn('create:spout', bar['machine_ids'])
        self.assertIn('create:spout', resin['machine_ids'])
        self.assertNotIn('create:mechanical_press', bar['machine_ids'])
        self.assertNotIn('create:mechanical_press', resin['machine_ids'])

    def test_new_prerequisites_follow_actual_after_and_cross_mod_refinery_link(self):
        global_links = {qid: (mod['mod_id'], stage) for mod in self.document['mods']
                        for qid, stage in links(mod).items()}
        contracts = {row['quest_id']: row for row in self.mod['quest_dependency_contract_v13']}
        self.assertEqual(set(contracts), set(SPECS))
        for quest in self.catalog:
            stage = self.stage_map[quest['research_stage']]
            local, external, mapped = [], [], []
            for parent_id in quest['after']:
                owner, parent = global_links[parent_id]
                self.assertLessEqual(parent['epoch'], stage['epoch'])
                ref = {'mod_id': owner, 'stage_id': parent['id'], 'quest_id': parent_id}
                mapped.append(ref)
                (local if owner == MOD else external).append(parent['id'] if owner == MOD else ref)
            self.assertEqual(stage['prerequisites'], local)
            self.assertEqual(stage['external_research_prerequisites'], external)
            self.assertEqual(stage['external_quest_prerequisites'], [])
            row = contracts[quest['id']]
            self.assertEqual(row['after'], quest['after'])
            self.assertEqual(row['mapped_prerequisite_stages'], mapped)
            self.assertEqual(row['external_quest_prerequisites'], [])
        resin = self.stage_map[MOD+'.molds_v13.duroplast']
        self.assertEqual(resin['external_research_prerequisites'], [{
            'mod_id': 'immersiveengineering', 'stage_id': 'immersiveengineering.depth.refinery',
            'quest_id': 'V5_DEPTH_IMMERSIVEENGINEERING_REFINERY'}])

    def test_component_predicates_are_exact_inventory_profiles_without_manufacturing_claims(self):
        for quest in self.catalog:
            stage = self.stage_map[quest['research_stage']]
            _, _, profile = SPECS[quest['id']]
            self.assertEqual(stage['component_predicates'], [{
                'item': 'createdieselgenerators:mold',
                'components': {'createdieselgenerators:mold_type': MOD+':'+profile},
                'match_components': 'fuzzy', 'count': 1, 'consume': False, 'craft': False}])
            self.assertEqual(stage['proof_scope'], 'component_profile_and_product_samples')
            self.assertFalse(any(task['type'] == 'advancement' for task in quest['tasks']))
            self.assertIs(quest['required'], False)
        coverage = self.mod['coverage_v13']
        self.assertEqual(coverage['research_stages'], 30)
        self.assertEqual(coverage['new_optional_quest_links'], 6)
        self.assertEqual(set(coverage['known_profiles']), {MOD+':'+name for name in ('lines', 'bowl', 'chain', 'bar')})
        for field in ('native_production_receipt_added', 'full_mod_recipe_coverage',
                      'installed_binary_equivalence_verified', 'full_client_tested', 'legacy_generic_mold_tasks_changed'):
            self.assertIs(coverage[field], False)
        self.assertIs(self.mod['complete'], False)

    def test_existing_generic_mold_catalog_is_unchanged(self):
        raw = (ROOT/'content/quests/v12_create_addons_course.json').read_bytes()
        self.assertEqual(hashlib.sha256(raw).hexdigest(), OLD_V12_CATALOG_SHA)
        quest = next(quest for quest in json.loads(raw)['quests'] if quest['id'] == 'V12_E12_cdg_panel_tooling')
        mold = next(task for task in quest['tasks'] if task.get('item') == 'createdieselgenerators:mold')
        self.assertNotIn('components', mold)
        self.assertNotIn('match_components', mold)

    def test_historical_projection_excludes_only_exact_reviewed_v14_identities(self):
        stage = {'id': APPROVED_V14_STAGE}
        unknown = {'id': 'createdieselgenerators.native_v14.unreviewed'}
        self.assertEqual(v13_stages({'stages': [stage, unknown]}), [unknown])
        sources = [{'path': path} for path in APPROVED_V14_SOURCES]
        unknown_source = {'path': 'content/research/evidence/cdg_panel_native_v14/unreviewed.json'}
        self.assertEqual(v13_sources({'sources': sources + [unknown_source]}), [unknown_source])
        unknown_quest = 'V14_E12_cdg_unreviewed'
        self.assertEqual(v13_optional_quests({'optional_quest_ids': [APPROVED_V14_QUEST, unknown_quest]}),
                         [unknown_quest])


if __name__ == '__main__':
    unittest.main()
