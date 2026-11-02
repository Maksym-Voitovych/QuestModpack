"""Explicit overlay for existing NASA goals and independent space action gates.

No historical task is replaced: FTB stores progress by task ID without a type
marker, so possession progress must never be reinterpreted as native production.
The Java receipt gate is authoritative; this module only compiles/validates its
visible FTB requirements and matching two-epoch runtime declaration.
"""
import copy
import hashlib
import json
from pathlib import Path

try:
    from . import build_nasa_process_v7 as nasa
except ImportError:
    import build_nasa_process_v7 as nasa

ROOT = Path(__file__).resolve().parents[1]
MIGRATION = 'content/audit/v10-space-required-migration.json'
OVERLAYS = 'content/audit/v5-quest-content-migrations.json'
RUNTIME = 'kubejs/config/aia2_runtime.json'
EXPECTED = {37: {'tech': ['nasa_tier_1_rocket', 'nasa_tier_2_rocket'], 'arcane': []},
            38: {'tech': ['nasa_tier_3_rocket', 'nasa_tier_4_rocket'], 'arcane': []}}


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def canonical(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
                                     separators=(',', ':')).encode()).hexdigest()


def uid(logical):
    return hashlib.sha256(('aia2-runtime-v1:' + logical).encode()).hexdigest()[:12].upper().rjust(16, '0')


def link_current_promoted(quests, records, root=ROOT):
    """A globally required earlier-stage prerequisite must also gate its own epoch.

    A later NASA course can mark an earlier optional goal required. Link only
    missing current-epoch prerequisites to the terminal trial, never to one of
    their parent milestones. Existing dependencies and all task data are retained.
    """
    migration = read(Path(root) / MIGRATION)
    epochs = {uid(record['id']): record['epoch'] for record in records}
    changed = set()
    for epoch in EXPECTED:
        trial = quests[uid(f'E{epoch:02d}_EXPANSION_TRIAL')]
        ancestors = set()
        def visit(ident):
            if ident in ancestors: return
            ancestors.add(ident)
            for parent in quests[ident].get('dependencies', []): visit(parent)
        visit(trial['id'])
        for ident in migration['promoted_compiled_quest_ids']:
            if epochs.get(ident) == epoch and ident not in ancestors:
                trial['dependencies'].append(ident)
                visit(ident)
                changed.add(epoch)
    return sorted(changed)


