"""Current ProjectE menu/output authorization and exact native stale-cache boundaries."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]

class ProjectEOutputTests(unittest.TestCase):
    def test_exact_native_output_fuel_cache_and_preserved_knowledge_boundaries(self):
        manifest=json.loads((ROOT/'content/research/evidence/projecte_guard_next_v5/manifest.json').read_text())
        self.assertEqual(manifest['pin'],'f432b0c66837759fb0731c9144dc53176b949c5d')
        source={}
        for row in manifest['files']:
            raw=(ROOT/row['path']).read_bytes()
            self.assertEqual(hashlib.sha256(raw).hexdigest(),row['sha256'])
            source[Path(row['path']).name]=raw.decode()
        self.assertIn('projecte_version=1.1.0',source['gradle.properties'])
        mapping=source['EMCMappingHandler.java'];fire=mapping[mapping.index('private static void fireEmcRemapEvent()'):mapping.index('public static int getLoadIndex()')]
        self.assertLess(fire.index('FuelMapper.loadMap()'),fire.index('new EMCRemapEvent()'))
        remove=source['SlotOutput.java'][source['SlotOutput.java'].index('public ItemStack remove(int amount)'):source['SlotOutput.java'].index('public void initialize')]
        self.assertNotIn('emcValue <= 0',remove)
        self.assertIn('inv.removeEmc(bigEmcValue)',remove)
        self.assertIn('this.hand == null ||',source['PEHandContainer.java'])
        self.assertIn('iterator.remove()',source['KnowledgeImpl.java'])
        script=(ROOT/'kubejs/server_scripts/aia2/35_projecte.js').read_text()
        self.assertNotIn('pruneStaleKnowledge(',script)
        registered=json.loads((ROOT/'companion/src/main/resources/aia2_machine_guard.mixins.json').read_text())['mixins']
        for name in ['ProjectEHandMenuMixin','ProjectETransmutationMixin','ProjectEOutputSlotMixin']:self.assertIn(name,registered)

    def test_actual_helpers_and_handlers_stage_remap_variants_and_current_emc(self):
        jdk=Path(os.environ.get('JAVA_HOME','/workspace/aia2-toolchains/jdk-21.0.9'))
        if not (jdk/'bin/javac').is_file():self.skipTest('External JDK21 unavailable')
        cache=Path(os.environ.get('GRADLE_USER_HOME','/workspace/aia2-toolchains/gradle-home'))/'caches/modules-2/files-2.1/com.google.code.gson/gson'
        jars=list(cache.glob('**/gson-2.10.1.jar'))
        if not jars:self.skipTest('External real Gson unavailable')
        base=json.loads((ROOT/'tests/fixtures/projecte-output-host.json').read_text())
        for mode in ['hand','quick']:
            fixture=dict(base)
            if mode=='quick':
                name='moze_intel/projecte/gameObjs/container/TransmutationContainer.java'
                fixture[name]=fixture[name].replace('extends ua.aia2.guard.mixin.HandMixinHost','extends ua.aia2.guard.mixin.QuickMixinHost')
            with tempfile.TemporaryDirectory(prefix='aia2-projecte-output-') as temp:
                files=[]
                for name,text in fixture.items():
                    path=Path(temp)/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_text(text);files.append(str(path))
                files += [str(ROOT/'tests/fixtures/ProjectEOutputHarness.java')]
                files += [str(ROOT/f'companion/src/main/java/ua/aia2/guard/{name}.java') for name in ['GuardPolicy','ProjectEAccess']]
                files += [str(ROOT/f'companion/src/main/java/ua/aia2/guard/mixin/{name}.java') for name in ['ProjectEHandMenuMixin','ProjectETransmutationMixin','ProjectEOutputSlotMixin']]
                cp=os.pathsep.join([temp,str(jars[0])])
                compiled=subprocess.run([str(jdk/'bin/javac'),'-encoding','UTF-8','-cp',cp,'-d',temp,*files],capture_output=True,text=True)
                self.assertEqual(compiled.returncode,0,compiled.stdout+compiled.stderr)
                command=[str(jdk/'bin/java'),'-cp',cp,'ua.aia2.guard.mixin.ProjectEOutputHarness']+(['quick'] if mode=='quick' else [])
                result=subprocess.run(command,capture_output=True,text=True)
                self.assertEqual(result.returncode,0,result.stdout+result.stderr)
                self.assertIn('actual-helper/handler/real-policy assertions',result.stdout)
                print(result.stdout.strip())
