"""Exact Nitro producer closure, native costs, reachability and deterministic compilation."""
import copy
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from tools import build_powah_generators_balance_v5 as B

ROOT = Path(__file__).resolve().parents[1]


class PowahGeneratorTests(unittest.TestCase):
    def inputs(self):
        return (B.read(ROOT/B.CATALOG), B.read(ROOT/'kubejs/config/aia2_recipes.json'),
                B.read(ROOT/'kubejs/config/aia2_runtime.json'))

    def fixture(self, catalog, bundle, rules):
        tmp = tempfile.TemporaryDirectory(); self.addCleanup(tmp.cleanup); root = Path(tmp.name)
        B.write(root/B.CATALOG,catalog); B.write(root/'kubejs/config/aia2_recipes.json',bundle); B.write(root/'kubejs/config/aia2_runtime.json',rules)
        sources = catalog['sources'] + [catalog['producer_scan'],catalog['registry_evidence']] + [s for r in catalog['recipes'] for s in r['sources']]
        for source in sources:
            p=root/source['path']; p.parent.mkdir(parents=True,exist_ok=True); p.write_bytes((ROOT/source['path']).read_bytes())
        for p in (ROOT/'content/quests').glob('*.json'):
            out=root/p.relative_to(ROOT);out.parent.mkdir(parents=True,exist_ok=True);out.write_bytes(p.read_bytes())
        return root

    def test_compiled_costs_gates_and_quest_linkage(self):
        catalog,bundle,rules=self.inputs()
        report=B.validate(ROOT,catalog,bundle,rules,compiled=True)
        self.assertEqual(report['native_producers_replaced'],3)
        self.assertEqual(report['published_custom_recipes_preserved'],615)
        linked=set()
        for p in (ROOT/'content/quests').glob('*.json'):
            data=B.read(p)
            for q in data if isinstance(data,list) else data.get('quests',[]):
                linked.update(t.get('item') for t in q.get('tasks',[]) if t.get('type')=='item' and not t.get('craft'))
        self.assertTrue(B.TARGETS <= linked)

    def test_changed_native_cost_quantity_mirror_and_pattern_rejected(self):
        catalog,bundle,rules=self.inputs()
        edits=[lambda j:j['result'].update(count=True),lambda j:j.update(accept_mirrored=True),
               lambda j:j['key']['M'].update(item='minecraft:dirt'),lambda j:j.update(pattern=['MgggT','c d c','g   g']),
               lambda j:j['key']['c'].update(count=2)]
        for edit in edits:
            changed=copy.deepcopy(catalog);edit(changed['recipes'][0]['json'])
            with self.assertRaises(AssertionError): B.validate(ROOT,changed,bundle,rules)

    def test_future_machine_input_and_published_recipe_drift_rejected(self):
        catalog,bundle,rules=self.inputs()
        future=copy.deepcopy(rules);future['blockGates']['create:mechanical_crafter']=37
        with self.assertRaisesRegex(AssertionError,'Future mechanical'): B.validate(ROOT,catalog,bundle,future)
        future=copy.deepcopy(rules);future['itemGates'][catalog['recipes'][0]['magic_input']]=37
        with self.assertRaisesRegex(AssertionError,'Future/unknown'): B.validate(ROOT,catalog,bundle,future)
        changed=copy.deepcopy(bundle);changed['add'][0]['category']='modified'
        with self.assertRaisesRegex(AssertionError,'baseline changed'): B.validate(ROOT,catalog,changed,rules)

    def test_native_alternative_and_vanilla_craft_task_conflicts_rejected(self):
        catalog,bundle,rules=self.inputs()
        changed=copy.deepcopy(catalog);changed['recipes'][0]['remove_recipe_ids']=[]
        with self.assertRaisesRegex(AssertionError,'Incomplete Nitro'): B.validate(ROOT,changed,bundle,rules)
        changed=copy.deepcopy(bundle);changed['remove'].remove(catalog['recipes'][0]['remove_recipe_ids'][0])
        with self.assertRaisesRegex(AssertionError,'Cheap native Nitro'): B.validate(ROOT,catalog,changed,rules,compiled=True)
        root=self.fixture(catalog,bundle,rules)
        B.write(root/'content/quests/bad.json',{'quests':[{'id':'invalid','tasks':[{'type':'item','item':'powah:furnator_nitro','craft':True}]}]})
        with self.assertRaisesRegex(AssertionError,'craft:true'): B.validate(root,catalog,bundle,rules)

    def test_full_export_producer_scan(self):
        export=Path('/workspace/aia2-reference/export/recipes')
        if not export.is_dir(): self.skipTest('External export unavailable')
        catalog,bundle,rules=self.inputs()
        report=B.validate(ROOT,catalog,bundle,rules,compiled=True,export_recipes=export)
        self.assertTrue(report['full_export_verified_this_run'])

    def test_repeated_and_cross_process_compilation_is_byte_identical(self):
        catalog,bundle,rules=self.inputs();root=self.fixture(catalog,bundle,rules)
        files=['kubejs/config/aia2_recipes.json','kubejs/config/aia2_runtime.json']
        B.apply(root);before=[(root/p).read_bytes() for p in files]; B.apply(root)
        self.assertEqual(before,[(root/p).read_bytes() for p in files])
        script='import sys;from pathlib import Path;from tools.build_powah_generators_balance_v5 import apply;apply(Path(sys.argv[1]))'
        for seed in ['17','43']:
            env=dict(os.environ,PYTHONHASHSEED=seed)
            run=subprocess.run([sys.executable,'-c',script,str(root)],cwd=ROOT,env=env,capture_output=True,text=True)
            self.assertEqual(run.returncode,0,run.stdout+run.stderr)
            self.assertEqual(before,[(root/p).read_bytes() for p in files])
