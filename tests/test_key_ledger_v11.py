"""Actual key journal behavior with modeled typed NBT/storage/native completion."""
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class KeyLedgerTests(unittest.TestCase):
    def run_helper(self, legacy_data=False):
        jdk = Path(os.environ.get('JAVA_HOME', '/workspace/aia2-toolchains/jdk-21.0.9'))
        cache = Path(os.environ.get('GRADLE_USER_HOME', '/workspace/aia2-toolchains/gradle-home'))
        jars = sorted((cache / 'caches/modules-2/files-2.1/com.google.code.gson/gson').glob('**/gson-*.jar'))
        if not (jdk/'bin/javac').is_file() or not jars:
            self.skipTest('JDK21/Gson unavailable')
        sources = json.loads((ROOT/'tests/fixtures/key-space-actions-host-v10.json').read_text())
        with tempfile.TemporaryDirectory(prefix='aia2-key-ledger-v11-') as temporary:
            directory = Path(temporary); files = []
            for relative, source in sources.items():
                path = directory/relative; path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(source); files.append(str(path))
            production = ROOT/'companion/src/main/java/ua/aia2/guard'
            if legacy_data:
                source = (production/'KeyProductionBridge.java').read_text()
                marker = '    private static ReceiptData data(MinecraftServer server) {'
                self.assertEqual(source.count(marker), 1)
                start = source.index(marker); opening = source.index('{', start); depth = 1; end = opening + 1
                while depth:
                    depth += (source[end] == '{') - (source[end] == '}'); end += 1
                old = marker + '\n        return server.overworld().getDataStorage().computeIfAbsent(ReceiptData.FACTORY, DATA_NAME);\n    }'
                path = directory/'ua/aia2/guard/KeyProductionBridge.java'
                path.write_text(source[:start]+old+source[end:]); files.append(str(path))
            else:
                files.append(str(production/'KeyProductionBridge.java'))
            files += [str(production/'RequiredSpaceActions.java'), str(ROOT/'tests/fixtures/KeyLedgerHarness.java')]
            classpath = os.pathsep.join([temporary, str(jars[-1])])
            compile_result = subprocess.run([str(jdk/'bin/javac'), '--release', '21', '-encoding', 'UTF-8',
                                             '-cp', classpath, '-d', temporary, *files], capture_output=True, text=True)
            self.assertEqual(compile_result.returncode, 0, compile_result.stdout+compile_result.stderr)
            return subprocess.run([str(jdk/'bin/java'), '-cp', classpath, 'ua.aia2.guard.KeyLedgerHarness',
                                   str(directory/'worlds')], capture_output=True, text=True)

    def test_actual_key_journal_preserves_corruption_full_history_and_caps(self):
        tested = self.run_helper()
        self.assertEqual(tested.returncode, 0, tested.stdout+tested.stderr)
        self.assertRegex(tested.stdout, r'\d+ key actual-bridge journal modeled assertions PASS')
        print(tested.stdout.strip())

    def test_legacy_empty_journal_fallback_fails_behavior_regression(self):
        tested = self.run_helper(legacy_data=True)
        self.assertNotEqual(tested.returncode, 0)
        # The negative control must detect lazy/safe storage behavior before any
        # untrusted file could be overwritten, not an unrelated compile failure.
        self.assertTrue('read does not install or write a fresh journal' in tested.stderr or
                        'unreadable existing key file must stay closed' in tested.stderr,
                        tested.stdout+tested.stderr)
