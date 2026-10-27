"""ProjectE armor effect guard contracts, actual helpers/handlers in a modeled host."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
MIXINS = ['ProjectEArmorEventsMixin', 'ProjectEArmorFireMixin', 'ProjectEGemArmorMixin',
          'ProjectEGemChestMixin', 'ProjectEGemHelmetMixin', 'ProjectEGemFeetMixin',
          'ProjectEArmorAbilitiesMixin', 'ProjectEEquipmentAttributesMixin']


class ProjectEArmorTests(unittest.TestCase):
    def test_installed_armor_calls_and_cleanup_source_contracts(self):
        manifest = json.loads((ROOT/'content/research/evidence/projecte_armor_guard_v5/manifest.json').read_text())
        self.assertEqual(manifest['pin'], 'f432b0c66837759fb0731c9144dc53176b949c5d')
        sources = {}
        for row in manifest['sources']:
            raw = (ROOT/row['path']).read_bytes()
            self.assertEqual(hashlib.sha256(raw).hexdigest(), row['sha256'])
            sources[Path(row['repository_path']).name] = raw.decode()
        self.assertIn('projecte_version=1.1.0', sources['gradle.properties'])
        self.assertIn('minecraft_version=1.21.1', sources['gradle.properties'])
        self.assertIn('event.getEntity().getArmorSlots()', sources['PlayerEvents.java'])
        self.assertIn('player.getArmorSlots()', sources['TickEvents.java'])
        self.assertIn('InternalAbilities.tick(player)', sources['TickEvents.java'])
        for slot in ['HEAD', 'CHEST']:
            self.assertIn(f'player.getItemBySlot(EquipmentSlot.{slot})', sources['InternalAbilities.java'])
        self.assertIn('attributeInstance.removeModifier(modifier.id())', sources['InternalAbilities.java'])
        self.assertIn('public static void doExplode(Player player)', sources['GemChest.java'])
        self.assertIn('public static void doZap(Player player)', sources['GemHelmet.java'])
        self.assertIn('public static void toggleNightVision(ItemStack helm, Player player)', sources['GemHelmet.java'])
        self.assertIn('public static void toggleStepAssist(ItemStack boots, Player player)', sources['GemFeet.java'])
        self.assertIn('EquipmentSlotGroup.ANY', sources['Arcana.java'])
        for name in MIXINS:
            text = (ROOT/f'companion/src/main/java/ua/aia2/guard/mixin/{name}.java').read_text()
            self.assertIn('require = 1', text, name)
        equipment = (ROOT/'companion/src/main/java/ua/aia2/guard/mixin/ProjectEEquipmentAttributesMixin.java').read_text()
        self.assertIn('ordinal = 1', equipment, 'filter only new application; native old-stack removal must continue')
        self.assertNotIn('ordinal = 0', equipment)
        self.assertIn('at = @At("RETURN")', equipment, 'unchanged items require stage-change reconciliation')
        for name in ['ProjectEArmorAccess', 'ProjectEArmorAttributes']:
            helper = (ROOT/f'companion/src/main/java/ua/aia2/guard/{name}.java').read_text()
            self.assertNotIn('setItemSlot', helper, 'policy must never visually unequip real gear')
            self.assertNotIn('setCount', helper)

    def test_actual_armor_helpers_handlers_real_policy_stage_transitions(self):
        jdk = Path(os.environ.get('JAVA_HOME', '/workspace/aia2-toolchains/jdk-21.0.9'))
        if not (jdk/'bin/javac').exists():
            self.skipTest('External JDK21 unavailable')
        fixtures = json.loads((ROOT/'tests/fixtures/projecte-armor-host.json').read_text())
        with tempfile.TemporaryDirectory(prefix='aia2-projecte-armor-') as tmp:
            files = []
            for name, text in fixtures.items():
                path = Path(tmp)/name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(text)
                files.append(str(path))
            files.append(str(ROOT/'tests/fixtures/ProjectEArmorHarness.java'))
            files += [str(ROOT/f'companion/src/main/java/ua/aia2/guard/{name}.java')
                      for name in ['GuardPolicy', 'ProjectEArmorAccess', 'ProjectEArmorAttributes']]
            files += [str(ROOT/f'companion/src/main/java/ua/aia2/guard/mixin/{name}.java') for name in MIXINS]
            compile = subprocess.run([str(jdk/'bin/javac'), '-encoding', 'UTF-8', '-d', tmp, *files], capture_output=True, text=True)
            self.assertEqual(compile.returncode, 0, compile.stdout+compile.stderr)
            run = subprocess.run([str(jdk/'bin/java'), '-cp', tmp, 'ua.aia2.guard.mixin.ProjectEArmorHarness'], capture_output=True, text=True)
            self.assertEqual(run.returncode, 0, run.stdout+run.stderr)
            self.assertIn('actual-helper/handler/real-policy assertions', run.stdout)
            print(run.stdout.strip())
