"""Actual NASA production helper/handlers/bridge in a modeled host; no weaving claim."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class NasaProductionTests(unittest.TestCase):
    def test_pinned_native_order_and_narrow_required_redirects(self):
        manifest = json.loads((ROOT / 'content/research/evidence/ad_astra_core_v6/manifest.json').read_text())
        row = next(row for row in manifest['sources'] if row['repository_path'].endswith('/NasaWorkbenchBlockEntity.java'))
        raw = (ROOT / row['path']).read_bytes()
        self.assertEqual(hashlib.sha256(raw).hexdigest(), row['sha256'])
        native = raw.decode().split('public void craft() {', 1)[1].split('public void spawnWorkingParticles', 1)[0]
        ordered = ['if (recipe == null)', 'spawnResultParticles()', 'Containers.dropItemStack',
                   'getItem(14).copy()', 'setItem(14, ItemStack.EMPTY)', 'getItem(i).shrink(1)', 'recipe = null']
        positions = [native.index(step) for step in ordered]
        self.assertEqual(positions, sorted(positions))
        mixin = (ROOT / 'companion/src/main/java/ua/aia2/guard/mixin/AdAstraNasaMixin.java').read_text()
        drop = (ROOT / 'companion/src/main/java/ua/aia2/guard/mixin/NasaDropMixin.java').read_text()
        self.assertIn('NasaProductionAccess.enterNative(machine)', mixin)
        self.assertIn('NasaProductionAccess.craft(machine)', mixin)
        for target in ['Lnet/minecraft/world/Containers;dropItemStack(Lnet/minecraft/world/level/Level;DDDLnet/minecraft/world/item/ItemStack;)V',
                       'Lnet/minecraft/world/item/ItemStack;shrink(I)V']:
            self.assertIn(target, mixin)
        self.assertEqual(mixin.count('@Redirect(method = "craft()V"'), 2)
        self.assertEqual(mixin.count('require = 1, allow = 1'), 2)
        self.assertIn('dropItemStack(Lnet/minecraft/world/level/Level;DDDLnet/minecraft/world/item/ItemStack;)V', drop)
        self.assertIn('Lnet/minecraft/world/level/Level;addFreshEntity(Lnet/minecraft/world/entity/Entity;)Z', drop)
        self.assertIn('require = 1, allow = 1', drop)
        registered = json.loads((ROOT / 'companion/src/main/resources/aia2_machine_guard.mixins.json').read_text())['mixins']
        self.assertIn('NasaDropMixin', registered)

    def test_frozen_minecraft_bytecode_uses_level_acceptance_descriptor(self):
        manifest = json.loads((ROOT / 'content/research/evidence/nasa_production_v7/manifest.json').read_text())
        row = next(row for row in manifest['sources'] if row['repository_path'] == 'net.minecraft.world.Containers.javap.txt')
        raw = (ROOT / row['path']).read_bytes()
        self.assertEqual(hashlib.sha256(raw).hexdigest(), row['sha256'])
        bytecode = raw.decode().split('public static void dropItemStack(', 1)[1].split('public static void ', 1)[0]
        self.assertEqual(bytecode.count('Level.addFreshEntity:'), 1)
        self.assertRegex(bytecode, r'invokevirtual[^\n]+net/minecraft/world/level/Level\.addFreshEntity:'
                         r'\(Lnet/minecraft/world/entity/Entity;\)Z\s*\n\s*\d+: pop')

    def test_actual_helper_handlers_bridge_and_current_policy(self):
        jdk = Path(os.environ.get('JAVA_HOME', '/workspace/aia2-toolchains/jdk-21.0.9'))
        if not (jdk / 'bin/javac').is_file():
            self.skipTest('JDK21 unavailable')
        cache = Path(os.environ.get('GRADLE_USER_HOME', '/workspace/aia2-toolchains/gradle-home'))
        jars = sorted((cache / 'caches/modules-2/files-2.1/com.google.code.gson/gson').glob('**/gson-*.jar'))
        if not jars:
            self.skipTest('Gson dependency unavailable')
        fixture = json.loads((ROOT / 'tests/fixtures/nasa-production-host-v7.json').read_text())
        with tempfile.TemporaryDirectory(prefix='aia2-nasa-production-v7-') as directory:
            files = []
            for name, source in fixture.items():
                path = Path(directory) / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(source)
                files.append(str(path))
            files.append(str(ROOT / 'tests/fixtures/NasaProductionHarness.java'))
            files += [str(ROOT / f'companion/src/main/java/ua/aia2/guard/{name}.java') for name in
                      ['GuardPolicy', 'AdAstraNasaAccess', 'NasaIngredients', 'NasaProductionAccess', 'GuardedNasaDrop', 'ProductionMilestoneBridge']]
            files += [str(ROOT / f'companion/src/main/java/ua/aia2/guard/mixin/{name}.java') for name in
                      ['AdAstraNasaMixin', 'AdAstraNasaBaseMenuMixin', 'NasaDropMixin']]
            classpath = os.pathsep.join([directory, str(jars[-1])])
            rules = Path(directory) / 'nasa-rules.json'
            pending = json.loads((ROOT / 'content/research/nasa_process_pending_v7.json').read_text())
            rules.write_text(json.dumps(pending['mechanic_rules']))
            compiled = subprocess.run([str(jdk / 'bin/javac'), '-encoding', 'UTF-8', '-cp', classpath,
                                       '-d', directory, *files], capture_output=True, text=True)
            self.assertEqual(compiled.returncode, 0, compiled.stdout + compiled.stderr)
            tested = subprocess.run([str(jdk / 'bin/java'), '-cp', classpath,
                                     'ua.aia2.guard.mixin.NasaProductionHarness', str(rules)], capture_output=True, text=True)
            self.assertEqual(tested.returncode, 0, tested.stdout + tested.stderr)
            self.assertRegex(tested.stdout, r'\d+ NASA production actual-helper/handlers/bridge/real-policy modeled assertions PASS; no weaving claim')
            print(tested.stdout.strip())
