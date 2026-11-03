"""Pinned FTB component matching, executed unchanged against a typed modeled host.

These tests do not load Minecraft, register real DataComponentType values or run
FTB UI/ItemTask events. Native ItemStack CODEC is a separate integration check.
"""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
FREEZE = ROOT/'content/research/evidence/cdg_molds_v13'
FTB = FREEZE/'ftbquests/common/src/main/java/dev/ftb/mods/ftbquests'
MATCHER = FTB/'integration/item_filtering/ItemMatchingSystem.java'
ADAPTER = FTB/'api/ItemFilterAdapter.java'
MATCHER_SHA = '3eee1a1b0e1ebec8774d21fe118658319c31f77abfb10146047710d34c59b865'
ADAPTER_SHA = 'f855111085de3caaa521c39c180ca6bd03d0b87f4b97da36ba58fda4a4a1a3a8'
PROFILES = {'createdieselgenerators:'+shape for shape in ('bowl', 'lines', 'chain', 'bar')}


class MoldMatchingTests(unittest.TestCase):
    def run_matcher(self, ignore_components=False):
        jdk = Path(os.environ.get('JAVA_HOME', '/workspace/aia2-toolchains/jdk-21.0.9'))
        javac = jdk/'bin/javac'
        java = jdk/'bin/java'
        if not javac.is_file() or not java.is_file():
            if not shutil.which('javac') or not shutil.which('java'):
                self.skipTest('JDK21 unavailable for actual matcher compile')
            javac, java = Path(shutil.which('javac')), Path(shutil.which('java'))
        raw = MATCHER.read_bytes()
        self.assertEqual(hashlib.sha256(raw).hexdigest(), MATCHER_SHA)
        self.assertEqual(hashlib.sha256(ADAPTER.read_bytes()).hexdigest(), ADAPTER_SHA)
        host = json.loads((ROOT/'tests/fixtures/mold-matching-host-v13.json').read_text())
        with tempfile.TemporaryDirectory(prefix='aia2-mold-matching-v13-') as temporary:
            directory = Path(temporary); files = []
            for relative, source in host.items():
                path = directory/relative; path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(source, encoding='utf-8'); files.append(str(path))
            if ignore_components:
                source = raw.decode('utf-8')
                before = 'case FUZZY -> fuzzyMatch(stackA.getComponents(), stackB.getComponents());'
                self.assertEqual(source.count(before), 1)
                mutated = directory/'dev/ftb/mods/ftbquests/integration/item_filtering/ItemMatchingSystem.java'
                mutated.parent.mkdir(parents=True, exist_ok=True)
                mutated.write_text(source.replace(before, 'case FUZZY -> true;'), encoding='utf-8')
                files.append(str(mutated))
            else:
                files.append(str(MATCHER))
            files += [str(ADAPTER), str(ROOT/'tests/fixtures/MoldMatchingHarness.java')]
            compiled = subprocess.run([str(javac), '--release', '21', '-encoding', 'UTF-8',
                                       '-d', temporary, *files], capture_output=True, text=True)
            self.assertEqual(compiled.returncode, 0, compiled.stdout+compiled.stderr)
            return subprocess.run([str(java), '-cp', temporary, 'ua.aia2.tests.MoldMatchingHarness'],
                                  capture_output=True, text=True)

    def test_actual_matcher_profiles_modes_defaults_names_counts_and_adapter_boundary(self):
        tested = self.run_matcher()
        self.assertEqual(tested.returncode, 0, tested.stdout+tested.stderr)
        self.assertRegex(tested.stdout, r'\d+ Mold actual-FTB-matcher assertions PASS')
        print(tested.stdout.strip())

    def test_shape_agnostic_negative_control_fails_on_wrong_profile(self):
        tested = self.run_matcher(ignore_components=True)
        self.assertNotEqual(tested.returncode, 0)
        self.assertIn('A wrong Mold profile must not satisfy fuzzy matching', tested.stderr)

    def test_exact_source_codec_and_all_four_recipe_component_values(self):
        contract = json.loads((FREEZE/'contracts/component-contract.json').read_text())
        self.assertEqual(contract['java_value_type'], 'net.minecraft.resources.ResourceLocation')
        self.assertEqual(contract['persistent_codec'], 'ResourceLocation.CODEC')
        self.assertEqual(set(contract['profiles']), PROFILES)
        self.assertEqual(contract['ftbquests']['matching_modes'], ['none', 'fuzzy', 'strict'])
        self.assertEqual(contract['task_schema_example']['match_components'], 'fuzzy')
        self.assertEqual(contract['task_schema_example']['item']['components'],
                         {'createdieselgenerators:mold_type': 'createdieselgenerators:lines'})
        for shape in ('bowl', 'lines', 'chain', 'bar'):
            recipe = json.loads((FREEZE/f'recipes/createdieselgenerators/cutting/{shape}_mold.json').read_text())
            self.assertEqual(recipe['type'], 'create:cutting')
            self.assertEqual(recipe['results'], [{'id': 'createdieselgenerators:mold',
                'components': {'createdieselgenerators:mold_type': 'createdieselgenerators:'+shape}}])
        manifest = json.loads((FREEZE/'manifest.json').read_text())
        data = next(row for row in manifest['files'] if row['path'].endswith('/CDGDataComponents.java'))
        raw = (ROOT/data['path']).read_bytes()
        self.assertEqual(hashlib.sha256(raw).hexdigest(), data['sha256'])
        block = raw.decode().split('MOLD_TYPE =', 1)[1].split(';', 1)[0]
        self.assertIn('register("mold_type"', block)
        self.assertIn('builder.persistent(ResourceLocation.CODEC)', block)
        self.assertIn('networkSynchronized(ResourceLocation.STREAM_CODEC)', block)
        name_map = FREEZE/'ftblibrary/common/src/main/java/dev/ftb/mods/ftblibrary/config/NameMap.java'
        entry = next(row for row in manifest['files'] if row['path'] == name_map.relative_to(ROOT).as_posix())
        self.assertEqual(hashlib.sha256(name_map.read_bytes()).hexdigest(), entry['sha256'])
        self.assertIn('return value == null ? defaultValue : value;', name_map.read_text())


if __name__ == '__main__':
    unittest.main()
