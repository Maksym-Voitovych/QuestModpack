"""Compiled source-shaped NASA fixtures and real Sponge annotations, not installed Ad Astra ABI."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
import zipfile

import install_runtime as installer
from tools import check_optional_mixin_targets_v6 as checker

ROOT = Path(__file__).resolve().parents[1]
PREFIX = 'earth/terrarium/adastra/'
MIXINS = {'AdAstraNasaMixin', 'AdAstraNasaMenuMixin', 'AdAstraNasaBaseMenuMixin'}
MACHINE = PREFIX + 'common/blockentities/machines/NasaWorkbenchBlockEntity'
BASE_MENU = PREFIX + 'common/menus/base/BaseContainerMenu'
NASA_MENU = PREFIX + 'common/menus/machines/NasaWorkbenchMenu'
JAVA = Path(os.environ.get('JAVA_HOME', '/workspace/aia2-toolchains/jdk-21.0.9')) / 'bin/javac'
GRADLE_HOME = Path(os.environ.get('GRADLE_USER_HOME', '/workspace/aia2-toolchains/gradle-home'))


def method_bounds(source, signature):
    start = source.index(signature)
    opening = source.index('{', start)
    depth = 1
    for offset in range(opening + 1, len(source)):
        if source[offset] == '{':
            depth += 1
        elif source[offset] == '}':
            depth -= 1
            if not depth:
                return start, offset + 1
    raise AssertionError('Unclosed modeled method ' + signature)


class NasaAbiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not JAVA.is_file():
            raise unittest.SkipTest('JDK21 unavailable for source-shaped NASA bytecode fixtures')
        cache = GRADLE_HOME / 'caches/modules-2/files-2.1'
        annotations = sorted((cache / 'net.fabricmc/sponge-mixin').glob('**/sponge-mixin-*.jar'))
        gson = sorted((cache / 'com.google.code.gson/gson').glob('**/gson-*.jar'))
        if not annotations or not gson:
            raise unittest.SkipTest('Actual Sponge annotation library or Gson dependency unavailable')
        cls.annotations = annotations[-1]
        cls.gson = gson[-1]
        cls.temp = tempfile.TemporaryDirectory(prefix='aia2-nasa-source-shaped-abi-')
        cls.directory = Path(cls.temp.name)
        cls.sources = json.loads((ROOT / 'tests/fixtures/nasa-production-host-v7.json').read_text())
        # These receivers must remain unwoven: annotation matching is against
        # compiled optional targets, not manually invoked guard handlers.
        cls.sources = {name: text for name, text in cls.sources.items()
                       if not name.startswith('org/spongepowered/asm/mixin/')}
        cls.sources['net/minecraft/world/level/block/entity/BlockEntity.java'] = cls.sources[
            'net/minecraft/world/level/block/entity/BlockEntity.java'].replace(
                ' extends ua.aia2.guard.mixin.AdAstraNasaMixin', '')
        cls.sources['net/minecraft/world/inventory/AbstractContainerMenu.java'] = cls.sources[
            'net/minecraft/world/inventory/AbstractContainerMenu.java'].replace(
                ' extends ua.aia2.guard.mixin.AdAstraNasaBaseMenuMixin', '')
        containers = 'net/minecraft/world/Containers.java'
        cls.sources[containers] = cls.sources[containers].replace(
            'import ua.aia2.guard.mixin.NasaProductionHarness;', '').replace(
                'NasaProductionHarness.spawn(level,entity)', 'level.addFreshEntity(entity)')
        manifest = json.loads((ROOT / 'content/research/evidence/nasa_production_v7/manifest.json').read_text())
        cls.row = next(row for row in manifest['sources']
                       if row['repository_path'].endswith('/NasaWorkbenchBlockEntity.java')
                       and row['source_kind'] == 'ad_astra')
        cls.native_source = (ROOT / cls.row['path']).read_text()
        start, end = method_bounds(cls.native_source, 'public void craft()')
        cls.native_craft = cls.native_source[start:end]
        machine = MACHINE + '.java'
        source = cls.sources[machine].replace('import ua.aia2.guard.mixin.NasaProductionHarness;', '').replace(
            'NasaProductionHarness.select(this,nativeResult)', 'nativeResult')
        source = source.replace('import net.minecraft.world.Container;',
                                'import net.minecraft.world.Container;import net.minecraft.world.Containers;')
        start, end = method_bounds(source, 'public void craft()')
        cls.sources[machine] = source[:start] + cls.native_craft + source[end:]
        base = BASE_MENU + '.java'
        source = cls.sources[base]
        cls.sources[base] = source[:source.rindex('}')] + '''
public boolean stillValid(net.minecraft.world.entity.player.Player player){return true;}
public net.minecraft.world.item.ItemStack quickMoveStack(net.minecraft.world.entity.player.Player player,int slot){return net.minecraft.world.item.ItemStack.EMPTY;}
}'''
        menu = NASA_MENU + '.java'
        source = cls.sources[menu]
        cls.sources[menu] = source[:source.rindex('}')] + '''
public void clicked(int slot,int button,net.minecraft.world.inventory.ClickType type,net.minecraft.world.entity.player.Player player){}
}'''
        cls.classes = cls.compile('native', cls.sources)
        cls.guard_classes = {path.relative_to(cls.classes).as_posix(): path.read_bytes()
                             for path in cls.classes.rglob('*.class')
                             if path.relative_to(cls.classes).as_posix().startswith('ua/aia2/guard/')}
        cls.target_classes = {path.relative_to(cls.classes).as_posix(): path.read_bytes()
                              for path in cls.classes.rglob('*.class')
                              if path.relative_to(cls.classes).as_posix().startswith(PREFIX)}
        cls.guard_jar = cls.jar(cls.directory / 'actual-guard-source-shaped-fixture.jar', cls.guard_classes)
        cls.target_jar = cls.jar(cls.directory / 'Ad-Astra-source-shaped-fixture.jar', cls.target_classes)

    @classmethod
    def tearDownClass(cls):
        if hasattr(cls, 'temp'):
            cls.temp.cleanup()

    @classmethod
    def compile(cls, name, sources):
        work = cls.directory / name
        output = work / 'classes'
        output.mkdir(parents=True)
        files = []
        for relative, source in sources.items():
            path = work / 'src' / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(source)
            files.append(str(path))
        files += [str(ROOT / f'companion/src/main/java/ua/aia2/guard/{name}.java') for name in
                  ['GuardPolicy', 'AdAstraNasaAccess', 'NasaIngredients', 'NasaProductionAccess',
                   'GuardedNasaDrop', 'ProductionMilestoneBridge']]
        files += [str(ROOT / f'companion/src/main/java/ua/aia2/guard/mixin/{name}.java') for name in sorted(MIXINS)]
        command = [str(JAVA), '--release', '21', '-proc:none', '-encoding', 'UTF-8',
                   '-cp', os.pathsep.join(map(str, [cls.annotations, cls.gson])), '-d', str(output), *files]
        result = subprocess.run(command, capture_output=True, text=True)
        if result.returncode:
            raise AssertionError(result.stdout + result.stderr)
        return output

    @staticmethod
    def jar(path, entries):
        with zipfile.ZipFile(path, 'w') as artifact:
            for name, raw in entries.items():
                artifact.writestr(name, raw)
        return path

    def check(self, guard=None, target=None):
        return checker.check(guard or self.guard_jar, [target or self.target_jar],
                             prefix=PREFIX, mixin_names=MIXINS)

    def test_exact_frozen_native_body_is_compiled_unwoven_with_real_annotations(self):
        self.assertEqual(hashlib.sha256((ROOT / self.row['path']).read_bytes()).hexdigest(), self.row['sha256'])
        source = self.sources[MACHINE + '.java']
        start, end = method_bounds(source, 'public void craft()')
        self.assertEqual(source[start:end], self.native_craft)
        self.assertNotIn('NasaProductionHarness', source)
        self.assertNotIn('NasaProductionAccess', source)
        self.assertFalse(any(name.startswith('org/spongepowered/asm/mixin/') for name in self.sources))
        target = checker.class_file(self.target_classes[MACHINE + '.class'])
        self.assertEqual(target['super'], 'net/minecraft/world/level/block/entity/BlockEntity')
        block_entity = checker.class_file((self.classes / 'net/minecraft/world/level/block/entity/BlockEntity.class').read_bytes())
        self.assertEqual(block_entity['super'], 'java/lang/Object')
        menu = checker.class_file((self.classes / 'net/minecraft/world/inventory/AbstractContainerMenu.class').read_bytes())
        self.assertEqual(menu['super'], 'java/lang/Object')

    def test_three_actual_optional_mixins_match_all_source_shaped_targets(self):
        report = self.check()
        self.assertEqual(report['status'], 'PASSED_BYTECODE_CONTRACTS_NOT_WEAVING', report)
        self.assertEqual(set(report['checked_mixins']), MIXINS)
        self.assertEqual(len(report['checks']), 7)
        self.assertTrue(all(row['require'] == 1 and len(row['matched_methods']) == 1 for row in report['checks']))
        invokes = [row for entry in report['checks'] for row in entry['invoke_checks']]
        self.assertEqual(len(invokes), 2)
        self.assertTrue(all(row['matches'] == 1 for row in invokes))
        self.assertEqual(report['unverified_details'], [])
        self.assertEqual(report['actual_mixin_transform'], 'NOT_RUN')
        data = checker.class_file(self.guard_classes['ua/aia2/guard/mixin/AdAstraNasaMixin.class'])
        redirects = [annotation for method in data['methods'] for annotation in method['annotations']
                     if annotation['type'].endswith('/Redirect;')]
        self.assertEqual(len(redirects), 2)
        self.assertTrue(all(row['require'] == row['allow'] == 1 for row in redirects))

    def test_actual_sponge_applies_all_three_to_source_shaped_fixture_only(self):
        cache = GRADLE_HOME / 'caches/modules-2/files-2.1'
        jars = [self.annotations, self.gson]
        for folder, pattern in [(f'org.ow2.asm/{name}', '*.jar') for name in
                                ['asm', 'asm-tree', 'asm-commons', 'asm-util', 'asm-analysis']] + [
                                    ('com.google.guava/guava', '*.jar')]:
            matches = sorted((cache / folder).glob('**/' + pattern))
            if not matches:
                self.skipTest('Actual isolated Sponge transformer dependency unavailable: ' + folder)
            jars.append(matches[0])
        host = self.directory / 'isolated-source-fixture'
        host.mkdir()
        main = host / 'NasaSourceMixinMain.java'
        main.write_text('''package fixture;
import java.util.Arrays;
import org.objectweb.asm.ClassReader;
import org.objectweb.asm.tree.ClassNode;
import org.objectweb.asm.tree.MethodInsnNode;
import org.spongepowered.asm.launch.MixinBootstrap;
import org.spongepowered.asm.mixin.MixinEnvironment;
import org.spongepowered.asm.mixin.Mixins;
import org.spongepowered.asm.mixin.transformer.IMixinTransformer;
public final class NasaSourceMixinMain {
 private static int calls(ClassNode node,String method,String owner,String name){
  int count=0;for(var m:node.methods)if(m.name.equals(method))for(var instruction:m.instructions)
   if(instruction instanceof MethodInsnNode call&&(owner==null||call.owner.equals(owner))&&call.name.contains(name))count++;
  return count;
 }
 public static void main(String[] arguments)throws Exception{
  MixinBootstrap.init();Mixins.addConfiguration("nasa-source-fixture.mixins.json");
  var phase=MixinEnvironment.class.getDeclaredMethod("gotoPhase",MixinEnvironment.Phase.class);
  phase.setAccessible(true);phase.invoke(null,MixinEnvironment.Phase.DEFAULT);
  var constructor=Class.forName("org.spongepowered.asm.mixin.transformer.MixinTransformer").getDeclaredConstructor();
  constructor.setAccessible(true);var transformer=(IMixinTransformer)constructor.newInstance();
  String prefix="earth.terrarium.adastra.common.";
  for(String suffix:new String[]{"menus.base.BaseContainerMenu","menus.machines.NasaWorkbenchMenu","blockentities.machines.NasaWorkbenchBlockEntity"}){
   String name=prefix+suffix;byte[] input;
   try(var stream=NasaSourceMixinMain.class.getClassLoader().getResourceAsStream(name.replace('.','/')+".class")){
    if(stream==null)throw new AssertionError("Missing source-shaped target "+name);input=stream.readAllBytes();
   }
   byte[] output=transformer.transformClassBytes(name,name,input);
   if(Arrays.equals(input,output))throw new AssertionError("Unchanged optional target "+name);
   var node=new ClassNode();new ClassReader(output).accept(node,0);
   if(suffix.endsWith("NasaWorkbenchBlockEntity")){
    if(calls(node,"craft","net/minecraft/world/Containers","dropItemStack")!=0
       ||calls(node,"craft","net/minecraft/world/item/ItemStack","shrink")!=0
       ||calls(node,"craft",null,"aia2$drop")!=1||calls(node,"craft",null,"aia2$debit")!=1
       ||calls(node,"craft",null,"aia2$finish")!=1||calls(node,"canCraft",null,"aia2$select")!=1)
     throw new AssertionError("NASA native drop/debit or entry/selection injection mismatch");
   }else if(suffix.endsWith("BaseContainerMenu")){
    if(calls(node,"stillValid",null,"aia2$stillOwned")!=1||calls(node,"quickMoveStack",null,"aia2$shiftMove")!=1)
     throw new AssertionError("Base menu injections missing");
   }else if(calls(node,"clicked",null,"aia2$ownerClick")!=1)throw new AssertionError("NASA click injection missing");
  }
  System.out.println("REAL_SPONGE_THREE_NASA_SOURCE_SHAPED_TARGETS_APPLIED: exact native craft body; modeled dependencies; installed Ad Astra binary and client boot NOT tested");
 }
}''')
        classpath = os.pathsep.join(map(str, jars))
        compiled = subprocess.run([str(JAVA), '--release', '21', '-proc:none', '-cp', classpath,
                                   '-d', str(host), str(ROOT / 'tests/fixtures/isolated-mixin-v6/IsolatedMixinService.java'),
                                   str(main)], capture_output=True, text=True)
        self.assertEqual(compiled.returncode, 0, compiled.stdout + compiled.stderr)
        services = host / 'META-INF/services'
        services.mkdir(parents=True)
        (services / 'org.spongepowered.asm.service.IMixinService').write_text('fixture.IsolatedMixinService\n')
        (services / 'org.spongepowered.asm.service.IGlobalPropertyService').write_text('fixture.IsolatedMixinService$Properties\n')
        (host / 'nasa-source-fixture.mixins.json').write_text(json.dumps({
            'required': True, 'minVersion': '0.8', 'package': 'ua.aia2.guard.mixin',
            'compatibilityLevel': 'JAVA_21', 'mixins': sorted(MIXINS), 'injectors': {'defaultRequire': 1}}))
        transformed = subprocess.run([str(JAVA.with_name('java')), '-cp',
                                      os.pathsep.join([str(host), str(self.classes), classpath]),
                                      'fixture.NasaSourceMixinMain'], cwd=self.directory,
                                     capture_output=True, text=True, timeout=45)
        self.assertEqual(transformed.returncode, 0, transformed.stdout + transformed.stderr)
        self.assertIn('REAL_SPONGE_THREE_NASA_SOURCE_SHAPED_TARGETS_APPLIED', transformed.stdout)
        print(transformed.stdout.strip())

    def test_wrong_compiled_craft_descriptor_is_rejected(self):
        entries = dict(self.guard_classes)
        name = 'ua/aia2/guard/mixin/AdAstraNasaMixin.class'
        self.assertIn(b'craft()V', entries[name])
        entries[name] = entries[name].replace(b'craft()V', b'craft()Z')
        jar = self.jar(self.directory / 'wrong-craft-descriptor-guard.jar', entries)
        report = self.check(guard=jar)
        self.assertEqual(report['status'], 'FAILED')
        self.assertIn('missing_method', {row['kind'] for row in report['errors']})

    def test_missing_native_drop_or_debit_invocation_is_rejected(self):
        for original, changed in [(b'dropItemStack', b'dropItemStacX'), (b'shrink', b'shrinX')]:
            with self.subTest(invocation=original.decode()):
                entries = dict(self.target_classes)
                self.assertIn(original, entries[MACHINE + '.class'])
                entries[MACHINE + '.class'] = entries[MACHINE + '.class'].replace(original, changed)
                target = self.jar(self.directory / (original.decode() + '-missing-source-shaped.jar'), entries)
                report = self.check(target=target)
                self.assertEqual(report['status'], 'FAILED')
                self.assertEqual({row['kind'] for row in report['errors']}, {'missing_invocation'})

    def test_each_missing_optional_target_class_is_rejected(self):
        for name in [MACHINE, BASE_MENU, NASA_MENU]:
            with self.subTest(target=name):
                entries = {key: value for key, value in self.target_classes.items() if key != name + '.class'}
                target = self.jar(self.directory / (name.rsplit('/', 1)[-1] + '-missing.jar'), entries)
                report = self.check(target=target)
                self.assertEqual(report['status'], 'FAILED')
                self.assertIn({'kind': 'missing_class', 'mixin':
                               'AdAstraNasaMixin' if name == MACHINE else
                               'AdAstraNasaBaseMenuMixin' if name == BASE_MENU else 'AdAstraNasaMenuMixin',
                               'target': name}, report['errors'])

    def test_installer_preflight_checks_fixture_jar_without_world_or_backup_writes(self):
        for mode in ['valid', 'descriptor', 'drop', 'shrink', 'missing_class']:
            with self.subTest(mode=mode), tempfile.TemporaryDirectory(prefix='aia2-nasa-abi-preflight-') as temporary:
                instance = Path(temporary) / 'instance'
                (instance / 'mods').mkdir(parents=True)
                marker = instance / 'saves/world/level.dat'
                marker.parent.mkdir(parents=True)
                marker.write_bytes(b'opaque-existing-space-and-team-progress')
                targets, guards = dict(self.target_classes), dict(self.guard_classes)
                if mode == 'descriptor':
                    key = 'ua/aia2/guard/mixin/AdAstraNasaMixin.class'
                    guards[key] = guards[key].replace(b'craft()V', b'craft()Z')
                elif mode in {'drop', 'shrink'}:
                    before, after = (b'dropItemStack', b'dropItemStacX') if mode == 'drop' else (b'shrink', b'shrinX')
                    targets[MACHINE + '.class'] = targets[MACHINE + '.class'].replace(before, after)
                elif mode == 'missing_class':
                    del targets[NASA_MENU + '.class']
                target = self.jar(instance / 'mods/Ad-Astra-neoforge-1.21.1-1.16.26-source-shaped-fixture.jar', targets)
                guard = self.jar(Path(temporary) / 'actual-guard-annotations-fixture.jar', guards)
                snapshot = lambda: {path.relative_to(instance).as_posix(): path.read_bytes()
                                    for path in instance.rglob('*') if path.is_file()}
                before = snapshot()
                if mode == 'valid':
                    report = installer.validate_ad_astra_nasa_pair(ROOT, instance, guard)
                    self.assertEqual(report['status'], 'PASSED_BYTECODE_CONTRACTS_NOT_WEAVING')
                    self.assertEqual(report['target_artifacts'][0]['sha256'], hashlib.sha256(target.read_bytes()).hexdigest())
                    self.assertEqual(report['actual_mixin_transform'], 'NOT_RUN')
                else:
                    kind = 'missing_method' if mode == 'descriptor' else 'missing_class' if mode == 'missing_class' else 'missing_invocation'
                    with self.assertRaisesRegex(installer.InstallError, 'Ad Astra NASA Mixin contract failed before installation: ' + kind):
                        installer.validate_ad_astra_nasa_pair(ROOT, instance, guard)
                self.assertEqual(snapshot(), before)
                self.assertFalse((instance / 'aia2-backups').exists())
                self.assertFalse((instance / 'kubejs').exists())
