"""Explicit seventeenth process contract; no original CDG dispatch claim."""
import copy
import hashlib
import json
from pathlib import Path
import shutil
import tempfile
import unittest

from tools import build_cdg_panel_v14 as P
from tools import build_create_addons_v12 as C
from tools import build_nasa_process_v7 as N

ROOT = Path(__file__).resolve().parents[1]


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def write(path, document):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(document, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')


def snapshot(root):
    return {p.relative_to(root).as_posix(): p.read_bytes() for p in root.rglob('*') if p.is_file()}


def author_quest():
    return {'id': P.QUEST_ID, 'epoch': 12, 'required': False, 'mod': 'createdieselgenerators',
            'after': ['V13_E12_cdg_mold_lines'], 'proof_scope': P.PROOF_SCOPE,
            'tasks': [{'type': 'advancement', 'advancement': 'aia2:mechanics/'+P.RULE_ID},
                      {'type': 'item', 'item': 'createdieselgenerators:sheet_metal_panel',
                       'count': 4, 'consume': False, 'craft': False}]}


class CdgPanelExtensionTests(unittest.TestCase):
    def fixture(self, root):
        relatives = (P.PENDING, P.RECIPE_PATH, C.PENDING, C.RECIPE_PATH,
                     'kubejs/config/aia2_runtime.json', 'kubejs/config/aia2_recipes.json')
        for relative in relatives:
            target = root/relative; target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT/relative, target)
        document = read(ROOT/P.MECHANICS); by_id = {r['id']: r for r in document['rules']}
        document['rules'] = [by_id[ident] for ident in P.BASELINE_HASHES]
        write(root/P.MECHANICS, document)
        write(root/P.QUESTS, {'schema': 1, 'quests': [author_quest()]})
        write(root/C.QUESTS, {'schema': 1, 'quests': [{
            'id': 'V12_E15_cca_electrum_native', 'epoch': 15, 'required': False,
            'mod': 'createaddition', 'tasks': [
                {'type': 'advancement', 'advancement': 'aia2:mechanics/cca_electrum_mixing'},
                {'type': 'item', 'item': 'immersiveengineering:ingot_electrum', 'count': 2,
                 'consume': False, 'craft': False}]}]})
        process = read(ROOT/P.PROCESS_MAP)
        def baseline(value):
            if isinstance(value, dict):
                if value.get('path') == P.MECHANICS: value['sha256'] = P.PUBLISHED_CONFIG_SHA
                for child in value.values(): baseline(child)
            elif isinstance(value, list):
                for child in value: baseline(child)
        baseline(process); write(root/P.PROCESS_MAP, process)
        marker = root/'saves/world/data/aia2_mechanics_v1.dat'
        marker.parent.mkdir(parents=True); marker.write_bytes(b'opaque-existing-receipts')

    def compiled_quest(self, root):
        quest = {'id': P.uid(P.QUEST_ID), 'optional': True, 'hide_until_deps_complete': True,
                 'dependencies': [P.uid('V13_E12_cdg_mold_lines')], 'tasks': [
                     {'id': P.uid(P.QUEST_ID+':task:0'), 'type': 'advancement', 'advancement': 'aia2:mechanics/'+P.RULE_ID},
                     {'id': P.uid(P.QUEST_ID+':task:1'), 'type': 'item',
                      'item': {'id': 'createdieselgenerators:sheet_metal_panel', 'count': 1},
                      'count': 4, 'consume_items': False, 'only_from_crafting': False},
                     {'id': P.uid(P.QUEST_ID+':stage'), 'type': 'advancement', 'advancement': 'aia2:stages/e12'}]}
        write(root/'config/ftbquests/quests/chapters/test.snbt', {'quests': [quest]})
        return quest

    def assert_refuses_without_writes(self, root, pattern=None):
        before = snapshot(root)
        with self.assertRaises(AssertionError) as error: P.apply(root)
        if pattern: self.assertIn(pattern, str(error.exception))
        self.assertEqual(snapshot(root), before)

    def test_exact_published_sixteen_and_native_recipe_are_frozen(self):
        pending = read(ROOT/P.PENDING)
        self.assertEqual(len(P.BASELINE_HASHES), 16)
        self.assertEqual(pending['published_mechanic_hashes'], P.BASELINE_HASHES)
        self.assertEqual(P.RECIPE_SHA, '9841618670e0a89bea6788df3d213a8acb60849c3c5430b91b89ffa78a138d3b')
        self.assertEqual(hashlib.sha256((ROOT/P.RECIPE_PATH).read_bytes()).hexdigest(), P.RECIPE_SHA)
        own = P.extension_rule()
        self.assertEqual(own['epoch'], 12)
        self.assertEqual(own['serializer'], 'createdieselgenerators:compression_molding')
        self.assertEqual(own['evidence'][0]['json']['mold'], 'createdieselgenerators:lines')
        self.assertEqual(own['evidence'][0]['json']['results'], [{'id': own['output'], 'count': 4}])
        self.assertNotIn('heat_requirement', own['evidence'][0]['json'])

    def test_additive_apply_keeps_all_rules_and_opaque_old_receipts(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); self.fixture(root); before = read(root/P.MECHANICS)
            marker = root/'saves/world/data/aia2_mechanics_v1.dat'; marker_before = marker.read_bytes()
            report = P.apply(root); after = read(root/P.MECHANICS)
            self.assertEqual(after['rules'][:16], before['rules'])
            self.assertEqual(after['rules'][16], P.extension_rule(root))
            self.assertEqual({k: v for k, v in after.items() if k != 'rules'}, P.BASELINE_METADATA)
            self.assertEqual(read(root/f'kubejs/data/aia2/advancement/mechanics/{P.RULE_ID}.json'), P.ADVANCEMENT)
            self.assertEqual(report['published_rules_preserved'], 16)
            self.assertEqual(report['mechanic_rules'], 17)
            self.assertEqual(report['new_recipes'], 0)
            self.assertFalse(report['native_create_dispatch_tested'])
            self.assertEqual(marker.read_bytes(), marker_before)
            once = snapshot(root); P.apply(root); self.assertEqual(snapshot(root), once)

    def test_existing_v12_rebuild_preserves_explicit_seventeenth_rule(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); self.fixture(root); P.apply(root)
            once = snapshot(root); report = C.apply(root)
            self.assertEqual(report['mechanic_rules'], 17)
            # v12 independently emits its advancement when this minimal fixture lacks it.
            allowed = 'kubejs/data/aia2/advancement/mechanics/cca_electrum_mixing.json'
            after = snapshot(root); after.pop(allowed)
            self.assertEqual(after, once)
            P.apply(root); twice = snapshot(root); C.apply(root); P.apply(root)
            self.assertEqual(snapshot(root), twice)
            self.assertEqual(C.validate(root, compiled=True)['status'], 'passed')

    def test_all_six_process_references_refresh_without_changing_stages(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); self.fixture(root); before = read(root/P.PROCESS_MAP)
            report = P.apply(root); after = read(root/P.PROCESS_MAP)
            self.assertEqual(report['preserved_process_map_references_refreshed'], 6)
            self.assertNotEqual(before, after)
            def restore(value):
                if isinstance(value, dict):
                    if value.get('path') == P.MECHANICS: value['sha256'] = P.PUBLISHED_CONFIG_SHA
                    for child in value.values(): restore(child)
                elif isinstance(value, list):
                    for child in value: restore(child)
            restore(after); self.assertEqual(after, before)

    def test_each_published_rule_is_protected_before_writes(self):
        for ident in P.BASELINE_HASHES:
            with self.subTest(rule=ident), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary); self.fixture(root); document = read(root/P.MECHANICS)
                next(row for row in document['rules'] if row['id'] == ident)['epoch'] = 1
                write(root/P.MECHANICS, document)
                self.assert_refuses_without_writes(root, 'Published mechanic rule changed')

    def test_unknown_duplicate_missing_order_and_header_changes_are_refused(self):
        for mutation in ('unknown', 'duplicate', 'missing', 'order', 'header'):
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary); self.fixture(root); document = read(root/P.MECHANICS)
                if mutation == 'unknown':
                    extra = copy.deepcopy(document['rules'][0]); extra['id'] = 'unknown'; document['rules'].append(extra)
                elif mutation == 'duplicate': document['rules'].append(copy.deepcopy(document['rules'][0]))
                elif mutation == 'missing': document['rules'].pop()
                elif mutation == 'order': document['rules'][0], document['rules'][1] = document['rules'][1], document['rules'][0]
                else: document['proof_semantics'] = 'presence'
                write(root/P.MECHANICS, document); self.assert_refuses_without_writes(root)

    def test_changed_generated_panel_identity_is_refused(self):
        for field, value in [('epoch', 1), ('output', 'minecraft:iron_ingot'), ('serializer', 'create:mixing'),
                             ('recipeIds', ['create:mixing/andesite_alloy']), ('advancement', 'minecraft:story/root')]:
            with self.subTest(field=field), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary); self.fixture(root); own = P.extension_rule(root); own[field] = value
                document = read(root/P.MECHANICS); document['rules'].append(own); write(root/P.MECHANICS, document)
                self.assert_refuses_without_writes(root, 'Generated panel rule changed')
                with self.assertRaises(AssertionError): C.validate_mechanic_rules(root)

    def test_pending_contract_and_exact_recipe_mutations_are_refused(self):
        for mutation in ('baseline', 'hash', 'metadata', 'dispatch', 'advancement', 'producer', 'scope', 'recipe'):
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary); self.fixture(root); document = read(root/P.PENDING)
                if mutation == 'baseline': document['baseline'] = '0'*40
                elif mutation == 'hash': document['published_mechanic_hashes']['cca_electrum_mixing'] = '0'*64
                elif mutation == 'metadata': document['published_metadata']['schema'] = 2
                elif mutation == 'dispatch': document['native_create_dispatch_tested'] = True
                elif mutation == 'advancement': document['advancement_json']['criteria']['native_process']['trigger'] = 'minecraft:tick'
                elif mutation == 'producer': document['producer_requirements']['itemGates']['create:basin'] = 12
                elif mutation == 'scope': document['proof_scope'] = 'inventory'
                else: (root/P.RECIPE_PATH).write_bytes(b'{}')
                write(root/P.PENDING, document); self.assert_refuses_without_writes(root)

    def test_future_producer_removed_recipe_and_weakened_author_task_are_refused(self):
        for mutation in ('future', 'removed', 'inventory', 'sample_count', 'zero_flag', 'mandatory', 'parent'):
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary); self.fixture(root)
                if mutation == 'future':
                    document = read(root/'kubejs/config/aia2_runtime.json'); document['blockGates']['create:basin'] = 13
                    write(root/'kubejs/config/aia2_runtime.json', document)
                elif mutation == 'removed':
                    document = read(root/'kubejs/config/aia2_recipes.json'); document['remove'].append(P.RECIPE_ID)
                    write(root/'kubejs/config/aia2_recipes.json', document)
                else:
                    document = read(root/P.QUESTS); quest = document['quests'][0]
                    if mutation == 'inventory': quest['tasks'].pop(0)
                    elif mutation == 'sample_count': quest['tasks'][1]['count'] = 1
                    elif mutation == 'zero_flag': quest['tasks'][1]['consume'] = 0
                    elif mutation == 'mandatory': quest['required'] = True
                    else: quest['after'] = []
                    write(root/P.QUESTS, document)
                self.assert_refuses_without_writes(root)

    def test_stale_process_reference_is_rejected_before_any_write(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); self.fixture(root); document = read(root/P.PROCESS_MAP)
            document['mods'][0]['sources'][0]['sha256'] = '0'*64
            write(root/P.PROCESS_MAP, document)
            self.assert_refuses_without_writes(root, 'Unreviewed panel process-map source contract SHA')

    def test_compiled_projection_keeps_impossible_proof_and_gated_stage(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); self.fixture(root); P.apply(root); self.compiled_quest(root)
            self.assertEqual(P.validate(root, compiled=True)['status'], 'passed')
            for mutation in ('missing_proof', 'missing_stage', 'count', 'predicate', 'dependency', 'visibility', 'advancement'):
                with self.subTest(mutation=mutation):
                    quest = self.compiled_quest(root)
                    if mutation == 'missing_proof': quest['tasks'].pop(0)
                    elif mutation == 'missing_stage': quest['tasks'].pop()
                    elif mutation == 'count': quest['tasks'][1]['count'] = 1
                    elif mutation == 'predicate': quest['tasks'][1]['only_from_crafting'] = True
                    elif mutation == 'dependency': quest['dependencies'] = []
                    elif mutation == 'visibility': quest['hide_until_deps_complete'] = False
                    else: quest['tasks'][0]['advancement'] = 'minecraft:story/root'
                    write(root/'config/ftbquests/quests/chapters/test.snbt', {'quests': [quest]})
                    with self.assertRaises(AssertionError): P.validate(root, compiled=True)

    def test_unreviewed_eighteenth_rule_cannot_use_successor_permission(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); self.fixture(root); P.apply(root)
            document = read(root/P.MECHANICS); extra = copy.deepcopy(document['rules'][-1]); extra['id'] = 'invented_casting'
            document['rules'].append(extra); write(root/P.MECHANICS, document)
            with self.assertRaises(AssertionError): C.validate_mechanic_rules(root)
            self.assert_refuses_without_writes(root)

    def test_nasa_v12_panel_pipeline_preserves_seventeen_rule_order_and_receipts(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); self.fixture(root)
            pending = read(ROOT/N.PENDING)
            relatives = [N.PENDING, N.QUESTS, N.RESEARCH, 'content/quests/v5_ad_astra_depth.json']
            relatives += [source['frozen_path'] for rule in pending['mechanic_rules']
                          for source in rule['evidence']]
            for relative in relatives:
                target = root/relative; target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(ROOT/relative, target)
            C.apply(root); P.apply(root)
            frozen = (root/P.MECHANICS).read_bytes()
            self.assertEqual(N.apply(root)['nasa_mechanic_rules'], 4)
            self.assertEqual((root/P.MECHANICS).read_bytes(), frozen)
            C.apply(root); P.apply(root); once = snapshot(root)
            N.apply(root); C.apply(root); P.apply(root)
            self.assertEqual(snapshot(root), once)
            self.assertEqual((root/P.MECHANICS).read_bytes(), frozen)
            self.assertEqual((root/'saves/world/data/aia2_mechanics_v1.dat').read_bytes(), b'opaque-existing-receipts')
            (root/P.PENDING).unlink()
            with self.assertRaisesRegex(AssertionError, 'Unreviewed explicit mechanic extension set'):
                C.validate_mechanic_rules(root)


if __name__ == '__main__':
    unittest.main()
