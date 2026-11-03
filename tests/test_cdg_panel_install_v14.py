"""Read-only CDG proof deployment pairing, on real temporary files and installer.

The companion contents are pairing-gate fixtures, never executed Java classes.
The final package delivery test separately installs the real built companion.
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

from tools import build_cdg_panel_v14 as P

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('aia2_panel_install_v14', ROOT/'install_runtime.py')
installer = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = installer
SPEC.loader.exec_module(installer)
CHAPTER = 'config/ftbquests/quests/chapters/aia2_panel_fixture.snbt'
HELPER = 'tools/build_cdg_panel_v14.py'
JAR = 'mods/aia2-machine-guard-fixture-v14.jar'
HELPER_CLASS = 'ua/aia2/guard/CdgPanelAccess.class'
BRIDGE_CLASS = 'ua/aia2/guard/ProductionMilestoneBridge.class'
ADVANCEMENT = 'kubejs/data/aia2/advancement/mechanics/cdg_panel_compression.json'


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def write(path, document):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(document, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')


def snapshot(root):
    return {p.relative_to(root).as_posix(): p.read_bytes() if p.is_file() else None for p in root.rglob('*')}


def replace_jar(path, mutation):
    with zipfile.ZipFile(path) as archive:
        contents = {name: archive.read(name) for name in archive.namelist()}
    mutation(contents)
    with zipfile.ZipFile(path, 'w') as archive:
        for name, raw in contents.items(): archive.writestr(name, raw)


class CdgPanelInstallTests(unittest.TestCase):
    def fixture(self, directory):
        source, instance = directory/'package', directory/'instance'
        for relative in (P.PENDING, P.RECIPE_PATH, P.QUESTS, HELPER,
                         'kubejs/config/aia2_runtime.json', 'kubejs/config/aia2_recipes.json'):
            target = source/relative; target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT/relative, target)
        document = read(ROOT/P.MECHANICS); by_id = {row['id']: row for row in document['rules']}
        document['rules'] = [by_id[ident] for ident in P.BASELINE_HASHES] + [P.extension_rule()]
        write(source/P.MECHANICS, document)
        write(source/ADVANCEMENT, P.ADVANCEMENT)
        runtime = read(source/'kubejs/config/aia2_runtime.json')
        quest = {'id': P.uid(P.QUEST_ID), 'title': 'Реальна партія панелей',
                 'optional': True, 'hide_until_deps_complete': True,
                 'dependencies': [P.uid('V13_E12_cdg_mold_lines'), runtime['epochs'][10]['finalQuestId']],
                 'tasks': [
                     {'id': P.uid(P.QUEST_ID+':task:0'), 'type': 'advancement', 'advancement': 'aia2:mechanics/cdg_panel_compression'},
                     {'id': P.uid(P.QUEST_ID+':task:1'), 'type': 'item',
                      'item': {'id': 'createdieselgenerators:sheet_metal_panel', 'count': 1},
                      'count': 4, 'consume_items': False, 'only_from_crafting': False},
                     {'id': P.uid(P.QUEST_ID+':stage'), 'type': 'advancement', 'advancement': 'aia2:stages/e12'}]}
        write(source/CHAPTER, {'id': 'FFFFFF0014140001', 'quests': [quest]})
        target_jar = source/JAR; target_jar.parent.mkdir(parents=True, exist_ok=True)
        base = next((ROOT/'mods').glob('aia2-machine-guard-*.jar'))
        shutil.copyfile(base, target_jar)
        def pairing_fixture(contents):
            # Preserve the existing full guard class set, but only model the
            # new pairing constants. These bytes do not claim JVM/ABI validity.
            contents.setdefault(HELPER_CLASS, b'pairing-gate-fixture-not-executed-java')
            for marker in (b'createdieselgenerators:compression_molding', b'ua/aia2/guard/CdgPanelAccess'):
                if marker not in contents[BRIDGE_CLASS]: contents[BRIDGE_CLASS] += b'\x00'+marker
        replace_jar(target_jar, pairing_fixture)
        markers = {
            'mods/aia2-machine-guard-old.jar': b'opaque previous owned JAR',
            'mods/foreign.jar': b'opaque foreign mod',
            'kubejs/server_scripts/foreign.js': b'// preserved foreign script\n',
            'saves/preserved/level.dat': b'opaque world',
            'saves/preserved/data/aia2_key_production_v1.dat': b'opaque 96-key journal',
            'saves/preserved/data/aia2_mechanics_v1.dat': b'opaque old mechanical receipts',
            'saves/preserved/data/ftbquests.dat': b'opaque FTB progress',
        }
        for relative, data in markers.items():
            target = instance/relative; target.parent.mkdir(parents=True, exist_ok=True); target.write_bytes(data)
        return source, instance, markers

    def assert_rejected_without_writes(self, source, instance):
        before = snapshot(instance)
        for dry in (False, True):
            with self.subTest(dry=dry), patch.object(installer, '_atomic_write') as atomic:
                with self.assertRaises(installer.InstallError):
                    installer.install(source, instance, dry_run=dry, output=lambda _: None)
                atomic.assert_not_called(); self.assertEqual(snapshot(instance), before)
                self.assertFalse((instance/'aia2-backups').exists())

    def test_valid_json_pair_dryrun_upgrade_repeat_and_opaque_progress(self):
        with tempfile.TemporaryDirectory() as temporary:
            source, instance, markers = self.fixture(Path(temporary))
            source_before = snapshot(source)
            with zipfile.ZipFile(source/JAR) as jar:
                self.assertEqual(installer.validate_panel_production(source, jar)['mechanic_rules'], 17)
            self.assertEqual(snapshot(source), source_before)
            before = snapshot(instance)
            installer.install(source, instance, dry_run=True, output=lambda _: None)
            self.assertEqual(snapshot(instance), before)
            installer.install(source, instance, output=lambda _: None)
            for relative, data in markers.items():
                if relative != 'mods/aia2-machine-guard-old.jar': self.assertEqual((instance/relative).read_bytes(), data)
            self.assertFalse((instance/'mods/aia2-machine-guard-old.jar').exists())
            backups = list((instance/'aia2-backups').rglob('aia2-machine-guard-old.jar'))
            self.assertEqual(len(backups), 1); self.assertEqual(backups[0].read_bytes(), markers['mods/aia2-machine-guard-old.jar'])
            after = snapshot(instance)
            installer.install(source, instance, output=lambda _: None)
            self.assertEqual(snapshot(instance), after)

    def test_real_snbt_flags_counts_and_compiled_prerequisites_pass(self):
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
            (source/CHAPTER).write_text(nbtlib.serialize_tag(tag(read(source/CHAPTER)))+'\n', encoding='utf-8')
            with self.assertRaises(json.JSONDecodeError): read(source/CHAPTER)
            with zipfile.ZipFile(source/JAR) as jar:
                self.assertEqual(installer.validate_panel_production(source, jar)['panel_native_goals'], 1)
            before = snapshot(instance)
            installer.install(source, instance, dry_run=True, output=lambda _: None)
            self.assertEqual(snapshot(instance), before)

    def test_missing_catalog_pending_and_mechanic_activation_cannot_bypass_pairing(self):
        for mutation in ('catalog', 'catalog-and-pending', 'escaped-catalog-and-pending', 'pending', 'helper', 'recipe', 'advancement'):
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as temporary:
                source, instance, _ = self.fixture(Path(temporary))
                if mutation == 'catalog': (source/P.QUESTS).unlink()
                elif mutation in ('catalog-and-pending', 'escaped-catalog-and-pending'):
                    (source/P.QUESTS).unlink(); (source/P.PENDING).unlink()
                    if mutation == 'escaped-catalog-and-pending':
                        path = source/P.MECHANICS
                        path.write_text(path.read_text().replace('"cdg_panel_compression"', '"cdg_\\u0070anel_compression"'))
                else:
                    relative = {'pending': P.PENDING, 'helper': HELPER, 'recipe': P.RECIPE_PATH,
                                'advancement': ADVANCEMENT}[mutation]
                    (source/relative).unlink()
                self.assert_rejected_without_writes(source, instance)

    def test_legacy_sixteen_rule_package_without_v14_markers_has_no_requirement(self):
        with tempfile.TemporaryDirectory() as temporary:
            source, instance, _ = self.fixture(Path(temporary))
            for relative in (P.QUESTS, P.PENDING, HELPER, ADVANCEMENT): (source/relative).unlink()
            document = read(source/P.MECHANICS); document['rules'].pop(); write(source/P.MECHANICS, document)
            replace_jar(source/JAR, lambda entries: entries.pop(HELPER_CLASS))
            self.assertEqual(installer.validate_panel_production(source, None), {'status': 'legacy_package'})
            before = snapshot(instance)
            installer.install(source, instance, dry_run=True, output=lambda _: None)
            self.assertEqual(snapshot(instance), before)

    def test_symlinked_helper_and_helper_parent_are_refused(self):
        for mutation in ('helper', 'parent', 'catalog'):
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as temporary:
                source, instance, _ = self.fixture(Path(temporary))
                if mutation == 'parent':
                    directory = source/'tools'; relocated = source/'tools-original'; directory.rename(relocated); directory.symlink_to(relocated, target_is_directory=True)
                else:
                    original = source/(HELPER if mutation == 'helper' else P.QUESTS)
                    relocated = original.with_name(original.name+'.original'); original.rename(relocated); original.symlink_to(relocated)
                self.assert_rejected_without_writes(source, instance)

    def test_old_helper_or_bridge_pairing_and_bad_jar_are_refused(self):
        for mutation in ('missing-helper', 'missing-serializer', 'missing-reference', 'bad-jar'):
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as temporary:
                source, instance, _ = self.fixture(Path(temporary))
                def change(contents):
                    if mutation == 'missing-helper': contents.pop(HELPER_CLASS)
                    elif mutation == 'missing-serializer': contents[BRIDGE_CLASS] = contents[BRIDGE_CLASS].replace(b'createdieselgenerators:compression_molding', b'changed:serializer')
                    else: contents[BRIDGE_CLASS] = contents[BRIDGE_CLASS].replace(b'ua/aia2/guard/CdgPanelAccess', b'ua/aia2/guard/OldPanelAccess')
                if mutation == 'bad-jar': (source/JAR).write_bytes(b'not a ZIP')
                else: replace_jar(source/JAR, change)
                self.assert_rejected_without_writes(source, instance)

    def test_weak_compiled_native_goal_never_reaches_instance_writes(self):
        mutations = ('missing-goal', 'duplicate-goal', 'missing-proof', 'inventory-proof', 'wrong-count',
                     'legacy-stack', 'extra-stack-key', 'consume', 'integer-false', 'craft-only',
                     'wrong-stage', 'missing-stage', 'missing-parent', 'missing-epoch', 'visible', 'mandatory')
        for mutation in mutations:
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as temporary:
                source, instance, _ = self.fixture(Path(temporary)); document = read(source/CHAPTER)
                quest = document['quests'][0]
                if mutation == 'missing-goal': document['quests'].clear()
                elif mutation == 'duplicate-goal': document['quests'].append(copy.deepcopy(quest))
                elif mutation == 'missing-proof': quest['tasks'].pop(0)
                elif mutation == 'inventory-proof': quest['tasks'][0]['advancement'] = 'minecraft:story/root'
                elif mutation == 'wrong-count': quest['tasks'][1]['count'] = 1
                elif mutation == 'legacy-stack': quest['tasks'][1]['item'] = {'id': 'createdieselgenerators:sheet_metal_panel', 'Count': 1}
                elif mutation == 'extra-stack-key': quest['tasks'][1]['item']['components'] = {}
                elif mutation == 'consume': quest['tasks'][1]['consume_items'] = True
                elif mutation == 'integer-false': quest['tasks'][1]['consume_items'] = 0
                elif mutation == 'craft-only': quest['tasks'][1]['only_from_crafting'] = True
                elif mutation == 'wrong-stage': quest['tasks'][2]['advancement'] = 'aia2:stages/e13'
                elif mutation == 'missing-stage': quest['tasks'].pop()
                elif mutation == 'missing-parent': quest['dependencies'].pop(0)
                elif mutation == 'missing-epoch': quest['dependencies'].pop()
                elif mutation == 'visible': quest['hide_until_deps_complete'] = False
                else: quest['optional'] = False
                write(source/CHAPTER, document); self.assert_rejected_without_writes(source, instance)

    def test_changed_source_rules_guard_or_advancement_are_refused(self):
        for mutation in ('changed-old-rule', 'missing-rule', 'unknown-rule', 'changed-native-rule',
                         'guard-optional', 'progression-legacy', 'future-producer', 'inventory-advancement',
                         'source-inventory', 'source-mandatory'):
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as temporary:
                source, instance, _ = self.fixture(Path(temporary))
                if mutation in ('changed-old-rule', 'missing-rule', 'unknown-rule', 'changed-native-rule'):
                    document = read(source/P.MECHANICS)
                    if mutation == 'changed-old-rule': document['rules'][0]['epoch'] = 1
                    elif mutation == 'missing-rule': document['rules'].pop()
                    elif mutation == 'unknown-rule':
                        extra = copy.deepcopy(document['rules'][-1]); extra['id'] = 'invented'; document['rules'].append(extra)
                    else: document['rules'][-1]['serializer'] = 'create:compacting'
                    write(source/P.MECHANICS, document)
                elif mutation in ('guard-optional', 'progression-legacy', 'future-producer'):
                    path = source/'kubejs/config/aia2_runtime.json'; document = read(path)
                    if mutation == 'guard-optional': document['machineGuard']['mode'] = 'optional'
                    elif mutation == 'progression-legacy': document['progressionVersion'] = 0
                    else: document['itemGates']['createdieselgenerators:mold'] = 13
                    write(path, document)
                elif mutation == 'inventory-advancement':
                    write(source/ADVANCEMENT, {'criteria': {'native_process': {'trigger': 'minecraft:inventory_changed'}}})
                else:
                    document = read(source/P.QUESTS)
                    if mutation == 'source-inventory': document['quests'][0]['tasks'].pop(0)
                    else: document['quests'][0]['required'] = True
                    write(source/P.QUESTS, document)
                self.assert_rejected_without_writes(source, instance)


if __name__ == '__main__':
    unittest.main()
