"""Reproduce source-reviewed machine replacements without touching the real runtime."""
import copy
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from tools import build_industrial_core_balance_v5 as B

ROOT = Path(__file__).resolve().parents[1]


class IndustrialCoreBalanceTests(unittest.TestCase):
    def inputs(self):
        return (B.read(ROOT/B.CATALOG), B.read(ROOT/'kubejs/config/aia2_recipes.json'),
                B.read(ROOT/'kubejs/config/aia2_runtime.json'))

    def fixture(self, catalog, bundle, rules):
        temporary = tempfile.TemporaryDirectory(prefix='aia2-industrial-core-')
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        for rel, data in [(B.CATALOG,catalog),('kubejs/config/aia2_recipes.json',bundle),('kubejs/config/aia2_runtime.json',rules)]:
            p=root/rel;p.parent.mkdir(parents=True,exist_ok=True);B.write(p,data)
        sources = catalog['sources']+[catalog['producer_scan']]+[
            source for spec in catalog['recipes'] for source in spec['sources']]+[
            evidence['source'] for evidence in catalog['tag_evidence'].values()]
        for source in sources:
            p=root/source['path'];p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((ROOT/source['path']).read_bytes())
        (root/'implementation').mkdir()
        return root

    def test_native_material_costs_and_real_machine_capacities_are_preserved(self):
        catalog,bundle,rules=self.inputs()
        report=B.validate(ROOT,catalog,bundle,rules)
        self.assertEqual(report['published_custom_recipes_preserved'],606)
        self.assertEqual(report['native_producers_replaced'],6)
        self.assertEqual(report['serializers'],{'modern_industrialization:assembler':3,'oritech:assembler':1})
        fuel=next(r for r in catalog['recipes'] if r['target']=='oritech:fuel_generator_block')
        amounts=B.cost(B.inputs(fuel['json']))
        self.assertEqual(amounts[('tag','c:ingots/steel')],7)
        self.assertEqual(amounts[('item','oritech:basic_generator_block')],2)
        self.assertEqual(amounts[('tag','oritech:plating')],1)
        self.assertEqual(amounts[('item','oritech:enderic_lens')],1)
        self.assertEqual(amounts[('item','botania:rune_fire')],1)
        controller=next(r for r in catalog['recipes'] if r['target']=='oritech:reactor_controller')
        self.assertEqual(B.cost(B.inputs(controller['json']))[('item','oritech:processing_unit')],2)
        self.assertEqual(len(controller['json']['ingredients']),4)

    def test_future_inputs_bootstrap_cycles_weakened_cost_and_unsupported_capacity_fail(self):
        catalog,bundle,rules=self.inputs()
        changed=copy.deepcopy(catalog);changed['recipes'][0]['json']['item_inputs'][-1]['item']='missing:invented_part'
        with self.assertRaisesRegex(AssertionError,'Future/unknown'):B.validate(ROOT,changed,bundle,rules)
        changed=copy.deepcopy(catalog);changed['recipes'][0]['json']['item_inputs'][-1]['item']='modern_industrialization:mv_diesel_generator'
        with self.assertRaisesRegex(AssertionError,'bootstrap/key'):B.validate(ROOT,changed,bundle,rules)
        changed=copy.deepcopy(catalog);fuel=next(r for r in changed['recipes'] if r['target']=='oritech:fuel_generator_block')
        fuel['json']['item_inputs'][0]['amount']=1
        with self.assertRaisesRegex(AssertionError,'material cost weakened'):B.validate(ROOT,changed,bundle,rules)
        changed=copy.deepcopy(catalog);controller=next(r for r in changed['recipes'] if r['target']=='oritech:reactor_controller')
        controller['json']['ingredients'].append({'item':'minecraft:stone'})
        with self.assertRaises(AssertionError):B.validate(ROOT,changed,bundle,rules)
        changed_rules=copy.deepcopy(rules);changed_rules['blockGates']['modern_industrialization:assembler']=26
        with self.assertRaises(AssertionError):B.validate(ROOT,catalog,bundle,changed_rules)

    def test_published_recipe_drift_and_reopened_native_alternatives_are_detected(self):
        catalog,bundle,rules=self.inputs()
        changed=copy.deepcopy(bundle)
        next(r for r in changed['add'] if r['id'] in catalog['baseline_recipe_hashes'])['epoch']=-1
        with self.assertRaisesRegex(AssertionError,'baseline changed'):B.validate(ROOT,catalog,changed,rules)
        root=self.fixture(catalog,bundle,rules);B.apply(root)
        actual=B.read(root/'kubejs/config/aia2_recipes.json');updated=B.read(root/'kubejs/config/aia2_runtime.json')
        self.assertEqual(updated['itemGates']['oritech:reactor_controller'],32)
        self.assertEqual(updated['blockGates']['oritech:reactor_controller'],32)
        self.assertEqual(len(actual['add'])-len([r for r in bundle['add'] if not r['id'].startswith(B.PREFIX)]),4)
        original='modern_industrialization:electric_age/machine/mv_diesel_generator_asbl'
        actual['remove'].remove(original)
        with self.assertRaisesRegex(AssertionError,'cheaper route remains'):B.validate(root,catalog,actual,updated,compiled=True)

    def test_apply_is_idempotent_and_hash_seed_independent(self):
        catalog,bundle,rules=self.inputs();root=self.fixture(catalog,bundle,rules)
        B.apply(root)
        paths=['kubejs/config/aia2_recipes.json','kubejs/config/aia2_runtime.json']
        first={rel:(root/rel).read_bytes() for rel in paths};B.apply(root)
        self.assertEqual(first,{rel:(root/rel).read_bytes() for rel in paths})
        fresh_rules=copy.deepcopy(rules)
        for ident in list(fresh_rules['recipeGates']):
            if ident.startswith(B.PREFIX):del fresh_rules['recipeGates'][ident]
        outputs=[]
        for seed in ['11','29']:
            B.write(root/paths[0],bundle);B.write(root/paths[1],fresh_rules)
            env=os.environ.copy();env.update(PYTHONHASHSEED=seed,PYTHONPATH=str(ROOT))
            command=[sys.executable,'-c','from tools.build_industrial_core_balance_v5 import apply; import sys; apply(sys.argv[1])',str(root)]
            result=subprocess.run(command,env=env,text=True,capture_output=True)
            self.assertEqual(result.returncode,0,result.stdout+result.stderr)
            outputs.append({rel:(root/rel).read_bytes() for rel in paths})
        self.assertEqual(outputs[0],outputs[1])
