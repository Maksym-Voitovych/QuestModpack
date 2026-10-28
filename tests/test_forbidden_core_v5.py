"""Exact-version Forbidden Arcanus course; no fullpack dispatch claim."""
import copy
import hashlib
import json
from pathlib import Path
import unittest

from tools import quest_content_migrations, validate_native_advancements_v5 as native
from tools import validate_v5 as V

ROOT=Path(__file__).resolve().parents[1]
FOLDER=ROOT/'content/research/evidence/forbidden_core_next_v5'
read=lambda p:json.loads(Path(p).read_text())

class ForbiddenCoreTests(unittest.TestCase):
    def setUp(self):
        self.quests=read(ROOT/'content/quests/v5_forbidden_core_depth.json')['quests']
        self.mod=next(m for m in read(ROOT/'content/research/magic_adventure_v5.json')['mods'] if m['mod_id']=='forbidden_arcanus')
        self.rules=read(ROOT/'kubejs/config/aia2_runtime.json')
        self.registries={k:set(v) for k,v in read(ROOT/'content/audit/registries.json')['registries'].items()}
        self.actions={t['advancement'] for q in self.quests for t in q['tasks'] if t['type']=='advancement'}

    def test_exact_source_hashes_and_prior_stage_identity(self):
        manifest=read(FOLDER/'manifest.json')
        self.assertEqual(manifest['pin'],'34f83feb76204fd773e1d2e1d69ecc5b2f2bb933')
        self.assertEqual(manifest['installed_version'],'2.6.1')
        self.assertEqual(len(manifest['sources']),49)
        for source in manifest['sources']:
            self.assertEqual(hashlib.sha256((ROOT/source['path']).read_bytes()).hexdigest(),source['sha256'])
        properties=(FOLDER/'official/gradle.properties').read_text()
        self.assertIn('mod_version=2.6.1',properties)
        self.assertIn('minecraft_version=1.21.1',properties)
        self.assertEqual([{'id':s['id'],'existing':s.get('existing_quest_ids',[]),'new':s.get('new_quest_ids',[])} for s in self.mod['stages'][:8]],read(FOLDER/'preserved_stages.json'))
        self.assertGreaterEqual(len(self.mod['stages']),24)
        V.validate_graph({s['id']:{'dependencies':s.get('prerequisites',[])} for s in self.mod['stages']})

    def test_optional_course_has_real_tasks_current_targets_and_thematic_rewards(self):
        self.assertEqual(len(self.quests),16)
        self.assertEqual(len({q['id'] for q in self.quests}),16)
        self.assertTrue(all(not q['required'] and q['tasks'] for q in self.quests))
        others=[q for p in sorted((ROOT/'content/quests').glob('*.json')) if p.name!='v5_forbidden_core_depth.json' for d in [read(p)] for q in (d if isinstance(d,list) else d['quests'])]
        report=V.validate_catalog(self.quests,self.rules,self.registries,old_records=others,native_action_advancements=self.actions)
        self.assertEqual(report['new_authored_quests'],16)
        self.assertEqual(report['task_types']['advancement'],6)
        self.assertGreaterEqual(len({r['item'] for q in self.quests for r in q['reward']}),7)
        self.assertTrue(all(r['item'].startswith('forbidden_arcanus:') for q in self.quests for r in q['reward']))
        for q in self.quests:
            for t in q['tasks']:
                self.assertFalse(t.get('craft',False),'No vanilla craft counter can prove a Forge ritual')
        # Internal block-only controllers are observation targets, never item icons.
        self.assertNotIn('forbidden_arcanus:hephaestus_forge_tier_1',{q['icon'] for q in self.quests})
        clibano=[q for q in self.quests if '_clibano_' in q['id']]
        self.assertTrue(all(any(t.get('block')=='forbidden_arcanus:clibano_center' for t in q['tasks']) for q in clibano))
        self.assertTrue(all(not any(t.get('item')=='forbidden_arcanus:obsidiansteel_ingot' for t in q['tasks']) for q in clibano))

    def test_future_goal_duplicate_or_unreviewed_action_rejected(self):
        bad=copy.deepcopy(self.quests);bad[0]['tasks'][0]['item']='projecte:transmutation_tablet'
        with self.assertRaisesRegex(AssertionError,'Future quest target'):
            V.validate_catalog(bad,self.rules,self.registries,native_action_advancements=self.actions)
        bad=copy.deepcopy(self.quests);bad[1]['tasks']=copy.deepcopy(bad[0]['tasks'])
        with self.assertRaisesRegex(AssertionError,'Duplicate objectives'):
            V.validate_catalog(bad,self.rules,self.registries,native_action_advancements=self.actions)
        with self.assertRaisesRegex(AssertionError,'decorative stage proof'):
            V.validate_catalog(self.quests,self.rules,self.registries)

    def test_six_native_criteria_match_exact_ritual_ids_and_real_dispatch(self):
        contracts={a['id']:a for a in read(ROOT/native.CONTRACT)['advancements']}
        self.assertEqual(len(self.actions),6)
        base=FOLDER/'official/neoforge/src/main/java/com/stal111/forbidden_arcanus'
        codec=(base/'common/advancements/critereon/RitualCompletedTrigger.java').read_text()
        self.assertIn('ResourceLocation.CODEC.fieldOf("recipe_id")',codec)
        self.assertIn('this.ritualId.equals(ritualId)',codec)
        dispatch=(base/'common/block/entity/forge/ritual/RitualManager.java').read_text()
        trigger=dispatch.index('FACriteriaTriggers.RITUAL.get().trigger(serverPlayer, data.getRitualId())')
        self.assertLess(trigger,dispatch.index('result.executeLevelEffect(this.level, this.pos)'))
        self.assertLess(trigger,dispatch.index('return result.getResultItem(this.dataCache.mainIngredient())'))
        self.assertIn('level.getPlayerByUUID(data.getStartedBy())',dispatch)
        self.assertIn('player instanceof ServerPlayer',dispatch)
        for ident in self.actions:
            contract=contracts[ident]
            self.assertEqual(contract['required_action_triggers'],['forbidden_arcanus:ritual_completed'])
            self.assertEqual(contract['expected_conditions'],{'forbidden_arcanus:ritual_completed':{'recipe_id':ident.replace('aia2:forbidden/','forbidden_arcanus:')}})
            path=ROOT/'kubejs/data/aia2/advancement'/f'{ident.split(":",1)[1]}.json'
            self.assertEqual(read(path),read(ROOT/contract['json_path']))
            self.assertEqual(read(path)['requirements'],[['ritual']])
            self.assertIn('online',contract['proof_scope_uk'])

    def test_all_native_contracts_are_used_and_verified_without_game_launch(self):
        records=[q for p in sorted((ROOT/'content/quests').glob('v5_*.json')) for q in read(p)['quests']]
        result=native.validate(ROOT,records,self.rules,V.installed_versions(ROOT))
        self.assertEqual(result['status'],'passed')
        self.assertGreaterEqual(result['native_action_quests'],105)
        self.assertEqual(result['full_pack_dispatch'],'not_run')

    def test_icon_only_migration_and_incremental_snapshot_preserve_saved_ids(self):
        documents=[read(p) for p in sorted((ROOT/'content/quests').glob('*.json'))]
        records=[q for d in documents for q in (d if isinstance(d,list) else d['quests'])]
        previous=next(q for q in records if q['id']=='E15_X_forge')
        current=next(q for q in quest_content_migrations.apply(records,ROOT) if q['id']==previous['id'])
        self.assertEqual(previous['icon'],'forbidden_arcanus:hephaestus_forge_tier_1')
        self.assertEqual(current['icon'],'forbidden_arcanus:mundabitur_dust')
        self.assertEqual({k:v for k,v in previous.items() if k!='icon'},{k:v for k,v in current.items() if k!='icon'})
        snapshot=read(ROOT/'content/audit/v5-checkpoint-80051c0-ids.json')
        self.assertEqual(sum(len(c['quests']) for c in snapshot['chapters'].values()),16)
        self.assertEqual(len(snapshot['chapters']),140)
        self.assertEqual(len(snapshot['recipes']),623)

    def test_native_ritual_inputs_are_pedestal_counts_and_not_a_recipe_serializer(self):
        base=FOLDER/'official/neoforge/src/generated/resources/data/forbidden_arcanus/forbidden_arcanus/hephaestus_forge/ritual'
        mixture=read(base/'ferrognetic_mixture.json')
        self.assertEqual(sum(i['amount'] for i in mixture['inputs']),7)
        self.assertNotIn('type',mixture)
        for tier in range(2,6):
            data=read(base/f'upgrade_tier_{tier}.json')
            self.assertEqual(data.get('forge_tier',1),tier-1)
            self.assertTrue(data['match_tier_exact'])
            self.assertEqual(data['result'],{'type':'forbidden_arcanus:upgrade_tier','result_tier':tier})
            self.assertEqual(sum(i['amount'] for i in data['inputs']),8)
        self.assertEqual(read(base/'eternal_stella.json')['forge_tier'],3)

    def test_frozen_recipes_equal_actual_export_when_available(self):
        export=Path('/workspace/aia2-reference/export/recipes')
        if not export.is_dir(): self.skipTest('External installed export unavailable')
        recipes=[s for s in read(FOLDER/'manifest.json')['sources'] if s.get('source_kind')=='installed_export_recipe']
        self.assertEqual(len(recipes),6)
        for source in recipes:
            self.assertEqual(read(ROOT/source['path']),read(export/(source['recipe_id'].replace(':','/')+'.json')))
