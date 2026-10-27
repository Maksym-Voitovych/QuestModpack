"""Exact passive capability calls must use their personal player or original receiver."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]

class ProjectEStorageTests(unittest.TestCase):
    def test_exact_server_capability_dispatch_and_erased_signatures(self):
        manifest=json.loads((ROOT/'content/research/evidence/projecte_storage_passive_v5/manifest.json').read_text())
        self.assertEqual(manifest['pin'],'f432b0c66837759fb0731c9144dc53176b949c5d')
        sources={}
        for row in manifest['sources']:
            raw=(ROOT/row['path']).read_bytes();self.assertEqual(hashlib.sha256(raw).hexdigest(),row['sha256'])
            sources[Path(row['repository_path']).name]=raw.decode()
        self.assertIn('projecte_version=1.1.0',sources['gradle.properties'])
        self.assertIn('minecraft_version=1.21.1',sources['gradle.properties'])
        gates=json.loads((ROOT/'kubejs/config/aia2_runtime.json').read_text())['itemGates']
        bag_floors={key:value for key,value in gates.items() if key.startswith('projecte:') and key.endswith('_alchemical_bag')}
        self.assertEqual(len(bag_floors),16)
        self.assertEqual(set(bag_floors.values()),{45},'Installed bag feature floor changed; update its explicit capability gate')
        self.assertIn('alchBagItem.updateInAlchBag(inv, player, current)',sources['TickEvents.java'])
        chest=sources['AlchBlockEntityChest.java'].split('public static void tickServer',1)[1]
        self.assertIn('alchChestItem.updateInAlchChest(level, pos, stack)',chest)
        pedestal=sources['DMPedestalBlockEntity.java'].split('public static void tickServer',1)[1]
        self.assertIn('pedestalItem.updateInPedestal(stack, level, pos, pedestal)',pedestal)
        self.assertIn('PEDESTAL extends BlockEntity & IDMPedestal',sources['IPedestalItem.java'])
        self.assertIn('boolean updateInAlchBag(@NotNull IItemHandler inv, @NotNull Player player, @NotNull ItemStack stack)',sources['IAlchBagItem.java'])
        for name in ['ProjectEBagPassiveMixin','ProjectEChestPassiveMixin','ProjectEPedestalPassiveMixin']:
            source=(ROOT/f'companion/src/main/java/ua/aia2/guard/mixin/{name}.java').read_text()
            self.assertIn('require = 1',source)
        for name in ['ProjectEChestPassiveMixin','ProjectEPedestalPassiveMixin']:
            source=(ROOT/f'companion/src/main/java/ua/aia2/guard/mixin/{name}.java').read_text()
            self.assertIn('@Coerce Object originalTile',source)

    def test_actual_helper_handlers_real_policy_receiver_player_and_cleanup(self):
        jdk=Path(os.environ.get('JAVA_HOME','/workspace/aia2-toolchains/jdk-21.0.9'))
        if not (jdk/'bin/javac').exists():self.skipTest('External JDK21 unavailable')
        fixtures=json.loads((ROOT/'tests/fixtures/projecte-storage-host.json').read_text())
        with tempfile.TemporaryDirectory(prefix='aia2-projecte-storage-') as tmp:
            files=[]
            for name,text in fixtures.items():
                p=Path(tmp)/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(text);files.append(str(p))
            files += [str(ROOT/'tests/fixtures/ProjectEStorageHarness.java')]
            files += [str(ROOT/f'companion/src/main/java/ua/aia2/guard/{name}.java') for name in ['GuardPolicy','ProjectEStorageAccess']]
            files += [str(ROOT/f'companion/src/main/java/ua/aia2/guard/mixin/{name}.java') for name in ['ProjectEBagPassiveMixin','ProjectEChestPassiveMixin','ProjectEPedestalPassiveMixin']]
            compile=subprocess.run([str(jdk/'bin/javac'),'-encoding','UTF-8','-d',tmp,*files],capture_output=True,text=True)
            self.assertEqual(compile.returncode,0,compile.stdout+compile.stderr)
            run=subprocess.run([str(jdk/'bin/java'),'-cp',tmp,'ua.aia2.guard.mixin.ProjectEStorageHarness'],capture_output=True,text=True)
            self.assertEqual(run.returncode,0,run.stdout+run.stderr)
            self.assertIn('actual-helper/handler/real-policy assertions',run.stdout);print(run.stdout.strip())
