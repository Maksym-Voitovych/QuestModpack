#!/usr/bin/env python3
"""Install AIA2 runtime files with a complete preflight, backups and failure rollback."""
import argparse
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import sys
import tempfile
import zipfile


class InstallError(RuntimeError):
    """An installation failed safely or needs explicit recovery from its backup."""


@dataclass
class Operation:
    relative: Path
    data: object  # bytes for a write; None for removal of an older AIA2 companion.
    previous: object  # Original bytes, or None for a file that did not exist.
    mode: int = 0o644

    def journal_entry(self):
        return {
            'path': self.relative.as_posix(),
            'action': 'remove_old_companion' if self.data is None else 'write',
            'previously_existed': self.previous is not None,
            'previous_sha256': _digest(self.previous),
            'installed_sha256': _digest(self.data),
        }


def _digest(data):
    return hashlib.sha256(data).hexdigest() if data is not None else None


def _is_link(path):
    # Resolve the selected instance root first: Windows junctions selecting the
    # instance are supported. Links *within* it are never followed for writes.
    return path.is_symlink() or (hasattr(path, 'is_junction') and path.is_junction())


def _target(instance, relative):
    if relative.is_absolute() or '..' in relative.parts:
        raise InstallError('Unsafe package path: ' + str(relative))
    current = instance
    for index, part in enumerate(relative.parts):
        current = current / part
        if _is_link(current):
            raise InstallError('Refusing to write through a symlink/junction: ' + str(current))
        if index < len(relative.parts) - 1 and current.exists() and not current.is_dir():
            raise InstallError('Expected a directory: ' + str(current))
    if current.exists() and not current.is_file():
        raise InstallError('Expected a regular file: ' + str(current))
    return current


