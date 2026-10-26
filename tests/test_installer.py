"""Installer transactions: preserve foreign quests, complete backups, atomic rollback."""
import builtins
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import zipfile
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('aia2_installer_under_test', ROOT / 'install_runtime.py')
installer = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = installer
SPEC.loader.exec_module(installer)

try:
    import nbtlib
except ImportError:
    nbtlib = None


class InstallerTest(unittest.TestCase):
    def test_required_mode_backup_dry_run_and_repeat_install(self):
        with tempfile.TemporaryDirectory() as tmp:
            instance = Path(tmp)
            (instance / 'mods').mkdir()
            config = instance / 'kubejs/config/aia2_runtime.json'
            config.parent.mkdir(parents=True)
            original = b'{"machineGuard":{"mode":"required"},"schema":1}'
            config.write_bytes(original)
            ftb = instance / 'config/ftbquests/quests/data.snbt'
            ftb.parent.mkdir(parents=True)
            ftb.write_text('{version:13,custom_setting:true}')
            user_script = instance / 'kubejs/server_scripts/user.js'
            user_script.parent.mkdir(parents=True)
            user_script.write_text('// preserve this')
            command = [sys.executable, str(ROOT / 'install_runtime.py'), str(instance)]
            result = subprocess.run(command + ['--dry-run'], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(config.read_bytes(), original)
            self.assertFalse((instance / 'aia2-backups').exists())
            result = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(config.read_text())['machineGuard']['mode'], 'required')
            self.assertEqual(ftb.read_text(), '{version:13,custom_setting:true}')
            self.assertEqual(user_script.read_text(), '// preserve this')
            bundled = list((ROOT / 'mods').glob('aia2-machine-guard-*.jar'))
            self.assertEqual(len(bundled), 1)
            self.assertEqual((instance / 'mods' / bundled[0].name).read_bytes(), bundled[0].read_bytes())
            self.assertFalse((instance / 'README.uk.md').exists())
            self.assertFalse((instance / 'companion').exists())
            backups = list((instance / 'aia2-backups').iterdir())
            self.assertEqual(len(backups), 1)
            self.assertEqual((backups[0] / 'original/kubejs/config/aia2_runtime.json').read_bytes(), original)
            self.assertEqual(json.loads((backups[0] / 'journal.json').read_text())['state'], 'completed')
            digest = hashlib.sha256(config.read_bytes()).digest()
            result = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn('No changes needed', result.stdout)
            self.assertEqual(hashlib.sha256(config.read_bytes()).digest(), digest)
            self.assertEqual(len(list((instance / 'aia2-backups').iterdir())), 1)


class InstallerTransactionTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        root = Path(self.temporary.name)
        self.source, self.instance = root / 'package', root / 'instance'
        self.put(self.source, 'mods/aia2-machine-guard-0.3.0-alpha.jar', b'new guard')
        self.put(self.source, 'mods/unrelated-bundled.jar', b'never copy')
        self.put(self.source, 'kubejs/server_scripts/aia2/runtime.js', b'new runtime')
        self.put(self.source, 'kubejs/startup_scripts/aia2/new_item.js', b'new item')
        self.put(self.source, 'kubejs/config/aia2_runtime.json', b'{"machineGuard":{"mode":"optional"}}')
        self.put(self.source, 'config/ftbquests/quests/data.snbt', b'{"version":13}')
        self.put(self.source, 'config/ftbquests/quests/chapter_groups.snbt', json.dumps({
            'chapter_groups': [{'id': 'ABCDEF0000000001', 'title': 'Епохи'},
                               {'id': 'ABCDEF0000000002', 'title': 'Магія'}]
        }).encode())
        self.put(self.source, 'config/ftbquests/quests/chapters/aia2_epoch_01.snbt', json.dumps({
            'id': 'ABCDEF0000000010', 'title': 'Перша епоха',
            'group': 'ABCDEF0000000001', 'quests': [
                {'id': 'ABCDEF0000000011', 'title': 'Оновлена віха', 'tasks': []}]
        }).encode())
        self.put(self.instance, 'mods/aia2-machine-guard-0.2.0-alpha.jar', b'old guard')
        self.put(self.instance, 'mods/another-mod.jar', b'user mod')
        self.put(self.instance, 'kubejs/server_scripts/aia2/runtime.js', b'old runtime')
        self.put(self.instance, 'kubejs/server_scripts/foreign.js', b'user script')
        self.put(self.instance, 'saves/world/level.dat', b'world progress, never modify')
        self.put(self.instance, 'saves/world/ftbquests/player.snbt', b'quest progress, never modify')
        self.put(self.instance, 'config/ftbquests/quests/data.snbt', b'{version:13,custom_setting:true}')

    @staticmethod
    def put(root, relative, data):
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        return path

    def install(self, dry_run=False):
        return installer.install(self.source, self.instance, dry_run=dry_run, output=lambda message: None)

    def snapshot(self):
        return {p.relative_to(self.instance).as_posix(): p.read_bytes()
                for p in self.instance.rglob('*')
                if p.is_file() and 'aia2-backups' not in p.relative_to(self.instance).parts}

    def test_json_merge_preserves_foreign_groups_and_fifty_two_extra_quests(self):
        group = 'config/ftbquests/quests/chapter_groups.snbt'
        chapter = 'config/ftbquests/quests/chapters/aia2_epoch_01.snbt'
        foreign = [{'id': f'F00000000000{n:04X}', 'title': f'Власний квест {n}', 'tasks': []}
                   for n in range(52)]
        self.put(self.instance, group, json.dumps({'custom_setting': 'keep', 'chapter_groups': [
            {'id': 'abcdef0000000001', 'title': 'Old epochs'},
            {'id': 'F000000000000001', 'title': 'Власна група'}]}).encode())
        self.put(self.instance, chapter, json.dumps({'id': 'ABCDEF0000000010', 'quests': [
            {'id': 'ABCDEF0000000011', 'title': 'Legacy milestone'}, *foreign]}).encode())
        extra_chapter = self.put(self.instance, 'config/ftbquests/quests/chapters/foreign.snbt',
                                 b'{id:"F000000000000002",quests:[]}')
        before = self.snapshot()
        backup = self.install()
        installed = json.loads((self.instance / chapter).read_text())
        self.assertEqual(len(installed['quests']), 53)
        self.assertEqual(installed['quests'][1:], foreign)
        self.assertEqual(installed['quests'][0]['title'], 'Оновлена віха')
        groups = json.loads((self.instance / group).read_text())
        self.assertEqual(len(groups['chapter_groups']), 3)
        self.assertEqual(groups['chapter_groups'][0]['title'], 'Епохи')
        self.assertEqual(groups['chapter_groups'][-1]['title'], 'Власна група')
        self.assertEqual(groups['custom_setting'], 'keep')
        self.assertEqual(extra_chapter.read_bytes(), before[extra_chapter.relative_to(self.instance).as_posix()])
        for relative in ('saves/world/level.dat', 'saves/world/ftbquests/player.snbt',
                         'kubejs/server_scripts/foreign.js', 'mods/another-mod.jar',
                         'config/ftbquests/quests/data.snbt'):
            self.assertEqual((self.instance / relative).read_bytes(), before[relative])
        self.assertEqual((backup / 'original' / chapter).read_bytes(), before[chapter])
        self.assertEqual((backup / 'original/mods/aia2-machine-guard-0.2.0-alpha.jar').read_bytes(), b'old guard')
        self.assertFalse((self.instance / 'mods/aia2-machine-guard-0.2.0-alpha.jar').exists())
        self.assertEqual((self.instance / 'mods/aia2-machine-guard-0.3.0-alpha.jar').read_bytes(), b'new guard')
        self.assertFalse((self.instance / 'mods/unrelated-bundled.jar').exists())
        installed_snapshot = self.snapshot()
        self.assertIsNone(self.install())
        self.assertEqual(self.snapshot(), installed_snapshot)
        self.assertEqual(len(list((self.instance / 'aia2-backups').iterdir())), 1)

    @unittest.skipUnless(nbtlib, 'nbtlib required to verify actual installed FTB SNBT')
    def test_actual_snbt_groups_and_chapters_keep_foreign_typed_data(self):
        group = 'config/ftbquests/quests/chapter_groups.snbt'
        chapter = 'config/ftbquests/quests/chapters/aia2_epoch_01.snbt'
        self.put(self.instance, group, b'{custom_flag:1b, chapter_groups:[{id:"F000000000000001", title:"Foreign", custom_array:[I;1,2]}]}')
        self.put(self.instance, chapter, b'{id:"ABCDEF0000000010",quests:[{id:"F000000000000002",title:"Foreign quest",custom_flag:1b}]}')
        self.install()
        groups = nbtlib.parse_nbt((self.instance / group).read_text())
        quests = nbtlib.parse_nbt((self.instance / chapter).read_text())
        self.assertIsInstance(groups['custom_flag'], nbtlib.Byte)
        self.assertIsInstance(groups['chapter_groups'][-1]['custom_array'], nbtlib.IntArray)
        self.assertIsInstance(quests['quests'][-1]['custom_flag'], nbtlib.Byte)
        self.assertEqual(len(groups['chapter_groups']), 3)
        self.assertEqual(len(quests['quests']), 2)
        self.assertIsNone(self.install())

    @unittest.skipUnless(nbtlib, 'nbtlib required to verify FTB Library dialect')
    def test_ftb_editor_comments_optional_commas_and_escaped_text_roundtrip(self):
        group = 'config/ftbquests/quests/chapter_groups.snbt'
        text = r'''{
# FTB Library whole-line comment
chapter_groups = [
  {
    id: "F000000000000001"
    title: "Foreign\nsecond line"
    // Editor comments and comma-free fields
    custom_array: [I; 1 2,3]
  }
]
custom_flag: true
custom_word: Епохи
custom_exponent: 1E4
}'''
        self.put(self.instance, group, text.encode())
        self.install()
        result = installer._FTBSNBTReader((self.instance / group).read_text(), nbtlib).read()
        self.assertEqual(str(result['chapter_groups'][-1]['title']), 'Foreign\nsecond line')
        self.assertEqual(list(result['chapter_groups'][-1]['custom_array']), [1, 2, 3])
        self.assertIsInstance(result['custom_flag'], nbtlib.Byte)
        self.assertEqual(str(result['custom_word']), 'Епохи')
        self.assertIsInstance(result['custom_exponent'], nbtlib.Double)
        self.assertEqual(float(result['custom_exponent']), 10000)
        self.assertIsNone(self.install())

    def test_missing_snbt_parser_is_an_explicit_preflight_failure(self):
        self.put(self.instance, 'config/ftbquests/quests/chapter_groups.snbt',
                 b'{chapter_groups:[{id:"F000000000000001",title:"Foreign"}]}')
        original_import = builtins.__import__
        def no_nbtlib(name, *args, **kwargs):
            if name == 'nbtlib':
                raise ImportError('not installed')
            return original_import(name, *args, **kwargs)
        before = self.snapshot()
        with patch('builtins.__import__', side_effect=no_nbtlib):
            with self.assertRaisesRegex(installer.InstallError, 'python -m pip install nbtlib'):
                self.install()
        self.assertEqual(self.snapshot(), before)
        self.assertFalse((self.instance / 'aia2-backups').exists())

    def test_late_source_read_failure_happens_before_any_backup_or_replacement(self):
        bad_source = self.source / 'mods/aia2-machine-guard-0.3.0-alpha.jar'
        original_read = Path.read_bytes
        def fail_source(path):
            if path == bad_source:
                raise OSError('source became unreadable')
            return original_read(path)
        before = self.snapshot()
        with patch.object(Path, 'read_bytes', fail_source):
            with self.assertRaisesRegex(OSError, 'source became unreadable'):
                self.install()
        self.assertEqual(self.snapshot(), before)
        self.assertFalse((self.instance / 'aia2-backups').exists())

    def test_all_originals_are_backed_up_before_the_first_runtime_write(self):
        destination, operations = installer.plan_install(self.source, self.instance)
        original_write = installer._atomic_write
        checked = []
        def verify_before_write(path, data, mode=0o644):
            if 'aia2-backups' not in path.relative_to(destination).parts:
                backups = list((destination / 'aia2-backups').iterdir())
                self.assertEqual(len(backups), 1)
                journal = json.loads((backups[0] / 'journal.json').read_text())
                self.assertEqual(journal['state'], 'prepared')
                for operation in operations:
                    if operation.previous is not None:
                        self.assertEqual((backups[0] / 'original' / operation.relative).read_bytes(), operation.previous)
                checked.append(path)
            return original_write(path, data, mode)
        with patch.object(installer, '_atomic_write', side_effect=verify_before_write):
            installer.apply_plan(destination, operations, output=lambda message: None)
        self.assertTrue(checked)

    def test_failed_backup_does_not_change_any_runtime_file(self):
        before = self.snapshot()
        original_write = installer._atomic_write
        def fail_backup(path, data, mode=0o644):
            if 'original' in path.parts:
                raise OSError('backup volume full')
            return original_write(path, data, mode)
        with patch.object(installer, '_atomic_write', side_effect=fail_backup):
            with self.assertRaisesRegex(installer.InstallError, 'before any runtime file was changed'):
                self.install()
        self.assertEqual(self.snapshot(), before)

    def test_failure_after_writes_and_old_jar_removal_rolls_back_every_file(self):
        before = self.snapshot()
        original_write = installer._atomic_write
        failed = []
        def fail_completion(path, data, mode=0o644):
            if path.name == 'journal.json' and json.loads(data)['state'] == 'completed':
                self.assertFalse((self.instance / 'mods/aia2-machine-guard-0.2.0-alpha.jar').exists())
                self.assertTrue((self.instance / 'mods/aia2-machine-guard-0.3.0-alpha.jar').exists())
                failed.append(True)
                raise OSError('injected late write failure')
            return original_write(path, data, mode)
        with patch.object(installer, '_atomic_write', side_effect=fail_completion):
            with self.assertRaisesRegex(installer.InstallError, 'all changed runtime files rolled back'):
                self.install()
        self.assertTrue(failed)
        self.assertEqual(self.snapshot(), before)
        backups = list((self.instance / 'aia2-backups').iterdir())
        journal = json.loads((backups[0] / 'journal.json').read_text())
        self.assertEqual(journal['state'], 'rolled_back')
        self.assertEqual(journal['rollback_errors'], [])
        self.assertFalse(list(self.instance.rglob('*.aia2-*')))

    def test_failure_immediately_after_atomic_replace_also_rolls_back(self):
        before = self.snapshot()
        original_write = installer._atomic_write
        failed = []
        def fail_after_replace(path, data, mode=0o644):
            original_write(path, data, mode)
            if path == self.instance / 'kubejs/server_scripts/aia2/runtime.js' and not failed:
                failed.append(True)
                raise OSError('post-replace fault')
        with patch.object(installer, '_atomic_write', side_effect=fail_after_replace):
            with self.assertRaisesRegex(installer.InstallError, 'all changed runtime files rolled back'):
                self.install()
        self.assertEqual(self.snapshot(), before)

    def test_dry_run_reads_merges_and_plans_jar_migration_without_creating_files(self):
        before = self.snapshot()
        self.install(dry_run=True)
        self.assertEqual(self.snapshot(), before)
        self.assertFalse((self.instance / 'aia2-backups').exists())

    def test_ambiguous_source_companion_and_different_chapter_ids_fail_preflight(self):
        second = self.put(self.source, 'mods/aia2-machine-guard-0.2.0-alpha.jar', b'ambiguous source')
        before = self.snapshot()
        with self.assertRaisesRegex(installer.InstallError, 'exactly one'):
            self.install()
        second.unlink()
        self.put(self.instance, 'config/ftbquests/quests/chapters/aia2_epoch_01.snbt',
                 b'{"id":"F000000000000001","quests":[]}')
        before = self.snapshot()
        with self.assertRaisesRegex(installer.InstallError, 'chapter ID changed'):
            self.install()
        self.assertEqual(self.snapshot(), before)
        self.assertFalse((self.instance / 'aia2-backups').exists())

    def test_changed_target_after_preflight_is_not_overwritten(self):
        destination, operations = installer.plan_install(self.source, self.instance)
        self.put(self.instance, 'kubejs/server_scripts/aia2/runtime.js', b'concurrent edit')
        before = self.snapshot()
        with self.assertRaisesRegex(installer.InstallError, 'Destination changed during preflight'):
            installer.apply_plan(destination, operations, output=lambda message: None)
        self.assertEqual(self.snapshot(), before)
        self.assertFalse((self.instance / 'aia2-backups').exists())

    def test_symlink_destination_is_rejected_without_following_it(self):
        external = Path(self.temporary.name) / 'outside'
        external.mkdir()
        (self.instance / 'kubejs/startup_scripts').symlink_to(external, target_is_directory=True)
        with self.assertRaisesRegex(installer.InstallError, 'symlink/junction'):
            self.install()
        self.assertFalse(list(external.iterdir()))
        self.assertFalse((self.instance / 'aia2-backups').exists())


