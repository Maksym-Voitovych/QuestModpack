"""Executable fire worksite boundary plus exact optional native-edge source evidence."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class FireWorksiteTests(unittest.TestCase):
    def test_exact_native_shared_spawn_edge_precedes_random_output_and_base_change(self):
        evidence = ROOT / 'content/research/evidence/energy_guard_next_v5/enderio'
        manifest = json.loads((evidence / 'manifest.json').read_text())
        sources = {}
        for entry in manifest['files'] + manifest.get('shared_files', []):
            if Path(entry['repository_path']).name in {'FireCraftingManager.java', 'FireCraftingRecipe.java'}:
                raw = (ROOT / entry['evidence_path']).read_bytes()
                self.assertEqual(hashlib.sha256(raw).hexdigest(), entry['sha256'])
                sources[Path(entry['repository_path']).name] = raw.decode()
        manager = sources['FireCraftingManager.java']
        self.assertEqual(manager.count('spawnInfinityDrops(level, pos, matchingRecipe)'), 2)
        common = manager[manager.index('private static void spawnInfinityDrops'):manager.index('@UseOnly')]
        self.assertLess(common.index('for (var result : recipe.results())'), common.index('level.addFreshEntity(itemEntity)'))
        self.assertLess(common.index('level.addFreshEntity(itemEntity)'), common.index('level.setBlock(pos.below()'))
        self.assertIn('level.getRecipeManager() != cachedRecipeManager.get()', manager)
        recipe = sources['FireCraftingRecipe.java']
        for token in ['record Result(ItemStack result, int minCount, int maxCount, float chance)',
                      'boolean isBaseValid(Block block)', 'boolean isDimensionValid(ResourceKey<Level> dimension)']:
            self.assertIn(token, recipe)
        registered = json.loads((ROOT / 'companion/src/main/resources/aia2_machine_guard.mixins.json').read_text())['mixins']
        self.assertIn('EnderFireCraftingMixin', registered)

    def test_actual_helper_and_handlers_reload_probabilities_all_outputs_and_policy(self):
        jdk = Path(os.environ.get('JAVA_HOME', '/workspace/aia2-toolchains/jdk-21.0.9'))
        if not (jdk / 'bin/javac').is_file():
            self.skipTest('External JDK21 unavailable')
        cache = Path(os.environ.get('GRADLE_USER_HOME', '/workspace/aia2-toolchains/gradle-home')) / 'caches/modules-2/files-2.1'
        jars = []
        for group, pattern in [('com.mojang/logging', 'logging-*.jar'), ('com.google.code.gson/gson', 'gson-2.10.1.jar'), ('com.mojang/datafixerupper', 'datafixerupper-8.0.16.jar'), ('com.google.guava/guava', 'guava-*.jar'), ('org.slf4j/slf4j-api', 'slf4j-api-*.jar'), ('it.unimi.dsi/fastutil', 'fastutil-*.jar')]:
            matches = sorted((cache / group).glob('**/' + pattern))
            if not matches:
                self.skipTest('External real codec dependency unavailable: ' + group)
            jars.append(str(matches[-1]))
        fixtures = json.loads((ROOT / 'tests/fixtures/energy-native-host.json').read_text())
        fixtures.update(json.loads((ROOT / 'tests/fixtures/fire-native-host.json').read_text()))
        # Unrelated energy host classes reference its own bridge, which is not this fixture's API.
        fixtures.pop('ua/aia2/guard/ProductionMilestoneBridge.java')
        with tempfile.TemporaryDirectory(prefix='aia2-fire-worksite-') as temp:
            files = []
            for name, text in fixtures.items():
                path = Path(temp) / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(text)
                files.append(str(path))
            files += [str(ROOT / 'tests/fixtures/FireWorksiteHarness.java')]
            files += [str(ROOT / f'companion/src/main/java/ua/aia2/guard/{name}.java') for name in ['GuardPolicy', 'FireWorksiteAccess']]
            files += [str(ROOT / 'companion/src/main/java/ua/aia2/guard/mixin/EnderFireCraftingMixin.java')]
            cp = os.pathsep.join([temp, *jars])
            result = subprocess.run([str(jdk / 'bin/javac'), '-encoding', 'UTF-8', '-cp', cp, '-d', temp, *files], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            result = subprocess.run([str(jdk / 'bin/java'), '-cp', cp, 'ua.aia2.guard.mixin.FireWorksiteHarness'], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn('actual-helper/handler/real-policy assertions', result.stdout)
            print(result.stdout.strip())
