"""Installer regression: preserve a user's required guard and existing unrelated files."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


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
            self.assertTrue((instance / 'mods/aia2-machine-guard-0.2.0-alpha.jar').is_file())
            self.assertFalse((instance / 'README.uk.md').exists())
            self.assertFalse((instance / 'companion').exists())
            backups = list((instance / 'aia2-backups').iterdir())
            self.assertEqual(len(backups), 1)
            self.assertEqual((backups[0] / 'original/kubejs/config/aia2_runtime.json').read_bytes(), original)
            digest = hashlib.sha256(config.read_bytes()).digest()
            result = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn('No changes needed', result.stdout)
            self.assertEqual(hashlib.sha256(config.read_bytes()).digest(), digest)
            self.assertEqual(len(list((instance / 'aia2-backups').iterdir())), 1)


if __name__ == '__main__':
    unittest.main()
