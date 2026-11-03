"""Portable research coverage and preservation; does not launch optional mods."""
import hashlib
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
MODS = ('createaddition', 'createdieselgenerators')
OTHER_MODS_SHA = 'd28efec694d37bf3c3bf715d8fe9436610cb59891fa2fa76354daab8ea3dba8a'
OLD_STAGE_SHA = {
    'createaddition.phase.01': '77b584f915188fd5dcb2260d6371a4e1c28efe15ab16db7edbeb44835f7673ab',
    'createaddition.phase.02': 'b120e5b26f7b4c3f22c457a8646081b7a4dc6130a9c64997dcec0585e04d55ad',
    'createaddition.phase.03': '067ff651039757e4262a53c168aca18b3f598a558ee97eb3bf0258f12b74eebf',
    'createaddition.phase.04': 'cb03ba01bd9f0f6e284efdb1c3796e3065966778537aeadf07a51d9b4102290b',
    'createaddition.phase.05': '8835c9e1db004a800d810f195d84c60a8d41844ebe75c14da82e6892ac982bc0',
    'createaddition.phase.06': 'c707989b84c10d3676d2bcd75364d4129440fa9de3e81e53111f2c418daa54a4',
    'createaddition.phase.07': '69b7911dbbe30a47cacbc17239d9bc8b9c983f7c8b9db048521314cb51d82671',
    'createdieselgenerators.phase.01': '16507f369be4071536651a56ad0e90e991c132f50aaa254110b340d0cc4bbce2',
    'createdieselgenerators.phase.02': '4946853c2392df8487419c8f41c894ce0ec8f48e7dde490d933b013d699140db',
    'createdieselgenerators.phase.03': '67b0067a7f714ff1f30a94408f356d43b213419934affd27d807ee6664ff80ae',
    'createdieselgenerators.phase.04': 'fa14e7d79f2afd5641705b687261825b7879307f7f959fbe7eca00e0585497e2',
    'createdieselgenerators.phase.05': '63e36ef2b0e6ef1be183dbc1281262eb376c67c910fc36359bf17f30314c3de0',
    'createdieselgenerators.phase.06': 'e54df66308210bd7bc872a847d37bf1f5f53045a5354bd700eab8959f935597c',
    'createdieselgenerators.phase.07': '2223028bed35b5a0e186eb3a85401f5d6f1921c792d39d086bb5dd57db6b16ac',
}
ROLLING_STAGE_PROTECTED_SHA = 'ae80e299aa4bc3c08f7b55d9347ada3c5cb1921243c6f6f3011d7d3f97ed1708'
# v12 is a historical contract. Exclude only this reviewed six-stage extension,
# never a broad prefix which could hide an unexpected future map addition.
APPROVED_V13_STAGES = frozenset('createdieselgenerators.molds_v13.'+name
    for name in ('lines', 'bowl', 'chain', 'bar', 'heated_lines', 'duroplast'))
APPROVED_V13_QUESTS = frozenset({
    'V13_E12_cdg_mold_lines', 'V13_E12_cdg_mold_bowl', 'V13_E12_cdg_mold_chain',
    'V13_E15_cdg_mold_bar', 'V13_E15_cdg_mold_heated_lines', 'V13_E18_cdg_mold_duroplast',
})


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def sha(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
                                     separators=(',', ':')).encode()).hexdigest()


def v12_stages(mod):
    return [stage for stage in mod['stages'] if stage['id'] not in APPROVED_V13_STAGES]


def quest_links(mod):
    return {qid: stage for stage in v12_stages(mod)
            for qid in stage.get('existing_quest_ids', []) + stage.get('new_quest_ids', [])}


class CreateAddonMapTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.document = read(ROOT/'content/research/technology_v5.json')
        cls.mods = {mod['mod_id']: mod for mod in cls.document['mods']}
        cls.new = read(ROOT/'content/quests/v12_create_addons_course.json')['quests']
        cls.quests = {}
        for path in sorted((ROOT/'content/quests').glob('*.json')):
            document = read(path)
            for quest in document if isinstance(document, list) else document.get('quests', []):
                if quest['id'] in cls.quests:
                    raise AssertionError('Duplicate authored quest: '+quest['id'])
                cls.quests[quest['id']] = quest

    def test_other_mod_records_are_semantically_identical_to_checkpoint(self):
        self.assertEqual(sha([mod for mod in self.document['mods'] if mod['mod_id'] not in MODS]),
                         OTHER_MODS_SHA)

    def test_fourteen_published_stages_preserved_except_exact_rolling_evidence(self):
        stages = {stage['id']: stage for name in MODS for stage in self.mods[name]['stages']}
        for identity, expected in OLD_STAGE_SHA.items():
            with self.subTest(stage=identity):
                actual = stages[identity]
                if identity == 'createaddition.phase.05':
                    self.assertEqual(sha({key: value for key, value in actual.items()
                                          if key != 'recipe_evidence'}), ROLLING_STAGE_PROTECTED_SHA)
                    self.assertNotEqual(sha(actual), expected)
                    self.assertEqual([row['recipe_id'] for row in actual['recipe_evidence']],
                                     ['createaddition:rolling/electrum_plate'])
                    self.assertEqual(actual['recipe_evidence'][0]['type'], 'createaddition:rolling')
                else:
                    self.assertEqual(sha(actual), expected)
        correction = self.mods['createaddition']['research_corrections_v12']
        self.assertEqual(len(correction), 1)
        self.assertEqual(correction[0]['changed_fields'], ['recipe_evidence'])
        self.assertEqual(correction[0]['old_evidence'][0]['recipe_id'],
                         'create:cutting/compat/immersiveengineering/wire_electrum')

    def test_all_sixteen_selected_legacy_goals_and_fifteen_additions_mapped_once(self):
        bases = {
            'createaddition': {'E11_X_alternator', 'E11_X_connector', 'E11_X_rolling_mill', 'E11_X_motor'},
            'createdieselgenerators': {'E12_X_survey', 'E12_X_canister', 'E12_X_pumpjack_parts', 'E12_X_engine'},
        }
        for name, v4prefix, v5prefix, epochs, expected in [
            ('createaddition', 'V4_E11_electric_bridge_', 'electromechanical_work', [11, 19, 28, 32], 23),
            ('createdieselgenerators', 'V4_E12_diesel_', 'diesel_contract', [12, 18, 28, 44], 24),
        ]:
            mod = self.mods[name]
            legacy = bases[name] | {v4prefix+f'{i:02d}' for i in range(1, 9)}
            legacy |= {f'V5_E{epoch:02d}_{v5prefix}_{i:02d}' for i, epoch in enumerate(epochs, 1)}
            additions = {quest['id'] for quest in self.new if quest['mod'] == name}
            self.assertEqual(len(legacy), 16)
            self.assertEqual(set(quest_links(mod)), legacy | additions)
            self.assertEqual(len(v12_stages(mod)), expected)
            self.assertEqual(sum(len(stage.get('existing_quest_ids', [])) + len(stage.get('new_quest_ids', []))
                                 for stage in v12_stages(mod)), expected)
            self.assertEqual(mod['coverage_v12']['previously_unmapped_legacy_goals_added'], 9)
            self.assertEqual(mod['coverage_v12']['new_quest_links'], len(additions))
            for quest in self.new:
                if quest['mod'] == name:
                    self.assertEqual(quest_links(mod)[quest['id']]['id'], quest['research_stage'])

    def test_added_stage_dependencies_match_real_after_including_cross_mod_links(self):
        global_map = {qid: (name, stage) for name in MODS for qid, stage in quest_links(self.mods[name]).items()}
        for name in MODS:
            for qid, stage in quest_links(self.mods[name]).items():
                if stage['id'] in OLD_STAGE_SHA:
                    continue
                quest = self.quests[qid]
                local, cross, external = [], [], []
                for parent_id in quest.get('after', []):
                    parent = self.quests.get(parent_id)
                    if parent:
                        self.assertLessEqual(parent['epoch'], quest['epoch'])
                    if parent_id in global_map:
                        owner, parent_stage = global_map[parent_id]
                        if owner == name:
                            local.append(parent_stage['id'])
                        else:
                            cross.append({'mod_id': owner, 'stage_id': parent_stage['id'], 'quest_id': parent_id})
                    else:
                        external.append(parent_id)
                self.assertEqual(stage['prerequisites'], local)
                self.assertEqual(stage['external_research_prerequisites'], cross)
                self.assertEqual(stage['external_quest_prerequisites'], external)
        biomass = global_map['V12_E15_cca_biomass_loop'][1]
        self.assertEqual(biomass['external_research_prerequisites'][0]['quest_id'], 'V12_E12_cdg_seed_oils')
        backup = global_map['V12_E18_cdg_backup_energy'][1]
        self.assertEqual(backup['external_research_prerequisites'][0]['quest_id'], 'V12_E11_cca_relay_contacts')

    def test_actual_quest_dependency_contract_preserves_old_and_new_after_fields(self):
        for name in MODS:
            mod = self.mods[name]
            rows = {row['quest_id']: row for row in mod['quest_dependency_contract_v12']}
            self.assertEqual(set(rows), set(quest_links(mod)))
            for qid, row in rows.items():
                self.assertEqual(row['after'], self.quests[qid].get('after', []))
                self.assertEqual(row['epoch'], self.quests[qid]['epoch'])
                self.assertEqual(row['stage_id'], quest_links(mod)[qid]['id'])
            required = {qid for qid in rows if self.quests[qid].get('required') is True}
            self.assertEqual(set(mod['mandatory_quest_ids']), required)
            self.assertEqual(set(mod['optional_quest_ids']) & set(rows), set(rows)-required)
            self.assertTrue(set(mod['optional_quest_ids'])-set(rows) <= APPROVED_V13_QUESTS)

    def test_v12_projection_excludes_only_the_six_reviewed_stage_identities(self):
        unknown = {'id': 'createdieselgenerators.molds_v13.unreviewed',
                   'new_quest_ids': ['UNREVIEWED']}
        reviewed = {'id': 'createdieselgenerators.molds_v13.lines',
                    'new_quest_ids': ['V13_E12_cdg_mold_lines']}
        self.assertEqual(v12_stages({'stages': [reviewed, unknown]}), [unknown])
        self.assertEqual(set(quest_links({'stages': [reviewed, unknown]})), {'UNREVIEWED'})

    def test_stage_graphs_are_acyclic_and_have_no_future_parent(self):
        for name in MODS:
            stages = {stage['id']: stage for stage in self.mods[name]['stages']}
            visited, visiting = set(), set()
            def visit(identity):
                self.assertNotIn(identity, visiting)
                if identity in visited:
                    return
                visiting.add(identity)
                for parent in stages[identity].get('prerequisites', []):
                    self.assertIn(parent, stages)
                    self.assertLessEqual(stages[parent]['epoch'], stages[identity]['epoch'])
                    visit(parent)
                visiting.remove(identity)
                visited.add(identity)
            for identity in stages:
                visit(identity)
            self.assertEqual(len(visited), len(stages))

    def test_active_source_versions_and_historical_mismatch_remain_honest(self):
        cca, cdg = (self.mods[name] for name in MODS)
        history = [row for row in cca['sources'] if row.get('pin') == '1c81fab9aaaf157c58e16ad0acbe95c8523cd4e4']
        self.assertEqual(len(history), 4)
        for row in history:
            self.assertIs(row['version_match'], False)
            self.assertIs(row['historical_context'], True)
            self.assertIn('1.7.2', row['scope_uk'])
        active = [row for row in cca['sources'] if row.get('pin') == '51e4a389ab044a113c02be383e66beaf69ec3110']
        self.assertEqual(len(active), 17)
        self.assertTrue(all(row['version_match'] is True for row in active))
        props = next(row for row in active if row['path'].endswith('/gradle.properties'))
        self.assertIn('mod_version=1.6.0', (ROOT/props['path']).read_text())
        self.assertIn('minecraft_version=1.21.1', (ROOT/props['path']).read_text())
        old_cdg = [row for row in cdg['sources'] if '/technology_v5/createdieselgenerators/official/' in row['path']]
        self.assertEqual(len(old_cdg), 4)
        self.assertTrue(all(row['version_match'] is True and 'source-version match' in row['scope_uk'] for row in old_cdg))
        for mod in [cca, cdg]:
            self.assertIs(mod['complete'], False)
            self.assertIs(mod['coverage_v12']['full_mod_recipe_coverage'], False)
            self.assertIs(mod['coverage_v12']['installed_binary_equivalence_verified'], False)
            self.assertNotIn(mod['status'], {'complete', 'fully_implemented'})
            self.assertTrue(any('NOT_RUN' in text for text in mod['uncertainties_uk']))

    def test_every_appended_source_and_stage_recipe_hash_is_portable_and_current(self):
        for name in MODS:
            for row in self.mods[name]['sources'] + [row for stage in self.mods[name]['stages'] for row in stage.get('recipe_evidence', [])]:
                path = Path(row['path'])
                self.assertFalse(path.is_absolute())
                self.assertNotIn('..', path.parts)
                self.assertEqual(hashlib.sha256((ROOT/path).read_bytes()).hexdigest(), row['sha256'], str(path))
        for folder, expected in [('cca', 128), ('cdg', 130)]:
            index = read(ROOT/f'content/research/evidence/create_addons_core_v12/{folder}/recipe-index.json')
            self.assertEqual(index['recipe_count'], expected)
            self.assertEqual(len(index['recipes']), expected)

    def test_native_electrum_and_inventory_fluid_limits_are_separate(self):
        links = quest_links(self.mods['createaddition'])
        native = links['V12_E15_cca_electrum_native']
        self.assertEqual(native['epoch'], 15)
        self.assertEqual(native['proof_scope'], 'current_machine_owner_team_native_post_consumption')
        self.assertEqual([row['recipe_id'] for row in native['recipe_evidence']], ['createaddition:mixing/electrum'])
        evidence = native['recipe_evidence'][0]
        recipe = read(ROOT/evidence['path'])
        self.assertEqual(recipe['type'], 'create:mixing')
        self.assertEqual(recipe['heat_requirement'], 'heated')
        self.assertEqual(recipe['results'], [{'count': 2, 'id': 'immersiveengineering:ingot_electrum'}])
        for qid, stage in quest_links(self.mods['createdieselgenerators']).items():
            if qid.startswith('V12_'):
                self.assertIn(stage['proof_scope'], {'inventory_samples',
                    'block_observation_and_inventory', 'crafting_and_inventory'})
                self.assertFalse(any(task['type'] == 'advancement' and
                    task.get('advancement', '').startswith('aia2:mechanics/')
                    for task in self.quests[qid]['tasks']),
                    'Item/fluid samples cannot fabricate a native fluid receipt')


if __name__ == '__main__':
    unittest.main()
