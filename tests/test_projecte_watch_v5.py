"""ProjectE bonus ticks must authorize and scope the actual target, never its caller."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
EVIDENCE=ROOT/'content/research/evidence/projecte_watch_guard_v5'


class ProjectEWatchTests(unittest.TestCase):
    def test_exact_projecte_direct_ticker_bypass_and_redirect_contract(self):
        manifest=json.loads((EVIDENCE/'manifest.json').read_text())
        self.assertEqual(manifest['pin'],'f432b0c66837759fb0731c9144dc53176b949c5d')
        text={}
        for row in manifest['sources']:
            raw=(ROOT/row['path']).read_bytes()
            self.assertEqual(hashlib.sha256(raw).hexdigest(),row['sha256'])
            text[Path(row['repository_path']).name]=raw.decode()
        self.assertIn('projecte_version=1.1.0',text['gradle.properties'])
        self.assertIn('minecraft_version=1.21.1',text['gradle.properties'])
        source=text['TimeWatch.java']
        method=source[source.index('private <T extends BlockEntity> void provideBonusTicks'):source.index('private void speedUpRandomTicks')]
        self.assertIn('BoundTickingBlockEntity<T> tickingBE',method)
        self.assertIn('for (int i = 0; i < bonusTicks; i++)',method)
        self.assertIn('tickingBE.ticker.tick(level, pos, state, be)',method)
        self.assertIn('tickingWrapper.tick()',source)
        guard=(ROOT/'companion/src/main/java/ua/aia2/guard/mixin/ProjectETimeWatchMixin.java').read_text()
        self.assertIn('provideBonusTicks(Lnet/minecraft/world/level/Level;',guard)
        self.assertIn('Lnet/minecraft/world/level/chunk/LevelChunk$BoundTickingBlockEntity;I)V',guard)
        self.assertIn('finally { Aia2MachineGuard.exitTick(parent); }',guard)

    def test_actual_redirect_target_policy_nested_owner_and_exception_cleanup(self):
        jdk=Path(os.environ.get('JAVA_HOME','/workspace/aia2-toolchains/jdk-21.0.9'))
        if not (jdk/'bin/javac').is_file():self.skipTest('External JDK21 unavailable')
        fixture=json.loads((ROOT/'tests/fixtures/projecte-watch-host.json').read_text())
        with tempfile.TemporaryDirectory(prefix='aia2-projecte-watch-') as temp:
            files=[]
            for name,text in fixture.items():
                path=Path(temp)/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_text(text);files.append(str(path))
            files += [str(ROOT/'tests/fixtures/ProjectEWatchHarness.java'),
                      str(ROOT/'companion/src/main/java/ua/aia2/guard/GuardPolicy.java'),
                      str(ROOT/'companion/src/main/java/ua/aia2/guard/mixin/ProjectETimeWatchMixin.java')]
            compile=subprocess.run([str(jdk/'bin/javac'),'-encoding','UTF-8','-d',temp,*files],capture_output=True,text=True)
            self.assertEqual(compile.returncode,0,compile.stdout+compile.stderr)
            run=subprocess.run([str(jdk/'bin/java'),'-cp',temp,'ua.aia2.guard.mixin.ProjectEWatchHarness'],capture_output=True,text=True)
            self.assertEqual(run.returncode,0,run.stdout+run.stderr)
            self.assertIn('actual-handler/real-policy assertions',run.stdout)
            print(run.stdout.strip())
