"""Exact source boundaries and executable optional handlers in a modeled host."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]


class EnergyNativeGuardTests(unittest.TestCase):
    def test_exact_source_boundaries_and_release_version(self):
        folder=ROOT/'content/research/evidence/energy_guard_next_v5'
        texts={}
        for module in ['enderio','powah']:
            manifest=json.loads((folder/module/'manifest.json').read_text())
            for source in manifest['files']+manifest.get('shared_files',[]):
                raw=(ROOT/source['evidence_path']).read_bytes()
                self.assertEqual(hashlib.sha256(raw).hexdigest(),source['sha256'])
                texts[Path(source['repository_path']).name]=raw.decode()
        task=texts['CraftingMachineTask.java']
        tick=task[task.index('public void tick()'):task.index('public float getProgress()')]
        self.assertLess(tick.index('outputs ='),tick.index('makeProgress('))
        self.assertLess(tick.index('placeOutputs(outputs, false)'),tick.index('consumeInputs(recipe.value())'))
        self.assertIn('byKey(id)',task)
        self.assertIn('POWAH_VERSION',texts['build.gradle'])
        self.assertIn('github.event.release.tag_name',texts['release.yml'])
        orb=texts['EnergizingOrbTile.java']
        self.assertLess(orb.index('this.inv.clear()'),orb.index('this.inv.setStackInSlot(0, stack.copy())'))
        self.assertIn('buffer.setCapacity(0)',orb)
        registered=json.loads((ROOT/'companion/src/main/resources/aia2_machine_guard.mixins.json').read_text())['mixins']
        for name in ['EnderCraftingTaskMixin','EnderCrafterMixin','EnderTankMixin','PowahEnergizingOrbMixin']:
            self.assertIn(name,registered)

    def test_actual_handlers_receiving_owner_saved_outputs_reload_and_context(self):
        jdk=Path(os.environ.get('JAVA_HOME','/workspace/aia2-toolchains/jdk-21.0.9'))
        if not (jdk/'bin/javac').is_file(): self.skipTest('External JDK21 unavailable')
        cache=Path(os.environ.get('GRADLE_USER_HOME','/workspace/aia2-toolchains/gradle-home'))/'caches/modules-2/files-2.1'
        jars=[]
        for group,pattern in [('com.google.code.gson/gson','gson-2.10.1.jar'),('com.mojang/datafixerupper','datafixerupper-8.0.16.jar'),('com.google.guava/guava','guava-*.jar'),('org.slf4j/slf4j-api','slf4j-api-*.jar'),('it.unimi.dsi/fastutil','fastutil-*.jar')]:
            matches=sorted((cache/group).glob('**/'+pattern))
            if not matches:self.skipTest('External real codec dependency unavailable: '+group)
            jars.append(str(matches[-1]))
        fixtures=json.loads((ROOT/'tests/fixtures/energy-native-host.json').read_text())
        with tempfile.TemporaryDirectory(prefix='aia2-energy-native-') as temp:
            files=[]
            for name,text in fixtures.items():
                p=Path(temp)/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(text);files.append(str(p))
            files += [str(ROOT/'tests/fixtures/EnergyGuardHarness.java')]
            files += [str(ROOT/f'companion/src/main/java/ua/aia2/guard/{name}.java') for name in ['GuardPolicy','EnderTaskAccess','PowahOrbAccess']]
            files += [str(ROOT/f'companion/src/main/java/ua/aia2/guard/mixin/{name}.java') for name in ['EnderCraftingTaskMixin','EnderCrafterMixin','EnderTankMixin','PowahEnergizingOrbMixin']]
            cp=os.pathsep.join([temp,*jars])
            result=subprocess.run([str(jdk/'bin/javac'),'-encoding','UTF-8','-cp',cp,'-d',temp,*files],capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stdout+result.stderr)
            result=subprocess.run([str(jdk/'bin/java'),'-cp',cp,'ua.aia2.guard.mixin.EnergyGuardHarness'],capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stdout+result.stderr)
            self.assertIn('actual-helper/handler/real-policy assertions',result.stdout)
            print(result.stdout.strip())
