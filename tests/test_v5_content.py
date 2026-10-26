"""Mutation tests for v5 content safety; these do not launch Minecraft."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('aia2_v5_validator', ROOT/'tools/validate_v5.py')
V = importlib.util.module_from_spec(spec)
spec.loader.exec_module(V)


class V5ContentValidationTests(unittest.TestCase):
    def setUp(self):
        self.rules = {'epochs': [{'number':n,'key':f'kubejs:key_{n}'} for n in range(1,49)],
                      'dualKeys': [{'output':'kubejs:tech_key'}],
                      'itemGates': {'minecraft:book':0,'minecraft:iron_ingot':1,
                                    'minecraft:redstone':4,'create:mechanical_press':4,
                                    'kubejs:tech_key':1,'mymod:creative_pool':99},
                      'blockGates': {'create:mechanical_press':4},'dimensionGates':{}}
        self.registries = {'item':set(self.rules['itemGates']), 'block':{'create:mechanical_press'},
                           'dimension':set(),'entity_type':set(),'worldgen/biome':set(),'custom_stat':set()}
        self.quest = {'id':'V5_FIRST','epoch':1,'title_uk':'Підготовка майстерні',
                      'description_uk':['Перевірте запас сировини й підготуйте матеріали для наступної виробничої операції. '
                                        'Завдання перевіряє зазначений комплект ресурсів у вашому інвентарі.'],
                      'icon':'minecraft:book','tasks':[{'type':'item','item':'minecraft:iron_ingot','count':8}],
                      'reward':[{'item':'minecraft:book','count':1}], 'after':[], 'required':False,'mod':'minecraft'}

    def test_real_objective_and_source_counts(self):
        report = V.validate_catalog([self.quest], self.rules, self.registries)
        self.assertEqual(report['new_authored_quests'],1)
        self.assertEqual(report['task_types'],{'item':1})

    def test_counts_and_text_cannot_disguise_duplicate_objectives(self):
        other = copy.deepcopy(self.quest);other['id']='V5_SECOND'
        other['tasks'][0]['count']=128;other['title_uk']='Інша назва того самого завдання'
        with self.assertRaisesRegex(AssertionError,'Duplicate objectives'):
            V.validate_catalog([self.quest,other],self.rules,self.registries)
        with self.assertRaisesRegex(AssertionError,'Duplicate objectives'):
            V.validate_catalog([other],self.rules,self.registries,old_records=[self.quest])

    def test_unregistered_and_future_items_are_rejected(self):
        for item in ['missing:invented_ingot','minecraft:redstone']:
            q=copy.deepcopy(self.quest);q['tasks'][0]['item']=item
            with self.subTest(item=item),self.assertRaises(AssertionError):
                V.validate_catalog([q],self.rules,self.registries)

    def test_empty_decorative_and_manual_tasks_are_rejected(self):
        for tasks in [[],[{'type':'checkmark'}],[{'type':'advancement','advancement':'aia2:stages/e01'}]]:
            q=copy.deepcopy(self.quest);q['tasks']=tasks
            with self.subTest(tasks=tasks),self.assertRaises(AssertionError):
                V.validate_catalog([q],self.rules,self.registries)

    def test_key_and_machine_rewards_do_not_bypass_production(self):
        for item,epoch in [('kubejs:tech_key',1),('create:mechanical_press',4)]:
            q=copy.deepcopy(self.quest);q['epoch']=epoch;q['reward']=[{'item':item,'count':1}]
            with self.subTest(item=item),self.assertRaises(AssertionError):
                V.validate_catalog([q],self.rules,self.registries)

    def test_post_completion_targets_require_actual_final_proof(self):
        q=copy.deepcopy(self.quest);q.update(epoch=48,post_completion=True)
        q['tasks'][0]['item']='mymod:creative_pool'
        compiled={V.uid(q['id']):{'title':q['title_uk'],'tasks':[
            {'id':V.uid(q['id']+':task:0'),'type':'item','item':{'id':'mymod:creative_pool','count':1},
             'count':8,'consume_items':False,'only_from_crafting':False},
            {'id':V.uid(q['id']+':stage'),'type':'advancement','advancement':'aia2:stages/e48'}]}}
        with self.assertRaisesRegex(AssertionError,'final completion proof'):
            V.validate_catalog([q],self.rules,self.registries,compiled)
        compiled[V.uid(q['id'])]['tasks'][-1]['advancement']='aia2:keys/e48'
        V.validate_catalog([q],self.rules,self.registries,compiled)
        q.pop('post_completion')
        with self.assertRaisesRegex(AssertionError,'Future quest target'):
            V.validate_catalog([q],self.rules,self.registries,compiled)

    def test_compiled_tasks_cannot_change_item_count_or_crafting_provenance(self):
        q=copy.deepcopy(self.quest)
        compiled={'tasks':[{'id':V.uid(q['id']+':task:0'),'type':'item',
                           'item':{'id':'minecraft:iron_ingot','count':1},'count':8,
                           'consume_items':False,'only_from_crafting':False},
                          {'id':V.uid(q['id']+':stage'),'type':'advancement','advancement':'aia2:stages/e01'}]}
        V.validate_compiled_tasks(q,compiled)
        for field,value in [('item',{'id':'minecraft:book','count':1}),('count',1),('only_from_crafting',True)]:
            changed=copy.deepcopy(compiled);changed['tasks'][0][field]=value
            with self.subTest(field=field),self.assertRaisesRegex(AssertionError,'semantics changed'):
                V.validate_compiled_tasks(q,changed)

    def test_actual_v4_save_contract_and_current_compiled_graph(self):
        snapshot=V.read(ROOT/'content/audit/v4-ids.json')
        chapters={p.name:V.read(p) for p in (ROOT/'config/ftbquests/quests/chapters').glob('*.snbt')}
        recipes=V.read(ROOT/'kubejs/config/aia2_recipes.json')['add']
        migration_file=ROOT/'content/audit/v5-migrations.json'
        migrations=V.read(migration_file).get('quests',[]) if migration_file.is_file() else []
        report=V.validate_preservation(snapshot,chapters,[r['id'] for r in recipes],migrations)
        self.assertGreater(report['preserved_quests'],2000)
        quests={q['id']:q for chapter in chapters.values() for q in chapter['quests']}
        self.assertEqual(V.validate_graph(quests),len(quests))
        current = V.validate(ROOT)
        self.assertEqual(current['status'], 'passed')
        self.assertEqual(current['compiled_quests'],len(quests))
        self.assertGreaterEqual(len(current['native_action_proofs']['approved_advancements']),49)

    def test_old_ids_dependencies_and_recipes_are_preserved(self):
        chapters={'one.snbt':{'id':'CHAPTER','quests':[{'id':'QUEST','tasks':[{'id':'TASK'}],
                            'rewards':[{'id':'REWARD'}],'dependencies':['PARENT']}]}}
        snapshot={'chapters':{'one.snbt':{'id':'CHAPTER','quests':[{'id':'QUEST','tasks':['TASK'],
                            'rewards':['REWARD'],'dependencies':['PARENT']}]}},'recipes':['aia2:old_recipe']}
        self.assertEqual(V.validate_preservation(snapshot,chapters,['aia2:old_recipe'])['preserved_quests'],1)
        for key in ['tasks','rewards','dependencies']:
            changed=copy.deepcopy(chapters)
            changed['one.snbt']['quests'][0][key]=['CHANGED'] if key=='dependencies' else [{'id':'CHANGED'}]
            with self.subTest(key=key),self.assertRaisesRegex(AssertionError,'Undocumented'):
                V.validate_preservation(snapshot,changed,['aia2:old_recipe'])
        with self.assertRaisesRegex(AssertionError,'recipe removed'):
            V.validate_preservation(snapshot,chapters,[])

    def test_migration_must_match_exact_old_and_new_contracts(self):
        old={'tasks':['TASK'],'rewards':[],'dependencies':['BEFORE']}
        new={'tasks':['TASK'],'rewards':[],'dependencies':['AFTER']}
        snapshot={'chapters':{'a':{'id':'CHAPTER','quests':[{'id':'QUEST',**old}]}},'recipes':[]}
        chapters={'a':{'id':'CHAPTER','quests':[{'id':'QUEST','tasks':[{'id':'TASK'}],
                         'dependencies':['AFTER']}]}}
        change={'quest_id':'QUEST','reason_uk':'Підтверджена міграція залежності зі збереженням усіх даних гравця.',
                'old':old,'new':new}
        V.validate_preservation(snapshot,chapters,[],[change])
        change['old']['dependencies']=['OTHER']
        with self.assertRaisesRegex(AssertionError,'exact old/new'):
            V.validate_preservation(snapshot,chapters,[],[change])

    def test_graph_missing_dependencies_and_cycles_are_rejected(self):
        for graph in [{'a':{'dependencies':['missing']}},
                      {'a':{'dependencies':['b']},'b':{'dependencies':['a']}}]:
            with self.subTest(graph=graph),self.assertRaises(AssertionError):
                V.validate_graph(graph)

    def research_fixture(self,root):
        source=root/'source.json';source.write_text('{"type":"minecraft:crafting_shaped"}')
        evidence={'path':'source.json','sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'verified':True}
        stage={'id':'first','epoch':1,'title_uk':'Початок досліджень','item_ids':['minecraft:iron_ingot'],
               'prerequisites':[],'existing_quest_ids':[],'new_quest_ids':['V5_FIRST']}
        return {'schema':1,'mods':[{'mod_id':'example','installed_version':'1.2.3','sources':[evidence],
                                  'stages':[stage]}]}

    def validate_research_fixture(self,root,document):
        return V.validate_research(root,[document],{'example':'1.2.3'},self.rules,self.registries,
                                  {self.quest['id']:self.quest},{V.uid(self.quest['id']):{}})

    def test_research_reports_partial_scope_without_claiming_completion(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);document=self.research_fixture(root)
            report=self.validate_research_fixture(root,document)
            self.assertEqual(report['hash_verified_source_files'],1)
            self.assertEqual(report['partial_or_gap_documented_mods'],1)
            self.assertNotIn('claimed_complete_mods',report)
            document['mods'][0]['complete']=True
            with self.assertRaisesRegex(AssertionError,'complete mod progression'):
                self.validate_research_fixture(root,document)

    def test_repeated_map_records_do_not_inflate_mod_or_source_file_counts(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);document=self.research_fixture(root)
            document['mods'].append(copy.deepcopy(document['mods'][0]))
            report=self.validate_research_fixture(root,document)
            self.assertEqual(report['research_mod_records'],2)
            self.assertEqual(report['research_mods'],1)
            self.assertEqual(report['partial_or_gap_documented_mod_records'],2)
            self.assertEqual(report['partial_or_gap_documented_mods'],1)
            self.assertEqual(report['hash_verified_source_references'],2)
            self.assertEqual(report['hash_verified_source_files'],1)

    def test_focused_partial_record_does_not_erase_a_completed_core_map(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);document=self.research_fixture(root)
            complete=copy.deepcopy(document['mods'][0]);complete['complete']=True
            complete['stages']=[dict(copy.deepcopy(complete['stages'][0]),id='stage_'+str(i)) for i in range(8)]
            document['mods'].append(complete)
            report=self.validate_research_fixture(root,document)
            self.assertEqual(report['research_mods'],1)
            self.assertEqual(report['claimed_complete_mods'],1)
            self.assertEqual(report['mods_with_partial_records'],1)
            self.assertEqual(report['partial_or_gap_documented_mods'],0)

    def test_verified_sources_require_portable_matching_hashes(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);document=self.research_fixture(root)
            for change in [{'path':'/outside/source.json'},{'sha256':'0'*64},{'path':'missing.json'}, {'path':'../escape.json'}]:
                changed=copy.deepcopy(document);changed['mods'][0]['sources'][0].update(change)
                with self.subTest(change=change),self.assertRaises(AssertionError):
                    self.validate_research_fixture(root,changed)
            with self.assertRaisesRegex(AssertionError,'path/hash'):
                V.verify_evidence(root,{'verified':True,'url':'https://example.invalid/docs'})

    def test_research_versions_items_quest_refs_and_stage_cycles_are_checked(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);document=self.research_fixture(root)
            for field,value in [('installed_version','wrong'),('mod_id','not_installed')]:
                changed=copy.deepcopy(document);changed['mods'][0][field]=value
                with self.subTest(field=field),self.assertRaisesRegex(AssertionError,'version mismatch'):
                    self.validate_research_fixture(root,changed)
            for field,value in [('item_ids',['invented:item']),('new_quest_ids',['V5_MISSING']),('prerequisites',['first'])]:
                changed=copy.deepcopy(document);changed['mods'][0]['stages'][0][field]=value
                with self.subTest(field=field),self.assertRaises(AssertionError):
                    self.validate_research_fixture(root,changed)

    def test_normal_epoch48_research_cannot_depend_on_post_completion_stage(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);document=self.research_fixture(root)
            parent=document['mods'][0]['stages'][0]
            parent.update(epoch=48,post_completion=True)
            child=copy.deepcopy(parent)
            child.update(id='ordinary_final_epoch',post_completion=False,prerequisites=['first'])
            document['mods'][0]['stages'].append(child)
            with self.assertRaisesRegex(AssertionError,'future stage'):
                self.validate_research_fixture(root,document)
            child['post_completion']=True
            self.validate_research_fixture(root,document)

    def mechanic_fixture(self):
        temporary = tempfile.TemporaryDirectory(prefix='aia2-mechanic-contract-')
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        config = root/'kubejs/config/aia2_mechanics.json'
        config.parent.mkdir(parents=True)
        config.write_bytes((ROOT/'kubejs/config/aia2_mechanics.json').read_bytes())
        shutil.copytree(ROOT/'kubejs/data/aia2/advancement/mechanics',
                        root/'kubejs/data/aia2/advancement/mechanics')
        for rule in V.read(config)['rules']:
            for source in rule['evidence']:
                if source.get('frozen_path'):
                    dest = root/source['frozen_path'];dest.parent.mkdir(parents=True,exist_ok=True)
                    dest.write_bytes((ROOT/source['frozen_path']).read_bytes())
        return root, config

    def test_only_eight_source_backed_native_process_contracts_are_approved(self):
        rules = V.read(ROOT/'kubejs/config/aia2_runtime.json')
        bundle = V.read(ROOT/'kubejs/config/aia2_recipes.json')
        allowed = V.verified_mechanic_advancements(ROOT, rules, bundle)
        self.assertEqual(allowed, {'aia2:mechanics/'+name for name in V.MECHANIC_CONTRACT})
        document = V.read(ROOT/'kubejs/config/aia2_mechanics.json')
        brass = next(r for r in document['rules'] if r['id']=='brass_mixing')
        self.assertIn('aia2:bootstrap/epoch_10_1', brass['recipeIds'])
        producer = next(r['json'] for r in bundle['add'] if r['id']=='aia2:bootstrap/epoch_10_1')
        self.assertNotIn('heat_requirement', producer,
                         'Epoch10 must have an attainable route before the epoch15 Blaze Burner')

    def test_native_contract_cannot_change_output_stage_or_recipe_alias(self):
        rules = V.read(ROOT/'kubejs/config/aia2_runtime.json')
        bundle = V.read(ROOT/'kubejs/config/aia2_recipes.json')
        for field, value in [('epoch',1), ('output','minecraft:iron_ingot'),
                             ('recipeIds',['invented:recipe'])]:
            root, path = self.mechanic_fixture()
            document = V.read(path); document['rules'][0][field] = value
            path.write_text(json.dumps(document))
            with self.subTest(field=field), self.assertRaises(AssertionError):
                V.verified_mechanic_advancements(root, rules, bundle)

    def test_inventory_or_missing_advancement_cannot_replace_native_execution(self):
        rules = V.read(ROOT/'kubejs/config/aia2_runtime.json')
        bundle = V.read(ROOT/'kubejs/config/aia2_recipes.json')
        for trigger in ['minecraft:inventory_changed', 'missing']:
            root, _ = self.mechanic_fixture()
            path = root/'kubejs/data/aia2/advancement/mechanics/andesite_mixing.json'
            if trigger == 'missing': path.unlink()
            else: path.write_text(json.dumps({'criteria':{'native_process':{'trigger':trigger}}}))
            with self.subTest(trigger=trigger), self.assertRaisesRegex(AssertionError,'impossible trigger'):
                V.verified_mechanic_advancements(root, rules, bundle)

    def test_frozen_native_evidence_and_removed_producers_are_checked(self):
        rules = V.read(ROOT/'kubejs/config/aia2_runtime.json')
        bundle = V.read(ROOT/'kubejs/config/aia2_recipes.json')
        root, path = self.mechanic_fixture()
        document = V.read(path)
        document['rules'][0]['evidence'][0]['json']['results'][0]['id'] = 'minecraft:iron_ingot'
        path.write_text(json.dumps(document))
        with self.assertRaisesRegex(AssertionError, 'hash mismatch'):
            V.verified_mechanic_advancements(root, rules, bundle)
        changed = copy.deepcopy(bundle)
        changed['remove'].append('create:mixing/andesite_alloy')
        with self.assertRaisesRegex(AssertionError, 'producer was removed'):
            V.verified_mechanic_advancements(ROOT, rules, changed)

    def test_epoch10_runtime_producer_must_match_frozen_evidence(self):
        rules = V.read(ROOT/'kubejs/config/aia2_runtime.json')
        bundle = V.read(ROOT/'kubejs/config/aia2_recipes.json')
        producer = next(r for r in bundle['add'] if r['id']=='aia2:bootstrap/epoch_10_1')
        producer['json']['heat_requirement'] = 'heated'
        with self.assertRaisesRegex(AssertionError, 'runtime producer differs'):
            V.verified_mechanic_advancements(ROOT, rules, bundle)

    def test_verified_native_execution_is_meaningful_but_never_a_future_goal(self):
        q=copy.deepcopy(self.quest); q['epoch']=4
        q['tasks']=[{'type':'advancement','advancement':'aia2:mechanics/andesite_mixing'}]
        allowed={'aia2:mechanics/'+name for name in V.MECHANIC_CONTRACT}
        V.validate_catalog([q],self.rules,self.registries,mechanic_advancements=allowed)
        with self.assertRaisesRegex(AssertionError,'Unverified native mechanic'):
            V.validate_catalog([q],self.rules,self.registries)
        q['tasks'][0]['advancement']='aia2:mechanics/infused_alloy'
        with self.assertRaisesRegex(AssertionError,'Future native mechanic'):
            V.validate_catalog([q],self.rules,self.registries,mechanic_advancements=allowed)

    def test_authored_dependency_cannot_require_a_future_or_postgame_parent(self):
        parent=copy.deepcopy(self.quest)
        parent.update(id='V5_PARENT',epoch=4)
        parent['tasks']=[{'type':'item','item':'minecraft:redstone','count':2}]
        child=copy.deepcopy(self.quest);child['after']=['V5_PARENT']
        with self.assertRaisesRegex(AssertionError,'future authored goal'):
            V.validate_catalog([child],self.rules,self.registries,old_records=[parent])
        parent.update(epoch=48,post_completion=True);child['epoch']=48
        with self.assertRaisesRegex(AssertionError,'future authored goal'):
            V.validate_catalog([child],self.rules,self.registries,old_records=[parent])
        child['post_completion']=True
        V.validate_catalog([child],self.rules,self.registries,old_records=[parent])


if __name__=='__main__':
    unittest.main()
