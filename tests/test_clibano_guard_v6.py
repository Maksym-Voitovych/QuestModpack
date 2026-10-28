"""Actual Clibano helper/handlers and pinned native logic under a modeled host.

This is not an optional-mod weaving, JEI or full Minecraft dispatch test.
"""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class ClibanoGuardTests(unittest.TestCase):
    def test_actual_helper_handlers_and_pinned_logic_with_real_policy(self):
        jdk = Path(os.environ.get('JAVA_HOME', '/workspace/aia2-toolchains/jdk-21.0.9'))
        if not (jdk / 'bin/javac').is_file():
            self.skipTest('External JDK21 unavailable')
        gson = sorted(Path('/workspace/aia2-toolchains/gradle-home/caches/modules-2/files-2.1/com.google.code.gson/gson').glob('*/*/gson-*.jar'))
        if not gson:
            self.skipTest('External Gson test dependency unavailable')
        fixture = json.loads((ROOT / 'tests/fixtures/clibano-native-host.json').read_text())
        with tempfile.TemporaryDirectory(prefix='aia2-clibano-guard-') as tmp:
            sources = []
            for relative, source in fixture.items():
                target = Path(tmp) / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(source)
                sources.append(str(target))
            sources.append(str(ROOT / 'tests/fixtures/ClibanoGuardHarness.java'))
            sources.extend(str(ROOT / f'companion/src/main/java/ua/aia2/guard/{name}.java')
                           for name in ['GuardPolicy', 'ClibanoPaidState', 'ClibanoAccess'])
            sources.extend(str(ROOT / f'companion/src/main/java/ua/aia2/guard/mixin/{name}.java')
                           for name in ['ClibanoMachineMixin', 'ClibanoResidueMixin'])
            run = subprocess.run([str(jdk / 'bin/javac'), '-encoding', 'UTF-8', '-cp', str(gson[-1]), '-d', tmp, *sources], capture_output=True, text=True)
            self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
            run = subprocess.run([str(jdk / 'bin/java'), '-cp', os.pathsep.join([tmp, str(gson[-1])]), 'ua.aia2.guard.ClibanoGuardHarness'], capture_output=True, text=True)
            self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
            self.assertIn('modeled assertions PASS', run.stdout)
            print(run.stdout.strip())

    def test_native_logic_fixtures_are_verbatim_exact_source(self):
        fixture = json.loads((ROOT / 'tests/fixtures/clibano-native-host.json').read_text())
        source_root = Path('/workspace/aia2-dev-sources/Forbidden-Arcanus-2.6.1/neoforge/src/main/java')
        expected = {
            'ClibanoAccessor': '10f152c6c81be55786b11a50c5a0f10109428b613b89f9192dbb704f31ecbad6',
            'ClibanoSmeltLogic': '6a78a15d8dad872caf4ba221973474070a55e4a83d4e7a5892d834da6d73e046',
            'DefaultSmeltLogic': 'd0a99e4b4ecdd6084088aa89cfb61aa229c530d3da215558b00c22abebce9409',
            'DoubleSmeltLogic': '98612bd539dcaef1c5fb16ed855ec004ec6891f7462afaeeff9ea45172997d25',
        }
        for name, digest in expected.items():
            relative = 'com/stal111/forbidden_arcanus/common/block/entity/clibano/logic/' + name + '.java'
            raw = fixture[relative].encode()
            self.assertEqual(hashlib.sha256(raw).hexdigest(), digest)
            if (source_root / relative).is_file():
                self.assertEqual(raw, (source_root / relative).read_bytes())
