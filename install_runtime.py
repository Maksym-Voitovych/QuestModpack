#!/usr/bin/env python3
"""Install AIA2 runtime files with a complete preflight, backups and failure rollback."""
import argparse
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import importlib.util
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


def validate_mold_component_tasks(source):
    """Read-only deployment check: a partial ItemStack must not become a broad filter."""
    catalog_path = source/'content/quests/v13_cdg_molds.json'
    if not catalog_path.is_file(): return {'status': 'legacy_package'}
    helper_path = source/'tools/item_task_components_v13.py'
    if not helper_path.is_file() or _is_link(helper_path):
        raise InstallError('Mold component preflight tool is missing')
    expected_profiles = {'V13_E12_cdg_mold_lines': 'lines', 'V13_E12_cdg_mold_bowl': 'bowl',
                         'V13_E12_cdg_mold_chain': 'chain', 'V13_E15_cdg_mold_bar': 'bar',
                         'V13_E15_cdg_mold_heated_lines': 'lines', 'V13_E18_cdg_mold_duroplast': 'bar'}
    try:
        spec = importlib.util.spec_from_file_location('_aia2_mold_predicates', helper_path)
        helper = importlib.util.module_from_spec(spec); spec.loader.exec_module(helper)
        catalog = json.loads(catalog_path.read_text(encoding='utf-8'))['quests']
        assert len(catalog) == len(expected_profiles) and {q['id'] for q in catalog} == set(expected_profiles), 'Expected six reviewed Mold goals'
        quests = {}
        for path in sorted((source/'config/ftbquests/quests/chapters').glob('*.snbt')):
            chapter = _document_pair(path.read_bytes(), None, str(path))[0]
            for quest in chapter.get('quests', []):
                ident = str(quest['id'])
                assert ident not in quests, 'Duplicate compiled quest ID'
                quests[ident] = quest
        uid = lambda value: hashlib.sha256(('aia2-runtime-v1:'+value).encode()).hexdigest()[:12].upper().rjust(16, '0')
        checked = 0
        for record in catalog:
            source_predicates = []
            for index, task in enumerate(record['tasks']):
                predicate = helper.predicate(task)
                if predicate is not None: source_predicates.append((index, task, predicate))
            assert len(source_predicates) == 1, 'Each Mold goal needs one explicit profile predicate'
            index, task, predicate = source_predicates[0]
            assert predicate['components'] == {'createdieselgenerators:mold_type': 'createdieselgenerators:'+expected_profiles[record['id']]} and task.get('count', 1) == 1, 'Mold goal profile/count differs from reviewed contract'
            compiled = quests[uid(record['id'])]
            matches = [t for t in compiled['tasks'] if str(t['id']) == uid(record['id']+':task:'+str(index))]
            assert len(matches) == 1, 'Missing unique compiled profile task'
            actual = matches[0]
            expected_stack = {'id': task['item'], 'count': 1, 'components': predicate['components']}
            assert actual.get('type') == 'item' and actual.get('item') == expected_stack, 'Missing or changed compiled Mold components'
            assert actual.get('match_components') == 'fuzzy', 'Missing literal fuzzy matching'
            assert actual.get('count') == task.get('count', 1) and actual.get('consume_items') == False and actual.get('only_from_crafting') == False, 'Changed Mold task count/inventory flags'
            checked += 1
        return {'status': 'passed', 'profile_tasks': checked}
    except InstallError:
        raise
    except Exception as failure:
        raise InstallError('Mold component predicate failed before installation: '+str(failure)) from failure


def _panel_package_requires_preflight(source):
    """A lost source catalog must not turn the seventeenth rule into legacy data."""
    source = Path(source)
    markers = (source/'content/quests/v14_cdg_panel_native.json',
               source/'content/research/cdg_panel_pending_v14.json')
    if any(path.exists() or _is_link(path) for path in markers):
        return True
    mechanics = source/'kubejs/config/aia2_mechanics.json'
    if not mechanics.is_file():
        return False
    try:
        document = json.loads(mechanics.read_text(encoding='utf-8'))
        return any(row.get('id') == 'cdg_panel_compression' for row in document.get('rules', []))
    except (OSError, ValueError, TypeError, AttributeError) as failure:
        raise InstallError('Mechanics configuration could not be checked before installation: '+str(failure)) from failure


