"""Exact pinned Ad Astra source contracts; no binary or optional runtime claim."""
import hashlib
import json
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
FOLDER = ROOT / 'content/research/evidence/ad_astra_core_v6'


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()


class AdAstraSourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = json.loads((FOLDER / 'manifest.json').read_text())
        cls.sources = {row['repository_path']: ROOT / row['path'] for row in cls.manifest['sources']}

    def named(self, name):
        matches = [p for rel, p in self.sources.items() if Path(rel).name == name]
        self.assertEqual(len(matches), 1, name)
        return matches[0].read_text()

    def test_all99_frozen_source_sha_and_exact_version_properties(self):
        self.assertEqual(len(self.manifest['sources']), 99)
        self.assertEqual(self.manifest['pin'], '45abf0ec05ea837c3df457f42ae440b6675e9cf0')
        self.assertTrue(self.manifest['source_version_matches_export'])
        self.assertEqual(self.manifest['binary_to_commit_provenance'], 'NOT_PROVEN')
        for row in self.manifest['sources']:
            with self.subTest(path=row['path']):
                self.assertEqual(hashlib.sha256((ROOT / row['path']).read_bytes()).hexdigest(), row['sha256'])
        props = self.named('gradle.properties')
        for line in ['version=1.16.26', 'minecraftVersion=1.21.1', 'neoforgeVersion=21.1.249']:
            self.assertIn(line, props.splitlines())

    def test_four_native_rocket_advancements_are_acquisition_not_manufacture(self):
        for tier in range(1, 5):
            name = f'tier_{tier}_rocket'
            relative = f'src/main/generated/resources/data/ad_astra/advancement/{name}.json'
            value = json.loads(self.sources[relative].read_text())
            criteria = value['criteria']
            self.assertEqual(set(criteria), {f'has_{name}'})
            self.assertEqual(criteria[f'has_{name}']['trigger'], 'minecraft:inventory_changed')
            self.assertEqual(criteria[f'has_{name}']['conditions']['items'][0]['items'], f'ad_astra:{name}')
            self.assertNotIn('minecraft:recipe_crafted', json.dumps(criteria))

    def test_nasa_native_output_precedes_input_consumption_and_preview_is_not_pickup(self):
        body = self.named('NasaWorkbenchBlockEntity.java')
        craft = body[body.index('public void craft()'):body.index('public void spawnWorkingParticles')]
        self.assertIn('if (recipe == null) return;', craft)
        self.assertNotIn('canCraft()', craft)
        self.assertLess(craft.index('Containers.dropItemStack'), craft.index('getItem(i).shrink(1)'))
        self.assertIn('for (int i = 0; i < 14; i++)', craft)
        self.assertIn('setItem(14, ItemStack.EMPTY)', craft)
        self.assertIn('recipe = null;', craft)
        self.assertIn('time % 30 == 0 && canFunction() && canCraft()', body)
        menu = self.named('NasaWorkbenchMenu.java')
        self.assertIn('CustomSlot.noPlaceOrTake(entity, 14', menu)
        self.assertRegex(menu, r'if \(slotIndex == 14\)\s*\{\s*if \(entity.canCraft\(\)\)\s*\{\s*entity.craft\(\);')

    def test_base_menu_still_valid_does_not_prove_live_receiver_ownership(self):
        parent = self.named('BaseContainerMenu.java')
        self.assertRegex(parent, r'boolean stillValid\(@NotNull Player player\)\s*\{\s*return true;\s*\}')
        self.assertNotIn('stillValid(', self.named('NasaWorkbenchMenu.java'))

    def test_station_aggregate_check_first_stack_debit_and_ignored_placement(self):
        recipe = self.named('SpaceStationRecipe.java')
        matches = recipe[recipe.index('boolean matches('):recipe.index('public CodecRecipeSerializer')]
        debit = recipe[recipe.index('public static void consumeIngredients'):]
        self.assertIn('count += stack.getCount();', matches)
        self.assertIn('if (count < holder.count()) return false;', matches)
        self.assertRegex(debit, r'inventory.removeItem\(i, holder.count\(\)\);\s*break;')
        self.assertIn('player.isCreative() || player.isSpectator()', debit)
        packet = self.named('ServerboundConstructSpaceStationPacket.java')
        self.assertLess(packet.index('SpaceStationRecipe.consumeIngredients'), packet.index('structure.placeInWorld'))
        line = next(line.strip() for line in packet.splitlines() if 'structure.placeInWorld(' in line)
        self.assertTrue(line.startswith('structure.placeInWorld('), line)
        self.assertLess(packet.index('structure.placeInWorld'), packet.index('SpaceStationHandler.constructSpaceStation'))
        marker = self.named('SpaceStationHandler.java')
        self.assertIn('stations.add(new SpaceStation(player.chunkPosition(), name));', marker)

    def test_canonical_source_export_comparison_manifest_and_scope(self):
        report = json.loads((ROOT / 'content/audit/v6-ad-astra-recipe-source-comparison.json').read_text())
        self.assertEqual((report['source_recipes'], report['export_recipes'], report['common_ids']), (533, 518, 517))
        self.assertEqual(report['counts'], {'equal_canonical': 461, 'different_canonical': 56, 'source_only': 16, 'export_only': 1})
        rows = report['rows']
        self.assertEqual(len({r['recipe_id'] for r in rows}), len(rows))
        self.assertEqual(rows, sorted(rows, key=lambda r: r['recipe_id']))
        digest_rows = []
        for row in rows:
            with self.subTest(recipe=row['recipe_id']):
                source, exported = row.get('source'), row.get('export')
                if row['status'] == 'equal_canonical':
                    self.assertEqual(source['canonical_sha256'], exported['canonical_sha256'])
                elif row['status'] == 'different_canonical':
                    self.assertNotEqual(source['canonical_sha256'], exported['canonical_sha256'])
                    self.assertTrue(row['different_top_level_fields'])
                self.assertNotIn('value', row)
                digest_rows.append({'recipe_id': row['recipe_id'], 'source_canonical_sha256': source['canonical_sha256'] if source else None,
                                    'export_canonical_sha256': exported['canonical_sha256'] if exported else None})
        self.assertEqual(hashlib.sha256(canonical(digest_rows)).hexdigest(), report['recipe_hash_manifest_sha256'])
        self.assertFalse(report['fullpack_run'])

    def test_frozen_comparison_matches_available_external_inputs(self):
        report = json.loads((ROOT / 'content/audit/v6-ad-astra-recipe-source-comparison.json').read_text())
        source_root = Path('/workspace/aia2-dev-sources/Ad-Astra-' + report['source_pin']) / report['source_recipe_folder']
        export_root = Path('/workspace/aia2-reference/export/recipes/ad_astra')
        if not source_root.is_dir() or not export_root.is_dir():
            self.skipTest('Optional exact external source/export workspace not mounted; portable SHA report still tested')
        for row in report['rows']:
            suffix = Path(row['recipe_id'].split(':', 1)[1] + '.json')
            for key, folder in [('source', source_root), ('export', export_root)]:
                if key not in row:
                    self.assertFalse((folder / suffix).exists())
                    continue
                raw = (folder / suffix).read_bytes()
                self.assertEqual(hashlib.sha256(raw).hexdigest(), row[key]['raw_sha256'])
                self.assertEqual(hashlib.sha256(canonical(json.loads(raw))).hexdigest(), row[key]['canonical_sha256'])