def _json_bytes(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode('utf-8')


class _FTBSNBTReader:
    """FTB Library 1.21.1 dialect: optional commas, '=' and whole-line comments.

    Structure/escaping follows FTB's SNBTParser/SNBTUtils. nbtlib supplies real
    typed tags; unsupported values fail before any instance mutation.
    """
    def __init__(self, text, nbt):
        self.text = '\n'.join(line for line in text.splitlines()
                              if not line.lstrip().startswith(('#', '//')))
        self.position = 0
        self.nbt = nbt

    def skip(self):
        while self.position < len(self.text) and (self.text[self.position].isspace() or self.text[self.position] == ','):
            self.position += 1

    def peek(self):
        self.skip()
        if self.position == len(self.text):
            raise ValueError('Unexpected end of FTB SNBT')
        return self.text[self.position]

    def string(self):
        quote = self.text[self.position]
        self.position += 1
        result = []
        escapes = {'"': '"', "'": "'", '\\': '\\', 't': '\t', 'b': '\b',
                   'n': '\n', 'r': '\r', 'f': '\f'}
        while self.position < len(self.text):
            char = self.text[self.position]
            self.position += 1
            if char == quote:
                return ''.join(result)
            if char in '\r\n':
                raise ValueError('Unclosed FTB SNBT string')
            if char == '\\':
                if self.position >= len(self.text):
                    raise ValueError('Unclosed FTB SNBT escape')
                char = self.text[self.position]
                self.position += 1
                if char not in escapes:
                    raise ValueError('Unsupported FTB SNBT escape: \\' + char)
                char = escapes[char]
            result.append(char)
        raise ValueError('Unclosed FTB SNBT string')

    def word(self):
        start = self.position
        while self.position < len(self.text):
            char = self.text[self.position]
            if not (char.isalpha() or char.isdigit() or char in '._-+∞'):
                break
            self.position += 1
        if self.position == start:
            raise ValueError('Unexpected FTB SNBT token at character ' + str(start))
        return self.text[start:self.position]

    def value(self):
        char = self.peek()
        if char in '\"\'':
            return self.nbt.String(self.string())
        if char == '{':
            self.position += 1
            result = self.nbt.Compound()
            while self.peek() != '}':
                key = self.string() if self.peek() in '\"\'' else self.word()
                if self.peek() not in ':=':
                    raise ValueError('Expected colon/equal after FTB SNBT key ' + key)
                self.position += 1
                result[key] = self.value()
            self.position += 1
            return result
        if char == '[':
            self.position += 1
            self.skip()
            array = re.match(r'([BbIiLl])\s*;', self.text[self.position:])
            if array:
                self.position += len(array.group())
            values = []
            while self.peek() != ']':
                values.append(self.value())
            self.position += 1
            if not array:
                return self.nbt.List(values)
            if any(isinstance(value, (self.nbt.String, self.nbt.Compound, self.nbt.List)) for value in values):
                raise ValueError('Expected numeric FTB SNBT array entries')
            kind = {'B': self.nbt.ByteArray, 'I': self.nbt.IntArray, 'L': self.nbt.LongArray}[array[1].upper()]
            return kind([int(value) for value in values])
        word = self.word()
        if word in ('true', 'false'):
            return self.nbt.Byte(word == 'true')
        if word in ('null', 'end', 'END'):
            raise ValueError('End/null FTB tags need manual migration; preserving the original file')
        normalized = word.replace('∞', 'Infinity')
        if re.fullmatch(r'[+-]?(?:Infinity|NaN)[df]?', normalized):
            kind = self.nbt.Float if normalized.endswith('f') else self.nbt.Double
            numeric = normalized[:-1] if normalized.endswith(('d', 'f')) else normalized
            return kind(float(numeric))
        # FTB permits Unicode bare words and exponent-only doubles (1E4),
        # both beyond nbtlib's literal grammar. Mirror SNBTUtils number rules.
        integer = r'[+-]?[0-9]+'
        numeric = r'[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?'
        if re.fullmatch(integer, word) and -(2**31) <= int(word) < 2**31:
            return self.nbt.Int(int(word))
        if re.fullmatch(integer + r'[bBsSlL]', word):
            kind = {'b': self.nbt.Byte, 's': self.nbt.Short, 'l': self.nbt.Long}[word[-1].lower()]
            return kind(int(word[:-1]))
        if re.fullmatch(numeric + r'[fFdD]', word):
            kind = self.nbt.Float if word[-1].lower() == 'f' else self.nbt.Double
            return kind(float(word[:-1]))
        if re.fullmatch(numeric, word):
            return self.nbt.Double(float(word))
        return self.nbt.String(word)

    def read(self):
        value = self.value()
        self.skip()
        if self.position != len(self.text):
            raise ValueError('Trailing FTB SNBT data')
        return value


def _encode_ftb(value, nbt, depth=0):
    """Keep typed foreign tags and FTB-compatible escaped string contents."""
    padding = '  ' * depth
    child_padding = '  ' * (depth + 1)
    if isinstance(value, dict):
        lines = [child_padding + json.dumps(str(key), ensure_ascii=False) + ': ' + _encode_ftb(entry, nbt, depth + 1)
                 for key, entry in value.items()]
        return '{\n' + ',\n'.join(lines) + '\n' + padding + '}' if lines else '{}'
    if isinstance(value, list):
        lines = [child_padding + _encode_ftb(entry, nbt, depth + 1) for entry in value]
        return '[\n' + ',\n'.join(lines) + '\n' + padding + ']' if lines else '[]'
    if isinstance(value, str):
        return json.dumps(str(value), ensure_ascii=False)
    if isinstance(value, (nbt.Float, nbt.Double)):
        import math
        if not math.isfinite(value):
            number = 'NaN' if math.isnan(value) else ('-Infinity' if value < 0 else 'Infinity')
            return number + ('f' if isinstance(value, nbt.Float) else 'd')
    return nbt.serialize_tag(value)


def _document_pair(incoming, existing, label):
    """Use stdlib JSON where possible; actual FTB SNBT needs nbtlib explicitly."""
    try:
        new = json.loads(incoming)
        old = json.loads(existing) if existing is not None else None
        return new, old, _json_bytes
    except (ValueError, UnicodeDecodeError):
        try:
            import nbtlib
        except ImportError as exc:
            raise InstallError(
                label + ': SNBT merge requires nbtlib before installation. '
                'Run: python -m pip install nbtlib (then repeat --dry-run). '
                'No instance files have been changed.'
            ) from exc
        def to_nbt(value):
            if isinstance(value, bool):
                return nbtlib.Byte(int(value))
            if isinstance(value, str):
                return nbtlib.String(value)
            if isinstance(value, int):
                return nbtlib.Int(value) if -(2**31) <= value < 2**31 else nbtlib.Long(value)
            if isinstance(value, float):
                return nbtlib.Double(value)
            if isinstance(value, list):
                return nbtlib.List([to_nbt(entry) for entry in value])
            if isinstance(value, dict):
                return nbtlib.Compound({key: to_nbt(entry) for key, entry in value.items()})
            raise ValueError('JSON value has no SNBT representation: ' + repr(value))
        def decode(data):
            # JSON permits Unicode/control escapes that SNBT does not. Convert
            # parsed values rather than feed escaped JSON directly to nbtlib.
            try:
                return to_nbt(json.loads(data))
            except json.JSONDecodeError:
                return _FTBSNBTReader(data.decode('utf-8'), nbtlib).read()
        try:
            new = decode(incoming)
            old = decode(existing) if existing is not None else None
        except (ValueError, TypeError, UnicodeDecodeError) as exc:
            raise InstallError(label + ': invalid JSON/SNBT: ' + str(exc)) from exc
        def encode(value):
            return (_encode_ftb(value, nbtlib) + '\n').encode('utf-8')
        return new, old, encode


def _id_map(entries, label):
    if not isinstance(entries, list):
        raise InstallError(label + ': expected a list')
    result = {}
    for entry in entries:
        if not isinstance(entry, dict) or not isinstance(entry.get('id'), str):
            raise InstallError(label + ': every entry must have a stable string id')
        identifier = str(entry['id']).upper()
        if re.fullmatch(r'[0-9A-F]{1,16}', identifier):
            identifier = identifier.zfill(16)
        if identifier in result:
            raise InstallError(label + ': duplicate stable id ' + identifier)
        result[identifier] = entry
    return result


def _merge_ftb(incoming, existing, collection, label):
    new, old, encode = _document_pair(incoming, existing, label)
    if not isinstance(new, dict) or (old is not None and not isinstance(old, dict)):
        raise InstallError(label + ': expected a compound/object')
    new_entries = new.get(collection, [])
    owned = _id_map(new_entries, label)
    if old is None:
        return incoming
    old_entries = old.get(collection, [])
    foreign = _id_map(old_entries, label)
    if collection == 'quests' and str(new.get('id', '')).upper() != str(old.get('id', '')).upper():
        raise InstallError(label + ': chapter ID changed; refusing to overwrite another chapter')
    retained = [entry for identifier, entry in foreign.items() if identifier not in owned]
    # Retain the Compound container and foreign NBT scalar/list types.
    merged = type(old)(old)
    merged.update(new)
    combined = list(new_entries) + retained
    container = new_entries if new_entries or not old_entries else old_entries
    merged[collection] = type(container)(combined)
    if not retained and new == old:
        return existing
    return encode(merged)


def _transform(relative, incoming, previous):
    name = relative.as_posix()
    if name == 'config/ftbquests/quests/chapter_groups.snbt':
        return _merge_ftb(incoming, previous, 'chapter_groups', name)
    if relative.parent.as_posix() == 'config/ftbquests/quests/chapters' and relative.suffix == '.snbt':
        return _merge_ftb(incoming, previous, 'quests', name)
    if previous is None:
        return incoming
    try:
        if name == 'kubejs/config/aia2_runtime.json':
            current, new = json.loads(previous), json.loads(incoming)
            if current.get('machineGuard', {}).get('mode') == 'required':
                new['machineGuard']['mode'] = 'required'
                return _json_bytes(new)
        if name == 'config/ProjectE/custom_emc.json':
            current, new = json.loads(previous), json.loads(incoming)
            by_id = {x['id']: x for x in current.get('entries', []) if 'id' in x and 'data' not in x}
            retained = [x for x in current.get('entries', []) if 'id' not in x or 'data' in x]
            by_id.update({x['id']: x for x in new['entries']})
            current['entries'] = list(by_id.values()) + retained
            current['comment'] = new['comment']
            return _json_bytes(current)
    except (ValueError, TypeError, KeyError, AttributeError) as exc:
        raise InstallError(name + ': configuration could not be merged: ' + str(exc)) from exc
    return incoming


def plan_install(source, instance):
    """Read and validate every selected source/target before changing the instance."""
    source, instance = Path(source).resolve(), Path(instance).expanduser().resolve()
    if source == instance:
        raise InstallError('The package and destination instance must be different directories')
    if not all((source / name).is_dir() for name in ('kubejs', 'config', 'mods')):
        raise InstallError('kubejs/, config/ and mods/ must be beside this installer')
    if not (instance / 'mods').is_dir() or _is_link(instance / 'mods'):
        raise InstallError('The instance must contain a regular mods/ directory')
    backup_root = instance / 'aia2-backups'
    if _is_link(backup_root) or (backup_root.exists() and not backup_root.is_dir()):
        raise InstallError('The backup directory must not be a symlink or a regular file')
    files = []
    for folder in ('kubejs', 'config'):
        if _is_link(source / folder):
            raise InstallError('Package folders must not be symlinks: ' + folder)
        for item in (source / folder).rglob('*'):
            if _is_link(item):
                raise InstallError('Package files must not be symlinks: ' + str(item))
            if item.is_file():
                files.append(item)
    # Deliberately never copy other mod JARs or enumerate worlds/saves/progress.
    bundled_jars = sorted((source / 'mods').glob('aia2-machine-guard-*.jar'))
    if len(bundled_jars) != 1 or not bundled_jars[0].is_file() or _is_link(bundled_jars[0]):
        raise InstallError('Package must contain exactly one regular aia2-machine-guard-*.jar')
    runtime_path = source / 'kubejs/config/aia2_runtime.json'
    if runtime_path.exists():
        runtime = json.loads(runtime_path.read_text(encoding='utf-8'))
        if runtime.get('progressionVersion', 0) >= 4:
            try:
                with zipfile.ZipFile(bundled_jars[0]) as jar:
                    required = {'ua/aia2/guard/Aia2MachineGuard.class',
                                'ua/aia2/guard/KeyProductionBridge.class',
                                'ua/aia2/guard/FtbQuestBridge.class',
                                'ua/aia2/guard/RhinoLongMapBridge.class'}
                    required.add('ua/aia2/guard/mixin/DraconicFusionCoreMixin.class')
                    if (source / 'kubejs/config/aia2_mechanics.json').is_file():
                        required.add('ua/aia2/guard/ProductionMilestoneBridge.class')
                    if not required <= set(jar.namelist()) or jar.testzip() is not None:
                        raise InstallError('Progression v4 needs the matching API4 companion with FTB, manufacturing, Rhino and cached-fusion guards')
                    creative_guard = {'ua/aia2/guard/CreativeManaGuard.class',
                                      'ua/aia2/guard/mixin/BotaniaManaItemHandlerMixin.class',
                                      'ua/aia2/guard/mixin/BotaniaManaTabletPoolMixin.class'}
                    if not creative_guard <= set(jar.namelist()):
                        raise InstallError('This package needs the matching component-aware creative mana guard')
            except zipfile.BadZipFile as error:
                raise InstallError('The progression v4 companion JAR is damaged or outdated') from error
    files.extend(bundled_jars)
    operations = []
    for item in sorted(files):
        relative = item.relative_to(source)
        target = _target(instance, relative)
        incoming = item.read_bytes()  # All source reads finish before any backup/write.
        previous = target.read_bytes() if target.exists() else None
        if relative.as_posix() == 'config/ftbquests/quests/data.snbt' and previous is not None:
            continue
        if incoming == previous:
            continue
        data = _transform(relative, incoming, previous)
        if data != previous:
            mode = stat.S_IMODE(target.stat().st_mode) if previous is not None else 0o644
            operations.append(Operation(relative, data, previous, mode))
    bundled_name = bundled_jars[0].name
    for older in sorted((instance / 'mods').glob('aia2-machine-guard-*.jar')):
        if older.name == bundled_name:
            continue
        relative = older.relative_to(instance)
        _target(instance, relative)
        operations.append(Operation(relative, None, older.read_bytes(), stat.S_IMODE(older.stat().st_mode)))
    return instance, operations


def _atomic_write(path, data, mode=0o644):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent, prefix='.' + path.name + '.aia2-', delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        temporary.chmod(mode)
        os.replace(temporary, path)
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()


def apply_plan(instance, operations, dry_run=False, output=print):
    if not operations:
        output('No changes needed; all selected files are already installed.')
        return None
    for op in operations:
        action = 'REMOVE old AIA2 companion ' if op.data is None else 'WRITE '
        output(('WOULD ' if dry_run else 'PLAN ') + action + op.relative.as_posix())
    if dry_run:
        output('Preflight passed; dry-run made no changes.')
        return None
    # Refuse stale plans, including files edited while source files were read.
    for op in operations:
        target = _target(instance, op.relative)
        current = target.read_bytes() if target.exists() else None
        if current != op.previous:
            raise InstallError('Destination changed during preflight: ' + str(op.relative))
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    backup = instance / 'aia2-backups' / stamp
    backup.mkdir(parents=True, exist_ok=False)
    journal = {'schema': 1, 'state': 'preparing_backups', 'operations': [op.journal_entry() for op in operations]}
    _atomic_write(backup / 'journal.json', _json_bytes(journal))
    try:
        # Complete *every* backup before replacing/removing the first target.
        for op in operations:
            if op.previous is not None:
                saved = backup / 'original' / op.relative
                _atomic_write(saved, op.previous, op.mode)
                if saved.read_bytes() != op.previous:
                    raise InstallError('Backup verification failed: ' + str(op.relative))
        journal['state'] = 'prepared'
        _atomic_write(backup / 'journal.json', _json_bytes(journal))
    except Exception as exc:
        raise InstallError('Backup failed before any runtime file was changed; details: ' + str(backup)) from exc
    applied = []
    try:
        for op in operations:
            target = _target(instance, op.relative)
            current = target.read_bytes() if target.exists() else None
            if current != op.previous:
                raise InstallError('Destination changed after backup: ' + str(op.relative))
            # Append before mutation so a fault immediately after os.replace is
            # still reversed. Restoring an unchanged file is harmless.
            applied.append(op)
            if op.data is None:
                target.unlink()
            else:
                _atomic_write(target, op.data, op.mode)
        journal['state'] = 'completed'
        _atomic_write(backup / 'journal.json', _json_bytes(journal))
    except Exception as exc:
        rollback_errors = []
        for op in reversed(applied):
            try:
                target = _target(instance, op.relative)
                if op.previous is None:
                    if target.exists():
                        target.unlink()
                else:
                    _atomic_write(target, op.previous, op.mode)
            except Exception as rollback_exc:
                rollback_errors.append(str(op.relative) + ': ' + str(rollback_exc))
        journal.update(state='rollback_incomplete' if rollback_errors else 'rolled_back',
                       failure=str(exc), rollback_errors=rollback_errors)
        try:
            _atomic_write(backup / 'journal.json', _json_bytes(journal))
        except Exception as journal_exc:
            rollback_errors.append('journal: ' + str(journal_exc))
        detail = 'rollback incomplete' if rollback_errors else 'all changed runtime files rolled back'
        raise InstallError('Installation failed; ' + detail + '. Backup: ' + str(backup) + '. Cause: ' + str(exc)) from exc
    output('Backup/journal: ' + str(backup))
    output('Restart BOTH client and server fully; /reload cannot load startup scripts/items.')
    return backup


def install(source, instance, dry_run=False, output=print):
    destination, operations = plan_install(source, instance)
    return apply_plan(destination, operations, dry_run=dry_run, output=output)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('instance', type=Path, help='Minecraft instance root containing mods/')
    parser.add_argument('--dry-run', action='store_true', help='Preflight and list changes without writing')
    args = parser.parse_args(argv)
    try:
        install(Path(__file__).resolve().parent, args.instance, dry_run=args.dry_run)
    except (InstallError, OSError) as exc:
        parser.exit(2, 'Installation stopped: ' + str(exc) + '\n')
    return 0


if __name__ == '__main__':
    sys.exit(main())
