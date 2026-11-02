"""Describe twelve saved space milestones honestly without changing their tasks.

Apply after the reward policy and before layout. Frozen baseline payloads include
the final approved reward profiles; no intermediate reward exception is accepted.
"""
import copy
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = 'content/audit/v11-space-milestone-presentation.json'
BASELINE = '35a4d5d8ea406a980e3253f814c7ced90e98700a'
OLD_PAYLOAD_SHA256 = {
    'E37_M1': 'fdfa70b3de749f0f60755044e3af2acb03b027aa3fc71e4e72186bfc1d1f093b',
    'E37_M2': '8c77f30fb878033b430bdf412931026dc048f44e69b250a482ea677edaa27bf7',
    'E37_M3': '057b26af3db1dd91dd86e074637cba93cf6a8de50597a6a9ccb68a470e9f81ce',
    'E37_M4': '2e466267ba9a75ff023f64be0343bab82097ca6110114c0e050b5c3efabf9a13',
    'E37_M5': 'cd06799db1d6cc5aa19e3542da8d9369d4114ad4e1e5eec2303af894f4074f97',
    'E37_M6': '44b5e5e1960e4ad52a5c7a6f37a32c4726ffefa5d457d6b8ea6c8f5f8b7f53ad',
    'E38_M1': '322f922ae1c69238512602fa121172742a48a26046978d587051d6bc45fe961c',
    'E38_M2': 'c81403a18f268f485220eb450b9a4e28d98f8e14b74956849c11ac31ae8d6ec4',
    'E38_M3': 'de1088142f510ae7efaf874a1010c7f4bb21b8ee30cf47bd35ce99d990cedae1',
    'E38_M4': 'c6547d70b1958b45eef15547eb899f5b560a4882ac18cc5ba9b102db95cf0ad3',
    'E38_M5': 'dd43af6b228e4cb994124aada8873d77bfcb494cef9da692f8e9ae2666314d06',
    'E38_M6': '6b459d424c372072c1ec79a2a0889e097c276082cf54620c9f73b928e8947c1f',
}


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def canonical(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
                                     separators=(',', ':')).encode()).hexdigest()


def uid(logical):
    return hashlib.sha256(('aia2-runtime-v1:' + logical).encode()).hexdigest()[:12].upper().rjust(16, '0')


def without_coords(payload):
    return {key: copy.deepcopy(value) for key, value in payload.items() if key not in ('x', 'y')}


def source_rows(root=ROOT):
    document = read(Path(root) / SOURCE)
    assert document.get('schema') == 1 and document.get('baseline') == BASELINE, 'Unsupported milestone presentation baseline'
    assert document.get('scope') == 'twelve_existing_base_space_milestones_presentation_only', 'Unreviewed milestone scope'
    assert all(document.get(field) == 0 for field in ('new_quests', 'new_recipes', 'new_items', 'changed_task_payloads', 'changed_reward_payloads')), 'Presentation must not invent content or change saved tasks'
    assert document.get('native_dispatch_tested') is False, 'Presentation cannot certify Minecraft dispatch'
    rows = document.get('quests', [])
    expected = set(OLD_PAYLOAD_SHA256)
    assert len(rows) == 12 and {row.get('logical_id') for row in rows} == expected, 'Exactly twelve distinct base milestones required'
    assert len({row['quest_id'] for row in rows}) == 12, 'Duplicate milestone quest ID'
    for row in rows:
        logical = row['logical_id']; epoch = int(logical[1:3])
        assert row['quest_id'] == uid(logical) and row['epoch'] == epoch, 'Milestone identity changed'
        assert row['chapter'] == f'config/ftbquests/quests/chapters/aia2_epoch_{epoch:02d}.snbt', 'Wrong milestone chapter'
        old = row['old_payload']
        assert old.get('id') == row['quest_id'] and 'x' not in old and 'y' not in old, 'Unstable baseline payload'
        assert row['old_payload_sha256'] == OLD_PAYLOAD_SHA256[logical] == canonical(old), 'Published milestone baseline changed'
        presentation = row.get('new_presentation', {})
        assert set(presentation) == {'title', 'description'}, 'Only title and description can change'
        assert isinstance(presentation['title'], str) and len(presentation['title'].strip()) >= 12, 'Missing Ukrainian milestone title'
        assert isinstance(presentation['description'], list) and len(presentation['description']) >= 3 and all(isinstance(line, str) and len(line.strip()) >= 60 for line in presentation['description']), 'Missing substantive Ukrainian explanation'
        assert presentation['title'] != old['title'] and presentation['description'] != old['description'], 'Milestone presentation was not repaired'
        items = [{'item': task['item']['id'], 'count': task.get('count', 1),
                  'consume_items': task.get('consume_items', False),
                  'only_from_crafting': task.get('only_from_crafting', False)}
                 for task in old['tasks'] if task['type'] == 'item']
        assert row['actual_items'] == items, 'Milestone item/consumption summary differs from saved tasks'
        assert items and all(not item['only_from_crafting'] for item in items), 'Unexpected manufacturing predicate in old milestone'
        scope = 'resource_submission' if all(item['consume_items'] for item in items) else 'inventory_presence'
        assert row['scope'] == scope, 'Milestone claims more than its item tasks prove'
    return rows


