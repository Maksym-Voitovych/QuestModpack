"""Portable exact-source contracts for current tag and enhancer dependency snapshots."""
import hashlib
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class ForbiddenDependencySourceTests(unittest.TestCase):
    def test_all_frozen_sources_match_manifest(self):
        manifest = json.loads((ROOT / 'content/research/evidence/forbidden_transitive_v6/manifest.json').read_text())
        self.assertEqual(len(manifest['sources']), 18)
        for source in manifest['sources']:
            with self.subTest(path=source['path']):
                self.assertEqual(hashlib.sha256((ROOT / source['path']).read_bytes()).hexdigest(), source['sha256'])

    def test_current_tag_binding_and_native_scalar_dependency_contracts(self):
        manifest = json.loads((ROOT / 'content/research/evidence/forbidden_transitive_v6/manifest.json').read_text())
        sources = {Path(row['path']).name: (ROOT / row['path']).read_text() for row in manifest['sources']}
        self.assertIn('public Value[] getValues()', sources['Ingredient.java'])
        self.assertIn('public boolean isCustom()', sources['Ingredient.java'])
        self.assertIn('this.itemStacks == null', sources['Ingredient.java'])
        self.assertIn('this.contents = List.copyOf', sources['HolderSet.java'])
        self.assertIn('runnable.run()', sources['HolderSet.java'])
        self.assertIn('computeIfAbsent', sources['MappedRegistry.java'])
        self.assertIn('HolderSet<EnhancerDefinition> enhancers', sources['RitualRequirements.java'])
        self.assertIn('Ingredient mainIngredient', sources['Ritual.java'])
        self.assertIn('record RitualInput(Ingredient ingredient, int amount)', sources['RitualInput.java'])
        self.assertIn('EssenceType essenceType, int value', sources['ModifyRequiredEssenceEffect.java'])
        self.assertIn('EssenceType essenceType, double multiplier', sources['MultiplyRequiredEssenceEffect.java'])
        self.assertIn('private final int startTime', sources['TimeCondition.java'])
        self.assertIn('inner_texture', sources['MagicCircleType.java'])


if __name__ == '__main__':
    unittest.main()