def validate_panel_production(source, jar):
    """Pair the reviewed seventeenth proof with its source, quest and guard JAR.

    This is read-only package validation, not optional-mod ABI or Mixin weaving.
    JSON and FTB SNBT chapters are accepted before any instance backup/write.
    """
    source = Path(source)
    catalog_relative = Path('content/quests/v14_cdg_panel_native.json')
    catalog_path = source/catalog_relative
    if not _panel_package_requires_preflight(source):
        return {'status': 'legacy_package'}
    helper_relative = Path('tools/build_cdg_panel_v14.py')
    helper_path = source/helper_relative
    try:
        for relative in (catalog_relative, helper_relative,
                         Path('content/research/cdg_panel_pending_v14.json'),
                         Path('content/research/evidence/cdg_molds_v13/recipes/createdieselgenerators/compression_molding/sheet_metal_panel.json')):
            current = source
            for part in relative.parts:
                current = current/part
                assert not _is_link(current), 'Panel preflight files must not be symlinks/junctions'
            assert current.is_file(), 'Panel preflight source/helper is missing'
        spec = importlib.util.spec_from_file_location('_aia2_panel_production', helper_path)
        helper = importlib.util.module_from_spec(spec)
        # Execute the reviewed local source without emitting package __pycache__.
        exec(compile(helper_path.read_bytes(), str(helper_path), 'exec'), helper.__dict__)
        own = helper.validate_mechanic_rules(source, compiled=True)
        runtime = json.loads((source/'kubejs/config/aia2_runtime.json').read_text(encoding='utf-8'))
        assert runtime.get('progressionVersion', 0) >= 4 and runtime.get('machineGuard', {}).get('mode') == 'required', 'Panel production requires API4 progression and required Machine Guard'
        for category, entries in helper.PRODUCERS.items():
            for ident, epoch in entries.items():
                assert runtime[category].get(ident) == epoch and epoch <= 12, 'Future or changed panel producer route'
        assert helper.RECIPE_ID not in json.loads((source/'kubejs/config/aia2_recipes.json').read_text(encoding='utf-8'))['remove'], 'Native panel recipe was removed'
        required = {'ua/aia2/guard/CdgPanelAccess.class', 'ua/aia2/guard/ProductionMilestoneBridge.class'}
        assert required <= set(jar.namelist()), 'Panel production needs the matching CdgPanelAccess companion'
        bridge = jar.read('ua/aia2/guard/ProductionMilestoneBridge.class')
        assert b'createdieselgenerators:compression_molding' in bridge and b'ua/aia2/guard/CdgPanelAccess' in bridge, 'Companion lacks the paired CDG serializer/helper reference'
        advancement = source/f'kubejs/data/aia2/advancement/mechanics/{helper.RULE_ID}.json'
        assert json.loads(advancement.read_text(encoding='utf-8')) == helper.ADVANCEMENT, 'Panel native proof must use only its impossible criterion'
        catalog = json.loads(catalog_path.read_text(encoding='utf-8'))
        assert catalog.get('schema') == 1 and len(catalog['quests']) == 1, 'Expected one reviewed panel goal'
        authored = catalog['quests'][0]
        expected_tasks = [
            {'type': 'advancement', 'advancement': own['advancement']},
            {'type': 'item', 'item': own['output'], 'count': 4, 'consume': False, 'craft': False}]
        assert authored.get('id') == helper.QUEST_ID and authored.get('epoch') == 12 and authored.get('required') is False and authored.get('mod') == 'createdieselgenerators', 'Wrong panel source goal identity/era'
        assert authored.get('after') == ['V13_E12_cdg_mold_lines'] and authored.get('proof_scope') == helper.PROOF_SCOPE and authored.get('tasks') == expected_tasks, 'Wrong panel source proof/tasks/prerequisite'
        assert authored['tasks'][1].get('consume') is False and authored['tasks'][1].get('craft') is False, 'Panel source inventory flags require Boolean false'
        quests = {}
        for path in sorted((source/'config/ftbquests/quests/chapters').glob('*.snbt')):
            document = _document_pair(path.read_bytes(), None, str(path))[0]
            for ident, quest in _id_map(document.get('quests', []), str(path)).items():
                assert ident not in quests, 'Duplicate compiled quest ID'
                quests[ident] = quest
        actual = quests[helper.uid(helper.QUEST_ID)]
        def flag(value, expected):
            if type(value) is bool:
                return value is expected
            # FTB SNBT represents its explicit true/false literals as Byte tags.
            return type(value).__module__ == 'nbtlib.tag' and type(value).__name__ == 'Byte' and int(value) == int(expected)
        def count(value, expected):
            return (type(value) is int or (type(value).__module__ == 'nbtlib.tag' and type(value).__name__ == 'Int')) and int(value) == expected
        assert flag(actual.get('optional'), True) and flag(actual.get('hide_until_deps_complete'), True), 'Panel goal must remain optional and gated'
        expected_dependencies = {helper.uid('V13_E12_cdg_mold_lines'), str(runtime['epochs'][10]['finalQuestId'])}
        assert set(map(str, actual.get('dependencies', []))) == expected_dependencies, 'Panel prerequisites or epoch gate changed'
        tasks = actual['tasks']
        assert len(tasks) == 3 and tasks[0] == {'id': helper.uid(helper.QUEST_ID+':task:0'), 'type': 'advancement', 'advancement': own['advancement']}, 'Compiled native panel proof missing/changed'
        sample = tasks[1]
        assert set(sample) == {'id', 'type', 'item', 'count', 'consume_items', 'only_from_crafting'}, 'Compiled panel sample fields changed'
        assert str(sample['id']) == helper.uid(helper.QUEST_ID+':task:1') and sample['type'] == 'item' and sample['item'] == {'id': own['output'], 'count': 1}, 'Compiled panel sample item/identity changed'
        assert count(sample['count'], 4) and count(sample['item']['count'], 1) and flag(sample['consume_items'], False) and flag(sample['only_from_crafting'], False), 'Compiled panel sample count/inventory flags changed'
        assert tasks[2] == {'id': helper.uid(helper.QUEST_ID+':stage'), 'type': 'advancement', 'advancement': 'aia2:stages/e12'}, 'Compiled panel stage check changed'
        return {'status': 'passed', 'panel_native_goals': 1, 'mechanic_rules': 17,
                'scope': 'package_pairing_not_optional_binary_dispatch'}
    except InstallError:
        raise
    except Exception as failure:
        raise InstallError('Panel production contract failed before installation: '+str(failure)) from failure