def _expected(row, payload):
    current = without_coords(payload)
    protected = {key: value for key, value in current.items() if key not in ('title', 'description')}
    original = {key: value for key, value in row['old_payload'].items() if key not in ('title', 'description')}
    assert protected == original, 'Protected milestone fields changed; presentation migration refused'
    old_presentation = {key: row['old_payload'][key] for key in ('title', 'description')}
    actual = {key: current.get(key) for key in ('title', 'description')}
    assert actual in (old_presentation, row['new_presentation']), 'Milestone presentation no longer matches old or approved new text'
    result = copy.deepcopy(payload)
    result.update(copy.deepcopy(row['new_presentation']))
    return result


def expected_presentation(quest_id, payload, root=ROOT):
    """Compose approved presentation with a saved contract; unknown IDs are unchanged."""
    rows = source_rows(root)
    row = next((row for row in rows if row['quest_id'] == quest_id), None)
    return copy.deepcopy(payload) if row is None else _expected(row, payload)


def _chapters(root, rows):
    chapters = {relative: read(Path(root) / relative) for relative in sorted({row['chapter'] for row in rows})}
    matches = {}
    for relative, chapter in chapters.items():
        for quest in chapter['quests']:
            if quest['id'] in {row['quest_id'] for row in rows}:
                assert quest['id'] not in matches, 'Duplicate compiled milestone ID'
                matches[quest['id']] = (relative, quest)
    assert set(matches) == {row['quest_id'] for row in rows}, 'Missing compiled milestone'
    return chapters, matches


def validate(root=ROOT, compiled=False):
    rows = source_rows(root)
    if compiled:
        _, matches = _chapters(root, rows)
        for row in rows:
            relative, quest = matches[row['quest_id']]
            assert relative == row['chapter'], 'Milestone moved to another chapter'
            assert quest == _expected(row, quest), 'Compiled milestone still has historical misleading presentation'
    return {'status': 'passed', 'milestone_titles_repaired': 12,
            'milestone_descriptions_repaired': 12, 'chapters': 2,
            'changed_task_payloads': 0, 'changed_reward_payloads': 0,
            'changed_dependencies_optional_icons_coordinates': 0,
            'new_quests': 0, 'new_recipes': 0, 'new_items': 0,
            'full_pack_run': False}


def apply(root=ROOT):
    """Validate every target before any write; persist only approved presentation."""
    root = Path(root)
    rows = source_rows(root)
    chapters, matches = _chapters(root, rows)
    edits = []
    for row in rows:
        relative, quest = matches[row['quest_id']]
        assert relative == row['chapter'], 'Milestone moved to another chapter'
        expected = _expected(row, quest)
        if quest != expected: edits.append((relative, quest, expected))
    changed = set()
    for relative, quest, expected in edits:
        before = {key: copy.deepcopy(value) for key, value in quest.items() if key not in ('title', 'description')}
        quest['title'] = expected['title']; quest['description'] = expected['description']
        assert before == {key: value for key, value in quest.items() if key not in ('title', 'description')}
        changed.add(relative)
    for relative in sorted(changed):
        (root / relative).write_text(json.dumps(chapters[relative], ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    report = validate(root, compiled=True)
    report['chapter_files_written'] = len(changed)
    return report


if __name__ == '__main__':
    print(json.dumps(apply(), ensure_ascii=False, indent=2))
