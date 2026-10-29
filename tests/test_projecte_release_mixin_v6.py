"""Compiled JVM selectors against exact release-source fixture, not a client boot."""
import copy
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
EVIDENCE = ROOT / 'content/research/evidence/projecte_release_hotfix_v6'
MIXIN = 'ua/aia2/guard/mixin/ProjectETabletSourceMixin.class'
JAVA = Path(os.environ.get('JAVA_HOME', '/workspace/aia2-toolchains/jdk-21.0.9')) / 'bin/javac'
GRADLE_HOME = Path(os.environ.get('GRADLE_USER_HOME',
                   '/workspace/aia2-toolchains/gradle-home' if Path('/workspace/aia2-toolchains/gradle-home').is_dir()
                   else str(Path.home()/'.gradle')))

STUBS = {
    'net/minecraft/network/RegistryFriendlyByteBuf.java': 'package net.minecraft.network; public class RegistryFriendlyByteBuf {public void writeBoolean(boolean b){} public void writeEnum(Enum<?> e){} public void writeByte(int b){}}',
    'net/minecraft/network/chat/Component.java': 'package net.minecraft.network.chat; public class Component {}',
    'net/minecraft/world/InteractionHand.java': 'package net.minecraft.world; public enum InteractionHand {MAIN_HAND, OFF_HAND}',
    'net/minecraft/world/InteractionResultHolder.java': 'package net.minecraft.world; public class InteractionResultHolder<T> {public static <T> InteractionResultHolder<T> success(T t){return new InteractionResultHolder<>();}}',
    'net/minecraft/world/MenuProvider.java': 'package net.minecraft.world; import net.minecraft.network.chat.Component; import net.minecraft.world.entity.player.*;import net.minecraft.world.inventory.AbstractContainerMenu;public interface MenuProvider {AbstractContainerMenu createMenu(int id, Inventory inv, Player player);Component getDisplayName();}',
    'net/minecraft/world/entity/player/Inventory.java': 'package net.minecraft.world.entity.player; public class Inventory {public int selected;}',
    'net/minecraft/world/entity/player/Player.java': 'package net.minecraft.world.entity.player; import java.util.*;import java.util.function.Consumer;import net.minecraft.network.RegistryFriendlyByteBuf;import net.minecraft.world.*;import net.minecraft.world.item.ItemStack;public class Player {public Inventory getInventory(){return new Inventory();}public ItemStack getItemInHand(InteractionHand h){return new ItemStack();}public OptionalInt openMenu(MenuProvider p,Consumer<RegistryFriendlyByteBuf> c){return OptionalInt.of(1);}}',
    'net/minecraft/world/inventory/AbstractContainerMenu.java': 'package net.minecraft.world.inventory; public class AbstractContainerMenu {}',
    'net/minecraft/world/item/ItemStack.java': 'package net.minecraft.world.item; public class ItemStack {}',
    'net/minecraft/world/item/Item.java': 'package net.minecraft.world.item; import net.minecraft.world.*;import net.minecraft.world.level.Level;import net.minecraft.world.entity.player.Player;public class Item {public static class Properties{} public Item(Properties p){} public InteractionResultHolder<ItemStack> use(Level l,Player p,InteractionHand h){return null;}}',
    'net/minecraft/world/level/Level.java': 'package net.minecraft.world.level; public class Level {public boolean isClientSide;}',
    'moze_intel/projecte/gameObjs/items/ItemPE.java': 'package moze_intel.projecte.gameObjs.items;public class ItemPE extends net.minecraft.world.item.Item {public ItemPE(Properties p){super(p);}}',
    'moze_intel/projecte/gameObjs/container/TransmutationContainer.java': 'package moze_intel.projecte.gameObjs.container;import net.minecraft.world.inventory.AbstractContainerMenu;import net.minecraft.world.entity.player.Inventory;import net.minecraft.world.InteractionHand;public class TransmutationContainer extends AbstractContainerMenu {public TransmutationContainer(int id,Inventory i,InteractionHand h,int selected){}}',
    'moze_intel/projecte/utils/text/PELang.java': 'package moze_intel.projecte.utils.text;import net.minecraft.network.chat.Component;public enum PELang {TRANSMUTATION_TRANSMUTE;public Component translate(){return new Component();}}',
    'org/jetbrains/annotations/NotNull.java': 'package org.jetbrains.annotations;import java.lang.annotation.*;@Retention(RetentionPolicy.CLASS) @Target({ElementType.METHOD,ElementType.PARAMETER,ElementType.TYPE_USE})public @interface NotNull {}',
    'ua/aia2/guard/ProjectEPassiveAccess.java': 'package ua.aia2.guard;import java.util.*;import java.util.function.Consumer;import net.minecraft.network.RegistryFriendlyByteBuf;import net.minecraft.world.*;import net.minecraft.world.entity.player.Player;import net.minecraft.world.item.Item;public class ProjectEPassiveAccess {public static OptionalInt openTablet(Item i,Player p,MenuProvider m,Consumer<RegistryFriendlyByteBuf> c){return p.openMenu(m,c);}}',
}


class ProjectEReleaseMixinTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not JAVA.is_file(): raise unittest.SkipTest('JDK21 unavailable for compiled selector regression')
        mixin_jars = list((GRADLE_HOME/'caches/modules-2/files-2.1/net.fabricmc/sponge-mixin').rglob('sponge-mixin-0.16.4+mixin.0.8.7.jar'))
        if not mixin_jars: raise unittest.SkipTest('Actual Sponge Mixin annotation library unavailable')
        cls.annotations = mixin_jars[0]
        cls.temp = tempfile.TemporaryDirectory(prefix='aia2-pe-release-bytecode-')
        cls.directory = Path(cls.temp.name)
        cls.source = EVIDENCE / 'official/src/main/java/moze_intel/projecte/gameObjs/items/TransmutationTablet.java'
        previous = json.loads((EVIDENCE/'manifest.json').read_text())['historical_aia2_mixin']
        raw = (ROOT/previous['path']).read_bytes()
        assert hashlib.sha256(raw).hexdigest() == previous['sha256'], 'Historical Mixin reproduction source changed'
        cls.bad = raw.decode()
        cls.fixed = (ROOT / 'companion/src/main/java/ua/aia2/guard/mixin/ProjectETabletSourceMixin.java').read_text()
        cls.bad_classes = cls.compile('old', cls.bad)
        cls.fixed_classes = cls.compile('fixed', cls.fixed)

    @classmethod
    def tearDownClass(cls):
        if hasattr(cls, 'temp'): cls.temp.cleanup()

    @classmethod
    def compile(cls, name, mixin):
        work = cls.directory / name; work.mkdir(); files = []
        for relative, value in dict(STUBS, **{
                'moze_intel/projecte/gameObjs/items/TransmutationTablet.java': cls.source.read_text(),
                'ua/aia2/guard/mixin/ProjectETabletSourceMixin.java': mixin}).items():
            target = work / 'src' / relative; target.parent.mkdir(parents=True, exist_ok=True); target.write_text(value); files.append(str(target))
        output = work / 'classes'; output.mkdir()
        command = [str(JAVA), '--release', '21', '-proc:none', '-encoding', 'UTF-8', '-cp', str(cls.annotations), '-d', str(output), *files]
        run = subprocess.run(command, capture_output=True, text=True)
        assert run.returncode == 0, run.stdout + run.stderr
        return output

    def check(self, guard=None, targets=None):
        return checker.check(guard or self.fixed_classes, targets if targets is not None else [self.fixed_classes], mixin_names={'ProjectETabletSourceMixin'})

    def test_release_source_hashes_and_development_pin_cannot_substitute(self):
        manifest = json.loads((EVIDENCE / 'manifest.json').read_text())
        self.assertEqual(manifest['release_pin'], '6aea247f7056eea1521db3f0c73d656857b75423')
        for row in manifest['sources']:
            self.assertEqual(hashlib.sha256((ROOT / row['path']).read_bytes()).hexdigest(), row['sha256'])
        source = self.source.read_text()
        self.assertIn('player.openMenu(', source)
        self.assertNotIn('openContainer(', source)
        self.assertNotIn('ITransmutationTablet', source)

    def test_old_compiled_selector_reproduces_zero_target_method_failure(self):
        report = self.check(self.bad_classes)
        self.assertEqual(report['status'], 'FAILED')
        self.assertEqual([e['kind'] for e in report['errors']], ['missing_method'])
        self.assertTrue(all(s.startswith('openContainer(') for s in report['errors'][0]['selectors']))
        self.assertEqual(report['errors'][0]['matched_methods'], [])

    def test_fixed_compiled_method_and_exact_invocation_keep_required_injection(self):
        report = self.check()
        self.assertEqual(report['status'], 'PASSED_BYTECODE_CONTRACTS_NOT_WEAVING')
        self.assertEqual(report['checks'][0]['require'], 1)
        self.assertEqual(len(report['checks'][0]['matched_methods']), 1)
        self.assertTrue(report['checks'][0]['matched_methods'][0].startswith('use('))
        self.assertEqual(report['checks'][0]['invoke_checks'][0]['matches'], 1)
        self.assertEqual(report['actual_mixin_transform'], 'NOT_RUN')

    def test_wrong_descriptor_and_wrong_invocation_are_rejected(self):
        raw = (self.fixed_classes / MIXIN).read_bytes()
        # Equal-length replacement leaves classfile structure intact and tests
        # actual compiled annotation descriptors rather than source regexes.
        for before, after, kind in [(b'InteractionResultHolder;', b'InteractionResultHoldeX;', 'missing_method'),
                                    (b';openMenu(', b';openMeny(', 'missing_invocation')]:
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as temporary:
                altered = Path(temporary) / MIXIN; altered.parent.mkdir(parents=True)
                self.assertIn(before, raw); altered.write_bytes(raw.replace(before, after))
                report = self.check(Path(temporary))
                self.assertEqual(report['status'], 'FAILED')
                self.assertIn(kind, [e['kind'] for e in report['errors']])

    def test_missing_actual_artifacts_never_passes_and_jar_crc_is_checked(self):
        report = self.check(targets=[])
        self.assertEqual(report['status'], 'BLOCKED')
        self.assertEqual(report['errors'][0]['kind'], 'missing_artifacts')
        with tempfile.TemporaryDirectory() as temporary:
            jar = Path(temporary) / 'release-source-fixture.jar'
            with zipfile.ZipFile(jar, 'w') as z:
                for path in self.fixed_classes.rglob('*.class'):
                    z.write(path, path.relative_to(self.fixed_classes).as_posix())
            result = self.check(targets=[jar])
            self.assertEqual(result['status'], 'PASSED_BYTECODE_CONTRACTS_NOT_WEAVING')
            self.assertEqual(result['target_artifacts'][0]['sha256'], hashlib.sha256(jar.read_bytes()).hexdigest())

    def test_class_parser_walks_lambda_and_reads_runtime_invisible_annotations(self):
        data = checker.class_file((self.fixed_classes / MIXIN).read_bytes())
        self.assertEqual(data['major'], 65)
        self.assertTrue(any(a['type'].endswith('/Mixin;') for a in data['annotations']))
        tablet = checker.class_file((self.fixed_classes / 'moze_intel/projecte/gameObjs/items/TransmutationTablet.class').read_bytes())
        use = next(m for m in tablet['methods'] if m['name'] == 'use')
        calls = checker.invocations(tablet, use)
        self.assertEqual(sum(c['name'] == 'openMenu' for c in calls), 1)
        self.assertTrue(any(m['name'].startswith('lambda$') for m in tablet['methods']))

    def test_actual_sponge_transformer_rejects_old_and_applies_fixed_redirect(self):
        cache = GRADLE_HOME/'caches/modules-2/files-2.1'
        jars = [self.annotations]
        for name in ['asm', 'asm-tree', 'asm-commons', 'asm-util', 'asm-analysis']:
            matches = list((cache/'org.ow2.asm'/name).rglob('*.jar'))
            if not matches: self.skipTest('Actual ASM transformer dependencies unavailable')
            jars.append(matches[0])
        for group, name in [('com.google.code.gson', 'gson'), ('com.google.guava', 'guava')]:
            matches = list((cache/group/name).rglob('*.jar'))
            if not matches: self.skipTest('Actual Mixin transformer dependency unavailable')
            jars.append(matches[0])
        host = self.directory/'mixin-host'; host.mkdir()
        cp = os.pathsep.join(map(str, jars))
        files = list((ROOT/'tests/fixtures/isolated-mixin-v6').glob('*.java'))
        compiled = subprocess.run([str(JAVA), '--release', '21', '-proc:none', '-cp', cp,
                                   '-d', str(host), *map(str, files)], capture_output=True, text=True)
        self.assertEqual(compiled.returncode, 0, compiled.stdout + compiled.stderr)
        services = host/'META-INF/services'; services.mkdir(parents=True)
        (services/'org.spongepowered.asm.service.IMixinService').write_text('fixture.IsolatedMixinService\n')
        (services/'org.spongepowered.asm.service.IGlobalPropertyService').write_text('fixture.IsolatedMixinService$Properties\n')
        (host/'release-fixture.mixins.json').write_text(json.dumps({
            'required': True, 'minVersion': '0.8', 'package': 'ua.aia2.guard.mixin',
            'compatibilityLevel': 'JAVA_21', 'mixins': ['ProjectETabletSourceMixin'],
            'injectors': {'defaultRequire': 1}}))
        for mode, classes, expected in [('bad', self.bad_classes, 'REAL_SPONGE_INVALID_INJECTION_REPRODUCED'),
                                         ('fixed', self.fixed_classes, 'REAL_SPONGE_FIXED_REDIRECT_APPLIED')]:
            with self.subTest(mode=mode):
                run = subprocess.run([str(JAVA.with_name('java')), '-cp', os.pathsep.join([str(host), str(classes), cp]),
                                      'fixture.IsolatedMixinMain', mode], cwd=self.directory,
                                     capture_output=True, text=True, timeout=45)
                self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
                self.assertIn(expected, run.stdout)
                print(run.stdout.strip())

    def test_installer_checks_actual_target_bytes_before_world_or_backup_writes(self):
        import install_runtime as installer
        with tempfile.TemporaryDirectory(prefix='aia2-pe-abi-install-') as temporary:
            work = Path(temporary); instance = work/'instance'; package = work/'package'
            (instance/'mods').mkdir(parents=True); (package/'mods').mkdir(parents=True)
            (package/'config').mkdir(); (package/'kubejs/config').mkdir(parents=True)
            (package/'kubejs/config/aia2_runtime.json').write_text('{"progressionVersion":4}')
            (package/'tools').mkdir(); (package/'tools/check_optional_mixin_targets_v6.py').write_bytes(
                (ROOT/'tools/check_optional_mixin_targets_v6.py').read_bytes())
            marker = instance/'saves/world/level.dat'; marker.parent.mkdir(parents=True); marker.write_bytes(b'opaque-saved-progress')
            with zipfile.ZipFile(instance/'mods/ProjectE-1.21.1-PE1.1.0.jar', 'w') as z:
                for path in self.fixed_classes.rglob('*.class'):
                    if path.relative_to(self.fixed_classes).as_posix().startswith('moze_intel/'):
                        z.write(path, path.relative_to(self.fixed_classes).as_posix())
            before = {p.relative_to(instance).as_posix(): p.read_bytes() for p in instance.rglob('*') if p.is_file()}
            companion = next((ROOT/'mods').glob('aia2-machine-guard-*.jar'))
            with zipfile.ZipFile(companion) as current:
                entries = {name: current.read(name) for name in current.namelist()}
            entries[MIXIN] = (self.bad_classes/MIXIN).read_bytes()
            owned = package/'mods/aia2-machine-guard-fixture.jar'
            with zipfile.ZipFile(owned, 'w') as bad:
                for name, raw in entries.items(): bad.writestr(name, raw)
            with self.assertRaisesRegex(installer.InstallError, 'ProjectE Tablet Mixin contract failed.*missing_method'):
                installer.install(package, instance, dry_run=True, output=lambda message: None)
            self.assertEqual(before, {p.relative_to(instance).as_posix(): p.read_bytes() for p in instance.rglob('*') if p.is_file()})
            self.assertFalse((instance/'aia2-backups').exists()); self.assertFalse((instance/'kubejs').exists())
            # The same preflight sees the fixed production annotation/redirect;
            # remaining compiled classes come from the current production JAR.
            with zipfile.ZipFile(owned) as original:
                entries = {name: original.read(name) for name in original.namelist()}
            entries[MIXIN] = (self.fixed_classes/MIXIN).read_bytes()
            with zipfile.ZipFile(owned, 'w') as fixed:
                for name, raw in entries.items(): fixed.writestr(name, raw)
            installer.install(package, instance, dry_run=True, output=lambda message: None)
            self.assertEqual(before, {p.relative_to(instance).as_posix(): p.read_bytes() for p in instance.rglob('*') if p.is_file()})
            self.assertFalse((instance/'aia2-backups').exists()); self.assertFalse((instance/'kubejs').exists())
