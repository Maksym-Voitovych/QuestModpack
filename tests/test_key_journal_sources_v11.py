"""Portable journal API evidence; optional exact SDK hashes are reported separately.

The repository distributes small factual records, not Minecraft Java sources.
An absent external SDK does not skip the portable evidence checks or imply that
the upstream source has been verified in that environment.
"""
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import unittest
import zipfile


ROOT = Path(__file__).resolve().parents[1]
FOLDER = ROOT / 'content/research/evidence/key_journal_v11'
SDK_NAME = 'sourcesAndCompiledWithNeoForge_b32b0518e91161afa9605812d7ed9e88514b80ab_output.jar'
SDK_SHA = '8ea65866101d67c9f13c3ff42b8154fb671974da51c1478fd494a145dbccf950'


class KeyJournalSourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = json.loads((FOLDER / 'manifest.json').read_text(encoding='utf-8'))

    def fact_files(self):
        return [(entry, ROOT / entry['path']) for entry in self.manifest['files']]

    def test_portable_four_fact_files_and_proof_space_remain_pinned(self):
        manifest = self.manifest
        self.assertEqual(manifest['schema'], 1)
        self.assertEqual(manifest['topic'], 'key_production_journal_preservation')
        self.assertEqual(manifest['baseline_commit'], '35a4d5d8ea406a980e3253f814c7ced90e98700a')
        self.assertEqual(manifest['baseline_key_bridge_sha256'],
                         'f8a2e293dee2fd0358451a6b3f47768b18d36431aee46f43ecab325e81286abf')
        self.assertEqual((manifest['minecraft'], manifest['neoforge']), ('1.21.1', '21.1.264'))
        self.assertEqual((manifest['data_name'], manifest['existing_schema']), ('aia2_key_production_v1', 1))
        self.assertEqual(manifest['canonical_proof_space'], {
            'epochs': 48, 'branches': ['tech', 'arcane'], 'maximum_canonical_proofs_per_team': 96})
        self.assertIs(manifest['full_modpack_client_tested'], False)
        self.assertEqual(len(manifest['files']), 4)
        self.assertEqual({Path(entry['path']).name for entry in manifest['files']}, {
            'CompoundTagTypes.json', 'DimensionDataStorage.json', 'SavedData.json', 'WorldDataPath.json'})
        self.assertFalse(list(FOLDER.rglob('*.java')), 'API evidence must not distribute full Minecraft source')
        self.assertTrue(manifest['baseline_format_facts'])
        self.assertTrue(manifest['installer_facts'])
        self.assertTrue(manifest['required_validation'])
        for entry, path in self.fact_files():
            with self.subTest(path=entry['path']):
                relative = PurePosixPath(entry['path'])
                self.assertFalse(relative.is_absolute())
                self.assertNotIn('..', relative.parts)
                self.assertEqual(path.parent, FOLDER / 'minecraft_api')
                self.assertEqual(entry['source_kind'], 'minecraft_api_facts')
                self.assertRegex(entry['sha256'], r'^[0-9a-f]{64}$')
                self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), entry['sha256'])

    def test_portable_source_references_are_complete_and_scoped(self):
        references = {}
        for _, path in self.fact_files():
            fact = json.loads(path.read_text(encoding='utf-8'))
            with self.subTest(fact=path.name):
                self.assertEqual((fact['schema'], fact['minecraft'], fact['neoforge']), (1, '1.21.1', '21.1.264'))
                self.assertEqual(fact['source_kind'], 'minecraft_api_facts')
                self.assertEqual((fact['artifact']['filename'], fact['artifact']['sha256']), (SDK_NAME, SDK_SHA))
                self.assertTrue(fact['facts'])
                self.assertTrue(all(isinstance(value, str) and value.strip() for value in fact['facts']))
                self.assertIn('no full proprietary Minecraft source', fact['scope'])
                self.assertTrue(fact['sources'])
                for source in fact['sources']:
                    entry = source['artifact_entry']
                    self.assertRegex(entry, r'^net/minecraft/[A-Za-z0-9_/]+\.java$')
                    self.assertNotIn('..', PurePosixPath(entry).parts)
                    self.assertRegex(source['sha256'], r'^[0-9a-f]{64}$')
                    lines = source['line_references']
                    self.assertTrue(lines)
                    self.assertEqual(lines, sorted(set(lines)))
                    self.assertTrue(all(type(line) is int and line > 0 for line in lines))
                    self.assertNotIn(entry, references, 'source fact entries must not conflict or duplicate')
                    references[entry] = source
        self.assertEqual(len(references), 9)
        self.assertIn('net/minecraft/world/level/storage/DimensionDataStorage.java', references)
        self.assertIn('net/minecraft/world/level/saveddata/SavedData.java', references)
        self.assertIn('net/minecraft/nbt/CompoundTag.java', references)

    def test_external_exact_sdk_source_hashes_when_available(self):
        cache = Path(os.environ.get('GRADLE_USER_HOME', '/workspace/aia2-toolchains/gradle-home'))
        explicit = os.environ.get('AIA2_NEOFORGE_SDK')
        sdk = Path(explicit) if explicit else cache / 'caches/neoformruntime/intermediate_results' / SDK_NAME
        if not sdk.is_file():
            self.assertFalse(explicit, 'An explicitly requested SDK must exist; this is not optional verification')
            print('Key journal upstream verification: NOT RUN (external exact SDK absent); portable fact checks still run')
            return
        self.assertEqual(hashlib.sha256(sdk.read_bytes()).hexdigest(), SDK_SHA)
        count = 0
        with zipfile.ZipFile(sdk) as archive:
            for _, path in self.fact_files():
                fact = json.loads(path.read_text(encoding='utf-8'))
                for source in fact['sources']:
                    with self.subTest(upstream=source['artifact_entry']):
                        raw = archive.read(source['artifact_entry'])
                        self.assertEqual(hashlib.sha256(raw).hexdigest(), source['sha256'])
                        lines = raw.decode('utf-8').splitlines()
                        self.assertLessEqual(max(source['line_references']), len(lines))
                        self.assertTrue(all(lines[line - 1].strip() for line in source['line_references']))
                        count += 1
        self.assertEqual(count, 9)
        print('Key journal upstream verification: exact SDK SHA and all9 referenced Minecraft source hashes PASS; no client runtime claim')


if __name__ == '__main__':
    unittest.main()
