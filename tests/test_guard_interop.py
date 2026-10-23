"""Regression for the exact Java/Rhino boundaries behind the reported v0.3 errors."""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
TOOLS = Path('/workspace/aia2-toolchains')

class GuardInteropTest(unittest.TestCase):
    def test_real_rhino_uuid_remapping_and_fastutil_overloads(self):
        jar = Path(os.environ.get('AIA2_RHINO_JAR', str(TOOLS/'rhino-2101.2.7-build.85-core-from-source.jar')))
        jdk = Path(os.environ.get('JAVA_HOME', str(TOOLS/'jdk-21.0.9')))
        jars = [jar]
        for pattern in ['com.google.guava/guava/32.1.2-jre/*/*.jar', 'com.google.code.gson/gson/2.10.1/*/*.jar', 'it.unimi.dsi/fastutil/8.5.12/*/*.jar']:
            found = list((TOOLS/'gradle-home/caches/modules-2/files-2.1').glob(pattern))
            if not found: self.skipTest('External exact Rhino/fastutil toolchain missing')
            jars.extend(found)
        if not jar.exists() or not (jdk/'bin/javac').exists(): self.skipTest('External exact Rhino85/JDK21 missing')
        cp = os.pathsep.join(map(str,jars))
        with tempfile.TemporaryDirectory(prefix='aia2-guard-interop-') as dest:
            compile_result = subprocess.run([str(jdk/'bin/javac'), '-encoding','UTF-8','-cp',cp,'-d',dest,
                str(ROOT/'companion/src/main/java/ua/aia2/guard/RhinoLongMapBridge.java'),
                str(ROOT/'tests/rhino/GuardInteropHarness.java')], capture_output=True,text=True)
            self.assertEqual(compile_result.returncode,0,compile_result.stdout+compile_result.stderr)
            run = subprocess.run([str(jdk/'bin/java'),'-cp',dest+os.pathsep+cp,'GuardInteropHarness',str(ROOT)],capture_output=True,text=True)
            self.assertEqual(run.returncode,0,run.stdout+run.stderr)
            self.assertIn('real fastutil primitive bridge passed',run.stdout)
            print(run.stdout.strip())
