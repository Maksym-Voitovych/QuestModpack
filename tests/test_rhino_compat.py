"""Real-engine regression; see tests/rhino/README.md for the external toolchain."""
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
TOOLCHAINS = Path('/workspace/aia2-toolchains')


class RhinoCompatibilityTest(unittest.TestCase):
    def test_build85_startup_server_and_reload(self):
        jar = Path(os.environ.get('AIA2_RHINO_JAR', str(
            TOOLCHAINS / 'rhino-2101.2.7-build.85-core-from-source.jar')))
        java_home = Path(os.environ.get('JAVA_HOME', str(TOOLCHAINS / 'jdk-21.0.9')))
        java = str(java_home / 'bin/java') if (java_home / 'bin/java').is_file() else shutil.which('java')
        javac = str(java_home / 'bin/javac') if (java_home / 'bin/javac').is_file() else shutil.which('javac')
        if not jar.is_file() or not java or not javac:
            self.skipTest('External Rhino build.85/JDK 21 not installed; see tests/rhino/README.md')
        dependencies = os.environ.get('AIA2_RHINO_CLASSPATH', '')
        if dependencies:
            classpath = os.pathsep.join((str(jar), dependencies))
        else:
            jars = []
            for pattern in (
                'com.google.guava/guava/32.1.2-jre/*/*.jar',
                'com.google.code.gson/gson/2.10.1/*/*.jar',
            ):
                jars.extend((TOOLCHAINS / 'gradle-home/caches/modules-2/files-2.1').glob(pattern))
            classpath = os.pathsep.join([str(jar), *map(str, jars)])
        with tempfile.TemporaryDirectory(prefix='aia2-rhino-') as output:
            compile_result = subprocess.run([
                javac, '-encoding', 'UTF-8', '-cp', classpath, '-d', output,
                str(ROOT / 'tests/rhino/RhinoCompatibilityHarness.java'),
            ], capture_output=True, text=True)
            self.assertEqual(compile_result.returncode, 0, compile_result.stdout + compile_result.stderr)
            result = subprocess.run([
                java, '-cp', os.pathsep.join((output, classpath)),
                'RhinoCompatibilityHarness', str(ROOT),
            ], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn('reload assertions passed', result.stdout)
            self.assertIn('2101.2.7-build.85', result.stdout)
            print(result.stdout.strip())


if __name__ == '__main__':
    unittest.main()
