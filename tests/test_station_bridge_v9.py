"""Actual durable station bridge with modeled typed NBT/MC receivers and real policy."""
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class StationBridgeTests(unittest.TestCase):
    def test_actual_bridge_configuration_admission_history_and_corruption_guards(self):
        jdk = Path(os.environ.get('JAVA_HOME', '/workspace/aia2-toolchains/jdk-21.0.9'))
        cache = Path(os.environ.get('GRADLE_USER_HOME', '/workspace/aia2-toolchains/gradle-home'))
        jars = sorted((cache / 'caches/modules-2/files-2.1/com.google.code.gson/gson').glob('**/gson-*.jar'))
        if not (jdk / 'bin/javac').is_file() or not jars:
            self.skipTest('JDK21/Gson unavailable')
        sources = json.loads((ROOT / 'tests/fixtures/station-bridge-host-v9.json').read_text())
        with tempfile.TemporaryDirectory(prefix='aia2-station-bridge-v9-') as tmp:
            directory = Path(tmp)
            files = []
            for relative, source in sources.items():
                path = directory / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(source)
                files.append(str(path))
            files += [str(ROOT / f'companion/src/main/java/ua/aia2/guard/{name}.java')
                      for name in ['GuardPolicy', 'StationProductionBridge']]
            files.append(str(ROOT / 'tests/fixtures/StationBridgeHarness.java'))
            classpath = os.pathsep.join([tmp, str(jars[-1])])
            compiled = subprocess.run([str(jdk / 'bin/javac'), '--release', '21', '-encoding', 'UTF-8',
                                       '-cp', classpath, '-d', tmp, *files], capture_output=True, text=True)
            self.assertEqual(compiled.returncode, 0, compiled.stdout + compiled.stderr)
            tested = subprocess.run([str(jdk / 'bin/java'), '-cp', classpath,
                                     'ua.aia2.guard.StationBridgeHarness', str(directory / 'worlds')],
                                    capture_output=True, text=True)
            self.assertEqual(tested.returncode, 0, tested.stdout + tested.stderr)
            self.assertRegex(tested.stdout, r'\d+ station actual-bridge/real-policy modeled assertions PASS')
            print(tested.stdout.strip())
