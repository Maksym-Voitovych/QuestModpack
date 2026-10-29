"""Domain regressions for the Moon/Mars ground-bootstrap course."""
import copy
import tempfile
from pathlib import Path
import shutil
import unittest

from tools import validate_ad_astra_course_v6 as course

ROOT = Path(__file__).resolve().parents[1]


class AdAstraCourseTests(unittest.TestCase):
    def setUp(self):
        self.catalog = course.read(ROOT / course.COURSE)
        self.rules = course.read(ROOT / 'kubejs/config/aia2_runtime.json')

    def test_reviewed_ground_bootstrap_and_recipe_facts(self):
        report = course.validate(ROOT, self.catalog, self.rules)
        self.assertEqual(report['quests'], 20)
        self.assertEqual(report['epochs'], [37, 38])
        self.assertEqual(report['frozen_recipe_sources'], 33)
        self.assertGreaterEqual(report['craft_tasks'], 15)
        self.assertEqual(report['cycle_errors'], 0)
        self.assertEqual(report['native_dispatch_fullpack_test'], 'NOT_RUN')

    def test_post_fact_rocket_entry_is_rejected(self):
        changed = copy.deepcopy(self.catalog)
        changed['quests'][0]['after'] = ['E37_M1']
        with self.assertRaisesRegex(AssertionError, 'precede rocket'):
            course.validate(ROOT, changed, self.rules)

    def test_machine_product_cannot_be_labelled_player_crafting(self):
        changed = copy.deepcopy(self.catalog)
        rocket = next(quest for quest in changed['quests'] if quest['id'].endswith('rocket_t1'))
        rocket['tasks'].append({'type': 'item', 'item': 'ad_astra:tier_1_rocket', 'count': 1, 'craft': True})
        with self.assertRaisesRegex(AssertionError, 'Machine output'):
            course.validate(ROOT, changed, self.rules)

    def test_future_reward_route_and_unreachable_parent_are_rejected(self):
        changed = copy.deepcopy(self.rules)
        changed['itemGates']['immersiveengineering:nugget_steel'] = 38
        with self.assertRaisesRegex(AssertionError, 'Future or missing course reward'):
            course.validate(ROOT, self.catalog, changed)
        changed = copy.deepcopy(self.rules)
        changed['dimensionGates']['ad_astra:earth_orbit'] = 38
        with self.assertRaisesRegex(AssertionError, 'Future or missing route'):
            course.validate(ROOT, self.catalog, changed)
        changed = copy.deepcopy(self.catalog)
        changed['quests'][1]['after'] = ['nonexistent:ground_workshop']
        with self.assertRaisesRegex(AssertionError, 'Missing course dependency'):
            course.validate(ROOT, changed, self.rules)

    def test_cycle_and_moon_metal_before_launch_are_rejected(self):
        changed = copy.deepcopy(self.catalog)
        changed['quests'][1]['after'].append(changed['quests'][2]['id'])
        with self.assertRaisesRegex(AssertionError, 'dependency cycle'):
            course.validate(ROOT, changed, self.rules)
        changed = copy.deepcopy(self.catalog)
        moon = next(quest for quest in changed['quests'] if quest['id'].endswith('moon_water'))
        moon['after'] = ['V5_E37_ad_astra_core_ground_workshop']
        with self.assertRaisesRegex(AssertionError, 'automation precedes Desh'):
            course.validate(ROOT, changed, self.rules)

    def test_glacio_dependent_cryo_bootstrap_and_source_drift_are_rejected(self):
        changed = copy.deepcopy(self.catalog)
        cryo = next(quest for quest in changed['quests'] if quest['id'].endswith('cryo_bootstrap'))
        cryo['tasks'].append({'type': 'item', 'item': 'ad_astra:ice_shard', 'count': 1, 'craft': False})
        with self.assertRaisesRegex(AssertionError, 'Glacio-only sample'):
            course.validate(ROOT, changed, self.rules)
        with tempfile.TemporaryDirectory(prefix='aia2-space-course-') as temporary:
            root = Path(temporary)
            needed = [course.COURSE, course.FINDINGS, course.CONTENT_SOURCES, 'kubejs/config/aia2_runtime.json']
            needed += [row['path'] for manifest in [course.read(ROOT / course.FINDINGS), course.read(ROOT / course.CONTENT_SOURCES)] for row in manifest['sources']]
            needed += [path.relative_to(ROOT).as_posix() for path in (ROOT / 'content/quests').glob('*.json')]
            for name in needed:
                target = root / name
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(ROOT / name, target)
            source = root / course.read(ROOT / course.FINDINGS)['sources'][0]['path']
            source.write_text('{}\n')
            with self.assertRaisesRegex(AssertionError, 'Changed course source'):
                course.validate(root)


if __name__ == '__main__':
    unittest.main()
