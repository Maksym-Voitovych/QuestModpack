"""Reproduce fusion upgrades without mutating runtime; reject cost/closure/tier drift."""
import copy
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from tools import build_draconic_power_v5 as B

ROOT=Path(__file__).resolve().parents[1]


class DraconicPowerTests(unittest.TestCase):
    def inputs(self):
        return B.read(ROOT/B.CATALOG),B.read(ROOT/'kubejs/config/aia2_recipes.json'),B.read(ROOT/'kubejs/config/aia2_runtime.json')

    def fixture(self,catalog,bundle,rules):
        temp=tempfile.TemporaryDirectory();self.addCleanup(temp.cleanup);root=Path(temp.name)
        B.write(root/B.CATALOG,catalog);B.write(root/'kubejs/config/aia2_recipes.json',bundle);B.write(root/'kubejs/config/aia2_runtime.json',rules)
        sources=catalog['sources']+[catalog['producer_scan'],catalog['registry_evidence']]+[s for row in catalog['recipes'] for s in row['sources']]+[row['source'] for row in catalog['preserved_producer_contracts'].values()]+[row['source'] for row in catalog['tag_evidence'].values()]
        for source in sources:
            path=root/source['path'];path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes((ROOT/source['path']).read_bytes())
        for path in (ROOT/'content/quests').glob('*.json'):
            out=root/path.relative_to(ROOT);out.parent.mkdir(parents=True,exist_ok=True);out.write_bytes(path.read_bytes())
        return root

    def test_native_cost_tier_energy_catalyst_and_output_preserved(self):
        catalog,bundle,rules=self.inputs();report=B.validate(ROOT,catalog,bundle,rules)
        self.assertEqual(report['recipes'],3);self.assertEqual(report['native_producers_replaced'],3)
        self.assertEqual(report['published_custom_recipes_preserved'],618)
        self.assertEqual(report['lossless_conversion_routes_preserved'],2)
        self.assertFalse(report['source_ci_build633_verified'])
        relay=next(row for row in catalog['recipes'] if row['target']=='draconicevolution:draconic_relay_crystal')
        self.assertEqual(relay['json']['catalyst']['count'],4);self.assertEqual(relay['json']['result']['count'],4)
        self.assertEqual(len(relay['json']['ingredients']),11)
        self.assertEqual(relay['json']['totalEnergy'],128000)
        root=self.fixture(catalog,bundle,rules);compiled=B.apply(root)
        self.assertEqual(compiled['maximum_injector_inputs'],11)
        self.assertTrue(B.validate(root,catalog,B.read(root/'kubejs/config/aia2_recipes.json'),B.read(root/'kubejs/config/aia2_runtime.json'),compiled=True)['native_tier_energy_catalyst_output_preserved'])

    def test_tier_catalyst_energy_quantities_and_consumption_drift_rejected(self):
        catalog,bundle,rules=self.inputs()
        edits=[lambda r:r['json'].update(totalEnergy=1),lambda r:r['json'].update(techLevel='draconium'),
               lambda r:r['json']['catalyst'].update(count=1),lambda r:r['json']['result'].update(count=True),
               lambda r:r['json']['ingredients'][0].update(consume=False),lambda r:r['json']['ingredients'].pop()]
        for edit in edits:
            changed=copy.deepcopy(catalog);edit(changed['recipes'][2])
            with self.assertRaises(AssertionError):B.validate(ROOT,changed,bundle,rules)

    def test_future_producer_input_and_native_tag_without_reachable_member_rejected(self):
        catalog,bundle,rules=self.inputs()
        changed=copy.deepcopy(rules);changed['blockGates']['draconicevolution:crafting_core']=43
        with self.assertRaisesRegex(AssertionError,'Future fusion core'):B.validate(ROOT,catalog,bundle,changed)
        changed=copy.deepcopy(rules);changed['blockGates']['draconicevolution:wyvern_crafting_injector']=42
        with self.assertRaisesRegex(AssertionError,'Future or self-dependent tier'):B.validate(ROOT,catalog,bundle,changed)
        changed=copy.deepcopy(rules);changed['itemGates'][catalog['recipes'][0]['magic_input']]=42
        with self.assertRaisesRegex(AssertionError,'Future or unknown'):B.validate(ROOT,catalog,bundle,changed)
        changed=copy.deepcopy(rules);changed['itemGates']['minecraft:diamond']=43
        with self.assertRaisesRegex(AssertionError,'No reachable native tag'):B.validate(ROOT,catalog,bundle,changed)

    def test_all_published_records_and_lossless_conversions_are_preserved(self):
        catalog,bundle,rules=self.inputs()
        changed=copy.deepcopy(bundle);changed['add'][0]['category']='changed'
        with self.assertRaisesRegex(AssertionError,'Published baseline changed'):B.validate(ROOT,catalog,changed,rules)
        changed=copy.deepcopy(bundle);changed['remove'].append(next(iter(B.CONVERSIONS)))
        with self.assertRaisesRegex(AssertionError,'Lossless conversion'):B.validate(ROOT,catalog,changed,rules)
        changed=copy.deepcopy(catalog);changed['recipes'][2]['remove_recipe_ids'].append('draconicevolution:machines/draconic_relay_crystal_combine')
        with self.assertRaisesRegex(AssertionError,'Unexpected producer removal'):B.validate(ROOT,changed,bundle,rules)
        root=self.fixture(catalog,bundle,rules);B.apply(root);updated=B.read(root/'kubejs/config/aia2_recipes.json');updated['remove'].remove(catalog['recipes'][0]['remove_recipe_ids'][0])
        with self.assertRaisesRegex(AssertionError,'Cheap native fusion'):B.validate(root,catalog,updated,B.read(root/'kubejs/config/aia2_runtime.json'),compiled=True)

    def test_full_effective_export_scan_reproduces_every_family_producer(self):
        export=Path('/workspace/aia2-reference/export/recipes')
        if not export.is_dir():self.skipTest('External export unavailable')
        catalog,bundle,rules=self.inputs();report=B.validate(ROOT,catalog,bundle,rules,export_recipes=export)
        self.assertTrue(report['full_export_verified_this_run'])
        scan=B.scan_export(export)
        self.assertEqual(len(scan['targets']['draconicevolution:draconic_relay_crystal']),2)
        self.assertEqual(len(scan['targets']['draconicevolution:draconic_io_crystal']),1)

    def test_source_changes_and_vanilla_craft_task_conflicts_fail_closed(self):
        catalog,bundle,rules=self.inputs();root=self.fixture(catalog,bundle,rules)
        B.write(root/'content/quests/bad.json',{'quests':[{'id':'wrong','tasks':[{'type':'item','item':'draconicevolution:chaotic_crafting_injector','craft':True}]}]})
        with self.assertRaisesRegex(AssertionError,'craft:true'):B.validate(root,catalog,bundle,rules)
        B.write(root/'content/quests/bad.json',{'quests':[]})
        path=root/catalog['sources'][0]['path'];path.write_bytes(path.read_bytes()+b'\n')
        with self.assertRaisesRegex(AssertionError,'Stale energy source'):B.validate(root,catalog,bundle,rules)

    def test_idempotence_and_separate_process_hash_seeds(self):
        catalog,bundle,rules=self.inputs();root=self.fixture(catalog,bundle,rules);B.apply(root)
        paths=['kubejs/config/aia2_recipes.json','kubejs/config/aia2_runtime.json']
        before=[(root/p).read_bytes() for p in paths];B.apply(root)
        self.assertEqual(before,[(root/p).read_bytes() for p in paths])
        script='import sys;from pathlib import Path;from tools.build_draconic_power_v5 import apply;apply(Path(sys.argv[1]))'
        for seed in ['13','29']:
            result=subprocess.run([sys.executable,'-c',script,str(root)],cwd=ROOT,env=dict(os.environ,PYTHONHASHSEED=seed),capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stdout+result.stderr)
            self.assertEqual(before,[(root/p).read_bytes() for p in paths])
