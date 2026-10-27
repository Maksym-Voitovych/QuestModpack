"""Suction pickup lookup is separate from ProjectE's normal inventory/bag tick."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class ProjectEBagSuctionTests(unittest.TestCase):
    def test_exact_native_lookup_has_two_stack_gates_before_suction_predicate(self):
        manifest = json.loads((ROOT / 'content/research/evidence/projecte_bag_suction_v5/manifest.json').read_text())
        self.assertEqual(manifest['pin'], 'f432b0c66837759fb0731c9144dc53176b949c5d')
        sources = {}
        for row in manifest['sources']:
            raw = (ROOT / row['path']).read_bytes()
            self.assertEqual(hashlib.sha256(raw).hexdigest(), row['sha256'])
            sources[Path(row['repository_path']).name] = raw.decode()
        self.assertIn('projecte_version=1.1.0', sources['gradle.properties'])
        self.assertIn('minecraft_version=1.21.1', sources['gradle.properties'])
        native = sources['AlchemicalBag.java'].split('public static ItemStack getFirstBagWithSuctionItem', 1)[1].split('private class ContainerProvider', 1)[0]
        self.assertEqual(native.count('.isEmpty()'), 2)
        self.assertIn('!stack.isEmpty() && stack.getItem() instanceof AlchemicalBag bag', native)
        self.assertIn('!ring.isEmpty() && (ring.is(PEItems.BLACK_HOLE_BAND) || ring.is(PEItems.VOID_RING))', native)
        self.assertIn('ring.getOrDefault(PEDataComponentTypes.ACTIVE, false)', native)
        self.assertIn('AlchemicalBag.getFirstBagWithSuctionItem(player, player.getInventory().items)', sources['PlayerEvents.java'])
        mixin = (ROOT / 'companion/src/main/java/ua/aia2/guard/mixin/ProjectEBagSuctionMixin.java').read_text()
        self.assertIn('require = 2, allow = 2', mixin)
        self.assertIn('stack.isEmpty() || !ProjectEPassiveAccess.mayUse(player, stack)', mixin)
        self.assertIn('NonNullList<ItemStack> inventory', mixin)

    def test_actual_redirect_actual_policy_preserves_native_candidate_selection(self):
        jdk = Path(os.environ.get('JAVA_HOME', '/workspace/aia2-toolchains/jdk-21.0.9'))
        if not (jdk / 'bin/javac').exists():
            self.skipTest('External JDK21 unavailable')
        fixtures = json.loads((ROOT / 'tests/fixtures/projecte-bag-suction-host.json').read_text())
        with tempfile.TemporaryDirectory(prefix='aia2-projecte-suction-') as tmp:
            files = []
            for name, source in fixtures.items():
                p = Path(tmp) / name
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_text(source)
                files.append(str(p))
            files += [str(ROOT / 'tests/fixtures/ProjectEBagSuctionHarness.java'),
                      str(ROOT / 'companion/src/main/java/ua/aia2/guard/GuardPolicy.java'),
                      str(ROOT / 'companion/src/main/java/ua/aia2/guard/mixin/ProjectEBagSuctionMixin.java')]
            compiled = subprocess.run([str(jdk / 'bin/javac'), '-encoding', 'UTF-8', '-d', tmp, *files], capture_output=True, text=True)
            self.assertEqual(compiled.returncode, 0, compiled.stdout + compiled.stderr)
            run = subprocess.run([str(jdk / 'bin/java'), '-cp', tmp, 'ua.aia2.guard.mixin.ProjectEBagSuctionHarness'], capture_output=True, text=True)
            self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
            self.assertIn('21 actual-handler/real-policy assertions', run.stdout)
            print(run.stdout.strip())