def validate_key_journal_pair(source, raw_class):
    """New presentation packages must include the matching durable key journal."""
    if not (source/'content/audit/v11-space-milestone-presentation.json').is_file():
        return {'status': 'legacy_package'}
    checker_path = source/'tools/check_optional_mixin_targets_v6.py'
    if not checker_path.is_file() or _is_link(checker_path):
        raise InstallError('Key journal protection preflight tool is missing')
    try:
        spec = importlib.util.spec_from_file_location('_aia2_key_journal_pairing', checker_path)
        checker = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(checker)
        return checker.key_journal_contract(raw_class)
    except Exception as failure:
        raise InstallError('This package needs key journal protection capability1: ' + str(failure)) from failure


def validate_projecte_tablet_pair(source, instance, companion):
    """Read-only ABI check against the instance's real ProjectE JAR, if present.

    This checks the critical tablet redirect, not all optional Mixin weaving.
    It runs before backups or writes, including during --dry-run.
    """
    candidates = [path for path in (instance / 'mods').glob('*.jar')
                  if re.match(r'^projecte(?:[-_.]|$)', path.name, re.IGNORECASE)]
    if not candidates:
        return {'status': 'not_installed', 'actual_mixin_transform': 'NOT_RUN'}
    if len(candidates) != 1 or _is_link(candidates[0]) or not candidates[0].is_file():
        raise InstallError('ProjectE ABI preflight needs one regular ProjectE JAR')
    checker_path = source / 'tools/check_optional_mixin_targets_v6.py'
    if not checker_path.is_file() or _is_link(checker_path):
        raise InstallError('Package is missing the ProjectE compiled Mixin preflight tool')
    try:
        spec = importlib.util.spec_from_file_location('_aia2_optional_mixin_preflight', checker_path)
        checker = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(checker)
        report = checker.check(companion, candidates, mixin_names={'ProjectETabletSourceMixin'})
    except (OSError, ValueError, AssertionError, KeyError, IndexError, zipfile.BadZipFile) as failure:
        raise InstallError('ProjectE compiled Mixin preflight could not read the target JAR: ' + str(failure)) from failure
    if report['status'] != 'PASSED_BYTECODE_CONTRACTS_NOT_WEAVING' or report['unverified_details']:
        problems = ', '.join(sorted({row['kind'] for row in report['errors']})) or 'unverified injection details'
        raise InstallError('ProjectE Tablet Mixin contract failed before installation: ' + problems)
    return report


