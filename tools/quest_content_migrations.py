"""Narrow, documented item-target repairs without changing persistent quest IDs."""
import copy
import json
from pathlib import Path

MIGRATIONS = 'content/audit/v5-quest-content-migrations.json'


def apply(records, root):
    result = copy.deepcopy(records)
    path = Path(root)/MIGRATIONS
    if not path.is_file():
        return result
    document = json.loads(path.read_text(encoding='utf-8'))
    assert document.get('schema') == 1, 'Unsupported quest content migration'
    by_id = {q['id']: q for q in result}
    seen = set()
    for migration in document.get('quests', []):
        identifier = migration['id']
        assert identifier in by_id and identifier not in seen, ('Missing/duplicate migrated quest', identifier)
        seen.add(identifier)
        assert len(migration.get('reason_uk', '').strip()) >= 30, ('Undocumented item-target repair', identifier)
        quest = by_id[identifier]
        for operation in migration['item_targets']:
            index = operation['task_index']
            assert type(index) is int and 0 <= index < len(quest['tasks']), ('Invalid migrated task index', identifier)
            task = quest['tasks'][index]
            assert task.get('type') == 'item' and task.get('item') == operation['from'], ('Quest target migration no longer matches its source', identifier)
            task['item'] = operation['to']
            quest['description_uk'] = [line.replace(operation['from'], operation['to']) for line in quest['description_uk']]
        if migration.get('description_note_uk'):
            quest['description_uk'].append(migration['description_note_uk'])
    return result
