"""Curated NASA action requirement helper, executed against explicit Java host models."""
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]


class RequiredSpaceActionsTests(unittest.TestCase):
    def test_actual_helper_exact_epochs_teams_reads_failures_and_no_adoption(self):
        jdk = Path(os.environ.get('JAVA_HOME', '/workspace/aia2-toolchains/jdk-21.0.9'))
        if not (jdk / 'bin/javac').is_file():
            self.skipTest('JDK21 unavailable')
        fixtures = json.loads((ROOT / 'tests/fixtures/required-space-actions-host-v10.json').read_text())
        with tempfile.TemporaryDirectory(prefix='aia2-required-space-actions-v10-') as temporary:
            directory = Path(temporary)
            files = []
            for relative, source in fixtures.items():
                path = directory / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(source)
                files.append(str(path))
            files += [str(ROOT / 'companion/src/main/java/ua/aia2/guard/RequiredSpaceActions.java'),
                      str(ROOT / 'tests/fixtures/RequiredSpaceActionsHarness.java')]
            compiled = subprocess.run([str(jdk / 'bin/javac'), '--release', '21', '-encoding', 'UTF-8',
                                       '-d', temporary, *files], capture_output=True, text=True)
            self.assertEqual(compiled.returncode, 0, compiled.stdout + compiled.stderr)
            tested = subprocess.run([str(jdk / 'bin/java'), '-cp', temporary,
                                     'ua.aia2.guard.RequiredSpaceActionsHarness'], capture_output=True, text=True)
            self.assertEqual(tested.returncode, 0, tested.stdout + tested.stderr)
            self.assertRegex(tested.stdout, r'\d+ required-space-action actual-helper modeled assertions PASS')
            print(tested.stdout.strip())

    def test_curated_ids_reference_existing_unchanged_native_nasa_rules(self):
        document = json.loads((ROOT / 'kubejs/config/aia2_mechanics.json').read_text())
        rules = {rule['id']: rule for rule in document['rules']}
        self.assertEqual(set(rules), {*json.loads((ROOT/'content/research/create_addons_pending_v12.json').read_text())['published_mechanic_hashes'], 'cca_electrum_mixing'})
        source = (ROOT / 'companion/src/main/java/ua/aia2/guard/RequiredSpaceActions.java').read_text()
        for tier, epoch in ((1, 37), (2, 37), (3, 38), (4, 38)):
            ident = f'nasa_tier_{tier}_rocket'
            self.assertIn('"' + ident + '"', source)
            rule = rules[ident]
            self.assertEqual(rule['epoch'], epoch)
            self.assertEqual(rule['output'], f'ad_astra:tier_{tier}_rocket')
            self.assertEqual(rule['serializer'], 'ad_astra:nasa_workbench')
            self.assertEqual(rule['recipeIds'], [f'ad_astra:nasa_workbench/tier_{tier}_rocket_from_nasa_workbench'])


if __name__ == '__main__':
    unittest.main()
