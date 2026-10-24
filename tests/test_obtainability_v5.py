"""Source audits must not mistake inputs or boss drops for missing craft recipes."""
import unittest
from tools.audit_obtainability_v5 import outputs, loot_items


class ObtainabilityEvidenceTest(unittest.TestCase):
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
