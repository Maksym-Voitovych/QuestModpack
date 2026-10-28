"""Source-backed Clibano course and pending contracts; optional dispatch is a separate test."""
import copy
import hashlib
import json
from pathlib import Path
import unittest
from unittest.mock import patch

from tools import validate_v5 as V

ROOT = Path(__file__).resolve().parents[1]
FOLDER = ROOT / 'content/research/evidence/clibano_core_v6'
NATIVE = FOLDER / 'official/neoforge/src/main/java/com/stal111/forbidden_arcanus'
GENERATED = FOLDER / 'official/neoforge/src/generated/resources/data/forbidden_arcanus'
read = lambda p: json.loads(Path(p).read_text())


class ClibanoCoreTests(unittest.TestCase):
    def setUp(self):
        self.catalog = read(ROOT / 'content/quests/v5_clibano_depth.json')['quests']
        self.contract = read(ROOT / 'content/audit/v5-clibano-content-pending.json')
        self.rules = read(ROOT / 'kubejs/config/aia2_runtime.json')
        self.registry = {k: set(v) for k, v in read(ROOT / 'content/audit/registries.json')['registries'].items()}
        self.proofs = {row['advancement'] for row in self.contract['mechanic_rules']}
        self.specs = {row['id']: (row['epoch'], row['serializer'], row['output'], set(row['recipeIds']))
                      for row in self.contract['mechanic_rules']}

    def validate(self, quests):
        # The pending contract is patched only into this local validation call. Root must
        # explicitly integrate the real whitelist/config before generation can accept it.
        with patch.dict(V.MECHANIC_CONTRACT, self.specs):
            return V.validate_catalog(quests, self.rules, self.registry, mechanic_advancements=self.proofs)

    def test_all_portable_sources_have_exact_version_and_sha(self):
        manifest = read(FOLDER / 'manifest.json')
        self.assertEqual(manifest['pin'], '34f83feb76204fd773e1d2e1d69ecc5b2f2bb933')
        self.assertEqual(manifest['installed_version'], '2.6.1')
        self.assertEqual(len(manifest['sources']), 34)
        for row in manifest['sources']:
            self.assertEqual(hashlib.sha256((ROOT / row['path']).read_bytes()).hexdigest(), row['sha256'])
        properties = (FOLDER / 'official/gradle.properties').read_text()
        self.assertIn('mod_version=2.6.1', properties)
        self.assertIn('minecraft_version=1.21.1', properties)

    def test_five_real_optional_goals_have_current_targets_and_safe_rewards(self):
        self.assertEqual(len(self.catalog), 5)
        self.assertEqual(len({q['id'] for q in self.catalog}), 5)
        self.assertTrue(all(q['tasks'] and not q['required'] for q in self.catalog))
        result = self.validate(self.catalog)
        self.assertEqual(result['new_authored_quests'], 5)
        self.assertEqual(result['task_types']['advancement'], 3)
        self.assertEqual(result['quests_per_epoch'], {15: 2, 21: 3})
        self.assertTrue(all(r['item'].startswith('forbidden_arcanus:') for q in self.catalog for r in q['reward']))
        self.assertEqual(len({r['item'] for q in self.catalog for r in q['reward']}), 5)
        self.assertFalse(any(t.get('craft') for q in self.catalog for t in q['tasks']))
        # Visible shell, not the inaccessible internal controller, is the observation target.
        self.assertEqual({t['block'] for q in self.catalog for t in q['tasks'] if t['type'] == 'observation'},
                         {'forbidden_arcanus:clibano_center'})

    def test_objectives_are_distinct_from_all_existing_catalogs(self):
        other = [q for p in sorted((ROOT / 'content/quests').glob('*.json'))
                 if p.name != 'v5_clibano_depth.json' for d in [read(p)]
                 for q in (d if isinstance(d, list) else d['quests'])]
        signatures = {V.objective_signature(q['tasks']): q['id'] for q in other}
        for q in self.catalog:
            signature = V.objective_signature(q['tasks'])
            self.assertNotIn(signature, signatures, q['id'])
            signatures[signature] = q['id']

    def test_pending_map_preserves_prior_24_stage_payloads_and_graph(self):
        entry = read(ROOT / 'content/research/clibano_entry_pending.json')
        previous = read(FOLDER / 'preserved_stages.json')
        current = next(m for m in read(ROOT / 'content/research/magic_adventure_v5.json')['mods']
                       if m['mod_id'] == 'forbidden_arcanus')
        self.assertEqual(len(previous), 24)
        self.assertEqual(entry['stages'][:24], previous)
        self.assertEqual(current['stages'][:24], previous)
        self.assertEqual(len(entry['stages']), 29)
        self.assertEqual(len({s['id'] for s in entry['stages']}), 29)
        graph = {s['id']: {'dependencies': s.get('prerequisites', [])} for s in entry['stages']}
        self.assertEqual(V.validate_graph(graph), 29)
        by_id = {s['id']: s for s in entry['stages']}
        for stage in entry['stages']:
            for parent in stage.get('prerequisites', []):
                self.assertLessEqual(by_id[parent]['epoch'], stage['epoch'])
        self.assertEqual({q['id'] for q in self.catalog},
                         {q for s in entry['stages'][24:] for q in s['new_quest_ids']})
        for stage in entry['stages'][24:]:
            for evidence in stage['recipe_evidence']:
                self.assertTrue(V.verify_evidence(ROOT, evidence, claimed=True))

    def test_three_curated_native_contracts_use_exact_exported_recipes(self):
        expected = {'clibano_arcane_dust': (15, 'arcane_crystal_dust'),
                    'clibano_rune': (15, 'rune'), 'clibano_obsidiansteel': (21, 'obsidiansteel_ingot')}
        self.assertEqual({r['id'] for r in self.contract['mechanic_rules']}, set(expected))
        for row in self.contract['mechanic_rules']:
            epoch, output = expected[row['id']]
            self.assertEqual(row['epoch'], epoch)
            self.assertEqual(row['serializer'], 'forbidden_arcanus:clibano_combustion')
            self.assertEqual(row['output'], 'forbidden_arcanus:' + output)
            self.assertEqual(row['advancement'], 'aia2:mechanics/' + row['id'])
            self.assertEqual(len(row['recipeIds']), 1)
            evidence = row['evidence'][0]
            data = read(ROOT / evidence['frozen_path'])
            self.assertEqual(data, evidence['json'])
            self.assertEqual(data, read(GENERATED / 'recipe/clibano_combustion' / Path(evidence['frozen_path']).name))
            self.assertEqual(hashlib.sha256((ROOT / evidence['frozen_path']).read_bytes()).hexdigest(), evidence['source_sha256'])
            canonical = hashlib.sha256(json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
            self.assertEqual(canonical, evidence['canonical_sha256'])
            self.assertEqual(data['result'], {'count': 1, 'id': row['output']})
            self.assertLessEqual(self.rules['recipeGates'][row['recipeIds'][0]], epoch)
            self.assertLessEqual(self.rules['itemGates'][row['output']], epoch)
        self.assertEqual(self.contract['advancement_json'],
                         {'criteria': {'native_process': {'trigger': 'minecraft:impossible'}}})
        self.assertEqual(self.contract['new_recipes'], 0)

    def test_frozen_effective_export_matches_when_available(self):
        export = Path('/workspace/aia2-reference/export')
        if not export.is_dir():
            self.skipTest('External installed export unavailable')
        for row in read(FOLDER / 'manifest.json')['sources']:
            if row['source_kind'] == 'installed_export_recipe':
                source = export / 'recipes' / (row['recipe_id'].replace(':', '/') + '.json')
                self.assertEqual(read(ROOT / row['path']), read(source))
            elif row['source_kind'] == 'installed_export_item_tag':
                self.assertEqual(read(ROOT / row['path']), read(export / row['export_path']))

    def test_exact_native_slot_cost_fire_and_residue_contracts(self):
        code = (NATIVE / 'common/item/crafting/ClibanoRecipe.java').read_text()
        self.assertIn('Codec.either(Ingredient.CODEC_NONEMPTY, Codec.mapPair(', code)
        self.assertIn('"clibano_combustion", ClibanoRecipe.Serializer::new',
                      (NATIVE / 'core/init/ModRecipeSerializers.java').read_text())
        main = (NATIVE / 'common/block/entity/clibano/ClibanoMainBlockEntity.java').read_text()
        finish = main.split('public void finishRecipe(', 1)[1].split('public int getCookingTime(', 1)[0]
        self.assertIn('this.getStack(slot).shrink(1)', finish)
        self.assertLess(finish.index('shrink(1)'), finish.index('this.addResidue('))
        self.assertLess(finish.index('stack.copy()'), finish.index('this.setRecipeUsed(recipe)'))
        residue = (NATIVE / 'common/block/entity/clibano/ResiduesStorage.java').read_text()
        self.assertIn('public static final int MAX_AMOUNT = 64', residue)
        self.assertIn('amount >= combineInfo.requiredAmount()', residue)
        for kind in ['arcane_crystal', 'rune', 'copper']:
            data = read(GENERATED / 'forbidden_arcanus/residue_type' / (kind + '.json'))
            self.assertEqual(data['combine_info']['required_amount'], 9)
        alloy = read(FOLDER / 'recipes/obsidiansteel_ingot_from_clibano_combustion.json')
        self.assertEqual(alloy['ingredients'], {'first': {'tag': 'c:raw_materials/iron'}, 'second': {'item': 'minecraft:obsidian'}})
        self.assertEqual(alloy['enhancer'], 'forbidden_arcanus:artisan_relic')
        self.assertEqual(alloy['fire_type'], 'fire')
        self.assertEqual(read(FOLDER / 'effective_tags/clibano/creates_enchanted_fire.json'), ['forbidden_arcanus:enchanted_soul'])

    def test_no_unverified_frame_automation_or_residue_action_claim(self):
        frame = (NATIVE / 'common/block/entity/clibano/ClibanoFrameBlockEntity.java').read_text()
        self.assertIn('//TODO: Fix this', frame)
        self.assertIn('//    public @NotNull <T> LazyOptional<T> getCapability', frame)
        preparation = [q for q in self.catalog if not any(t['type'] == 'advancement' for t in q['tasks'])]
        self.assertEqual(len(preparation), 2)
        self.assertTrue(all(any(t['type'] == 'observation' for t in q['tasks']) for q in preparation))
        self.assertTrue(all('перевір' in ' '.join(q['description_uk']).lower() for q in preparation))
        self.assertTrue(any('capability' in x for x in self.contract['limitations']))

    def test_future_duplicate_and_unverified_proof_regressions(self):
        bad = copy.deepcopy(self.catalog)
        bad[2]['tasks'][1]['item'] = 'projecte:transmutation_tablet'
        with self.assertRaisesRegex(AssertionError, 'Future quest target'):
            self.validate(bad)
        bad = copy.deepcopy(self.catalog)
        bad[1]['tasks'] = copy.deepcopy(bad[0]['tasks'])
        with self.assertRaisesRegex(AssertionError, 'Duplicate objectives'):
            self.validate(bad)
        with patch.dict(V.MECHANIC_CONTRACT, self.specs):
            with self.assertRaisesRegex(AssertionError, 'Unverified native mechanic proof'):
                V.validate_catalog(self.catalog, self.rules, self.registry)
