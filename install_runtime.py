#!/usr/bin/env python3
"""Install this checkout's kubejs/, config/ and AIA2 companion into an instance, with backups."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import sys
import tempfile


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('instance', type=Path, help='Minecraft instance root containing mods/')
    parser.add_argument('--dry-run', action='store_true', help='List operations without writing')
    args = parser.parse_args()
    source = Path(__file__).resolve().parent
    instance = args.instance.expanduser().resolve()
    if not all((source / folder).is_dir() for folder in ['kubejs', 'config', 'mods']):
        parser.error('kubejs/, config/ and mods/ must be beside this installer')
    if not (instance / 'mods').is_dir(): parser.error('The chosen instance must contain a mods/ directory')
    # Never downloads mods. Only the bundled AIA2 companion is installed;
    # an existing file with the same name is backed up before replacement.
    files = sorted([p for folder in ['kubejs', 'config'] for p in (source / folder).rglob('*') if p.is_file()]
                   + list((source / 'mods').glob('aia2-machine-guard-*.jar')))
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    backup = instance / 'aia2-backups' / stamp
    journal = []
    for item in files:
        relative = item.relative_to(source)
        target = instance / relative
        if target.is_symlink() or any(p.is_symlink() for p in target.parents if p != instance.parent):
            parser.error('Refusing to write through a symlink: ' + str(target))
        if relative.as_posix() == 'config/ftbquests/quests/data.snbt' and target.exists():
            print('KEEP existing FTB Quests settings:', relative)
            continue
        data = item.read_bytes()
        if target.exists() and target.read_bytes() == data:
            continue
        if relative.as_posix() == 'kubejs/config/aia2_runtime.json' and target.exists():
            try:
                existing_runtime = json.loads(target.read_text(encoding='utf-8'))
                new_runtime = json.loads(data)
                existing_mode = existing_runtime.get('machineGuard', {}).get('mode')
                # Updating the scripts must not silently downgrade an explicitly
                # required native guard to this package's optional source preview.
                if existing_mode == 'required':
                    new_runtime['machineGuard']['mode'] = 'required'
                    data = (json.dumps(new_runtime, ensure_ascii=False, indent=2)+'\n').encode('utf-8')
            except (ValueError, TypeError, KeyError, AttributeError) as exc:
                parser.error('Existing runtime configuration could not be read; leaving it untouched: ' + str(exc))
        if relative.as_posix() == 'config/ProjectE/custom_emc.json' and target.exists():
            try:
                existing = json.loads(target.read_text(encoding='utf-8'))
                new = json.loads(data)
                by_id = {x['id']: x for x in existing.get('entries', []) if 'id' in x and 'data' not in x}
                retained = [x for x in existing.get('entries', []) if 'id' not in x or 'data' in x]
                by_id.update({x['id']: x for x in new['entries']})
                existing['entries'] = list(by_id.values()) + retained
                existing['comment'] = new['comment']
                data = (json.dumps(existing, ensure_ascii=False, indent=2)+'\n').encode('utf-8')
            except (ValueError, TypeError, KeyError) as exc:
                parser.error('Existing custom_emc.json could not be merged; leaving it untouched: ' + str(exc))
        if target.exists() and target.read_bytes() == data:
            continue
        print(('WOULD WRITE ' if args.dry_run else 'WRITE '), relative)
        if args.dry_run: continue
        if target.exists():
            saved = backup / 'original' / relative
            saved.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(target, saved)
        entry = {'path': relative.as_posix(), 'previously_existed': target.exists(),
                 'installed_sha256': hashlib.sha256(data).hexdigest()}
        target.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(dir=target.parent, prefix=target.name+'.aia2-', delete=False) as output:
            output.write(data)
            temporary = Path(output.name)
        temporary.replace(target)
        journal.append(entry)
    if not args.dry_run and journal:
        backup.mkdir(parents=True, exist_ok=True)
        (backup/'journal.json').write_text(json.dumps(journal, indent=2)+'\n')
        print('Backup/journal:', backup)
        print('Restart BOTH client and server fully. /reload cannot register the 48 new items.')
    elif not args.dry_run:
        print('No changes needed; all selected files are already installed.')
    return 0


if __name__ == '__main__': sys.exit(main())
