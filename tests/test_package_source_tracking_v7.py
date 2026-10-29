"""A local distributable must not hide sources omitted from the Git checkpoint."""
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

from tools.package_runtime import validate_source_tracking


@unittest.skipUnless(shutil.which('git'), 'Git unavailable for isolated source tracking fixtures')
class PackageSourceTrackingTests(unittest.TestCase):
    def fixture(self, root):
        subprocess.run(['git', 'init', '--quiet', str(root)], check=True, capture_output=True)
        (root / '.gitignore').write_text('world/\n')
        fact = root / 'content/evidence/net/minecraft/world/Containers.json'
        fact.parent.mkdir(parents=True)
        fact.write_text('{"scope":"API facts, not a saved world"}\n')
        subprocess.run(['git', 'add', '.gitignore'], cwd=root, check=True, capture_output=True)
        return fact

    def test_ignored_world_named_source_cannot_hide_in_package(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            fact = self.fixture(root)
            before = fact.read_bytes()
            with self.assertRaisesRegex(ValueError, 'absent from the Git index.*Containers.json'):
                validate_source_tracking(root, [root / '.gitignore', fact])
            self.assertEqual(fact.read_bytes(), before)

    def test_reviewed_staged_source_is_packagable_without_a_commit(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            fact = self.fixture(root)
            subprocess.run(['git', 'add', '-f', str(fact)], cwd=root, check=True, capture_output=True)
            self.assertEqual(validate_source_tracking(root, [root / '.gitignore', fact]),
                             {'status': 'passed', 'checked': 2})

    def test_new_unstaged_source_is_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            self.fixture(root)
            new = root / 'new_source.py'
            new.write_text('# reviewed but not staged yet\n')
            with self.assertRaisesRegex(ValueError, 'new_source.py'):
                validate_source_tracking(root, [new])

    def test_extracted_archive_can_be_repackaged_without_git(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            source = root / 'portable.py'
            source.write_text('# extracted package\n')
            self.assertEqual(validate_source_tracking(root, [source]),
                             {'status': 'NOT_A_GIT_CHECKOUT', 'checked': 0})
