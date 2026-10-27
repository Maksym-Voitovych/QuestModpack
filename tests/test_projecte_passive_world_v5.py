"""Actual ProjectE passive/packet/world entry guards, with explicit host-model limits."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]

class ProjectEPassiveWorldTests(unittest.TestCase):
    def test_pinned_native_entrypoints_and_held_tool_contract(self):
        manifest=json.loads((ROOT/'content/research/evidence/projecte_world_audit_v5/manifest.json').read_text())
        self.assertEqual(manifest['pin'],'f432b0c66837759fb0731c9144dc53176b949c5d')
        sources={}
        for row in manifest['files']:
            raw=(ROOT/row['path']).read_bytes();self.assertEqual(hashlib.sha256(raw).hexdigest(),row['sha256'])
            sources[Path(row['repository_path']).name]=raw.decode()
        self.assertIn('projecte_version=1.1.0',sources['gradle.properties'])
        self.assertIn('minecraft_version=1.21.1',sources['gradle.properties'])
        self.assertIn('tryPerformCapability',sources['KeyPressPKT.java'])
        self.assertIn('tablet.openContainer(player)',sources['KeyPressPKT.java'])
        self.assertIn('fireVolley',sources['PacketHandler.java'])
        self.assertIn('onItemUseFirst',sources['PhilosophersStone.java'])
        for name in ['PEPickaxe.java','PEMorningStar.java']:
            self.assertNotIn('onBlockStartBreak',sources[name])
            self.assertIn('boolean mineBlock(',sources[name])
            self.assertIn('ToolHelper.digBasedOnMode',sources[name])
        self.assertIn('getStack().inventoryTick',sources['CurioItemCapability.java'])
        self.assertIn('getAttributeModifiers',sources['CurioItemCapability.java'])
        item=(ROOT/'companion/src/main/java/ua/aia2/guard/mixin/ProjectEItemStackUseMixin.java').read_text()
        self.assertIn('inventoryTick(Lnet/minecraft/world/level/Level;',item)
        self.assertIn('onItemUseFirst(Lnet/minecraft/world/item/context/UseOnContext;',item)
        self.assertIn('useOn(Lnet/minecraft/world/item/context/UseOnContext;',item)
        tablet=(ROOT/'companion/src/main/java/ua/aia2/guard/mixin/ProjectETabletSourceMixin.java').read_text()
        self.assertIn('openContainer(Lnet/minecraft/world/entity/player/Player;)V',tablet)
        self.assertIn('openContainer(Lnet/minecraft/world/entity/player/Player;Lnet/minecraft/world/InteractionHand;I)V',tablet)
        self.assertIn('ProjectEPassiveAccess.openTablet',tablet)
        script=(ROOT/'kubejs/server_scripts/aia2/30_access.js').read_text()
        broken=script[script.index('BlockEvents.broken'):script.index('BlockEvents.broken')+500]
        self.assertIn('Math.max',broken)
        self.assertIn('aia2ItemStage',broken)
        self.assertIn('getMainHandItem()',broken)

    def test_actual_helpers_handlers_guardpolicy_packets_world_and_tablet_origins(self):
        jdk=Path(os.environ.get('JAVA_HOME','/workspace/aia2-toolchains/jdk-21.0.9'))
        if not(jdk/'bin/javac').is_file():self.skipTest('External JDK21 unavailable')
        cache=Path(os.environ.get('GRADLE_USER_HOME','/workspace/aia2-toolchains/gradle-home'))/'caches/modules-2/files-2.1/com.google.code.gson/gson'
        jars=list(cache.glob('**/gson-2.10.1.jar'))
        if not jars:self.skipTest('External real Gson unavailable')
        fixture=json.loads((ROOT/'tests/fixtures/projecte-world-host.json').read_text())
        with tempfile.TemporaryDirectory(prefix='aia2-projecte-world-')as tmp:
            files=[]
            for name,source in fixture.items():
                path=Path(tmp)/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_text(source);files.append(str(path))
            files += [str(ROOT/'tests/fixtures/ProjectEWorldHarness.java')]
            files += [str(ROOT/f'companion/src/main/java/ua/aia2/guard/{name}.java')for name in ['GuardPolicy','ProjectEAccess','ProjectEPassiveAccess']]
            files += [str(ROOT/f'companion/src/main/java/ua/aia2/guard/mixin/{name}.java')for name in ['ProjectEItemStackUseMixin','ProjectEHotbarPredicateMixin','ProjectEKeyCapabilityMixin','ProjectEArchangelMixin','ProjectEGemModeMixin','ProjectETabletSourceMixin']]
            cp=os.pathsep.join([tmp,str(jars[0])])
            compiled=subprocess.run([str(jdk/'bin/javac'),'-encoding','UTF-8','-cp',cp,'-d',tmp,*files],capture_output=True,text=True)
            self.assertEqual(compiled.returncode,0,compiled.stdout+compiled.stderr)
            result=subprocess.run([str(jdk/'bin/java'),'-cp',cp,'ua.aia2.guard.mixin.ProjectEWorldHarness'],capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stdout+result.stderr)
            self.assertIn('actual-helper/handler/real-policy assertions',result.stdout);print(result.stdout.strip())
