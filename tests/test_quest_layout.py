"""Coordinate safety and real-graph checks; no Minecraft UI execution claimed."""
import copy
import importlib.util
import json
import math
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('aia2_quest_layout', ROOT/'tools/layout_quests.py')
LAYOUT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(LAYOUT)


def quest(qid, dependencies=(), **values):
    return dict(id=qid, title='Перевірка '+qid, dependencies=list(dependencies),
                tasks=[dict(id=qid+'T', type='item', item=dict(id='minecraft:stone', count=1))],
                rewards=[dict(id=qid+'R', type='xp', xp=2)], **values)


def coordinates(chapter):
    return {q['id']: (q['x'], q['y']) for q in chapter['quests']}


class QuestLayoutUnitTest(unittest.TestCase):
    def test_metrics_detect_actual_crossing_overlap_and_backward_edges(self):
        chapter = dict(quests=[quest('A', x=0, y=0), quest('B', ['A'], x=4, y=4),
                               quest('C', x=0, y=4), quest('D', ['C'], x=4, y=0),
                               quest('E', ['B'], x=4, y=4), quest('F', ['D'], x=2, y=6)])
        metrics = LAYOUT.chapter_metrics(chapter)
        self.assertEqual(metrics['overlaps'], 1)
        self.assertEqual(metrics['crossings'], 2)
        self.assertEqual(metrics['backwards_edges'], 1)
        self.assertEqual(metrics['vertical_edges'], 1)
        self.assertEqual(LAYOUT._totals(iter([metrics, metrics]))['local_edges'], 8)

    def test_diamond_layout_changes_only_coordinates_and_preserves_input(self):
        chapter = dict(id='CHAPTER', filename='diamond', quests=[
            quest('A', x=99, y=-10), quest('B', ['A']), quest('C', ['A']), quest('D', ['B', 'C'])])
        original = copy.deepcopy(chapter)
        after = LAYOUT.layout_chapter(chapter)
        self.assertEqual(chapter, original)
        self.assertEqual(LAYOUT._strip_coordinates(after), LAYOUT._strip_coordinates(original))
        metrics = LAYOUT.chapter_metrics(after)
        self.assertEqual(metrics['overlaps']+metrics['backwards_edges']+metrics['vertical_edges'], 0)
        self.assertEqual(metrics['crossings'], 0)

    def test_long_lines_and_excessive_crossings_are_explicit_review_warnings(self):
        long = LAYOUT.chapter_metrics(dict(quests=[quest('A', x=0, y=0), quest('B', ['A'], x=40, y=0)]))
        self.assertEqual(long['long_edge_limit'], 24)
        self.assertEqual(long['long_edges'], 1)
        self.assertEqual(long['max_edge_length'], 40)
        self.assertIn('long_dependency_lines', long['audit_warnings'])
        left = [quest('L'+str(i), x=0, y=i*2) for i in range(4)]
        right = [quest('R'+str(i), [q['id'] for q in left], x=4, y=i*2) for i in range(4)]
        tangled = LAYOUT.chapter_metrics(dict(quests=left+right))
        self.assertGreater(tangled['crossing_density'], LAYOUT.CROSSING_DENSITY_WARNING)
        self.assertIn('high_crossing_density', tangled['audit_warnings'])

    def test_semantic_hints_order_disconnected_courses_without_changing_dependencies(self):
        chapter = dict(quests=[quest('MAGIC'), quest('MAGIC_END', ['MAGIC']),
                               quest('TECH'), quest('TECH_END', ['TECH'])])
        hints = {qid: dict(epoch=1, zone='magic', logical='A_'+qid) for qid in ('MAGIC', 'MAGIC_END')}
        hints.update({qid: dict(epoch=1, zone='technology', logical='Z_'+qid) for qid in ('TECH', 'TECH_END')})
        result = LAYOUT.layout_chapter(chapter, hints)
        pos = coordinates(result)
        self.assertLess(pos['TECH'][0], pos['MAGIC'][0])
        self.assertEqual(LAYOUT._strip_coordinates(result), chapter)

    def test_layout_is_idempotent_independent_of_input_coordinates_and_list_order(self):
        chapter = dict(quests=[quest('A'), quest('B', ['A']), quest('C', ['A']),
                               quest('D', ['B', 'C']), quest('E')])
        first = LAYOUT.layout_chapter(chapter)
        self.assertEqual(coordinates(first), coordinates(LAYOUT.layout_chapter(first)))
        changed = copy.deepcopy(chapter)
        changed['quests'].reverse()
        for index, q in enumerate(changed['quests']):
            q.update(x=100-index*17, y=-index*19)
        self.assertEqual(coordinates(first), coordinates(LAYOUT.layout_chapter(changed)))

    def test_external_dependencies_are_counted_without_false_coordinate_constraints(self):
        chapter = dict(quests=[quest('A', ['OTHER_CHAPTER']), quest('B', ['A'])])
        after = LAYOUT.layout_chapter(chapter)
        metrics = LAYOUT.chapter_metrics(after)
        self.assertEqual(metrics['external_edges'], 1)
        self.assertEqual(metrics['local_edges'], 1)
        self.assertLess(coordinates(after)['A'][0], coordinates(after)['B'][0])

    def test_large_icons_have_real_clearance(self):
        chapter = dict(default_quest_size=4, quests=[quest('A'), quest('B', ['A']), quest('C', ['A'], size=6)])
        after = LAYOUT.layout_chapter(chapter)
        self.assertEqual(LAYOUT.chapter_metrics(after)['overlaps'], 0)
        self.assertGreaterEqual(coordinates(after)['B'][0]-coordinates(after)['A'][0], 7)

    def test_cycles_duplicates_and_nonfinite_audit_coordinates_fail(self):
        with self.assertRaisesRegex(ValueError, 'cycle'):
            LAYOUT.layout_chapter(dict(quests=[quest('A', ['B']), quest('B', ['A'])]))
        with self.assertRaisesRegex(ValueError, 'Duplicate'):
            LAYOUT.layout_chapter(dict(quests=[quest('A'), quest('A')]))
        with self.assertRaisesRegex(ValueError, 'Non-finite'):
            LAYOUT.chapter_metrics(dict(quests=[quest('A', x=math.nan, y=0)]))

    def test_virtual_transition_edges_position_final_without_changing_real_dependencies(self):
        chapter = dict(quests=[quest('A'), quest('FINAL', ['A']), quest('TECH', ['A']),
                               quest('ARCANE', ['TECH']), quest('TRIAL', ['ARCANE'])])
        hints = {'FINAL': dict(layout_after=['TECH', 'ARCANE', 'TRIAL'])}
        after = LAYOUT.layout_chapter(chapter, hints)
        positions = coordinates(after)
        self.assertTrue(all(positions['FINAL'][0] > positions[qid][0] for qid in ('TECH', 'ARCANE', 'TRIAL')))
        self.assertEqual(next(q for q in after['quests'] if q['id']=='FINAL')['dependencies'], ['A'])
        self.assertEqual(LAYOUT.chapter_metrics(after)['local_edges'], 4)

    def test_optional_leaves_get_a_side_strip_but_prerequisites_stay_in_main_graph(self):
        chapter = dict(quests=[quest('A'), quest('B', ['A']), quest('SIDE', ['A']), quest('SIDE2', ['A'])])
        hints = {qid: dict(side_optional=True) for qid in ('SIDE', 'SIDE2')}
        after = LAYOUT.layout_chapter(chapter, hints)
        pos = coordinates(after)
        self.assertEqual(pos['SIDE'][1], pos['SIDE2'][1])
        self.assertLess(pos['SIDE'][1], min(pos['A'][1], pos['B'][1]))
        self.assertNotEqual(pos['SIDE'][0], pos['SIDE2'][0])
        revised = copy.deepcopy(chapter)
        revised['quests'].append(quest('LATER', ['SIDE']))
        checked = LAYOUT.layout_chapter(revised, hints)
        self.assertLess(coordinates(checked)['SIDE'][0], coordinates(checked)['LATER'][0])

    def test_apply_preserves_all_containers_and_only_writes_coordinates(self):
        with tempfile.TemporaryDirectory(prefix='aia2-layout-test-') as temp:
            root = Path(temp)
            target = root/'config/ftbquests/quests/chapters'
            target.mkdir(parents=True)
            original = dict(id='UNCHANGED', filename='foreign_container', custom_setting=True,
                            quests=[quest('A'), quest('B', ['A'])])
            path = target/'foreign_container.snbt'
            path.write_text(json.dumps(original), encoding='utf-8')
            sentinel = root/'world/ftbquests/progress.snbt'
            sentinel.parent.mkdir(parents=True)
            sentinel.write_text('PLAYER PROGRESS', encoding='utf-8')
            before_bytes = path.read_bytes()
            preview = LAYOUT.preview(root)
            self.assertFalse(preview['applied'])
            self.assertEqual(path.read_bytes(), before_bytes)
            report = LAYOUT.apply(root)
            self.assertTrue(report['applied'])
            self.assertEqual(sorted(p.name for p in target.iterdir()), ['foreign_container.snbt'])
            self.assertEqual(LAYOUT._strip_coordinates(json.loads(path.read_text())), original)
            self.assertEqual(sentinel.read_text(), 'PLAYER PROGRESS')
            self.assertEqual(report['after']['local_edges'], 1)


class CompleteQuestLayoutTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.metadata = LAYOUT.load_metadata(ROOT)
        cls.chapters = {p.name: json.loads(p.read_text(encoding='utf-8'))
                        for p in sorted((ROOT/'config/ftbquests/quests/chapters').glob('*.snbt'))}
        cls.after = {name: LAYOUT.layout_chapter(chapter, cls.metadata) for name, chapter in cls.chapters.items()}

    def test_every_current_chapter_and_all_quest_data_survive(self):
        self.assertGreaterEqual(len(self.after), 130)
        self.assertEqual(set(self.chapters), set(self.after))
        self.assertGreaterEqual(sum(len(c['quests']) for c in self.after.values()), 2784)
        for name in self.chapters:
            with self.subTest(chapter=name):
                self.assertEqual(LAYOUT._strip_coordinates(self.chapters[name]), LAYOUT._strip_coordinates(self.after[name]))

    def test_all_real_local_dependencies_are_strictly_left_to_right_without_overlap(self):
        for name, chapter in self.after.items():
            with self.subTest(chapter=name):
                metrics = LAYOUT.chapter_metrics(chapter)
                self.assertEqual(metrics['overlaps'], 0)
                self.assertEqual(metrics['backwards_edges'], 0)
                self.assertEqual(metrics['vertical_edges'], 0)

    def test_all_48_visual_finals_follow_both_manufacture_nodes_and_trials(self):
        runtime = json.loads((ROOT/'kubejs/config/aia2_runtime.json').read_text())
        self.assertEqual(len(runtime['epochs']), 48)
        for epoch in runtime['epochs']:
            chapter = self.after[f"aia2_epoch_{epoch['number']:02d}.snbt"]
            positions = coordinates(chapter)
            for gate in list(epoch['branchKeyQuestIds'].values())+epoch.get('requiredQuestIds', []):
                with self.subTest(epoch=epoch['number'], gate=gate):
                    self.assertGreater(positions[epoch['finalQuestId']][0], positions[gate][0])

    def test_every_current_chapter_repeats_identical_coordinates(self):
        for name, chapter in self.after.items():
            with self.subTest(chapter=name):
                again = LAYOUT.layout_chapter(chapter, self.metadata)
                self.assertEqual(coordinates(chapter), coordinates(again))


if __name__ == '__main__':
    unittest.main()
