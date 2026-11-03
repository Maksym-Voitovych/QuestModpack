"""Closed Mold predicates and save-safe compilation; no Minecraft client claim."""
import copy
import json
import unittest
from unittest.mock import patch

from tools import build_expansion as compiler
from tools import item_task_components_v13 as components
from tools import validate_expansion as expansion
from tools import validate_v5 as validator


MOLD = 'createdieselgenerators:mold'
COMPONENT = 'createdieselgenerators:mold_type'
PROFILES = ('lines', 'bowl', 'chain', 'bar')


def task(profile='lines', count=1):
    return {'type': 'item', 'item': MOLD, 'count': count,
            'consume': False, 'craft': False,
            'components': {COMPONENT: 'createdieselgenerators:'+profile},
            'match_components': 'fuzzy'}


def quest(identity='V13_TEST_PROFILE', profile='lines', count=1):
    return {'id': identity, 'epoch': 12, 'required': False,
            'mod': 'createdieselgenerators', 'category': 'automation',
            'title_uk': 'Перевірена форма для оснащення чаші',
            'description_uk': [
                'Покажіть форму з потрібним профілем та перевірте її компонент. '
                'Це підтверджує лише підготовлений предмет, а не виробництво '
                'продукту чи успішний запуск механічного преса.'],
            'icon': 'createdieselgenerators:sheet_metal_panel',
            'tasks': [task(profile, count)], 'after': [],
            'reward': [{'item': 'createdieselgenerators:wood_chip', 'count': 2}]}


def compiled_quest(record):
    return {'id': validator.uid(record['id']), 'title': record['title_uk'],
            'icon': {'id': record['icon'], 'count': 1},
            'tasks': [compiler.compile_task(t, record['id'], i)
                      for i, t in enumerate(record['tasks'])] + [
                {'id': validator.uid(record['id']+':stage'),
                 'type': 'advancement', 'advancement': 'aia2:stages/e12'}]}


def catalog_context():
    gates = {MOLD: 12, 'createdieselgenerators:sheet_metal_panel': 12,
             'createdieselgenerators:wood_chip': 12}
    rules = {'epochs': [{'number': n, 'key': f'kubejs:test_key_{n}'}
                        for n in range(1, 49)],
             'dualKeys': [], 'itemGates': gates, 'blockGates': {},
             'dimensionGates': {}}
    registries = {'item': set(gates), 'block': set(), 'dimension': set(),
                  'entity_type': set(), 'worldgen/biome': set(),
                  'custom_stat': set()}
    return rules, registries


