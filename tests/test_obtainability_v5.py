"""Source audits must not mistake inputs or boss drops for missing craft recipes."""
import unittest
import json
import hashlib
from pathlib import Path
import tempfile
from tools.audit_obtainability_v5 import outputs, loot_items, source_context
from tools.item_normalization import normalize
from tools.build_expansion import compile_description


class ObtainabilityEvidenceTest(unittest.TestCase):
    def test_confirmed_duplicate_materials_use_real_exported_canonical_outputs(self):
        self.assertEqual(normalize('enderio:powdered_obsidian'), 'create:powdered_obsidian')
        self.assertEqual(normalize('oritech:nickel_ingot'), 'immersiveengineering:ingot_nickel')
        self.assertEqual(normalize('E25_X_nickel'), 'E25_X_nickel', 'Persistent IDs must never be normalized')
        record = {'description_uk': ['16 × oritech:nickel_ingot — мати в інвентарі.']}
        migration = {'from': 'oritech:nickel_ingot', 'to': 'immersiveengineering:ingot_nickel',
                     'description_note_uk': 'Канонічний злиток збірки.'}
        self.assertEqual(compile_description(record, migration),
                         ['16 × immersiveengineering:ingot_nickel — мати в інвентарі.', migration['description_note_uk']])
        self.assertIn('oritech:nickel_ingot', record['description_uk'][0], 'Authored catalogs stay unchanged')
    def test_input_and_native_metadata_are_never_counted_as_outputs(self):
        recipe={'type':'example:machine','ingredients':[{'item':'example:input'}],
                'output':{'id':'example:product','count':1},'fluid_input':{'id':'example:fluid'}}
        self.assertEqual(set(outputs(recipe)), {'example:product'})

    def test_wrapped_outputs_and_special_machine_fields_are_supported(self):
        recipe={'type':'example:wrapper','base':{'type':'example:machine',
                'main_output':{'id':'example:main'},'secondary_output':{'item':'example:bonus'}}}
        self.assertEqual(set(outputs(recipe)), {'example:main','example:bonus'})

    def test_boss_loot_is_evidence_not_an_ingredient_or_a_recipe_request(self):
        table={'pools':[{'entries':[{'type':'minecraft:item','name':'example:boss_drop'}],
                         'conditions':[{'condition':'minecraft:killed_by_player'}]}]}
        self.assertEqual(set(loot_items(table)), {'example:boss_drop'})
        self.assertEqual(set(outputs(table)), set())

    def test_amadron_and_sag_nested_outputs_do_not_include_inputs(self):
        recipe={'input':{'resource':{'id':'minecraft:emerald'}},
                'output':{'resource':{'id':'pneumaticcraft:pcb_blueprint'}}}
        self.assertEqual(set(outputs(recipe)), {'pneumaticcraft:pcb_blueprint'})
        self.assertEqual(set(outputs({'outputs':[{'item':{'id':'create:powdered_obsidian'}}]})), {'create:powdered_obsidian'})
        self.assertEqual(set(outputs({'baseRecipe':{'result':{'id':'immersiveengineering:survey_tools'}}})), {'immersiveengineering:survey_tools'})
        self.assertEqual(set(outputs({'byproducts':[{'output':{'id':'immersivepetroleum:bitumen'}}],
                                      'ingredients':[{'item':'example:input'}]})), {'immersivepetroleum:bitumen'})
        self.assertEqual(set(outputs({'outputs':[{'stack':{'id':'apotheosis:arcane_sands'}}]})), {'apotheosis:arcane_sands'})
        self.assertEqual(set(outputs({'effectConfig':{'result':{'id':'rootsclassic:living_pickaxe'}}})), {'rootsclassic:living_pickaxe'})

    def test_native_classification_requires_matching_version_and_unchanged_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/'design').mkdir();(root/'content/audit').mkdir(parents=True)
            (root/'design/mod-catalog.json').write_text(json.dumps({'mods':[{'exported_metadata':[{'id':'example','version':'1.0'}]}]}))
            (root/'content/audit/registries.json').write_text(json.dumps({'registries':{'item':['example:drop']}}))
            proof=root/'proof.java';proof.write_text('native_drop();')
            data={'schema':1,'items':[{'item':'example:drop','installed_version':'1.0','status':'source_verified_native_path',
                  'sources':[{'path':'proof.java','sha256':hashlib.sha256(proof.read_bytes()).hexdigest(),'version_match':True}]}]}
            path=root/'content/audit/v5-source-gaps-test.json';path.write_text(json.dumps(data))
            self.assertIn('example:drop',source_context(root))
            data['items'][0]['installed_version']='0.9';path.write_text(json.dumps(data))
            with self.assertRaisesRegex(AssertionError,'version mismatch'):source_context(root)
            data['items'][0]['installed_version']='1.0';path.write_text(json.dumps(data));proof.write_text('changed();')
            with self.assertRaisesRegex(AssertionError,'Stale native evidence'):source_context(root)