def validate_ad_astra_nasa_pair(source, instance, companion):
    """Check NASA and station target contracts against the instance before writes."""
    candidates = [path for path in (instance/'mods').glob('*.jar')
                  if re.match(r'^ad[_-]?astra(?:[-_.]|$)', path.name, re.IGNORECASE)]
    if not candidates:
        return {'status': 'not_installed', 'actual_mixin_transform': 'NOT_RUN'}
    if len(candidates) != 1 or _is_link(candidates[0]) or not candidates[0].is_file():
        raise InstallError('Ad Astra ABI preflight needs one regular Ad Astra JAR')
    checker_path = source/'tools/check_optional_mixin_targets_v6.py'
    if not checker_path.is_file() or _is_link(checker_path):
        raise InstallError('Package is missing the Ad Astra compiled Mixin preflight tool')
    try:
        spec = importlib.util.spec_from_file_location('_aia2_nasa_mixin_preflight', checker_path)
        checker = importlib.util.module_from_spec(spec); spec.loader.exec_module(checker)
        report = checker.check(companion, candidates, prefix='earth/terrarium/adastra/',
                               mixin_names={'AdAstraNasaMixin', 'AdAstraNasaMenuMixin', 'AdAstraNasaBaseMenuMixin',
                                            'AdAstraStationPacketMixin', 'AdAstraStationRecipeMixin', 'AdAstraStationRegisterMixin'})
    except (OSError, ValueError, AssertionError, KeyError, IndexError, zipfile.BadZipFile) as failure:
        raise InstallError('Ad Astra compiled Mixin preflight could not read the target JAR: ' + str(failure)) from failure
    if report['status'] != 'PASSED_BYTECODE_CONTRACTS_NOT_WEAVING' or report['unverified_details']:
        problems = ', '.join(sorted({row['kind'] for row in report['errors']})) or 'unverified injection details'
        raise InstallError('Ad Astra NASA Mixin contract failed before installation: ' + problems)
    return report


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
    validate_mold_component_tasks(source)
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
                    validate_key_journal_pair(source, jar.read('ua/aia2/guard/KeyProductionBridge.class'))
                    if (source / 'kubejs/config/aia2_mechanics.json').is_file():
                        required.add('ua/aia2/guard/ProductionMilestoneBridge.class')
                    if any(e.get('branchActionProofs') for e in runtime.get('epochs', [])):
                        if 'ua/aia2/guard/RequiredSpaceActions.class' not in jar.namelist():
                            raise InstallError('This package needs the matching required space action guard')
                    if (source / 'kubejs/config/aia2_stations.json').is_file():
                        station_proofs = {'ua/aia2/guard/StationProductionBridge.class',
                                          'ua/aia2/guard/StationRegistrationWitness.class'}
                        if not station_proofs <= set(jar.namelist()):
                            raise InstallError('This package needs the matching durable station production proof bridge')
                    if not required <= set(jar.namelist()) or jar.testzip() is not None:
                        raise InstallError('Progression v4 needs the matching API4 companion with FTB, manufacturing, Rhino and cached-fusion guards')
                    creative_guard = {'ua/aia2/guard/CreativeManaGuard.class',
                                      'ua/aia2/guard/mixin/BotaniaManaItemHandlerMixin.class',
                                      'ua/aia2/guard/mixin/BotaniaManaTabletPoolMixin.class'}
                    if not creative_guard <= set(jar.namelist()):
                        raise InstallError('This package needs the matching component-aware creative mana guard')
                    if 'ua/aia2/guard/mixin/RootsMortarMixin.class' not in jar.namelist():
                        raise InstallError('This package needs the matching Roots mortar interaction guard')
                    ritual_guard = {'ua/aia2/guard/RootsAltarAccess.class', 'ua/aia2/guard/RootsRitualProof.class',
                                    'ua/aia2/guard/mixin/RootsAltarMixin.class'}
                    if not ritual_guard <= set(jar.namelist()):
                        raise InstallError('This package needs the matching Roots ritual completion observer')
                    if 'ua/aia2/guard/mixin/ApothicSpawnerMixin.class' not in jar.namelist():
                        raise InstallError('This package needs the matching native spawner rune guard')
                    industrial_guard = {'ua/aia2/guard/ModernRecipeProxyAccess.class'}
                    industrial_guard.update('ua/aia2/guard/mixin/' + name + '.class' for name in [
                        'ModernCrafterMixin', 'ModernRecipeConversionsMixin', 'ModernReplicatorMixin',
                        'OritechMachineMixin', 'OritechFluidMachineMixin', 'OritechDustMixin', 'OritechRecipeLookupMixin', 'OritechBaseTickMixin',
                        'RootsMutationIngredientsMixin', 'RootsMutationRadiantMixin'])
                    if not industrial_guard <= set(jar.namelist()):
                        raise InstallError('This package needs the matching MI/Oritech native process and Roots mutation guards')
                    energy_guard = {'ua/aia2/guard/' + name + '.class' for name in ['EnderTaskAccess','EnderSmeltingProxyAccess','PowahOrbAccess']}
                    energy_guard.update('ua/aia2/guard/mixin/' + name + '.class' for name in ['EnderCraftingTaskMixin','EnderCrafterMixin','EnderTankMixin','PowahEnergizingOrbMixin'])
                    if not energy_guard <= set(jar.namelist()):
                        raise InstallError('This package needs the matching EnderIO/Powah cached production guards')
                    fire_guard = {'ua/aia2/guard/' + name + '.class' for name in ['FireWorksiteAccess', 'FireWorksiteInteraction']}
                    fire_guard.update('ua/aia2/guard/mixin/' + name + '.class' for name in ['EnderFireCraftingMixin', 'FireWorksiteBaseMixin'])
                    if not fire_guard <= set(jar.namelist()):
                        raise InstallError('This package needs the matching EnderIO fire worksite guards')
                    projecte_guard = {'ua/aia2/guard/ProjectEAccess.class'}
                    projecte_guard.update('ua/aia2/guard/mixin/' + name + '.class' for name in ['ProjectEHandMenuMixin', 'ProjectETransmutationMixin', 'ProjectEOutputSlotMixin', 'ProjectETimeWatchMixin'])
                    if not projecte_guard <= set(jar.namelist()):
                        raise InstallError('This package needs the matching ProjectE current-output and bonus-tick guards')
                    passive_guard = {'ua/aia2/guard/' + name + '.class' for name in [
                        'ProjectEPassiveAccess', 'ProjectEStorageAccess', 'ProjectEArmorAccess', 'ProjectEArmorAttributes', 'ProjectECurioAttributes']}
                    passive_guard.update('ua/aia2/guard/mixin/' + name + '.class' for name in [
                        'ProjectEItemStackUseMixin', 'ProjectEHotbarPredicateMixin', 'ProjectEKeyCapabilityMixin',
                        'ProjectEArchangelMixin', 'ProjectEGemModeMixin', 'ProjectETabletSourceMixin',
                        'ProjectEBagPassiveMixin', 'ProjectEChestPassiveMixin', 'ProjectEPedestalPassiveMixin',
                        'ProjectEArmorEventsMixin', 'ProjectEArmorFireMixin', 'ProjectEGemArmorMixin',
                        'ProjectEGemChestMixin', 'ProjectEGemHelmetMixin', 'ProjectEGemFeetMixin',
                        'ProjectEArmorAbilitiesMixin', 'ProjectEEquipmentAttributesMixin', 'ProjectEBagSuctionMixin',
                        'ProjectECurioAttributesMixin', 'ProjectECurioReconcileMixin'])
                    if not passive_guard <= set(jar.namelist()):
                        raise InstallError('This package needs the matching ProjectE passive wearer/receiver guards')
                    try:
                        registered = set(json.loads(jar.read('aia2_machine_guard.mixins.json'))['mixins'])
                    except (KeyError, ValueError, TypeError) as invalid:
                        raise InstallError('The companion passive mixin registration is missing or damaged') from invalid
                    passive_mixins = {name.rsplit('/', 1)[-1].removesuffix('.class')
                                      for name in passive_guard if '/mixin/' in name}
                    if not passive_mixins <= registered:
                        raise InstallError('The companion ProjectE passive mixin registration is incomplete')
                    evilcraft_mixins = {'EvilCraftInfuserMixin', 'EvilCraftSpiritOutputMixin', 'EvilCraftReanimatorMixin'}
                    evilcraft_classes = {'ua/aia2/guard/EvilCraftAccess.class'} | {
                        'ua/aia2/guard/mixin/' + name + '.class' for name in evilcraft_mixins}
                    if not evilcraft_classes <= set(jar.namelist()) or not evilcraft_mixins <= registered:
                        raise InstallError('This package needs the matching EvilCraft infusion and spirit guards')
                    forbidden_mixins = {'ForbiddenRitualMixin', 'ForbiddenEssencePaymentMixin', 'ForbiddenForgeInputMixin'}
                    forbidden_classes = {'ua/aia2/guard/' + name + '.class' for name in [
                        'ForbiddenRitualAccess', 'ForbiddenPaidState', 'ForbiddenForgeCommands', 'ForbiddenDependencies']}
                    forbidden_classes.update('ua/aia2/guard/mixin/' + name + '.class' for name in forbidden_mixins)
                    if not forbidden_classes <= set(jar.namelist()) or not forbidden_mixins <= registered:
                        raise InstallError('This package needs the matching Forbidden Arcanus paid ritual and essence guards')
                    clibano_mixins = {'ClibanoFrameMenuMixin', 'ClibanoMenuValidityMixin', 'ClibanoMachineMixin', 'ClibanoResidueMixin'}
                    clibano_classes = {'ua/aia2/guard/' + name + '.class' for name in [
                        'ClibanoOwnership', 'ClibanoAccess', 'ClibanoPaidState', 'ClibanoCommands', 'ClibanoDependencies', 'ClibanoDependencyState']}
                    clibano_classes.update('ua/aia2/guard/mixin/' + name + '.class' for name in clibano_mixins)
                    if not clibano_classes <= set(jar.namelist()) or not clibano_mixins <= registered:
                        raise InstallError('This package needs the matching Clibano controller ownership and paid production guards')
                    nasa_mixins = {'AdAstraNasaMixin', 'AdAstraNasaMenuMixin', 'AdAstraNasaBaseMenuMixin'}
                    nasa_classes = {'ua/aia2/guard/AdAstraNasaAccess.class'} | {
                        'ua/aia2/guard/mixin/' + name + '.class' for name in nasa_mixins}
                    if not nasa_classes <= set(jar.namelist()) or not nasa_mixins <= registered:
                        raise InstallError('This package needs the matching Ad Astra NASA cached recipe and menu guards')
                    station_mixins = {'AdAstraStationPacketMixin', 'AdAstraStationRecipeMixin', 'AdAstraStationRegisterMixin', 'StationTemplateMixin'}
                    station_classes = {'ua/aia2/guard/' + name + '.class' for name in
                                       ['StationConstructionAccess', 'StationIngredients', 'StationPaymentPlan', 'StationTemplateSnapshot', 'GuardedStationTemplate']}
                    station_classes |= {'ua/aia2/guard/mixin/' + name + '.class' for name in station_mixins}
                    if not station_classes <= set(jar.namelist()) or not station_mixins <= registered:
                        raise InstallError('This package needs the matching station payment and placement guards')
                    production_classes = {'ua/aia2/guard/' + name + '.class' for name in
                                          ['NasaProductionAccess', 'NasaIngredients', 'GuardedNasaDrop']}
                    production_classes.add('ua/aia2/guard/mixin/NasaDropMixin.class')
                    if not production_classes <= set(jar.namelist()) or 'NasaDropMixin' not in registered:
                        raise InstallError('This package needs the matching NASA accepted output and native debit witness')
            except zipfile.BadZipFile as error:
                raise InstallError('The progression v4 companion JAR is damaged or outdated') from error
            validate_projecte_tablet_pair(source, instance, bundled_jars[0])
            validate_ad_astra_nasa_pair(source, instance, bundled_jars[0])
    if _panel_package_requires_preflight(source):
        try:
            with zipfile.ZipFile(bundled_jars[0]) as jar:
                validate_panel_production(source, jar)
        except zipfile.BadZipFile as failure:
            raise InstallError('Panel production companion JAR is damaged') from failure
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
