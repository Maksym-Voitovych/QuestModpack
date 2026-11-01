"""Actual key-production and required-action classes against explicit native host receivers."""
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class KeySpaceActionTests(unittest.TestCase):
    def run_helper(self, remove_owner_check=False):
        jdk = Path(os.environ.get('JAVA_HOME', '/workspace/aia2-toolchains/jdk-21.0.9'))
        cache = Path(os.environ.get('GRADLE_USER_HOME', '/workspace/aia2-toolchains/gradle-home'))
        jars = sorted((cache / 'caches/modules-2/files-2.1/com.google.code.gson/gson').glob('**/gson-*.jar'))
        if not (jdk / 'bin/javac').is_file() or not jars:
            self.skipTest('JDK21/Gson unavailable')
        sources = json.loads((ROOT / 'tests/fixtures/key-space-actions-host-v10.json').read_text())
        with tempfile.TemporaryDirectory(prefix='aia2-key-space-v10-') as temporary:
            directory = Path(temporary)
            files = []
            for relative, source in sources.items():
                path = directory / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(source)
                files.append(str(path))
            production = ROOT / 'companion/src/main/java/ua/aia2/guard'
            if remove_owner_check:
                original = (production / 'KeyProductionBridge.java').read_text()
                condition = '                && attempt.team().equals(Aia2MachineGuard.getOwner(machine))\n'
                self.assertEqual(original.count(condition), 1)
                old_boundary = directory / 'ua/aia2/guard/KeyProductionBridge.java'
                old_boundary.write_text(original.replace(condition, '', 1))
                files.append(str(old_boundary))
            else:
                files.append(str(production / 'KeyProductionBridge.java'))
            files.append(str(production / 'RequiredSpaceActions.java'))
            files.append(str(ROOT / 'tests/fixtures/KeySpaceActionsHarness.java'))
            classpath = os.pathsep.join([temporary, str(jars[-1])])
            compiled = subprocess.run([str(jdk / 'bin/javac'), '--release', '21', '-encoding', 'UTF-8',
                                       '-cp', classpath, '-d', temporary, *files], capture_output=True, text=True)
            self.assertEqual(compiled.returncode, 0, compiled.stdout + compiled.stderr)
            tested = subprocess.run([str(jdk / 'bin/java'), '-cp', classpath,
                                     'ua.aia2.guard.KeySpaceActionsHarness',
                                     str(ROOT / 'kubejs/config/aia2_runtime.json')], capture_output=True, text=True)
            return tested

    def test_actual_key_admission_and_receipts_require_native_nasa_actions(self):
        tested = self.run_helper()
        self.assertEqual(tested.returncode, 0, tested.stdout + tested.stderr)
        self.assertRegex(tested.stdout, r'\d+ actual-key/required-space-action modeled assertions PASS')
        print(tested.stdout.strip())

    def test_historical_crafter_owner_gap_fails_the_behavior_regression(self):
        tested = self.run_helper(remove_owner_check=True)
        self.assertNotEqual(tested.returncode, 0)
        self.assertIn('crafter owner changed during native operation cannot grant either team', tested.stderr)