class ItemTaskComponentTests(unittest.TestCase):
    def invalid_cases(self):
        cases = {}
        for label, value in [('unqualified', 'lines'),
                             ('namespace', 'minecraft:lines'),
                             ('unknown', 'createdieselgenerators:star'),
                             ('wrong-case', 'createdieselgenerators:LINES'),
                             ('null-profile', None), ('profile-list', ['lines'])]:
            item = task(); item['components'][COMPONENT] = value; cases[label] = item
        for label, value in [('null-components', None), ('empty-components', {}),
                             ('list-components', []),
                             ('wrong-component-key', {'createdieselgenerators:MOLD_TYPE': 'createdieselgenerators:lines'}),
                             ('extra-component', {COMPONENT: 'createdieselgenerators:lines',
                                                  'minecraft:custom_name': 'unexpected filter condition'})]:
            item = task(); item['components'] = value; cases[label] = item
        item = task(); del item['components']; cases['missing-components'] = item
        item = task(); del item['match_components']; cases['missing-mode'] = item
        for label, mode in [('all', 'ALL'), ('none', 'none'), ('strict', 'strict'),
                            ('partial', 'partial'), ('wrong-case-mode', 'FUZZY'),
                            ('null-mode', None), ('empty-mode', '')]:
            item = task(); item['match_components'] = mode; cases[label] = item
        for field in ('craft', 'consume'):
            for label, value in [('true', True), ('null', None), ('integer', 0), ('string', 'false')]:
                item = task(); item[field] = value; cases[field+'-'+label] = item
        for label, value in [('zero-count', 0), ('negative-count', -1),
                             ('bool-count', True), ('float-count', 1.0), ('null-count', None)]:
            item = task(); item['count'] = value; cases[label] = item
        item = task(); item['type'] = 'observation'; item['block'] = 'create:basin'; cases['non-item'] = item
        item = task(); item['item'] = 'minecraft:iron_ingot'; cases['wrong-item'] = item
        item = task(); item['Components'] = item.pop('components'); item['Match_Components'] = item.pop('match_components')
        cases['mis-cased-author-fields'] = item
        item = task(); item['components '] = item.pop('components'); item['match_components '] = item.pop('match_components')
        cases['trailing-space-author-fields'] = item
        return cases

    def test_all_four_profiles_compile_modern_itemstack_with_literal_fuzzy_mode(self):
        for name in PROFILES:
            with self.subTest(profile=name):
                source = task(name)
                before = copy.deepcopy(source)
                built = compiler.compile_task(source, 'V13_TEST_PROFILE', 0)
                self.assertEqual(built, {
                    'id': '0000BD06E707B893', 'type': 'item',
                    'item': {'id': MOLD, 'count': 1,
                             'components': {COMPONENT: 'createdieselgenerators:'+name}},
                    'count': 1, 'consume_items': False,
                    'only_from_crafting': False, 'match_components': 'fuzzy'})
                self.assertNotIn('Count', built['item'])
                self.assertNotIn('tag', built['item'])
                self.assertEqual(source, before)

    def test_invalid_schema_is_rejected_before_task_identity_or_compilation(self):
        for label, source in self.invalid_cases().items():
            with self.subTest(case=label):
                before = copy.deepcopy(source)
                with patch.object(compiler, 'uid', wraps=compiler.uid) as make_id:
                    with self.assertRaises(AssertionError):
                        compiler.compile_task(source, 'V13_REJECT', 0)
                    make_id.assert_not_called()
                self.assertEqual(source, before)

    def test_catalog_and_expansion_signature_guard_reject_the_same_invalid_author_contracts(self):
        rules, registries = catalog_context()
        for label, invalid in self.invalid_cases().items():
            with self.subTest(case=label):
                record = quest(); record['tasks'] = [invalid]
                with self.assertRaises(AssertionError):
                    validator.validate_catalog([record], rules, registries)
                with self.assertRaises(AssertionError):
                    expansion.signature_suffix(invalid)

    def test_default_false_flags_are_supported_without_mutating_author_data(self):
        source = task(); del source['consume']; del source['craft']; del source['count']
        before = copy.deepcopy(source)
        built = compiler.compile_task(source, 'V13_TEST_PROFILE', 0)
        self.assertIs(built['consume_items'], False)
        self.assertIs(built['only_from_crafting'], False)
        self.assertEqual(built['count'], 1)
        self.assertEqual(source, before)

    def test_legacy_generic_mold_and_ordinary_items_are_byte_exact(self):
        examples = [
            ({'type': 'item', 'item': MOLD, 'count': 1, 'consume': False, 'craft': False},
             {'id': '00001824D2F8AFBE', 'type': 'item', 'item': {'id': MOLD, 'count': 1},
              'count': 1, 'consume_items': False, 'only_from_crafting': False}),
            ({'type': 'item', 'item': 'minecraft:iron_ingot', 'count': 8, 'consume': True, 'craft': True},
             {'id': '00001824D2F8AFBE', 'type': 'item', 'item': {'id': 'minecraft:iron_ingot', 'count': 1},
              'count': 8, 'consume_items': True, 'only_from_crafting': True}),
        ]
        for source, frozen in examples:
            with self.subTest(item=source['item']):
                before = copy.deepcopy(source)
                self.assertIsNone(components.predicate(source))
                self.assertEqual(components.signature_suffix(source), ())
                actual = compiler.compile_task(source, 'V13_TEST_LEGACY_ITEM', 0)
                encode = lambda value: json.dumps(value, ensure_ascii=False, separators=(',', ':')).encode()
                self.assertEqual(encode(actual), encode(frozen))
                self.assertEqual(source, before)
                self.assertNotIn('match_components', actual)
                self.assertNotIn('components', actual['item'])

    def test_legacy_non_item_task_keeps_existing_fields_and_identity(self):
        source = {'type': 'observation', 'block': 'create:mechanical_press', 'ticks': 40}
        self.assertEqual(compiler.compile_task(source, 'V13_TEST_OBSERVATION', 0), {
            'id': '0000FF2F080AF8FD', 'type': 'observation',
            'observation_type': 'block', 'to_observe': 'create:mechanical_press', 'timer': 40})
        self.assertEqual(expansion.signature_suffix(source), ())

    def test_profile_signatures_differ_but_quantities_do_not_disguise_duplicates(self):
        signatures = {name: validator.objective_signature([task(name)]) for name in PROFILES}
        self.assertEqual(len(set(signatures.values())), 4)
        generic = {'type': 'item', 'item': MOLD, 'count': 1, 'consume': False, 'craft': False}
        self.assertNotIn(validator.objective_signature([generic]), signatures.values())
        self.assertEqual(validator.objective_signature([task('lines', 1)]),
                         validator.objective_signature([task('lines', 99)]))
        self.assertEqual(expansion.signature_suffix(task('lines')), components.signature_suffix(task('lines')))

    def test_four_profile_quests_are_distinct_and_same_profile_count_change_is_duplicate(self):
        rules, registries = catalog_context()
        records = [quest('V13_TEST_'+name.upper(), name) for name in PROFILES]
        compiled = {validator.uid(record['id']): compiled_quest(record) for record in records}
        result = validator.validate_catalog(records, rules, registries, compiled)
        self.assertEqual(result['new_authored_quests'], 4)
        duplicate = quest('V13_DIFFERENT_AMOUNT', 'lines', 64)
        with self.assertRaisesRegex(AssertionError, 'Duplicate objectives'):
            validator.validate_catalog([duplicate], rules, registries, old_records=[records[0]])

    def test_compiled_profile_cannot_drop_or_change_component_or_matching_mode(self):
        record = quest(); valid = compiled_quest(record)
        validator.validate_compiled_tasks(record, valid)
        for mutation in ('missing-components', 'wrong-profile', 'wrong-component',
                         'missing-mode', 'none', 'ALL', 'strict', 'null-mode', 'extra-component'):
            with self.subTest(mutation=mutation):
                changed = copy.deepcopy(valid); result = changed['tasks'][0]
                if mutation == 'missing-components': del result['item']['components']
                elif mutation == 'wrong-profile': result['item']['components'][COMPONENT] = 'createdieselgenerators:bowl'
                elif mutation == 'wrong-component': result['item']['components'] = {'createdieselgenerators:MOLD_TYPE': 'createdieselgenerators:lines'}
                elif mutation == 'missing-mode': del result['match_components']
                elif mutation == 'extra-component': result['item']['components']['minecraft:custom_name'] = 'unexpected'
                else: result['match_components'] = None if mutation == 'null-mode' else mutation
                with self.assertRaisesRegex(AssertionError, 'Compiled task semantics changed'):
                    validator.validate_compiled_tasks(record, changed)

    def test_component_outputs_are_independent_copies_and_normal_product_icon_stays_generic(self):
        source = task(); before = copy.deepcopy(source)
        spec = components.predicate(source); stack = components.item_stack(source)
        spec['components'][COMPONENT] = 'createdieselgenerators:bar'
        stack['components'][COMPONENT] = 'createdieselgenerators:chain'
        self.assertEqual(source, before)
        record = quest(); frozen = copy.deepcopy(record)
        built = compiled_quest(record)
        rules, registries = catalog_context()
        validator.validate_catalog([record], rules, registries, {validator.uid(record['id']): built})
        self.assertEqual(record, frozen)
        self.assertEqual(built['icon'], {'id': 'createdieselgenerators:sheet_metal_panel', 'count': 1})
        self.assertNotIn('components', built['icon'])
        self.assertNotIn('match_components', built)


if __name__ == '__main__':
    unittest.main()
