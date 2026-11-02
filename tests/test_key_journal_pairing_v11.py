"""Compiled deployment capability and read-only installer rejection.

The tiny javac fixtures model an old/new companion ABI only. They do not test
journal behavior, Mixin dispatch, or Minecraft; separate suites cover those.
"""
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile
from unittest.mock import patch

from tools import check_optional_mixin_targets_v6 as checker

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('aia2_key_journal_installer_test', ROOT/'install_runtime.py')
installer = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = installer
SPEC.loader.exec_module(installer)
CLASS = 'ua/aia2/guard/KeyProductionBridge.class'


class KeyJournalPairingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        javac = Path(os.environ.get('JAVA_HOME', '/workspace/aia2-toolchains/jdk-21.0.9'))/'bin/javac'
        if not javac.is_file():
            available = shutil.which('javac')
            if available is None:
                raise unittest.SkipTest('javac unavailable for actual compiled capability fixtures')
            javac = Path(available)
        cls.temporary = tempfile.TemporaryDirectory(prefix='aia2-key-journal-pairing-')
        cls.directory = Path(cls.temporary.name)
        cls.classes = {}
        methods = {
            'valid': 'public static int journalProtectionVersion(){return 1;}',
            'missing': 'public static int oldJournalVersion(){return 1;}',
            'wrong-version': 'public static int journalProtectionVersion(){return 2;}',
            'private': 'private static int journalProtectionVersion(){return 1;}',
            'instance': 'public int journalProtectionVersion(){return 1;}',
            'long': 'public static long journalProtectionVersion(){return 1L;}',
            'argument': 'public static int journalProtectionVersion(int ignored){return 1;}',
        }
        for name, method in methods.items():
            folder = cls.directory/name
            source = folder/'src/ua/aia2/guard/KeyProductionBridge.java'
            source.parent.mkdir(parents=True)
            source.write_text('package ua.aia2.guard; public final class KeyProductionBridge {'+method+'}')
            result = subprocess.run([str(javac), '-encoding', 'UTF-8', '-d', str(folder/'classes'), str(source)],
                                    capture_output=True, text=True)
            if result.returncode:
                cls.temporary.cleanup()
                raise AssertionError(result.stdout+result.stderr)
            cls.classes[name] = (folder/'classes'/CLASS).read_bytes()

    @classmethod
    def tearDownClass(cls):
        cls.temporary.cleanup()

    def fixture(self, directory, raw):
        source, instance = directory/'package', directory/'instance'
        for folder in ('kubejs/config', 'config', 'mods', 'content/audit', 'tools'):
            (source/folder).mkdir(parents=True)
        (source/'kubejs/config/aia2_runtime.json').write_text(json.dumps({'progressionVersion': 4}))
        (source/'content/audit/v11-space-milestone-presentation.json').write_text('{}')
        shutil.copyfile(ROOT/'tools/check_optional_mixin_targets_v6.py',
                        source/'tools/check_optional_mixin_targets_v6.py')
        with zipfile.ZipFile(source/'mods/aia2-machine-guard-fixture.jar', 'w') as archive:
            archive.writestr(CLASS, raw)
        for relative, data in {
                'mods/aia2-machine-guard-old.jar': b'opaque old companion',
                'mods/foreign.jar': b'foreign mod',
                'saves/preserved/level.dat': b'opaque world',
                'saves/preserved/data/aia2_key_production_v1.dat': b'opaque 96-key journal',
                'saves/preserved/data/ftbquests.dat': b'opaque quest progress',
                'kubejs/config/aia2_runtime.json': b'old configuration'}.items():
            path = instance/relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
        return source, instance

    @staticmethod
    def snapshot(directory):
        return {path.relative_to(directory).as_posix(): path.read_bytes() if path.is_file() else None
                for path in directory.rglob('*')}

    def test_valid_compiled_public_static_int_capability_is_recognized(self):
        report = checker.key_journal_contract(self.classes['valid'])
        self.assertEqual(report['status'], 'passed')
        self.assertEqual(report['key_journal_protection'], 1)
        self.assertIn('behavioral tests remain separate', report['scope'])

    def test_each_incompatible_compiled_signature_and_version_is_rejected(self):
        for name, raw in self.classes.items():
            if name == 'valid':
                continue
            with self.subTest(compiled_fixture=name):
                with self.assertRaisesRegex(AssertionError, 'Missing key journal protection capability1'):
                    checker.key_journal_contract(raw)

    def test_wrong_class_and_truncated_compiled_bytes_are_rejected(self):
        raw = self.classes['valid']
        self.assertIn(b'ua/aia2/guard/KeyProductionBridge', raw)
        with self.assertRaisesRegex(AssertionError, 'Wrong key journal class'):
            checker.key_journal_contract(raw.replace(b'ua/aia2/guard/KeyProductionBridge',
                                                    b'ua/aia2/guard/KeyProductionBridgX'))
        for truncated in (b'', raw[:20], raw[:-1]):
            with self.subTest(length=len(truncated)):
                with self.assertRaises(AssertionError):
                    checker.key_journal_contract(truncated)

    def test_installer_validates_actual_compiled_capability(self):
        with tempfile.TemporaryDirectory(prefix='aia2-valid-key-pair-') as temporary:
            source, instance = self.fixture(Path(temporary), self.classes['valid'])
            before = self.snapshot(instance)
            report = installer.validate_key_journal_pair(source, self.classes['valid'])
            self.assertEqual(report['key_journal_protection'], 1)
            self.assertEqual(self.snapshot(instance), before)

    def test_installer_rejects_old_or_wrong_version_jar_before_any_write_even_dry_run(self):
        for name in ('missing', 'wrong-version'):
            for dry_run in (False, True):
                with self.subTest(compiled_fixture=name, dry_run=dry_run):
                    with tempfile.TemporaryDirectory(prefix='aia2-reject-old-key-pair-') as temporary:
                        source, instance = self.fixture(Path(temporary), self.classes[name])
                        before = self.snapshot(instance)
                        # Any attempted runtime/backup write is a test failure, independently
                        # of the full byte+directory snapshot below.
                        with patch.object(installer, '_atomic_write', side_effect=AssertionError('unexpected write')):
                            with self.assertRaisesRegex(installer.InstallError, 'key journal protection capability1'):
                                installer.install(source, instance, dry_run=dry_run, output=lambda _: None)
                        self.assertEqual(self.snapshot(instance), before)
                        self.assertFalse((instance/'aia2-backups').exists())

    def test_new_package_requires_preflight_tool_and_legacy_package_is_unchanged(self):
        with tempfile.TemporaryDirectory(prefix='aia2-key-pair-tool-') as temporary:
            source, instance = self.fixture(Path(temporary), self.classes['valid'])
            (source/'tools/check_optional_mixin_targets_v6.py').unlink()
            before = self.snapshot(instance)
            with self.assertRaisesRegex(installer.InstallError, 'preflight tool is missing'):
                installer.validate_key_journal_pair(source, self.classes['valid'])
            self.assertEqual(self.snapshot(instance), before)
            (source/'content/audit/v11-space-milestone-presentation.json').unlink()
            self.assertEqual(installer.validate_key_journal_pair(source, b'legacy fixture class'),
                             {'status': 'legacy_package'})


if __name__ == '__main__':
    unittest.main()
