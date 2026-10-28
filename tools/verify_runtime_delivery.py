#!/usr/bin/env python3
"""Verify a runtime archive and its extracted installer on an owned temporary instance.

This does not launch Minecraft, parse the synthetic world markers, or touch a Windows instance.
The report deliberately omits archive SHA to avoid embedding a self-referential archive hash.
"""
import argparse
import hashlib
import io
import json
import re
from pathlib import Path, PurePosixPath
import subprocess
import sys
import tarfile
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def sha(data):
    return hashlib.sha256(data).hexdigest()


def snapshot(root):
    return {p.relative_to(root).as_posix(): p.read_bytes() for p in root.rglob('*') if p.is_file()}


def safe_name(name):
    path = PurePosixPath(name)
    if path.is_absolute() or '..' in path.parts or '\\' in name:
        raise AssertionError('Unsafe archive path: ' + name)
    return path


def verify(archive, version, baseline):
    baseline = subprocess.run([
        'git', 'rev-parse', '--verify', '--end-of-options', baseline + '^{commit}'
    ], cwd=ROOT, check=True, capture_output=True, text=True).stdout.strip()
    with zipfile.ZipFile(archive) as package:
        assert package.testzip() is None, 'Archive CRC failed'
        manifest = json.loads(package.read('SHA256SUMS.json'))
        assert isinstance(manifest, dict), 'Invalid manifest'
        assert len(package.namelist()) == len(set(package.namelist())), 'Duplicate ZIP member'
        assert set(package.namelist()) == {*manifest, 'SHA256SUMS.json'}, 'Unmanifested ZIP member'
        for name, digest in manifest.items():
            safe_name(name)
            assert sha(package.read(name)) == digest, 'Manifest mismatch: ' + name
        runtime = {name: digest for name, digest in manifest.items()
                   if PurePosixPath(name).parts[0] in {'kubejs', 'config', 'mods'}}
        expected = {p.relative_to(ROOT).as_posix(): sha(p.read_bytes())
                    for folder in ('kubejs', 'config', 'mods')
                    for p in (ROOT / folder).rglob('*') if p.is_file()}
        assert runtime == expected, 'Packaged runtime differs from the current reviewed runtime'
        installer_hash = sha((ROOT / 'install_runtime.py').read_bytes())
        assert manifest['install_runtime.py'] == installer_hash, 'Packaged installer differs from reviewed source'

        with tempfile.TemporaryDirectory(prefix='aia2-runtime-delivery-') as temporary:
            work = Path(temporary)
            extracted, instance = work / 'package', work / 'instance'
            extracted.mkdir(); instance.mkdir()
            for name in package.namelist():
                target = extracted / safe_name(name)
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(package.read(name))

            # Recreate only this project's tracked old runtime, never any user world or personal data.
            old_archive = subprocess.run(
                ['git', 'archive', '--format=tar', baseline, 'kubejs', 'config', 'mods'],
                cwd=ROOT, check=True, capture_output=True).stdout
            with tarfile.open(fileobj=io.BytesIO(old_archive), mode='r:') as old:
                for member in old.getmembers():
                    safe_name(member.name)
                    if member.isdir():
                        (instance / member.name).mkdir(parents=True, exist_ok=True)
                    else:
                        assert member.isfile(), 'Unexpected non-file baseline entry'
                        target = instance / member.name
                        target.parent.mkdir(parents=True, exist_ok=True)
                        target.write_bytes(old.extractfile(member).read())
            old_jars = list((instance / 'mods').glob('aia2-machine-guard-*.jar'))
            assert len(old_jars) == 1, 'Baseline needs exactly one companion JAR'
            previous_version = old_jars[0].name.removeprefix('aia2-machine-guard-').removesuffix('.jar')
            assert previous_version != version, 'Choose a previous-version baseline for this upgrade test'
            old_jar, old_bytes = old_jars[0], old_jars[0].read_bytes()
            old_relative = old_jar.relative_to(instance)

            markers = {
                'saves/world/level.dat': b'synthetic-world-progress',
                'saves/world/ftbquests/team-progress.snbt': b'synthetic-team-progress',
                'saves/world/data/aia2_fire_worksites_v1.dat': b'synthetic-fire-ledger',
                'saves/world/data/projecte-knowledge.json': b'synthetic-knowledge',
                'saves/world/data/projecte-emc.json': b'synthetic-emc',
                # Receipt storage belongs to a block entity; this opaque marker represents its chunk.
                'saves/world/region/r.0.0.mca': b'synthetic-chunk-with-paid-ritual',
                'mods/foreign-mod.jar': b'foreign-mod',
                'kubejs/server_scripts/foreign.js': b'// foreign script\n',
            }
            for name, data in markers.items():
                target = instance / name
                target.parent.mkdir(parents=True, exist_ok=True); target.write_bytes(data)
            chapter_relative = 'config/ftbquests/quests/chapters/aia2_epoch_01.snbt'
            chapter = json.loads((instance / chapter_relative).read_text())
            foreign = {'id': 'FFFFFFF00A1A2001', 'title': 'Власна збережена ціль',
                       'tasks': [], 'custom_flag': True, 'description': ['Зберегти без змін.']}
            assert all(q['id'] != foreign['id'] for q in chapter['quests'])
            chapter['quests'].append(foreign)
            (instance / chapter_relative).write_text(json.dumps(chapter, ensure_ascii=False, indent=2) + '\n')
            before = snapshot(instance)
            before_directories = {p.relative_to(instance).as_posix() for p in instance.rglob('*') if p.is_dir()}
            command = [sys.executable, str(extracted / 'install_runtime.py'), str(instance)]
            dry = subprocess.run(command + ['--dry-run'], cwd=extracted, capture_output=True, text=True)
            assert dry.returncode == 0, dry.stdout + dry.stderr
            assert 'dry-run made no changes' in dry.stdout
            assert snapshot(instance) == before, 'Dry-run changed instance files'
            assert {p.relative_to(instance).as_posix() for p in instance.rglob('*') if p.is_dir()} == before_directories, 'Dry-run created directories'
            installed = subprocess.run(command, cwd=extracted, capture_output=True, text=True)
            assert installed.returncode == 0, installed.stdout + installed.stderr
            assert not old_jar.exists(), 'Old companion still active'
            new_jars = list((instance / 'mods').glob('aia2-machine-guard-*.jar'))
            assert len(new_jars) == 1 and new_jars[0].name == 'aia2-machine-guard-' + version + '.jar'
            assert sha(new_jars[0].read_bytes()) == runtime['mods/' + new_jars[0].name]
            journals = list((instance / 'aia2-backups').glob('*/journal.json'))
            assert len(journals) == 1
            journal = json.loads(journals[0].read_text())
            assert journal['state'] == 'completed'
            assert (journals[0].parent / 'original' / old_relative).read_bytes() == old_bytes
            for name, data in markers.items():
                assert (instance / name).read_bytes() == data, 'Lost synthetic marker: ' + name
            changed_chapter = json.loads((instance / chapter_relative).read_text())
            assert next(q for q in changed_chapter['quests'] if q['id'] == foreign['id']) == foreign
            # The actual second CLI call is also non-mutating after a successful upgrade.
            after = snapshot(instance)
            repeat = subprocess.run(command, cwd=extracted, capture_output=True, text=True)
            assert repeat.returncode == 0, repeat.stdout + repeat.stderr
            assert 'No changes needed' in repeat.stdout
            assert snapshot(instance) == after, 'Repeat install was not idempotent'

    return {
        'version': version, 'status': 'passed',
        'archive_manifest_entries': len(manifest), 'runtime_hashes_verified': len(runtime),
        'packaged_installer_hash': installer_hash, 'dry_run_writes': 0,
        'upgrade_from': previous_version, 'baseline_commit': baseline,
        'old_jar_backed_up': True, 'synthetic_world_progress_preserved': True,
        'foreign_quest_in_owned_chapter_preserved': True,
        'synthetic_fire_ledger_preserved': True, 'synthetic_knowledge_emc_preserved': True,
        'synthetic_paid_ritual_chunk_marker_preserved': True,
        'foreign_mod_and_script_preserved': True, 'repeat_install_idempotent': True,
        'fullpack_run': False, 'windows_instance_modified': False,
        'world_markers_are_opaque_synthetic_bytes_not_a_minecraft_persistence_test': True,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--version', required=True, help='Expected target package version, for example 0.4.13-alpha')
    parser.add_argument('--baseline', required=True, help='Previous-version Git commit used only for an owned test instance')
    parser.add_argument('--archive', type=Path, help='Defaults to /workspace/shared/downloads/AIA2-runtime-VERSION.zip')
    parser.add_argument('--report', type=Path, help='Write results here unless --check-only; no archive SHA is embedded')
    parser.add_argument('--check-only', action='store_true', help='Run all checks without changing the report')
    args = parser.parse_args()
    if not args.check_only and args.report is None:
        parser.error('--report is required unless --check-only is selected')
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9.+_-]*', args.version):
        parser.error('Invalid target version')
    archive = args.archive or Path('/workspace/shared/downloads') / ('AIA2-runtime-' + args.version + '.zip')
    report = verify(archive, args.version, args.baseline)
    if not args.check_only:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
