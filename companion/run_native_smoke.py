#!/usr/bin/env python3
"""Run actual native correctness tests and verify receipts after a second server boot."""
import json
import os
from pathlib import Path
import signal
import subprocess

ROOT = Path(__file__).resolve().parent
RUN = ROOT / 'run'


def main():
    RUN.mkdir(exist_ok=True)
    marker = RUN / '.aia2-native-smoke-allow'
    marker.write_text('Only the owned companion development world may be used.\n')
    evidence = RUN / 'aia2-native-smoke.json'
    env = os.environ.copy()
    env['JAVA_HOME'] = env.get('JAVA_HOME', '/workspace/aia2-toolchains/jdk-21.0.9')
    env['GRADLE_USER_HOME'] = env.get('GRADLE_USER_HOME', '/workspace/aia2-toolchains/gradle-home')
    command = [str(ROOT / ('gradlew.bat' if os.name == 'nt' else 'gradlew')), '--offline', 'runServer', '-x', 'downloadAssets', '--no-daemon', '--console=plain']

    def run_once(options, logfile):
        evidence.unlink(missing_ok=True)
        env['JAVA_TOOL_OPTIONS'] = options
        log = RUN / logfile
        with log.open('w') as output:
            process = subprocess.Popen(command, cwd=ROOT, env=env, stdout=output, stderr=subprocess.STDOUT,
                                       start_new_session=os.name != 'nt')
            try:
                code = process.wait(timeout=180)
            except subprocess.TimeoutExpired:
                if os.name != 'nt': os.killpg(process.pid, signal.SIGTERM)
                else: process.terminate()
                process.wait(timeout=20)
                raise SystemExit('Native smoke server timed out; see ' + str(log))
        if not evidence.is_file():
            raise SystemExit('Native smoke evidence not created; exit=' + str(code) + '; see ' + str(log))
        report = json.loads(evidence.read_text())
        report['runner_exit_code'] = code
        report['console_log'] = 'run/' + logfile + ' (ignored, not shipped)'
        return report

    try:
        first = run_once('-Daia2.guard.nativeSmoke=true', 'aia2-native-smoke-console.log')
        if first['status'] == 'passed' and first['runner_exit_code'] == 0:
            team = first['receipt_team']
            assert team.startswith('native-test-a-') and all(c.isalnum() or c == '-' for c in team)
            restart = run_once('-Daia2.guard.nativeSmoke=true -Daia2.guard.nativeSmokeReceiptVerify=true '
                               '-Daia2.guard.nativeSmokeReceiptTeam=' + team, 'aia2-native-smoke-restart-console.log')
            first['restart_verification'] = restart
            first['assertions_total'] = first['assertions'] + restart['assertions']
            if restart['status'] != 'passed' or restart['runner_exit_code'] != 0: first['status'] = 'failed'
        first['runner_command'] = './gradlew --offline runServer -x downloadAssets --no-daemon --console=plain; second JVM verifies SavedData persistence'
        (ROOT / 'native-smoke-report.json').write_text(json.dumps(first, ensure_ascii=False, indent=2) + '\n')
        print(json.dumps({'status': first['status'], 'assertions': first.get('assertions_total', first['assertions']),
                          'actual_server_ticks': first['actual_server_ticks'], 'server_boots': 2 if 'restart_verification' in first else 1,
                          'report': 'companion/native-smoke-report.json'}, indent=2))
        if first['status'] != 'passed' or first['runner_exit_code'] != 0:
            raise SystemExit('Native smoke checks failed; see companion/native-smoke-report.json and ignored console logs')
    finally:
        marker.unlink(missing_ok=True)


if __name__ == '__main__': main()
