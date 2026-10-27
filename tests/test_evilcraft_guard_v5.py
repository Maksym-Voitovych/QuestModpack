"""Actual guard and three handlers, with modeled optional hosts and real stage policy."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]

class EvilCraftGuardTests(unittest.TestCase):
    def test_exact_sources_cache_dispatch_cost_boundaries_and_manifest(self):
        data=json.loads((ROOT/'content/research/evidence/dark_magic_native_v5/manifest.json').read_text())
        sources={}
        for row in data['sources']:
            raw=(ROOT/row['path']).read_bytes()
            self.assertEqual(hashlib.sha256(raw).hexdigest(),row['sha256'])
            if row['mod_id']=='evilcraft':sources[Path(row['repository_path']).name]=raw.decode()
        self.assertIn('mod_version=1.2.99',sources['gradle.properties'].replace(' ',''))
        self.assertIn('minecraft_version=1.21.1',sources['gradle.properties'].replace(' ',''))
        self.assertIn('getRecipesFor(getRegistry()',sources['BlockEntityBloodInfuser.java'])
        self.assertIn('return recipeCache.get',sources['BlockEntityBloodInfuser.java'])
        infuse=sources['InfuseItemTickAction.java'].split('public void onTick',1)[1]
        self.assertLess(infuse.index('getRecipe(tile)'),infuse.index('getTank().drain'))
        reanimate=sources['ReanimateTickAction.java'].split('public void onTick',1)[1]
        self.assertLess(reanimate.index('getTank().drain'),reanimate.index('getEntityType()'))
        self.assertIn('public EntityType<?> getEntityType()',sources['BlockEntitySpiritReanimator.java'])
        self.assertIn('public void onItemDrop(ItemStack',sources['BlockEntitySpiritFurnace.java'])
        self.assertEqual(json.loads((ROOT/'kubejs/config/aia2_runtime.json').read_text())['itemGates']['minecraft:nether_star'],30,
                         'The future-loot scenario must reflect the actual pack floor')

    def test_actual_helpers_handlers_receiver_output_cache_reload_and_key_policy(self):
        jdk=Path(os.environ.get('JAVA_HOME','/workspace/aia2-toolchains/jdk-21.0.9'))
        if not (jdk/'bin/javac').is_file():self.skipTest('JDK21 unavailable')
        original=json.loads((ROOT/'tests/fixtures/evilcraft-infusion-host.json').read_text())
        for mode,parent in [('infuser','EvilCraftInfuserMixin'),('spirit','EvilCraftSpiritOutputMixin')]:
            with self.subTest(mode=mode),tempfile.TemporaryDirectory(prefix='aia2-evilcraft-') as tmp:
                files=[]
                for name,text in original.items():
                    if name.endswith('/BlockEntity.java'):text=text.replace('extends ua.aia2.guard.mixin.EvilCraftInfuserMixin','extends ua.aia2.guard.mixin.'+parent)
                    p=Path(tmp)/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(text);files.append(str(p))
                files += [str(ROOT/'tests/fixtures/EvilCraftGuardHarness.java')]
                files += [str(ROOT/f'companion/src/main/java/ua/aia2/guard/{n}.java') for n in ['GuardPolicy','EvilCraftAccess']]
                files += [str(ROOT/f'companion/src/main/java/ua/aia2/guard/mixin/{n}.java') for n in ['EvilCraftInfuserMixin','EvilCraftSpiritOutputMixin','EvilCraftReanimatorMixin']]
                run=subprocess.run([str(jdk/'bin/javac'),'-encoding','UTF-8','-d',tmp,*files],capture_output=True,text=True)
                self.assertEqual(run.returncode,0,run.stdout+run.stderr)
                run=subprocess.run([str(jdk/'bin/java'),'-cp',tmp,'ua.aia2.guard.mixin.EvilCraftGuardHarness',mode],capture_output=True,text=True)
                self.assertEqual(run.returncode,0,run.stdout+run.stderr)
                self.assertIn('modeled assertions PASS',run.stdout);print(run.stdout.strip())
