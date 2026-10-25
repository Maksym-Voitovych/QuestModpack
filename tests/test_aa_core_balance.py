import copy
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from tools import build_core_balance_v5 as B

ROOT = Path(__file__).resolve().parents[1]


class AACoreBalanceTests(unittest.TestCase):
    def inputs(self):
        return (B.read(ROOT/B.CATALOG), B.read(ROOT/'kubejs/config/aia2_recipes.json'),
                B.read(ROOT/'kubejs/config/aia2_runtime.json'))

    def test_three_machine_routes_preserve_existing603_and_paid_resets(self):
        data,bundle,rules=self.inputs()
        report=B.validate(ROOT,data,bundle,rules)
        self.assertEqual(report['baseline_custom_recipes_preserved'],603)
        self.assertEqual(report['recipes'],3)
        self.assertEqual(len(report['reset_routes_preserved']),3)
        # No oil is an input: the press/barrel/generator chain can start before fuel.
        for spec in data['recipes']:
            self.assertFalse(any(value['item'] in {'actuallyadditions:canola_oil_bucket',
                'actuallyadditions:refined_canola_oil_bucket', 'actuallyadditions:crystallized_canola_oil_bucket',
                'actuallyadditions:empowered_canola_oil_bucket'} for value in spec['json']['key'].values()))

    def test_future_ingredient_bootstrap_cycle_and_recipe_drift_fail(self):
        data,bundle,rules=self.inputs()
        for item in ['unregistered:part','actuallyadditions:oil_generator']:
            changed=copy.deepcopy(data);changed['recipes'][0]['json']['key']['M']['item']=item
            with self.subTest(item=item),self.assertRaises(AssertionError):B.validate(ROOT,changed,bundle,rules)
        changed=copy.deepcopy(rules);changed['itemGates']['botania:manasteel_ingot']=17
        with self.assertRaisesRegex(AssertionError,'Future/unknown'):B.validate(ROOT,data,bundle,changed)
        changed=copy.deepcopy(bundle);entry=next(r for r in changed['add'] if r['id'] in data['baseline_recipe_hashes']);entry['epoch']=1
        with self.assertRaisesRegex(AssertionError,'Published recipe changed'):B.validate(ROOT,data,changed,rules)
        changed=copy.deepcopy(bundle);changed['remove'].append('actuallyadditions:reset/canola_press')
        with self.assertRaisesRegex(AssertionError,'reset recipe removed'):B.validate(ROOT,data,changed,rules)

    def test_apply_is_idempotent_and_does_not_replace_unrelated_custom_recipes(self):
        data,bundle,rules=self.inputs()
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            for rel,value in [(B.CATALOG,data),('kubejs/config/aia2_recipes.json',bundle),('kubejs/config/aia2_runtime.json',rules)]:
                p=root/rel;p.parent.mkdir(parents=True,exist_ok=True);B.write(p,value)
            for row in data['recipes']:
                for source in row['sources']:
                    p=root/source['path'];p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((ROOT/source['path']).read_bytes())
            (root/'implementation').mkdir()
            B.apply(root)
            first=(root/'kubejs/config/aia2_recipes.json').read_bytes();B.apply(root)
            self.assertEqual(first,(root/'kubejs/config/aia2_recipes.json').read_bytes())
            after=B.read(root/'kubejs/config/aia2_recipes.json')
            self.assertEqual({r['id']:r for r in bundle['add'] if not r['id'].startswith(B.PREFIX)},
                             {r['id']:r for r in after['add'] if not r['id'].startswith(B.PREFIX)})
            # Separate Python processes must order new gate IDs identically.
            # Same-process idempotence cannot detect randomized set iteration.
            fresh_rules=copy.deepcopy(rules)
            for ident in list(fresh_rules['recipeGates']):
                if ident.startswith(B.PREFIX):del fresh_rules['recipeGates'][ident]
            outputs=[]
            for seed in ['11','29']:
                B.write(root/'kubejs/config/aia2_runtime.json',fresh_rules)
                B.write(root/'kubejs/config/aia2_recipes.json',bundle)
                env=os.environ.copy();env.update(PYTHONHASHSEED=seed,PYTHONPATH=str(ROOT))
                result=subprocess.run([sys.executable,'-c','from tools.build_core_balance_v5 import apply; import sys; apply(sys.argv[1])',str(root)],
                                      env=env,text=True,capture_output=True)
                self.assertEqual(result.returncode,0,result.stdout+result.stderr)
                outputs.append((root/'kubejs/config/aia2_runtime.json').read_bytes())
            self.assertEqual(outputs[0],outputs[1],'New recipe gates must not depend on PYTHONHASHSEED')
