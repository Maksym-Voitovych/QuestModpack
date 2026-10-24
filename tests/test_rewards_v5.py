"""Reward changes preserve IDs/progress and use only curated reachable-era materials."""
import copy
import hashlib
import json
import os
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

from tools import build_rewards_v5 as rewards

ROOT = Path(__file__).resolve().parents[1]


class RewardsV5Test(unittest.TestCase):
    def fixture(self, directory):
        root=Path(directory)
        for relative in [rewards.POLICY,'content/audit/registries.json',
                         'kubejs/config/aia2_runtime.json','design/progression.json']:
            dest=root/relative;dest.parent.mkdir(parents=True,exist_ok=True)
            shutil.copyfile(ROOT/relative,dest)
        records=[];quests=[]
        for logical,epoch,mod,item in [('V5_E04_create_01',4,'create','create:andesite_alloy'),
                                        ('V5_E05_botania_01',5,'botania','botania:mana_powder'),
                                        ('V5_E21_botania_02',21,'botania','botania:elementium_ingot')]:
            record={'id':logical,'epoch':epoch,'mod':mod,'icon':item,'tasks':[{'type':'item','item':item}],
                    'reward':[{'item':'minecraft:bread','count':4}]}
            records.append(record)
            quests.append({'id':rewards.uid(logical),'title':logical,'icon':{'id':item,'count':1},
                           'tasks':[{'id':rewards.uid(logical+':task'),'type':'item','item':{'id':item}}],
                           'rewards':[{'id':rewards.uid(logical+':reward:0'),'type':'item',
                                       'item':{'id':'minecraft:bread','count':1},'count':4}]})
        quests.append({'id':'fixture_final','title':'existing final','icon':{'id':'minecraft:book'},'tasks':[],
                       'rewards':[{'id':'stable-command','type':'command','command':'aia2 sync','permission_level':2}]})
        rewards.write(root/'content/quests/v5_technology_mechanics.json',{'quests':records})
        path=root/'config/ftbquests/quests/chapters/aia2_epoch_01.snbt'
        rewards.write(path,{'id':'fixture-chapter','quests':quests})
        return root,path

    def test_policy_uses_real_registry_canonical_materials_and_source_evidence(self):
        root=ROOT;policy=rewards.read(root/rewards.POLICY)
        allowed=rewards.validate_policy(root,policy,rewards.read(root/'kubejs/config/aia2_runtime.json')['itemGates'])
        self.assertGreater(len(allowed),90)
        self.assertEqual(policy['aliases']['ars_elemental']['profile'],'ars_nouveau')
        self.assertGreaterEqual(next(e['min_epoch'] for e in policy['profiles']['botania']['entries'] if 'elementium' in e['item']),21)
        if Path('/workspace/aia2-reference/export/recipes').is_dir():
            result=rewards.verify_producers(policy,'/workspace/aia2-reference/export')
            self.assertGreater(result['sources_verified'],200)

    def test_apply_preserves_ids_commands_nonreward_fields_and_source_catalogs(self):
        with tempfile.TemporaryDirectory() as directory,patch.dict(os.environ,{'AIA2_EXPORT_ROOT':directory+'/not-installed'}):
            root,path=self.fixture(directory);before=rewards.read(path)
            source=root/'content/quests/v5_technology_mechanics.json';digest=hashlib.sha256(source.read_bytes()).hexdigest()
            report=rewards.apply(root);after=rewards.read(path)
            self.assertEqual(report['item_rewards_audited'],3)
            self.assertEqual(report['command_rewards_preserved'],1)
            self.assertEqual(report['new_final_item_rewards'],0)
            self.assertEqual(before['quests'][-1],after['quests'][-1])
            for old,new in zip(before['quests'],after['quests']):
                self.assertEqual([r['id'] for r in old['rewards']],[r['id'] for r in new['rewards']])
                old.pop('rewards');new.pop('rewards');self.assertEqual(old,new)
            self.assertEqual(digest,hashlib.sha256(source.read_bytes()).hexdigest())
            self.assertEqual(rewards.validate(root)['future_or_banned_rewards'],0)
            first=path.read_bytes();rewards.apply(root);self.assertEqual(first,path.read_bytes())

    def test_early_botania_cannot_receive_alfheim_materials(self):
        with tempfile.TemporaryDirectory() as directory,patch.dict(os.environ,{'AIA2_EXPORT_ROOT':directory+'/none'}):
            root,path=self.fixture(directory);rewards.apply(root)
            data=rewards.read(path)
            early=data['quests'][1]['rewards'][0]['item']['id']
            self.assertNotIn(early,{'botania:elementium_nugget','botania:pixie_dust','botania:dragonstone'})
            self.assertTrue(early.startswith('botania:'))
            create=data['quests'][0]['rewards'][0]['item']['id'];self.assertTrue(create.startswith('create:'))

    def test_semantic_minimum_failure_prevents_any_chapter_write(self):
        with tempfile.TemporaryDirectory() as directory,patch.dict(os.environ,{'AIA2_EXPORT_ROOT':directory+'/none'}):
            root,path=self.fixture(directory);policy=rewards.read(root/rewards.POLICY)
            for entry in policy['profiles']['botania']['entries']:
                if 'elementium' in entry['item']:entry['min_epoch']=5
            rewards.write(root/rewards.POLICY,policy);before=path.read_bytes()
            with self.assertRaisesRegex(AssertionError,'Premature Alfheim'):rewards.apply(root)
            self.assertEqual(before,path.read_bytes())

    def test_machine_creative_boss_and_invalid_counts_are_rejected(self):
        original=rewards.read(ROOT/rewards.POLICY)
        gates=rewards.read(ROOT/'kubejs/config/aia2_runtime.json')['itemGates']
        for item in ['create:mechanical_press','create:creative_motor','botania:life_essence']:
            with self.subTest(item=item):
                policy=copy.deepcopy(original);entry=policy['profiles']['create']['entries'][0]
                entry.update(item=item,min_epoch=max(1,gates.get(item,48)))
                with self.assertRaises(AssertionError):rewards.validate_policy(ROOT,policy,gates)
        for count in [0,1,5,8,9,64,True,2.5]:
            with self.subTest(count=count):
                policy=copy.deepcopy(original);policy['profiles']['create']['entries'][0]['count']=count
                with self.assertRaises(AssertionError):rewards.validate_policy(ROOT,policy,gates)

    def test_changed_compiled_reward_or_forged_source_is_detected(self):
        with tempfile.TemporaryDirectory() as directory,patch.dict(os.environ,{'AIA2_EXPORT_ROOT':directory+'/none'}):
            root,path=self.fixture(directory);rewards.apply(root);chapter=rewards.read(path)
            chapter['quests'][0]['rewards'][0]['item']['id']='create:creative_motor'
            rewards.write(path,chapter)
            with self.assertRaisesRegex(AssertionError,'Reward policy mismatch'):rewards.validate(root)
        if Path('/workspace/aia2-reference/export/recipes').is_dir():
            policy=rewards.read(ROOT/rewards.POLICY)
            policy['profiles']['create']['entries'][0]['producer_evidence']['recipes'][0]['source_sha256']='0'*64
            with self.assertRaisesRegex(AssertionError,'Changed producer source'):
                rewards.verify_producers(policy,'/workspace/aia2-reference/export')


if __name__=='__main__':unittest.main()
