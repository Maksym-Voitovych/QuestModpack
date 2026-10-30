"""Actual bounded station allocator versus an exhaustive unit-assignment oracle; no mod runtime."""
import os
from pathlib import Path
import re
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class StationPaymentPlanTests(unittest.TestCase):
    def test_actual_allocator_against_independent_exhaustive_oracle(self):
        jdk = Path(os.environ.get('JAVA_HOME', '/workspace/aia2-toolchains/jdk-21.0.9'))
        if not (jdk / 'bin/javac').is_file():
            self.skipTest('JDK21 unavailable')
        files = [ROOT / 'companion/src/main/java/ua/aia2/guard/StationPaymentPlan.java',
                 ROOT / 'companion/src/policyTest/java/ua/aia2/guard/StationPaymentPlanTest.java']
        with tempfile.TemporaryDirectory(prefix='aia2-station-capacity-plan-') as folder:
            compiled = subprocess.run([str(jdk / 'bin/javac'), '--release', '21', '-encoding', 'UTF-8',
                                       '-d', folder, *map(str, files)], capture_output=True, text=True)
            self.assertEqual(compiled.returncode, 0, compiled.stdout + compiled.stderr)
            tested = subprocess.run([str(jdk / 'bin/java'), '-cp', folder,
                                     'ua.aia2.guard.StationPaymentPlanTest'], capture_output=True, text=True)
            self.assertEqual(tested.returncode, 0, tested.stdout + tested.stderr)
            match = re.search(r'StationPaymentPlanTest: (\d+) assertions passed; (\d+) exhaustive small', tested.stdout)
            self.assertIsNotNone(match, tested.stdout)
            self.assertGreater(int(match[1]), 110592)
            self.assertEqual(int(match[2]), 110604)
            print(tested.stdout.strip())