class V4PackagePairingTest(unittest.TestCase):
    def test_outdated_guard_fails_before_any_instance_change(self):
        with tempfile.TemporaryDirectory() as tmp:
            package=Path(tmp)/'package';instance=Path(tmp)/'instance'
            (package/'mods').mkdir(parents=True);(package/'config').mkdir()
            (package/'kubejs/config').mkdir(parents=True);(instance/'mods').mkdir(parents=True)
            (package/'mods/aia2-machine-guard-0.3.0-alpha.jar').write_bytes(b'old companion')
            (package/'kubejs/config/aia2_runtime.json').write_text('{"progressionVersion":4}')
            old=instance/'mods/aia2-machine-guard-0.3.0-alpha.jar';old.write_bytes(b'player installed companion')
            with self.assertRaisesRegex(installer.InstallError,'damaged|outdated|API4'):
                installer.install(package,instance)
            self.assertEqual(old.read_bytes(),b'player installed companion')
            self.assertFalse((instance/'aia2-backups').exists())
            self.assertFalse((instance/'kubejs').exists())


class RootsGuardPackagePairingTest(unittest.TestCase):
    def test_missing_energy_guard_is_rejected_before_any_backup(self):
        root=Path(__file__).resolve().parents[1]
        bundled=list((root/'mods').glob('aia2-machine-guard-*.jar'))
        self.assertEqual(len(bundled),1)
        with tempfile.TemporaryDirectory() as tmp:
            package=Path(tmp)/'package';instance=Path(tmp)/'instance'
            (package/'mods').mkdir(parents=True);(package/'config').mkdir()
            (package/'kubejs/config').mkdir(parents=True);(instance/'mods').mkdir(parents=True)
            (instance/'saves/world').mkdir(parents=True)
            marker=instance/'saves/world/level.dat';marker.write_bytes(b'world-preserved')
            with zipfile.ZipFile(bundled[0]) as original,zipfile.ZipFile(package/'mods'/bundled[0].name,'w') as altered:
                for name in original.namelist():
                    if name!='ua/aia2/guard/PowahOrbAccess.class':altered.writestr(name,original.read(name))
            (package/'kubejs/config/aia2_runtime.json').write_text('{"progressionVersion":4}')
            with self.assertRaisesRegex(installer.InstallError,'EnderIO/Powah cached production'):
                installer.install(package,instance)
            self.assertEqual(marker.read_bytes(),b'world-preserved')
            self.assertFalse((instance/'aia2-backups').exists())
            self.assertFalse((instance/'kubejs').exists())

    def test_missing_industrial_guard_is_rejected_before_instance_changes(self):
        source = Path(__file__).resolve().parents[1]
        bundled = list((source/'mods').glob('aia2-machine-guard-*.jar'))
        self.assertEqual(len(bundled), 1)
        with tempfile.TemporaryDirectory() as tmp:
            package=Path(tmp)/'package';instance=Path(tmp)/'instance'
            (package/'mods').mkdir(parents=True);(package/'config').mkdir()
            (package/'kubejs/config').mkdir(parents=True);(instance/'saves/world').mkdir(parents=True)
            (instance/'mods').mkdir()
            marker=instance/'saves/world/level.dat';marker.write_bytes(b'world-preserved')
            with zipfile.ZipFile(bundled[0]) as original, zipfile.ZipFile(package/'mods'/bundled[0].name,'w') as altered:
                for name in original.namelist():
                    if name != 'ua/aia2/guard/mixin/OritechFluidMachineMixin.class':
                        altered.writestr(name,original.read(name))
            (package/'kubejs/config/aia2_runtime.json').write_text('{"progressionVersion":4}')
            with self.assertRaisesRegex(installer.InstallError,'MI/Oritech native process'):
                installer.install(package,instance)
            self.assertEqual(marker.read_bytes(),b'world-preserved')
            self.assertFalse((instance/'aia2-backups').exists())
            self.assertFalse((instance/'kubejs').exists())

    def test_missing_ritual_observer_fails_before_backups(self):
        with tempfile.TemporaryDirectory() as tmp:
            package=Path(tmp)/'package';instance=Path(tmp)/'instance'
            (package/'mods').mkdir(parents=True);(package/'config').mkdir()
            (package/'kubejs/config').mkdir(parents=True);(instance/'mods').mkdir(parents=True)
            with zipfile.ZipFile(package/'mods/aia2-machine-guard-0.4.4-alpha.jar','w') as jar:
                for name in ['Aia2MachineGuard','KeyProductionBridge','FtbQuestBridge','RhinoLongMapBridge','ProductionMilestoneBridge','CreativeManaGuard']:
                    jar.writestr('ua/aia2/guard/'+name+'.class',b'fixture')
                for name in ['DraconicFusionCoreMixin','BotaniaManaItemHandlerMixin','BotaniaManaTabletPoolMixin','RootsMortarMixin']:
                    jar.writestr('ua/aia2/guard/mixin/'+name+'.class',b'fixture')
            (package/'kubejs/config/aia2_runtime.json').write_text('{"progressionVersion":4}')
            with self.assertRaisesRegex(installer.InstallError,'ritual completion observer'):
                installer.install(package,instance)
            self.assertFalse((instance/'aia2-backups').exists())
            self.assertFalse((instance/'kubejs').exists())

    def test_missing_interaction_guard_is_rejected_without_world_changes(self):
        with tempfile.TemporaryDirectory() as tmp:
            package=Path(tmp)/'package';instance=Path(tmp)/'instance'
            (package/'mods').mkdir(parents=True);(package/'config').mkdir()
            (package/'kubejs/config').mkdir(parents=True);(instance/'mods').mkdir(parents=True)
            (instance/'saves/world').mkdir(parents=True)
            marker=instance/'saves/world/level.dat';marker.write_bytes(b'world-preserved')
            with zipfile.ZipFile(package/'mods/aia2-machine-guard-0.4.3-alpha.jar','w') as jar:
                for name in ['Aia2MachineGuard','KeyProductionBridge','FtbQuestBridge','RhinoLongMapBridge','ProductionMilestoneBridge','CreativeManaGuard']:
                    jar.writestr('ua/aia2/guard/'+name+'.class',b'fixture')
                for name in ['DraconicFusionCoreMixin','BotaniaManaItemHandlerMixin','BotaniaManaTabletPoolMixin']:
                    jar.writestr('ua/aia2/guard/mixin/'+name+'.class',b'fixture')
            (package/'kubejs/config/aia2_runtime.json').write_text('{"progressionVersion":4}')
            with self.assertRaisesRegex(installer.InstallError,'Roots mortar'):
                installer.install(package,instance)
            self.assertEqual(marker.read_bytes(),b'world-preserved')
            self.assertFalse((instance/'aia2-backups').exists())
            self.assertFalse((instance/'kubejs').exists())

    def test_missing_cached_fusion_guard_is_rejected_even_with_other_v4_bridges(self):
        with tempfile.TemporaryDirectory() as tmp:
            package=Path(tmp)/'package';instance=Path(tmp)/'instance'
            (package/'mods').mkdir(parents=True);(package/'config').mkdir()
            (package/'kubejs/config').mkdir(parents=True);(instance/'mods').mkdir(parents=True)
            with zipfile.ZipFile(package/'mods/aia2-machine-guard-0.4.2-alpha.jar','w') as jar:
                for name in ['Aia2MachineGuard','KeyProductionBridge','FtbQuestBridge','RhinoLongMapBridge','ProductionMilestoneBridge']:
                    jar.writestr('ua/aia2/guard/'+name+'.class',b'fixture')
            (package/'kubejs/config/aia2_runtime.json').write_text('{"progressionVersion":4}')
            with self.assertRaisesRegex(installer.InstallError,'cached-fusion'):
                installer.install(package,instance)
            self.assertFalse((instance/'aia2-backups').exists())
            self.assertFalse((instance/'kubejs').exists())

    def test_missing_component_guard_is_rejected_before_backups_or_world_writes(self):
        with tempfile.TemporaryDirectory() as tmp:
            package=Path(tmp)/'package';instance=Path(tmp)/'instance'
            (package/'mods').mkdir(parents=True);(package/'config').mkdir()
            (package/'kubejs/config').mkdir(parents=True);(instance/'mods').mkdir(parents=True)
            (instance/'saves/world').mkdir(parents=True)
            marker=instance/'saves/world/level.dat';marker.write_bytes(b'world-preserved')
            with zipfile.ZipFile(package/'mods/aia2-machine-guard-0.4.2.1-alpha.jar','w') as jar:
                for name in ['Aia2MachineGuard','KeyProductionBridge','FtbQuestBridge','RhinoLongMapBridge','ProductionMilestoneBridge']:
                    jar.writestr('ua/aia2/guard/'+name+'.class',b'fixture')
                jar.writestr('ua/aia2/guard/mixin/DraconicFusionCoreMixin.class',b'fixture')
            (package/'kubejs/config/aia2_runtime.json').write_text('{"progressionVersion":4}')
            with self.assertRaisesRegex(installer.InstallError,'component-aware'):
                installer.install(package,instance)
            self.assertEqual(marker.read_bytes(),b'world-preserved')
            self.assertFalse((instance/'aia2-backups').exists())
            self.assertFalse((instance/'kubejs').exists())


if __name__ == '__main__':
    unittest.main()
