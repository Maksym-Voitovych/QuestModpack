"""Portable exact-version contracts for Clibano dependency and residue history."""
import hashlib
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class ClibanoDependencySourcesTests(unittest.TestCase):
    def test_exact_sources_and_native_default_dependency_counts(self):
        manifest = json.loads((ROOT / 'content/research/evidence/clibano_dependencies_v6/manifest.json').read_text())
        self.assertEqual(len(manifest['sources']), 35)
        recipes = []
        residues = []
        for row in manifest['sources']:
            raw = (ROOT / row['path']).read_bytes()
            self.assertEqual(hashlib.sha256(raw).hexdigest(), row['sha256'], row['path'])
            if '/recipe/clibano_combustion/' in row['path']:
                recipes.append(json.loads(raw))
            elif '/residue_type/' in row['path'] and row['path'].endswith('.json'):
                residues.append(json.loads(raw))
        self.assertEqual(len(recipes), 15)
        self.assertEqual(len(residues), 11)
        self.assertEqual(sum('"tag"' in json.dumps(r) for r in recipes), 13)
        self.assertTrue(all('residue' in r for r in recipes))
        self.assertEqual(sum('enhancer' in r for r in recipes), 1)

    def test_exact_matching_storage_packet_and_condition_contracts(self):
        manifest = json.loads((ROOT / 'content/research/evidence/clibano_dependencies_v6/manifest.json').read_text())
        sources = {Path(r['path']).name: (ROOT / r['path']).read_text() for r in manifest['sources'] if r['path'].endswith('.java')}
        self.assertIn('RecipeMatcher.findMatches', sources['ClibanoRecipe.java'])
        self.assertIn('Optional<Holder<EnhancerDefinition>> requiredEnhancer', sources['ClibanoRecipe.java'])
        self.assertIn('Codec<ResidueType> DIRECT_CODEC', sources['ResidueType.java'])
        self.assertIn('MAP_CODEC.encodeStart', sources['ResiduesStorage.java'])
        self.assertIn('return this.totalAmount != 0', sources['ResiduesStorage.java'])
        main = sources['ClibanoMainBlockEntity.java']
        credit = main[main.index('private void addResidue'):main.index('private void addResidue')+1200]
        self.assertLess(credit.index('increaseType'), credit.index('SetClibanoResiduesPayload'))
        self.assertIn('this.addResidue(recipe.value()', main)
        hooks = (ROOT / 'companion/src/main/java/ua/aia2/guard/mixin/ClibanoResidueMixin.java').read_text()
        self.assertIn('increaseType(Lnet/minecraft/core/Holder;I)V', hooks)
        self.assertIn('ClibanoAccess.increasedResidue', hooks)
        self.assertIn('ClibanoAccess.convertedResidues', hooks)
