"""Actual NASA guard/handlers with modeled optional receivers; no weaving claim."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class AdAstraNasaGuardTests(unittest.TestCase):
    def test_exact_source_contract_covers_cache_preview_and_both_callers(self):
        manifest = json.loads((ROOT/'content/research/evidence/ad_astra_core_v6/manifest.json').read_text())
        sources = {}
        for row in manifest['sources']:
            raw = (ROOT/row['path']).read_bytes()
            self.assertEqual(hashlib.sha256(raw).hexdigest(), row['sha256'])
            sources[row['repository_path']] = raw.decode()
        self.assertTrue(manifest['source_version_matches_export'])
        machine = sources['src/main/java/earth/terrarium/adastra/common/blockentities/machines/NasaWorkbenchBlockEntity.java']
        menu = sources['src/main/java/earth/terrarium/adastra/common/menus/machines/NasaWorkbenchMenu.java']
        base = sources['src/main/java/earth/terrarium/adastra/common/menus/base/BaseContainerMenu.java']
        recipe = sources['src/main/java/earth/terrarium/adastra/common/recipes/machines/NasaWorkbenchRecipe.java']
        self.assertIn('protected NasaWorkbenchRecipe recipe;', machine)
        self.assertIn('setItem(14, recipe.result());', machine)
        self.assertIn('if (time % 30 == 0 && canFunction() && canCraft())', machine)
        self.assertIn('if (slotIndex == 14)', menu)
        self.assertIn('entity.craft();', menu)
        self.assertIn('return true;', base.split('public boolean stillValid', 1)[1].split('}', 1)[0])
        self.assertIn('protected final T entity;', base)
        self.assertIn('public T getEntity()', base)
        self.assertIn('List<Ingredient> ingredients,', recipe)
        self.assertIn('ItemStack result', recipe)
        self.assertIn('ingredients.get(i).test(container.getItem(i))', recipe)
        native_body = machine.split('public void craft() {', 1)[1].split('\n    public void spawnWorkingParticles', 1)[0]
        fixture = json.loads((ROOT/'tests/fixtures/ad-astra-nasa-host.json').read_text())
        modeled = fixture['earth/terrarium/adastra/common/blockentities/machines/NasaWorkbenchBlockEntity.java']
        modeled_body = modeled.split('public void craft(){', 1)[1].split('if (!AdAstraNasaHarness.finish(this)) return;', 1)[1]
        # The handler runs before the exact original native cost/drop body.
        self.assertEqual(native_body.strip().removesuffix('}').strip(), modeled_body.strip().removesuffix('}').strip().removesuffix('}').strip())
        self.assertLess(native_body.index('Containers.dropItemStack'), native_body.index('getItem(i).shrink(1)'))
        self.assertNotIn('finishedMachine', (ROOT/'companion/src/main/java/ua/aia2/guard/AdAstraNasaAccess.java').read_text())

    def test_actual_helper_handlers_cached_recipe_output_owner_reload_and_menu(self):
        jdk = Path(os.environ.get('JAVA_HOME', '/workspace/aia2-toolchains/jdk-21.0.9'))
        if not (jdk/'bin/javac').is_file():
            self.skipTest('JDK21 unavailable')
        fixture = json.loads((ROOT/'tests/fixtures/ad-astra-nasa-host.json').read_text())
        for mode, parent in [('base', 'AdAstraNasaBaseMenuMixin'), ('nasa', 'AdAstraNasaMenuMixin')]:
            with self.subTest(mode=mode), tempfile.TemporaryDirectory(prefix='aia2-nasa-') as directory:
                files = []
                for name, text in fixture.items():
                    if name.endswith('/AbstractContainerMenu.java'):
                        text = text.replace('extends ua.aia2.guard.mixin.AdAstraNasaBaseMenuMixin', 'extends ua.aia2.guard.mixin.' + parent)
                    path = Path(directory)/name
                    path.parent.mkdir(parents=True, exist_ok=True); path.write_text(text)
                    files.append(str(path))
                files += [str(ROOT/'tests/fixtures/AdAstraNasaHarness.java')]
                files += [str(ROOT/f'companion/src/main/java/ua/aia2/guard/{name}.java') for name in ['GuardPolicy', 'AdAstraNasaAccess']]
                files += [str(ROOT/f'companion/src/main/java/ua/aia2/guard/mixin/{name}.java') for name in ['AdAstraNasaMixin', 'AdAstraNasaMenuMixin', 'AdAstraNasaBaseMenuMixin']]
                compiled = subprocess.run([str(jdk/'bin/javac'), '-encoding', 'UTF-8', '-d', directory, *files], capture_output=True, text=True)
                self.assertEqual(compiled.returncode, 0, compiled.stdout + compiled.stderr)
                tested = subprocess.run([str(jdk/'bin/java'), '-cp', directory, 'ua.aia2.guard.mixin.AdAstraNasaHarness', mode], capture_output=True, text=True)
                self.assertEqual(tested.returncode, 0, tested.stdout + tested.stderr)
                self.assertIn('Ad Astra NASA modeled assertions PASS', tested.stdout)
                print(tested.stdout.strip())
