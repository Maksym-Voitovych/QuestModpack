"""Actual station Mixin annotations/Sponge on source-shaped signatures only.

Optional target bodies and Minecraft/StationConstructionAccess dependencies are
modeled. This does not execute construction or certify the installed Ad Astra JAR.
"""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
import zipfile

from tools import check_optional_mixin_targets_v6 as checker

ROOT = Path(__file__).resolve().parents[1]
PREFIX = 'earth/terrarium/adastra/'
PACKET = PREFIX + 'common/network/packets/ServerboundConstructSpaceStationPacket'
TARGETS = {PACKET + '$Type', PREFIX + 'common/recipes/SpaceStationRecipe',
           PREFIX + 'common/handlers/SpaceStationHandler'}
MIXINS = {'AdAstraStationPacketMixin', 'AdAstraStationRecipeMixin', 'AdAstraStationRegisterMixin'}
JAVA = Path(os.environ.get('JAVA_HOME', '/workspace/aia2-toolchains/jdk-21.0.9')) / 'bin/javac'
GRADLE_HOME = Path(os.environ.get('GRADLE_USER_HOME',
    '/workspace/aia2-toolchains/gradle-home' if Path('/workspace/aia2-toolchains/gradle-home').is_dir()
    else str(Path.home() / '.gradle')))

# Deliberately minimal source-shaped signatures; the native consumer is NOT
# reproduced here. The real production guard is tested by its separate harness.
STUBS = {
    'net/minecraft/world/level/Level.java': 'package net.minecraft.world.level; public class Level {public boolean isClientSide(){return false;}}',
    'net/minecraft/world/entity/player/Player.java': 'package net.minecraft.world.entity.player; public class Player {}',
    'net/minecraft/server/level/ServerPlayer.java': 'package net.minecraft.server.level; public class ServerPlayer extends net.minecraft.world.entity.player.Player {}',
    'net/minecraft/server/level/ServerLevel.java': 'package net.minecraft.server.level; public class ServerLevel extends net.minecraft.world.level.Level {}',
    'net/minecraft/network/chat/Component.java': 'package net.minecraft.network.chat; public class Component {}',
    'net/minecraft/resources/ResourceKey.java': 'package net.minecraft.resources; public class ResourceKey<T> {}',
    PACKET + '.java': '''package earth.terrarium.adastra.common.network.packets;
import java.util.function.Consumer;import net.minecraft.world.entity.player.Player;
import net.minecraft.resources.ResourceKey;import net.minecraft.world.level.Level;import net.minecraft.network.chat.Component;
public record ServerboundConstructSpaceStationPacket(ResourceKey<Level> dimension,Component name){
 private static class Type {
  public Consumer<Player> handle(ServerboundConstructSpaceStationPacket packet){return (Consumer<Player>)(player -> {});}
  public Consumer<Player> handle(String unrelatedOverload){return player -> {};}
 }
}''',
    PREFIX + 'common/recipes/SpaceStationRecipe.java': '''package earth.terrarium.adastra.common.recipes;
import net.minecraft.world.entity.player.Player;import net.minecraft.world.level.Level;
public class SpaceStationRecipe {
 public static boolean hasIngredients(Player p,Level l,SpaceStationRecipe recipe){return true;}
 public static void consumeIngredients(Player p,Level l){}
}''',
    PREFIX + 'common/handlers/SpaceStationHandler.java': '''package earth.terrarium.adastra.common.handlers;
import net.minecraft.server.level.ServerPlayer;import net.minecraft.server.level.ServerLevel;import net.minecraft.network.chat.Component;
public class SpaceStationHandler {public static void constructSpaceStation(ServerPlayer player,ServerLevel level,Component name){}}
''',
    'ua/aia2/guard/StationConstructionAccess.java': '''package ua.aia2.guard;
import java.util.function.Consumer;import net.minecraft.world.entity.player.Player;import net.minecraft.world.level.Level;
import net.minecraft.server.level.ServerPlayer;import net.minecraft.server.level.ServerLevel;import net.minecraft.network.chat.Component;
public final class StationConstructionAccess {
 public static Consumer<Player> wrap(Object packet,Consumer<Player> nativeConsumer){return nativeConsumer;}
 public static boolean hasScope(){return true;}
 public static boolean hasIngredients(Player p,Level l,Object recipe){return true;}
 public static void consume(Player p,Level l){}
 public static boolean beforeRegister(ServerPlayer p,ServerLevel l,Component name){return true;}
 public static void afterRegister(ServerPlayer p,ServerLevel l,Component name){}
}''',
}


class StationAbiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not JAVA.is_file():
            raise unittest.SkipTest('JDK21 unavailable for source-shaped station ABI tests')
        cache = GRADLE_HOME / 'caches/modules-2/files-2.1'
        annotations = sorted((cache / 'net.fabricmc/sponge-mixin').glob('**/sponge-mixin-0.16.4+mixin.0.8.7.jar'))
        if not annotations:
            raise unittest.SkipTest('Real Sponge0.16.4+mixin0.8.7 annotation library unavailable')
        cls.annotations = annotations[-1]
        cls.temp = tempfile.TemporaryDirectory(prefix='aia2-station-source-shaped-abi-')
        cls.directory = Path(cls.temp.name)
        cls.classes = cls.compile('valid', STUBS)
        cls.guard_classes = {path.relative_to(cls.classes).as_posix(): path.read_bytes()
                             for path in cls.classes.rglob('*.class')
                             if path.relative_to(cls.classes).as_posix().startswith('ua/aia2/guard/')}
        cls.target_classes = {path.relative_to(cls.classes).as_posix(): path.read_bytes()
                              for path in cls.classes.rglob('*.class')
                              if path.relative_to(cls.classes).as_posix().startswith(PREFIX)}
        cls.guard = cls.jar(cls.directory / 'actual-station-mixins-modeled-helper.jar', cls.guard_classes)
        cls.targets = cls.jar(cls.directory / 'Ad-Astra-source-shaped-station-targets.jar', cls.target_classes)

    @classmethod
    def tearDownClass(cls):
        if hasattr(cls, 'temp'):
            cls.temp.cleanup()

    @classmethod
    def compile(cls, name, sources):
        directory = cls.directory / name
        classes = directory / 'classes'
        classes.mkdir(parents=True)
        paths = []
        for relative, source in sources.items():
            path = directory / 'src' / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(source)
            paths.append(str(path))
        paths += [str(ROOT / f'companion/src/main/java/ua/aia2/guard/mixin/{name}.java') for name in sorted(MIXINS)]
        result = subprocess.run([str(JAVA), '--release', '21', '-proc:none', '-encoding', 'UTF-8',
                                 '-cp', str(cls.annotations), '-d', str(classes), *paths], capture_output=True, text=True)
        if result.returncode:
            raise AssertionError(result.stdout + result.stderr)
        return classes

    @staticmethod
    def jar(path, entries):
        with zipfile.ZipFile(path, 'w') as archive:
            for name, raw in entries.items():
                archive.writestr(name, raw)
        return path

    def check(self, targets=None):
        return checker.check(self.guard, [targets or self.targets], prefix=PREFIX, mixin_names=MIXINS)

    def test_five_actual_handlers_have_exact_required_non_lambda_selectors(self):
        report = self.check()
        self.assertEqual(report['status'], 'PASSED_BYTECODE_CONTRACTS_NOT_WEAVING', report)
        self.assertEqual(set(report['checked_mixins']), MIXINS)
        self.assertEqual(len(report['checks']), 5)
        self.assertEqual(report['unverified_details'], [])
        self.assertEqual(report['actual_mixin_transform'], 'NOT_RUN')
        self.assertTrue(all(row['require'] == 1 and len(row['matched_methods']) == 1 for row in report['checks']))
        annotations = [annotation for name, raw in self.guard_classes.items()
                       if name.rsplit('/', 1)[-1].replace('.class', '') in MIXINS
                       for method in checker.class_file(raw)['methods'] for annotation in method['annotations']
                       if annotation['type'].endswith('/Inject;')]
        self.assertEqual(len(annotations), 5)
        selectors = [selector for annotation in annotations for selector in annotation['method']]
        self.assertTrue(all('(' in selector and 'lambda$' not in selector for selector in selectors))
        self.assertTrue(all(annotation['require'] == 1 for annotation in annotations))
        packet_checks = [row for row in report['checks'] if row['mixin'] == 'AdAstraStationPacketMixin']
        self.assertEqual(len(packet_checks), 1)
        self.assertEqual(len(packet_checks[0]['matched_methods']), 1)
        self.assertIn('ServerboundConstructSpaceStationPacket;)Ljava/util/function/Consumer;',
                      packet_checks[0]['matched_methods'][0])

    def test_frozen_source_declarations_support_only_the_claimed_shape(self):
        manifest = json.loads((ROOT / 'content/research/evidence/station_guard_v8/manifest.json').read_text())
        selected = {}
        for row in manifest['sources']:
            raw = (ROOT / row['path']).read_bytes()
            self.assertEqual(hashlib.sha256(raw).hexdigest(), row['sha256'])
            if row['source_kind'] == 'ad_astra':
                selected[row['repository_path']] = raw.decode() if row['repository_path'].endswith('.java') else ''
        packet = selected['src/main/java/earth/terrarium/adastra/common/network/packets/ServerboundConstructSpaceStationPacket.java']
        self.assertIn('private static class Type', packet)
        self.assertIn('public Consumer<Player> handle(ServerboundConstructSpaceStationPacket packet)', packet)
        self.assertIn('StructureTemplate structure', packet)
        self.assertNotIn('StructureTemplate structure', STUBS[PACKET + '.java'])
        recipe = selected['src/main/java/earth/terrarium/adastra/common/recipes/SpaceStationRecipe.java']
        self.assertIn('public static boolean hasIngredients(Player player, Level level, SpaceStationRecipe recipe)', recipe)
        self.assertIn('public static void consumeIngredients(Player player, Level level)', recipe)
        handler = selected['src/main/java/earth/terrarium/adastra/common/handlers/SpaceStationHandler.java']
        self.assertIn('public static void constructSpaceStation(ServerPlayer player, ServerLevel level, Component name)', handler)

    def test_wrong_compiled_handle_return_descriptor_is_rejected(self):
        sources = dict(STUBS)
        sources[PACKET + '.java'] = sources[PACKET + '.java'].replace(
            'public Consumer<Player> handle(ServerboundConstructSpaceStationPacket packet)',
            'public Object handle(ServerboundConstructSpaceStationPacket packet)')
        classes = self.compile('wrong-handle-return', sources)
        entries = {path.relative_to(classes).as_posix(): path.read_bytes()
                   for path in classes.rglob('*.class') if path.relative_to(classes).as_posix().startswith(PREFIX)}
        report = self.check(self.jar(self.directory / 'wrong-handle-return.jar', entries))
        self.assertEqual(report['status'], 'FAILED')
        self.assertIn('missing_method', {row['kind'] for row in report['errors']})

    def test_missing_required_station_method_is_rejected(self):
        entries = dict(self.target_classes)
        name = PREFIX + 'common/recipes/SpaceStationRecipe.class'
        self.assertIn(b'consumeIngredients', entries[name])
        entries[name] = entries[name].replace(b'consumeIngredients', b'consumeIngredientX')
        report = self.check(self.jar(self.directory / 'missing-native-payment-entry.jar', entries))
        self.assertEqual(report['status'], 'FAILED')
        self.assertIn('missing_method', {row['kind'] for row in report['errors']})

    def test_each_missing_station_target_class_is_rejected(self):
        for name in sorted(TARGETS):
            with self.subTest(target=name):
                entries = {key: value for key, value in self.target_classes.items() if key != name + '.class'}
                report = self.check(self.jar(self.directory / (name.rsplit('/', 1)[-1] + '-missing.jar'), entries))
                self.assertEqual(report['status'], 'FAILED')
                self.assertIn('missing_class', {row['kind'] for row in report['errors']})

    def test_real_sponge_applies_all_three_station_mixins_to_modeled_shapes(self):
        cache = GRADLE_HOME / 'caches/modules-2/files-2.1'
        jars = [self.annotations]
        for folder in ['com.google.code.gson/gson', 'com.google.guava/guava'] + [
                'org.ow2.asm/' + name for name in ['asm', 'asm-tree', 'asm-commons', 'asm-util', 'asm-analysis']]:
            found = sorted((cache / folder).glob('**/*.jar'))
            if not found:
                self.skipTest('Actual isolated Sponge dependency unavailable: ' + folder)
            jars.append(found[0])
        host = self.directory / 'isolated-transformer'
        host.mkdir()
        main = host / 'StationSourceMixinMain.java'
        main.write_text('''package fixture;
import java.util.Arrays;import org.objectweb.asm.ClassReader;import org.objectweb.asm.tree.ClassNode;
import org.objectweb.asm.tree.MethodInsnNode;import org.spongepowered.asm.launch.MixinBootstrap;
import org.spongepowered.asm.mixin.MixinEnvironment;import org.spongepowered.asm.mixin.Mixins;
import org.spongepowered.asm.mixin.transformer.IMixinTransformer;
public final class StationSourceMixinMain {
 private static int calls(ClassNode node,String method,String hook){int count=0;
  for(var m:node.methods)if(m.name.equals(method))for(var insn:m.instructions)
   if(insn instanceof MethodInsnNode call&&call.name.contains(hook))count++;return count;}
 public static void main(String[]args)throws Exception{
  MixinBootstrap.init();Mixins.addConfiguration("station-source-fixture.mixins.json");
  var phase=MixinEnvironment.class.getDeclaredMethod("gotoPhase",MixinEnvironment.Phase.class);
  phase.setAccessible(true);phase.invoke(null,MixinEnvironment.Phase.DEFAULT);
  var constructor=Class.forName("org.spongepowered.asm.mixin.transformer.MixinTransformer").getDeclaredConstructor();
  constructor.setAccessible(true);var transformer=(IMixinTransformer)constructor.newInstance();
  for(String name:new String[]{"earth.terrarium.adastra.common.network.packets.ServerboundConstructSpaceStationPacket$Type",
    "earth.terrarium.adastra.common.recipes.SpaceStationRecipe","earth.terrarium.adastra.common.handlers.SpaceStationHandler"}){
   byte[] input;try(var stream=StationSourceMixinMain.class.getClassLoader().getResourceAsStream(name.replace('.','/')+".class")){
    if(stream==null)throw new AssertionError("Missing fixture target "+name);input=stream.readAllBytes();}
   byte[]output=transformer.transformClassBytes(name,name,input);if(Arrays.equals(input,output))throw new AssertionError("Unchanged "+name);
   var node=new ClassNode();new ClassReader(output).accept(node,0);
   if(name.endsWith("$Type")){if(calls(node,"handle","aia2$stationScope")!=1)throw new AssertionError("Exact packet handle scope missing or duplicated");}
   else if(name.endsWith("SpaceStationRecipe")){
    if(calls(node,"hasIngredients","aia2$plan")!=1||calls(node,"consumeIngredients","aia2$pay")!=1)throw new AssertionError("Recipe guards missing");}
   else if(calls(node,"constructSpaceStation","aia2$register")!=2)throw new AssertionError("Registration HEAD/RETURN guards missing");
  }
  System.out.println("REAL_SPONGE_THREE_STATION_SOURCE_SHAPED_TARGETS_APPLIED: five actual handlers; modeled bodies/helper/Minecraft; installed binary and full client NOT tested");
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
        (host / 'station-source-fixture.mixins.json').write_text(json.dumps({
            'required': True, 'minVersion': '0.8', 'package': 'ua.aia2.guard.mixin',
            'compatibilityLevel': 'JAVA_21', 'mixins': sorted(MIXINS), 'injectors': {'defaultRequire': 1}}))
        result = subprocess.run([str(JAVA.with_name('java')), '-cp',
                                 os.pathsep.join([str(host), str(self.classes), classpath]),
                                 'fixture.StationSourceMixinMain'], cwd=self.directory,
                                capture_output=True, text=True, timeout=45)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn('REAL_SPONGE_THREE_STATION_SOURCE_SHAPED_TARGETS_APPLIED', result.stdout)
        print(result.stdout.strip())
