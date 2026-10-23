"""Mutation checks for the compiled native manufacture/transition contract.

These inspect the real generated files; they do not claim native Minecraft event
execution. Runtime receipt and inventory transaction tests live in their own
Java/Rhino suites.
"""
import copy
import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('aia2_contract_validator',ROOT/'tools/validate_game_pack.py')
VALIDATOR=importlib.util.module_from_spec(spec)
spec.loader.exec_module(VALIDATOR)


class DualManufactureContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rules=json.loads((ROOT/'kubejs/config/aia2_runtime.json').read_text())
        cls.bundle=json.loads((ROOT/'kubejs/config/aia2_recipes.json').read_text())
        cls.quests={q['id']:q for path in (ROOT/'config/ftbquests/quests/chapters').glob('*.snbt')
                    for q in json.loads(path.read_text())['quests']}
        if cls.rules.get('progressionVersion',3)<4:
            raise AssertionError('Compile the v4 dual-key runtime before running the v4 contract suite')

    def setUp(self):
        self.rules=copy.deepcopy(self.__class__.rules)
        self.bundle=copy.deepcopy(self.__class__.bundle)
        self.quests=copy.deepcopy(self.__class__.quests)

    def validate(self,root=ROOT):
        return VALIDATOR.validate_dual_keys(root,self.rules,self.bundle,self.quests)

    def test_all_96_manufacture_contracts_and_48_transitions(self):
        result=self.validate()
        self.assertEqual(result['keys'],96)
        self.assertEqual(result['transition_costs_checked'],48)
        self.assertGreater(len(result['native_processes']),1)

    def test_possession_task_cannot_replace_a_real_manufacture_proof(self):
        epoch=self.rules['epochs'][0]
        quest=self.quests[epoch['branchKeyQuestIds']['tech']]
        quest['tasks']=[{'id':quest['tasks'][0]['id'],'type':'item',
                         'item':{'id':epoch['branchKeys']['tech'],'count':1},'count':1}]
        with self.assertRaises(AssertionError):self.validate()

    def test_one_key_transition_and_future_component_are_rejected(self):
        first=self.rules['epochs'][0]
        first['transitionCost'].pop(first['branchKeys']['arcane'])
        with self.assertRaises(AssertionError):self.validate()
        self.rules=copy.deepcopy(self.__class__.rules)
        recipe_id=self.rules['dualKeys'][0]['recipeId']
        recipe=next(entry['json'] for entry in self.bundle['add'] if entry['id']==recipe_id)
        ingredient=next(iter(recipe['key'].values()))['item']
        self.rules['itemGates'][ingredient]=48
        with self.assertRaises(AssertionError):self.validate()

    def test_receipt_route_alias_and_branch_dependency_deadlock_are_rejected(self):
        self.rules['dualKeys'][1]['recipeId']=self.rules['dualKeys'][0]['recipeId']
        with self.assertRaises(AssertionError):self.validate()
        self.rules=copy.deepcopy(self.__class__.rules)
        epoch=self.rules['epochs'][0]
        qid=epoch['branchQuestIds']['tech'][0]
        self.quests[qid].setdefault('dependencies',[]).append(epoch['finalQuestId'])
        with self.assertRaises(AssertionError):self.validate()

    def test_inventory_advancement_trigger_cannot_issue_manufacture_evidence(self):
        with tempfile.TemporaryDirectory(prefix='aia2-proof-validation-') as temp:
            root=Path(temp)
            target=root/'kubejs/data/aia2/advancement/production'
            shutil.copytree(ROOT/'kubejs/data/aia2/advancement/production',target)
            path=target/'tech_01.json'
            path.write_text(json.dumps({'criteria':{'native_manufacture':{
                'trigger':'minecraft:inventory_changed','conditions':{'items':[]}}}}))
            with self.assertRaises(AssertionError):self.validate(root)


if __name__=='__main__':unittest.main()
