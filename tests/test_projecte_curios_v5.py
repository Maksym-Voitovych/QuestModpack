"""Actual Curio helper/handlers, with modeled Minecraft/Curios host and real GuardPolicy."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]

class ProjectECuriosTests(unittest.TestCase):
    def test_exact_source_capability_and_native_attribute_contract(self):
        manifest=json.loads((ROOT/'content/research/evidence/projecte_curios_guard_v5/manifest.json').read_text())
        self.assertEqual(manifest['pin'],'f432b0c66837759fb0731c9144dc53176b949c5d')
        sources={}
        for row in manifest['sources']:
            raw=(ROOT/row['path']).read_bytes();self.assertEqual(hashlib.sha256(raw).hexdigest(),row['sha256'])
            sources[Path(row['repository_path']).name]=raw.decode()
        self.assertIn('projecte_version=1.1.0',sources['gradle.properties'])
        self.assertIn('minecraft_version=1.21.1',sources['gradle.properties'])
        self.assertIn('EntityCapability<IItemHandler, Void> CURIO_ITEM_HANDLER',sources['IntegrationHelper.java'])
        self.assertIn('public record CurioItemCapability(ItemStack stack)',sources['CurioItemCapability.java'])
        self.assertIn('if (!slotContext.cosmetic() && stack.getItem() instanceof IExposesCurioAttributes',sources['CurioItemCapability.java'])
        self.assertIn('exposesCurioAttributes.addAttributes(attributes)',sources['CurioItemCapability.java'])
        self.assertIn('PECore.rl("arcana_flight"), 1, Operation.ADD_VALUE',sources['Arcana.java'])
        self.assertIn('attributes.put(NeoForgeMod.CREATIVE_FLIGHT, FLIGHT)',sources['Arcana.java'])
        self.assertIn('player.getCapability(IntegrationHelper.CURIO_ITEM_HANDLER)',sources['PlayerHelper.java'])
        for name in ['ProjectECurioAttributesMixin','ProjectECurioReconcileMixin']:
            self.assertIn('require = 1',(ROOT/f'companion/src/main/java/ua/aia2/guard/mixin/{name}.java').read_text())

    def test_actual_helpers_handlers_downgrade_reload_restore_and_shared_ids(self):
        jdk=Path(os.environ.get('JAVA_HOME','/workspace/aia2-toolchains/jdk-21.0.9'))
        guava=list(Path('/workspace/aia2-toolchains/gradle-home/caches/modules-2/files-2.1/com.google.guava/guava').glob('**/guava-*.jar'))
        if not (jdk/'bin/javac').exists() or not guava:self.skipTest('External JDK21/Guava unavailable')
        fixture=json.loads((ROOT/'tests/fixtures/projecte-curios-host.json').read_text())
        with tempfile.TemporaryDirectory(prefix='aia2-projecte-curios-') as tmp:
            files=[]
            for name,text in fixture.items():
                path=Path(tmp)/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_text(text);files.append(str(path))
            files += [str(ROOT/'tests/fixtures/ProjectECuriosHarness.java')]
            files += [str(ROOT/f'companion/src/main/java/ua/aia2/guard/{name}.java') for name in ['GuardPolicy','ProjectECurioAttributes']]
            files += [str(ROOT/f'companion/src/main/java/ua/aia2/guard/mixin/{name}.java') for name in ['ProjectECurioAttributesMixin','ProjectECurioReconcileMixin']]
            cp=str(guava[0])
            compile=subprocess.run([str(jdk/'bin/javac'),'-encoding','UTF-8','-cp',cp,'-d',tmp,*files],capture_output=True,text=True)
            self.assertEqual(compile.returncode,0,compile.stdout+compile.stderr)
            run=subprocess.run([str(jdk/'bin/java'),'-cp',tmp+os.pathsep+cp,'ua.aia2.guard.mixin.ProjectECuriosHarness'],capture_output=True,text=True)
            self.assertEqual(run.returncode,0,run.stdout+run.stderr)
            self.assertIn('actual-helper/handler/real-policy Curios model assertions PASS',run.stdout);print(run.stdout.strip())