def validate(root=ROOT, migration=None, runtime=None, compiled=False):
    root = Path(root)
    migration = copy.deepcopy(migration if migration is not None else read(root / MIGRATION))
    runtime = runtime if runtime is not None else read(root / RUNTIME)
    assert migration.get('schema') == 1, 'Unsupported required-space migration schema'
    assert migration.get('scope') == 'four_existing_nasa_goals_required_for_new_space_transitions_without_replacing_tasks', 'Unreviewed required-space scope'
    assert migration.get('new_quests') == migration.get('new_recipes') == 0, 'Space overlay must reuse existing goals and recipes'
    assert migration.get('native_dispatch_tested') is False, 'Source validation cannot claim native dispatch'
    evidence = migration.get('ftb_progress_evidence', {})
    assert evidence.get('path') == 'content/research/evidence/required_space_v10/ftbquests/task-progress-facts.json', 'Missing FTB migration evidence'
    facts_raw = (root / evidence['path']).read_bytes()
    assert hashlib.sha256(facts_raw).hexdigest() == evidence.get('sha256'), 'Changed FTB migration evidence'
    facts = json.loads(facts_raw)
    assert facts.get('installed_version') == '2101.1.36' and facts.get('source_commit') == '8c53f35a97d8897c861b097f1e39f4fc3beb3a15', 'Unreviewed FTB progress version'
    assert migration.get('pending_policy') == {
        'old_without_pendingActionContract': 'grandfather_already_paid_transition',
        'new_space_pendingActionContract': 1,
        'completed_epochs_and_recovery': 'unchanged'}, 'Unsupported pending compatibility policy'
    assert migration.get('branch_action_proofs') == {str(k): v for k, v in EXPECTED.items()}, 'Wrong required-space proof mapping'
    assert migration.get('raw_catalog') == nasa.QUESTS, 'Wrong raw NASA catalog'
    raw = (root / nasa.QUESTS).read_bytes()
    assert hashlib.sha256(raw).hexdigest() == migration.get('raw_catalog_sha256'), 'Published raw NASA catalog changed'
    catalog = {q['id']: q for q in json.loads(raw)['quests']}
    rows = migration.get('quests', [])
    expected_ids = {f'V7_E{37 if tier < 3 else 38}_nasa_manufacture_t{tier}' for tier in range(1, 5)}
    assert len(rows) == 4 and {row['quest_id'] for row in rows} == expected_ids, 'Exactly four existing NASA migrations required'
    assert len({row['compiled_id'] for row in rows}) == 4, 'Duplicate compiled NASA ID'
    overlays = read(root / OVERLAYS)
    assert overlays.get('schema') == 1, 'Unsupported quest overlay schema'
    owned = [row for row in overlays['quests'] if row.get('source_audit') == MIGRATION]
    assert len(owned) == 4 and {row['id'] for row in owned} == expected_ids, 'Missing or duplicate required-space overlay'
    by_overlay = {row['id']: row for row in owned}
    # Reuse the exact installed recipe hashes, fourteen input order, available
    # alternative-tag witnesses and existing fifteen-rule production contract.
    nasa_report = nasa.validate(root, runtime=runtime, compiled=compiled)
    mechanics = {r['id']: r for r in read(root / nasa.MECHANICS)['rules']}
    for row in rows:
        quest = catalog[row['quest_id']]
        assert canonical(quest) == row['raw_quest_sha256'], 'Published NASA goal changed'
        epoch, tier = quest['epoch'], int(row['quest_id'][-1])
        proof = f'nasa_tier_{tier}_rocket'
        assert row['epoch'] == epoch and row['native_proof_id'] == proof and proof in EXPECTED[epoch]['tech'], 'Wrong NASA epoch or proof'
        assert row['compiled_id'] == uid(row['quest_id']), 'Unstable compiled NASA ID'
        assert quest['required'] is False, 'Raw historical NASA requirement must remain unchanged'
        overlay = by_overlay[row['quest_id']]
        assert overlay.get('requirement_change') == {'from': False, 'to': True}, 'Missing exact false-to-true requirement migration'
        assert overlay.get('item_targets') == [] and not overlay.get('presentation_changes'), 'Space migration must not replace old tasks or presentation'
        note = row['description_note_uk']
        assert overlay.get('description_note_uk') == note and len(note) >= 200, 'Missing exact compatibility explanation'
        rule = mechanics[proof]
        assert rule['epoch'] == epoch and rule['serializer'] == 'ad_astra:nasa_workbench', 'Required native recipe is unavailable in this epoch'
        assert row['old_compiled_payload']['id'] == uid(row['quest_id']) and row['old_compiled_payload']['optional'] is True, 'Invalid previous compiled NASA payload'
    for epoch in runtime['epochs']:
        number = epoch['number']
        if number in EXPECTED:
            if compiled or 'branchActionProofs' in epoch:
                assert epoch.get('branchActionProofs') == EXPECTED[number], 'Missing or changed required-space runtime mapping'
        else:
            assert 'branchActionProofs' not in epoch, 'Space overlay must not modify the other forty-six epochs'
    if compiled:
        chapters = list((root / 'config/ftbquests/quests/chapters').glob('*.snbt'))
        assert chapters, 'Compiled space quests are missing'
        quests = {q['id']: q for path in chapters for q in read(path)['quests']}
        unchanged = migration.get('legacy_passthrough_payloads', [])
        assert {q['id'] for q in unchanged} == {uid('E37_M6'), uid('E37_KEY')}, 'Missing legacy passthrough contract'
        for expected in unchanged:
            actual = copy.deepcopy(quests[expected['id']])
            actual.pop('x', None); actual.pop('y', None)
            if (root/'content/audit/v11-space-milestone-presentation.json').exists():
                try:
                    from build_space_milestones_v11 import expected_presentation
                except ImportError:
                    from tools.build_space_milestones_v11 import expected_presentation
                expected = expected_presentation(expected['id'], expected, root)
            assert actual == expected, 'Unrelated legacy space quest changed during terminal link update'
        for row in rows:
            actual = copy.deepcopy(quests[row['compiled_id']])
            actual.pop('x', None); actual.pop('y', None)
            expected = copy.deepcopy(row['old_compiled_payload'])
            expected['optional'] = False
            expected['description'].append(row['description_note_uk'])
            assert actual == expected, 'Compiled NASA migration changed a task, ID, reward or dependency'
            assert row['compiled_id'] in runtime['epochs'][row['epoch'] - 1]['branchQuestIds']['tech'], 'Required NASA goal missing from technology key closure'
            assert row['compiled_id'] not in runtime['epochs'][row['epoch'] - 1]['branchQuestIds']['arcane'], 'NASA goal moved to magic branch'
            trial = quests[uid(f"E{row['epoch']:02d}_EXPANSION_TRIAL")]
            assert row['compiled_id'] in trial['dependencies'], 'NASA goal missing from final trial'
        promoted = migration.get('promoted_compiled_quest_ids', [])
        assert len(promoted) == len(set(promoted)) == 21, 'Wrong historical optional-to-required closure'
        assert {row['compiled_id'] for row in rows} <= set(promoted), 'Missing direct NASA promotions'
        for ident in promoted:
            assert quests[ident].get('optional') is False, 'NASA prerequisite remains optional'
        authored_epochs = {}
        for path in (root / 'content/quests').glob('*.json'):
            data = read(path)
            for quest in data if isinstance(data, list) else data['quests']:
                authored_epochs[uid(quest['id'])] = quest['epoch']
        for ident in promoted:
            epoch = authored_epochs[ident]
            assert ident in (runtime['epochs'][epoch - 1]['branchQuestIds']['tech'] +
                             runtime['epochs'][epoch - 1]['branchQuestIds']['arcane']), \
                'Promoted current-epoch prerequisite missing from its own key contract'
        station = read(root / 'content/quests/v5_station_construction.json')['quests']
        assert len(station) == 6
        for quest in station:
            assert quest['required'] is False and quests[uid(quest['id'])].get('optional') is True, 'Station construction must remain optional'
        # Current-stage reachability is checked independently from the layout.
        active, done = set(), set()
        def visit(ident):
            assert ident not in active, 'Required-space dependency cycle'
            if ident in done: return
            assert ident in quests, 'Missing required-space dependency'
            active.add(ident)
            for parent in quests[ident].get('dependencies', []): visit(parent)
            active.remove(ident); done.add(ident)
        for row in rows: visit(row['compiled_id'])
    return {'status': 'passed', 'migrated_existing_nasa_goals': 4,
            'promoted_required_prerequisite_closure': 21, 'new_quests': 0,
            'new_recipes': 0, 'replaced_tasks': 0, 'old_task_ids_preserved': True,
            'old_rewards_preserved': True, 'station_goals_still_optional': 6,
            'space_action_epochs': [37, 38], 'unchanged_other_epoch_action_contracts': 46,
            'nasa_recipe_input_alternatives': nasa_report['nasa_recipe_input_alternatives'],
            'native_dispatch_fullpack': 'NOT_RUN'}


def apply(root=ROOT):
    root = Path(root)
    runtime = read(root / RUNTIME)
    # Validate all source contracts before making the only generated write.
    report = validate(root, runtime=runtime)
    for epoch in runtime['epochs']:
        if epoch['number'] in EXPECTED:
            epoch['branchActionProofs'] = copy.deepcopy(EXPECTED[epoch['number']])
    (root / RUNTIME).write_text(json.dumps(runtime, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return report


if __name__ == '__main__':
    print(json.dumps(apply(), ensure_ascii=False, indent=2))
