"""Deployment must reject a broad/partially decoded Mold filter before writes.

The extracted package is modeled, while the public installer, file snapshots,
JSON/SNBT parser and on-disk backup paths are real. No Minecraft is launched.
"""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('aia2_mold_install_v13', ROOT/'install_runtime.py')
installer = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = installer
SPEC.loader.exec_module(installer)
CATALOG = 'content/quests/v13_cdg_molds.json'
CHAPTER = 'config/ftbquests/quests/chapters/aia2_mold_fixture.snbt'
HELPER = 'tools/item_task_components_v13.py'
COMPONENT = 'createdieselgenerators:mold_type'


def uid(value):
    return hashlib.sha256(('aia2-runtime-v1:'+value).encode()).hexdigest()[:12].upper().rjust(16, '0')


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def snapshot(directory):
    return {path.relative_to(directory).as_posix(): path.read_bytes() if path.is_file() else None
            for path in directory.rglob('*')}


class MoldInstallPreflightTests(unittest.TestCase):
    def fixture(self, directory):
        source, instance = directory/'package', directory/'instance'
        catalog = read(ROOT/CATALOG)
        write(source/CATALOG, catalog)
        target = source/HELPER; target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT/HELPER, target)
        write(source/'kubejs/config/aia2_runtime.json', {})
        (source/'mods').mkdir()
        with zipfile.ZipFile(source/'mods/aia2-machine-guard-fixture.jar', 'w') as archive:
            archive.writestr('fixture.txt', b'Only a regular owned JAR fixture; no API4/runtime claim')
        chapter = {'id': 'FFFFFF0013130001', 'title': 'Owned Mold fixture', 'quests': []}
        for record in catalog['quests']:
            index, task = next((index, task) for index, task in enumerate(record['tasks'])
                               if COMPONENT in task.get('components', {}))
            # Construct the expected wire format independently of compile_task,
            # so dropping that compiler's predicate would not bless this fixture.
            chapter['quests'].append({'id': uid(record['id']), 'title': record['title_uk'],
                'tasks': [{'id': uid(record['id']+':task:'+str(index)), 'type': 'item',
                           'item': {'id': 'createdieselgenerators:mold', 'count': 1,
                                    'components': copy.deepcopy(task['components'])},
                           'count': 1, 'consume_items': False,
                           'only_from_crafting': False, 'match_components': 'fuzzy'}]})
        write(source/CHAPTER, chapter)
        markers = {
            'mods/aia2-machine-guard-old.jar': b'opaque old owned companion',
            'mods/foreign.jar': b'foreign mod',
            'kubejs/server_scripts/foreign.js': b'// preserve foreign script\n',
            'kubejs/config/aia2_runtime.json': b'{"old": true}\n',
            'saves/preserved/level.dat': b'opaque world',
            'saves/preserved/data/aia2_key_production_v1.dat': b'opaque 96-key journal',
            'saves/preserved/data/ftbquests.dat': b'opaque FTB team progress',
        }
        for relative, data in markers.items():
            path = instance/relative; path.parent.mkdir(parents=True, exist_ok=True); path.write_bytes(data)
        return source, instance, markers

    def assert_rejected_without_instance_writes(self, source, instance):
        before = snapshot(instance)
        for dry in (False, True):
            with self.subTest(dry_run=dry), patch.object(installer, '_atomic_write') as atomic:
                with self.assertRaises(installer.InstallError):
                    installer.install(source, instance, dry_run=dry, output=lambda _: None)
                atomic.assert_not_called()
                self.assertEqual(snapshot(instance), before)
                self.assertFalse((instance/'aia2-backups').exists())

    def test_valid_json_predicates_dry_run_upgrade_and_repeat_preserve_opaque_progress(self):
        with tempfile.TemporaryDirectory() as temporary:
            source, instance, markers = self.fixture(Path(temporary))
            self.assertEqual(installer.validate_mold_component_tasks(source),
                             {'status': 'passed', 'profile_tasks': 6})
            before = snapshot(instance)
            installer.install(source, instance, dry_run=True, output=lambda _: None)
            self.assertEqual(snapshot(instance), before)
            installer.install(source, instance, output=lambda _: None)
            for relative, data in markers.items():
                if relative in {'mods/aia2-machine-guard-old.jar', 'kubejs/config/aia2_runtime.json'}:
                    continue
                self.assertEqual((instance/relative).read_bytes(), data)
            self.assertFalse((instance/'mods/aia2-machine-guard-old.jar').exists())
            backups = list((instance/'aia2-backups').rglob('aia2-machine-guard-old.jar'))
            self.assertEqual(len(backups), 1)
            self.assertEqual(backups[0].read_bytes(), markers['mods/aia2-machine-guard-old.jar'])
            self.assertEqual((instance/CHAPTER).read_bytes(), (source/CHAPTER).read_bytes())
            after = snapshot(instance)
            installer.install(source, instance, output=lambda _: None)
            self.assertEqual(snapshot(instance), after)

    def test_actual_snbt_component_compound_retains_profile_and_fuzzy_mode(self):
        import nbtlib
        def tag(value):
            if isinstance(value, bool): return nbtlib.Byte(int(value))
            if isinstance(value, int): return nbtlib.Int(value)
            if isinstance(value, str): return nbtlib.String(value)
            if isinstance(value, list): return nbtlib.List([tag(entry) for entry in value])
            if isinstance(value, dict): return nbtlib.Compound({key: tag(entry) for key, entry in value.items()})
            raise AssertionError(value)
        with tempfile.TemporaryDirectory() as temporary:
            source, instance, _ = self.fixture(Path(temporary))
            document = read(source/CHAPTER)
            (source/CHAPTER).write_text(nbtlib.serialize_tag(tag(document))+'\n', encoding='utf-8')
            with self.assertRaises(json.JSONDecodeError):
                read(source/CHAPTER)
            self.assertEqual(installer.validate_mold_component_tasks(source)['profile_tasks'], 6)
            before = snapshot(instance)
            installer.install(source, instance, dry_run=True, output=lambda _: None)
            self.assertEqual(snapshot(instance), before)

    def test_legacy_package_without_v13_catalog_has_no_new_preflight_requirement(self):
        with tempfile.TemporaryDirectory() as temporary:
            source, _, _ = self.fixture(Path(temporary))
            (source/CATALOG).unlink()
            (source/HELPER).unlink()
            self.assertEqual(installer.validate_mold_component_tasks(source), {'status': 'legacy_package'})

    def test_missing_or_symlinked_helper_rejects_before_any_normal_or_dry_run_write(self):
        for kind in ('missing', 'symlink'):
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as temporary:
                source, instance, _ = self.fixture(Path(temporary))
                helper = source/HELPER
                if kind == 'symlink':
                    reference = source/'helper-original.py'; shutil.copyfile(helper, reference)
                    helper.unlink(); helper.symlink_to(reference)
                else:
                    helper.unlink()
                self.assert_rejected_without_instance_writes(source, instance)

    def test_compiled_predicate_corruption_never_reaches_partial_itemstack_loading(self):
        def mutate(task, kind):
            if kind == 'missing-components': del task['item']['components']
            elif kind == 'wrong-profile': task['item']['components'][COMPONENT] = 'createdieselgenerators:bar'
            elif kind == 'invalid-resource-location': task['item']['components'][COMPONENT] = 'Bad Namespace:profile!'
            elif kind == 'wrong-component-type': task['item']['components'][COMPONENT] = 1
            elif kind == 'missing-mode': del task['match_components']
            elif kind in ('ALL', 'none', 'FUZZY'): task['match_components'] = kind
            elif kind == 'legacy-Count-tag':
                task['item'] = {'id': 'createdieselgenerators:mold', 'Count': 1,
                                'tag': {'mold_type': 'createdieselgenerators:lines'}}
            elif kind == 'consume': task['consume_items'] = True
            elif kind == 'craft': task['only_from_crafting'] = True
            elif kind == 'quantity': task['count'] = 0
            elif kind == 'extra-stack-key': task['item']['tag'] = {'legacy': True}
            else: raise AssertionError(kind)
        for kind in ('missing-components', 'wrong-profile', 'invalid-resource-location', 'wrong-component-type',
                     'missing-mode', 'ALL', 'none', 'FUZZY', 'legacy-Count-tag', 'consume', 'craft',
                     'quantity', 'extra-stack-key'):
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as temporary:
                source, instance, _ = self.fixture(Path(temporary))
                chapter = read(source/CHAPTER); mutate(chapter['quests'][0]['tasks'][0], kind)
                write(source/CHAPTER, chapter)
                self.assert_rejected_without_instance_writes(source, instance)

    def test_missing_and_duplicate_compiled_quest_or_profile_task_are_rejected(self):
        for kind in ('missing-quest', 'missing-task', 'duplicate-quest', 'duplicate-task'):
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as temporary:
                source, instance, _ = self.fixture(Path(temporary))
                chapter = read(source/CHAPTER)
                if kind == 'missing-quest': chapter['quests'].pop()
                elif kind == 'missing-task': chapter['quests'][0]['tasks'].clear()
                elif kind == 'duplicate-quest': chapter['quests'].append(copy.deepcopy(chapter['quests'][0]))
                else: chapter['quests'][0]['tasks'].append(copy.deepcopy(chapter['quests'][0]['tasks'][0]))
                write(source/CHAPTER, chapter)
                self.assert_rejected_without_instance_writes(source, instance)

    def test_source_predicates_cannot_be_removed_or_silently_misspelled(self):
        for kind in ('remove-all', 'upper-case-fields', 'trailing-space-fields', 'wrong-mode', 'null-profile'):
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as temporary:
                source, instance, _ = self.fixture(Path(temporary))
                catalog = read(source/CATALOG)
                for record in catalog['quests']:
                    task = next(task for task in record['tasks'] if COMPONENT in task.get('components', {}))
                    if kind == 'remove-all':
                        del task['components']; del task['match_components']
                    elif kind == 'upper-case-fields':
                        task['Components'] = task.pop('components'); task['Match_Components'] = task.pop('match_components')
                    elif kind == 'trailing-space-fields':
                        task['components '] = task.pop('components'); task['match_components '] = task.pop('match_components')
                    elif kind == 'wrong-mode': task['match_components'] = 'ALL'
                    else: task['components'][COMPONENT] = None
                write(source/CATALOG, catalog)
                self.assert_rejected_without_instance_writes(source, instance)

    def test_changed_source_goal_set_is_rejected_before_writes(self):
        for kind in ('missing', 'unknown', 'duplicate'):
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as temporary:
                source, instance, _ = self.fixture(Path(temporary))
                catalog = read(source/CATALOG)
                if kind == 'missing': catalog['quests'].pop()
                elif kind == 'unknown': catalog['quests'][0]['id'] = 'V13_UNREVIEWED'
                else: catalog['quests'][-1]['id'] = catalog['quests'][0]['id']
                write(source/CATALOG, catalog)
                self.assert_rejected_without_instance_writes(source, instance)


if __name__ == '__main__':
    unittest.main()
