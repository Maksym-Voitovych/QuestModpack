"""Actual receipt store using a modeled NBT host; no Forbidden mod lifecycle claim."""
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]

class ForbiddenPaidStateTests(unittest.TestCase):
    def test_actual_state_receipt_raw_preservation_payment_and_restart(self):
        jdk=Path(os.environ.get('JAVA_HOME','/workspace/aia2-toolchains/jdk-21.0.9'))
        if not (jdk/'bin/javac').is_file():self.skipTest('External JDK21 unavailable')
        fixture=json.loads((ROOT/'tests/fixtures/forbidden-paid-state-host.json').read_text())
        with tempfile.TemporaryDirectory(prefix='aia2-forbidden-paid-') as tmp:
            files=[]
            for name,text in fixture.items():
                p=Path(tmp)/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(text);files.append(str(p))
            files += [str(ROOT/'tests/fixtures/ForbiddenPaidStateHarness.java'),str(ROOT/'companion/src/main/java/ua/aia2/guard/ForbiddenPaidState.java')]
            run=subprocess.run([str(jdk/'bin/javac'),'-encoding','UTF-8','-d',tmp,*files],capture_output=True,text=True)
            self.assertEqual(run.returncode,0,run.stdout+run.stderr)
            run=subprocess.run([str(jdk/'bin/java'),'-cp',tmp,'ua.aia2.guard.ForbiddenPaidStateHarness'],capture_output=True,text=True)
            self.assertEqual(run.returncode,0,run.stdout+run.stderr)
            self.assertIn('modeled assertions PASS',run.stdout);print(run.stdout.strip())

    def test_storage_is_weak_scoped_and_not_a_runtime_reset_hook(self):
        source=(ROOT/'companion/src/main/java/ua/aia2/guard/ForbiddenPaidState.java').read_text()
        self.assertIn('new WeakHashMap<>()',source)
        self.assertNotIn('clearRuntime',source)
        self.assertNotIn('getServer',source)
        self.assertIn('encodedReceipt.copy()',source)
        self.assertIn('private static final Set<String> PAID_KEYS',source)
