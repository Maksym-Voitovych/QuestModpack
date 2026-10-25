"""Pin real native-action semantics and narrow repairs; fullpack dispatch is separate."""
import copy
import hashlib
import json
from pathlib import Path
import unittest

from tools.quest_content_migrations import apply

ROOT = Path(__file__).resolve().parents[1]


def read(path):
    return json.loads((ROOT/path).read_text())


class ApotheosisPetroleumDepthTests(unittest.TestCase):
    def test_purity_proofs_use_exact_codec_and_post_consumption_dispatch(self):
        base = ROOT/'content/research/evidence/apotheosis_core_next_v5/apotheosis'
        trigger = (base/'src/main/java/dev/shadowsoffire/apotheosis/advancements/GemCutTrigger.java').read_text()
        menu = (base/'src/main/java/dev/shadowsoffire/apotheosis/socket/gem/cutting/GemCuttingMenu.java').read_text()
        self.assertIn('ItemPredicate.CODEC.fieldOf("item")', trigger)
        self.assertIn('Purity.CODEC.optionalFieldOf("purity")', trigger)
        self.assertIn('this.purity.get() == inst.purity()', trigger)
        self.assertLess(menu.index('r.decrementInputs(this.rInput, player.level())'),
                        menu.index('Apoth.Triggers.GEM_CUTTING.trigger((ServerPlayer) player, out)'))
        self.assertLess(menu.index('this.inv.setStackInSlot(0, out)'),
                        menu.index('Apoth.Triggers.GEM_CUTTING.trigger((ServerPlayer) player, out)'))
        for purity in ['chipped', 'normal', 'perfect']:
            proof = read('kubejs/data/aia2/advancement/apotheosis/cut_'+purity+'.json')
            self.assertEqual(proof['criteria'], {'cut': {'trigger':'apotheosis:gem_cutting',
                'conditions':{'item':{'items':'apotheosis:gem'},'purity':purity}}})
            self.assertEqual(proof['requirements'], [['cut']])

    def test_frontier_proves_five_native_equipment_actions(self):
        path = 'content/research/evidence/apotheosis_core_next_v5/apotheosis/src/generated/resources/data/apotheosis/advancement/progression/frontier.json'
        proof = read(path)
        self.assertEqual(len(proof['criteria']),5)
        self.assertEqual({c['conditions']['slots'] for c in proof['criteria'].values()},
                         {'head','chest','legs','feet','hand'})
        self.assertEqual({c['trigger'] for c in proof['criteria'].values()}, {'apotheosis:equipped_item'})
        self.assertEqual({tuple(group) for group in proof['requirements']},
                         {(name,) for name in proof['criteria']})
        for criterion in proof['criteria'].values():
            self.assertIn('apotheosis:item_with_rarity',criterion['conditions']['items']['predicates'])

    def test_petroleum_repairs_match_actual_outputs_and_keep_save_identity(self):
        audit = read('content/audit/v5-petroleum-target-repairs.json')
        for source in audit['sources']:
            self.assertEqual(hashlib.sha256((ROOT/source['path']).read_bytes()).hexdigest(),source['sha256'])
        base = 'content/research/evidence/petroleum_core_next_v5/exported_recipes/'
        tower = read(base+'distillationtower/oil.json');coker = read(base+'coking/petcoke.json')
        self.assertEqual(tower['input']['amount'],60)
        self.assertIn('immersivepetroleum:diesel_sulfur',{s['id'] for s in tower['results']})
        self.assertNotIn('immersivepetroleum:diesel',{s['id'] for s in tower['results']})
        self.assertEqual(coker['result']['id'],'immersivepetroleum:petcoke')
        self.assertEqual(coker['resultfluid']['id'],'immersivepetroleum:diesel_sulfur')
        records=[q for p in sorted((ROOT/'content/quests').glob('*.json'))
                 for d in [json.loads(p.read_text())] for q in (d if isinstance(d,list) else d['quests'])]
        original = copy.deepcopy(records);repaired={q['id']:q for q in apply(records,ROOT)}
        self.assertEqual(records,original)
        for change in audit['changes']:
            old=next(q for q in records if q['id']==change['quest']);new=repaired[old['id']]
            self.assertEqual(old['tasks'][change['task_index']]['item'],change['from'])
            self.assertEqual(new['tasks'][change['task_index']]['item'],change['to'])
            self.assertEqual(old['after'],new['after']);self.assertEqual(old['reward'],new['reward'])
            self.assertEqual(len(old['tasks']),len(new['tasks']))

    def test_petroleum_native_grants_distinguish_setup_service_and_energy(self):
        contracts=read('content/audit/v5-native-advancement-contracts.json')['advancements']
        ip=[c for c in contracts if c['mod_id']=='immersivepetroleum']
        self.assertEqual(len(ip),10)
        for contract in ip:
            if contract.get('dispatch_mode')=='direct_native_grant':
                grant=contract['direct_grant'];source=(ROOT/grant['path']).read_text()
                self.assertTrue(all(token in source for token in grant['required_source_tokens']))
            else:
                self.assertEqual(contract['trigger_mod_versions'], {'immersiveengineering':'12.4.2-194'})
                proof=read(contract['json_path'])
                self.assertEqual({c['trigger'] for c in proof['criteria'].values()},
                                 {'immersiveengineering:multiblock_formed'})
        generator=next(c for c in ip if c['id'].endswith('/gas_generator'))
        self.assertIn('не виробництво енергії',generator['proof_scope_uk'])
        survey=next(c for c in ip if c['id'].endswith('/root'))
        self.assertTrue(any('CRUDEOIL' in t for t in survey['direct_grant']['required_source_tokens']))
