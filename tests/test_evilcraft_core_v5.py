"""Source-backed authored course and two cross-mod machine assemblies."""
import copy
import hashlib
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from tools import build_evilcraft_core_balance_v5 as balance

ROOT=Path(__file__).resolve().parents[1]
read=lambda p:json.loads(Path(p).read_text())

class EvilCraftCoreTests(unittest.TestCase):
    def test_source_fingerprints_old_stage_identity_and_real_capture_criterion(self):
        folder=ROOT/'content/research/evidence/evilcraft_core_next_v5'
        manifest=read(folder/'manifest.json')
        self.assertEqual(manifest['pin'],'de23efdb83ea1b84addad6e3b1dc51a37147dc1a')
        for source in manifest['sources']:
            self.assertEqual(hashlib.sha256((ROOT/source['path']).read_bytes()).hexdigest(),source['sha256'])
        mod=next(m for m in read(ROOT/'content/research/magic_adventure_v5.json')['mods'] if m['mod_id']=='evilcraft')
        previous=read(folder/'preserved_stages.json')
        self.assertEqual(len(previous),8)
        self.assertEqual([{'id':s['id'],'existing':s.get('existing_quest_ids',[]),'new':s.get('new_quest_ids',[])} for s in mod['stages'][:8]],previous)
        quests=read(ROOT/'content/quests/v5_evilcraft_core_depth.json')['quests']
        self.assertEqual(len(quests),16)
        self.assertEqual(len({q['id'] for q in quests}),16)
        self.assertTrue(all(not q['required'] and q['tasks'] for q in quests))
        capture=next(q for q in quests if q['id'].endswith('capture_spirit'))
        self.assertEqual(capture['tasks'],[{'type':'advancement','advancement':'evilcraft:closure'}])
        self.assertEqual(read(folder/'official/src/main/resources/data/evilcraft/advancement/closure.json')['criteria'],{'criteria_0':{'trigger':'evilcraft:box_of_eternal_closure_capture'}})
        for q in quests:
            for task in q['tasks']:
                if task.get('item') in balance.TARGETS:self.assertFalse(task.get('craft',False),'Mechanical assembly cannot use vanilla crafting task')

    def test_costs_current_stage_and_published_recipes_preserved(self):
        report=balance.validate(ROOT,read(ROOT/balance.CATALOG),read(ROOT/'kubejs/config/aia2_recipes.json'),read(ROOT/'kubejs/config/aia2_runtime.json'),True)
        self.assertEqual(report['recipes'],2);self.assertEqual(report['published_custom_recipes_preserved'],621)

    def test_future_material_missing_native_cost_and_incomplete_closure_rejected(self):
        catalog=read(ROOT/balance.CATALOG);bundle=read(ROOT/'kubejs/config/aia2_recipes.json');rules=read(ROOT/'kubejs/config/aia2_runtime.json')
        bad=copy.deepcopy(catalog);bad['recipes'][0]['json']['pattern'][0]='     '
        with self.assertRaisesRegex(AssertionError,'Native materials|Unused'):balance.validate(ROOT,bad,bundle,rules)
        bad=copy.deepcopy(catalog);bad['recipes'][0]['added_item_ids'][0]='projecte:transmutation_tablet';bad['recipes'][0]['json']['key']['Y']={'item':'projecte:transmutation_tablet'}
        with self.assertRaisesRegex(AssertionError,'Future'):balance.validate(ROOT,bad,bundle,rules)
        bad=copy.deepcopy(catalog);bad['recipes'][0]['remove_recipe_ids']=[]
        with self.assertRaisesRegex(AssertionError,'producer'):balance.validate(ROOT,bad,bundle,rules)
        bad=copy.deepcopy(bundle);bad['add'][0]['json']['type']='invalid:changed'
        with self.assertRaisesRegex(AssertionError,'Published'):balance.validate(ROOT,catalog,bad,rules)

    def test_apply_is_idempotent_and_source_drift_rejected(self):
        catalog=read(ROOT/balance.CATALOG)
        with tempfile.TemporaryDirectory() as tmp:
            target=Path(tmp)
            for name in [balance.CATALOG,'kubejs/config/aia2_recipes.json','kubejs/config/aia2_runtime.json',*[r['source']['path'] for r in catalog['recipes']],*[r['path'] for r in catalog['format_sources']]]:
                p=target/name;p.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/name,p)
            (target/'implementation').mkdir()
            balance.apply(target)
            first={p.relative_to(target):p.read_bytes() for p in target.rglob('*') if p.is_file()}
            balance.apply(target)
            self.assertEqual(first,{p.relative_to(target):p.read_bytes() for p in target.rglob('*') if p.is_file()})
            source=target/catalog['recipes'][0]['source']['path'];source.write_text('{}')
            with self.assertRaisesRegex(AssertionError,'Stale source'):balance.apply(target)

    def test_full_effective_export_producer_scan(self):
        export=Path('/workspace/aia2-reference/export')
        if not export.is_dir():self.skipTest('External user export unavailable')
        self.assertEqual(balance.scan(export),read(ROOT/balance.CATALOG)['producer_scan'])
