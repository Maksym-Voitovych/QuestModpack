"""Actual lane/residue dependency ledger under a modeled NBT host; no optional mod dispatch."""
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class ClibanoDependencyStateTests(unittest.TestCase):
    def test_actual_state_lanes_restart_corruption_copies_and_tombstone(self):
        jdk = Path(os.environ.get('JAVA_HOME', '/workspace/aia2-toolchains/jdk-21.0.9'))
        if not (jdk / 'bin/javac').is_file():
            self.skipTest('External JDK21 unavailable')
        fixture = json.loads((ROOT / 'tests/fixtures/clibano-paid-state-host.json').read_text())
        with tempfile.TemporaryDirectory(prefix='aia2-clibano-dependency-') as tmp:
            files = []
            for name, source in fixture.items():
                target = Path(tmp) / name
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(source)
                files.append(str(target))
            files.extend(str(ROOT / name) for name in [
                'tests/fixtures/ClibanoDependencyStateHarness.java',
                'companion/src/main/java/ua/aia2/guard/ClibanoDependencyState.java'])
            run = subprocess.run([str(jdk / 'bin/javac'), '-encoding', 'UTF-8', '-d', tmp, *files], capture_output=True, text=True)
            self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
            run = subprocess.run([str(jdk / 'bin/java'), '-cp', tmp, 'ua.aia2.guard.ClibanoDependencyStateHarness'], capture_output=True, text=True)
            self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
            self.assertIn('modeled assertions PASS', run.stdout)
            print(run.stdout.strip())
