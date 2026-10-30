"""Station runtime helpers under modeled receivers; not optional Mixin dispatch."""
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class StationConstructionTests(unittest.TestCase):
    def test_actual_helpers_allocator_and_real_policy_under_modeled_receivers(self):
        jdk = Path(os.environ.get('JAVA_HOME', '/workspace/aia2-toolchains/jdk-21.0.9'))
        if not (jdk / 'bin/javac').is_file():
            self.skipTest('JDK21 unavailable')
        cache = Path(os.environ.get('GRADLE_USER_HOME', '/workspace/aia2-toolchains/gradle-home'))
        jars = sorted((cache / 'caches/modules-2/files-2.1/com.google.code.gson/gson').glob('**/gson-*.jar'))
        if not jars:
            self.skipTest('Gson dependency unavailable')
        sources = json.loads((ROOT / 'tests/fixtures/station-host-v8.json').read_text())
        with tempfile.TemporaryDirectory(prefix='aia2-station-runtime-v8-') as temporary:
            directory = Path(temporary)
            files = []
            for relative, source in sources.items():
                path = directory / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(source)
                files.append(str(path))
            files += [str(ROOT / f'companion/src/main/java/ua/aia2/guard/{name}.java') for name in
                      ['GuardPolicy', 'StationPaymentPlan', 'StationIngredients', 'StationConstructionAccess']]
            files.append(str(ROOT / 'tests/fixtures/StationConstructionHarness.java'))
            classpath = os.pathsep.join([str(directory), str(jars[-1])])
            compiled = subprocess.run([str(jdk / 'bin/javac'), '--release', '21', '-encoding', 'UTF-8',
                                       '-cp', classpath, '-d', str(directory), *files], capture_output=True, text=True)
            self.assertEqual(compiled.returncode, 0, compiled.stdout + compiled.stderr)
            tested = subprocess.run([str(jdk / 'bin/java'), '-cp', classpath,
                                     'ua.aia2.guard.StationConstructionHarness'], capture_output=True, text=True)
            self.assertEqual(tested.returncode, 0, tested.stdout + tested.stderr)
            self.assertRegex(tested.stdout, r'\d+ station actual-helper/allocator/real-policy modeled assertions PASS')
            print(tested.stdout.strip())
