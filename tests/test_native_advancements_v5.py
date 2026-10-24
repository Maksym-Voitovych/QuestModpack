"""An action quest must retain a mandatory, version-pinned native proof."""
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from tools import validate_native_advancements_v5 as V


class NativeActionContractTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.record = {'id': 'V5_ACTION', 'epoch': 7, 'tasks': [
            {'type': 'advancement', 'advancement': 'example:ritual'}]}
        self.contract = {'id': 'example:ritual', 'epoch': 7, 'mod_id': 'example',
                         'installed_version': '1.0', 'json_path': 'proof/ritual.json',
                         'required_action_triggers': ['example:ritual'],
                         'expected_conditions': {'example:ritual': {'ritual_id': 'example:binding'}},
                         'proof_scope_uk': 'Завершення конкретного нативного ритуалу на сервері, а не отримання предмета.'}
        self.advancement = {'criteria': {'action': {'trigger': 'example:ritual',
                            'conditions': {'ritual_id': 'example:binding'}}}}
        self.sources = {'proof/Trigger.java': 'class Trigger { void completed() {} }',
                        'proof/version.properties': 'mod_version=1.0'}

    def write(self):
        for path, text in self.sources.items():
            target = self.root/path; target.parent.mkdir(parents=True, exist_ok=True); target.write_text(text)
        self.contract['sources'] = [{'path': path, 'sha256': hashlib.sha256(text.encode()).hexdigest()} for path,text in self.sources.items()]
        path = self.root/self.contract['json_path']; path.parent.mkdir(parents=True,exist_ok=True)
        data = (json.dumps(self.advancement)+'\n').encode(); path.write_bytes(data)
        self.contract['json_sha256'] = hashlib.sha256(data).hexdigest()
        target = self.root/V.CONTRACT; target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps({'schema': 1, 'advancements': [self.contract]}))

    def validate(self):
        return V.validate(self.root, [self.record], {}, {'example': '1.0'})

    def test_native_action_with_and_inventory_is_valid(self):
        self.advancement['criteria']['material'] = {'trigger': 'minecraft:inventory_changed'}
        self.write()
        self.assertEqual(self.validate()['native_action_quests'], 1)

    def test_or_inventory_fallback_cannot_prove_action(self):
        self.advancement['criteria']['material'] = {'trigger': 'minecraft:inventory_changed'}
        self.advancement['requirements'] = [['action', 'material']]
        self.write()
        with self.assertRaisesRegex(AssertionError, 'bypass the native action'): self.validate()

    def test_changed_conditions_and_passive_trigger_are_rejected(self):
        self.advancement['criteria']['action']['conditions']['ritual_id'] = 'example:other'
        self.write()
        with self.assertRaisesRegex(AssertionError, 'declared action'): self.validate()
        self.contract['required_action_triggers'] = ['minecraft:inventory_changed']; self.write()
        with self.assertRaisesRegex(AssertionError, 'Passive or foreign'): self.validate()

    def test_version_hash_and_portability_are_required(self):
        self.write(); self.contract['installed_version'] = '0.9'; self.write()
        with self.assertRaisesRegex(AssertionError, 'version mismatch'): self.validate()
        self.contract['installed_version'] = '1.0'; self.write()
        (self.root/'proof/Trigger.java').write_text('changed')
        with self.assertRaisesRegex(AssertionError, 'Stale native'): self.validate()
        self.write()
        document = json.loads((self.root/V.CONTRACT).read_text())
        document['advancements'][0]['json_path'] = '../outside.json'
        (self.root/V.CONTRACT).write_text(json.dumps(document))
        with self.assertRaisesRegex(AssertionError, 'Nonportable'): self.validate()

    def test_future_and_unreviewed_actions_are_rejected(self):
        self.write(); self.record['epoch'] = 6
        with self.assertRaisesRegex(AssertionError, 'future native action'): self.validate()
        self.record['epoch'] = 7; self.record['tasks'][0]['advancement'] = 'example:unknown'
        with self.assertRaisesRegex(AssertionError, 'unreviewed native'): self.validate()

    def test_dependency_trigger_requires_its_own_installed_version(self):
        self.contract['required_action_triggers'] = ['core:configured']
        self.contract['expected_conditions'] = {}
        self.advancement = {'criteria': {'action': {'trigger':'core:configured'}}}
        self.write()
        with self.assertRaisesRegex(AssertionError, 'Passive or foreign'): self.validate()
        self.contract['trigger_mod_versions'] = {'core':'2.0'}; self.write()
        self.assertEqual(V.validate(self.root,[self.record],{}, {'example':'1.0','core':'2.0'})['native_action_quests'],1)
        with self.assertRaisesRegex(AssertionError, 'owner version mismatch'):
            V.validate(self.root,[self.record],{}, {'example':'1.0','core':'2.1'})

    def test_impossible_needs_exact_reviewed_direct_grant(self):
        self.contract['required_action_triggers'] = ['minecraft:impossible']
        self.contract['expected_conditions'] = {}
        self.advancement = {'criteria': {'triggered_in_code': {'trigger': 'minecraft:impossible'}}}
        self.write()
        with self.assertRaisesRegex(AssertionError, 'Passive or foreign'): self.validate()
        text = 'if (validStructure) grant("example:ritual", "triggered_in_code");'
        self.sources['proof/Grant.java'] = text
        self.contract.update(dispatch_mode='direct_native_grant', direct_grant={
            'path': 'proof/Grant.java', 'sha256': hashlib.sha256(text.encode()).hexdigest(),
            'required_source_tokens': ['example:ritual', 'triggered_in_code', 'validStructure']})
        self.write()
        self.assertEqual(self.validate()['direct_native_grants'], 1)
        self.contract['direct_grant']['required_source_tokens'][2] = 'anotherCondition'; self.write()
        with self.assertRaisesRegex(AssertionError, 'source contract changed'): self.validate()

    def test_custom_runtime_json_must_match_and_unused_contracts_fail(self):
        self.contract['id'] = 'aia2:rituals/binding'; self.record['tasks'][0]['advancement'] = self.contract['id']; self.write()
        with self.assertRaisesRegex(AssertionError, 'differs from reviewed'): self.validate()
        path = self.root/'kubejs/data/aia2/advancement/rituals/binding.json'; path.parent.mkdir(parents=True)
        path.write_bytes((self.root/self.contract['json_path']).read_bytes())
        self.assertEqual(self.validate()['native_action_quests'], 1)
        self.record['tasks'] = []
        with self.assertRaisesRegex(AssertionError, 'Unused native action'): self.validate()
