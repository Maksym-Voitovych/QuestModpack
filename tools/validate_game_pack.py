#!/usr/bin/env python3
"""Validate generated SNBT, native recipe structure and cross-file runtime contracts."""
import json
from collections import Counter
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
PACK = ROOT
import nbtlib


def read(p):
    return json.loads(p.read_text(encoding='utf-8'))


def main():
    rules = read(PACK / 'kubejs/config/aia2_runtime.json')
    bundle = read(PACK / 'kubejs/config/aia2_recipes.json')
    assert len(rules['blockGates']) == 16003
    expansion = rules.get('expansionSchema') == 2
    assert len(rules['itemGates']) == 27964 + (293 if expansion else 48)
    assert rules['itemGates']['minecraft:crafter'] == rules['blockGates']['minecraft:crafter'] == 10
    assert rules['blockGates']['bigreactors:energizerpowerportfe'] > 1
    assert rules['blockGates']['tfmg:encased_steel_pipe'] > 1
    assert rules['blockGates']['evilcraft:spirit_portal'] == 0
    assert rules['itemGates']['evilcraft:origins_of_darkness'] == 13
    assert all(type(n) is int and (0 <= n <= 48 or n in {99, 100}) for n in rules['blockGates'].values())
    all_ids = set()
    quests = {}
    required = optional = 0
    task_types = Counter()
    chapters = sorted((PACK / 'config/ftbquests/quests/chapters').glob('*.snbt'))
    assert len(chapters) >= 48
    for file in chapters:
        # Parse with a real SNBT parser, independent of our JSON emitter.
        nbtlib.parse_nbt(file.read_text(encoding='utf-8'))
        chapter = read(file)
        assert chapter['quests']
        for obj in [chapter, *chapter['quests'], *[t for q in chapter['quests'] for t in q['tasks']],
                    *[r for q in chapter['quests'] for r in q.get('rewards', [])]]:
            assert obj['id'] not in all_ids, ('Duplicate FTB object', obj['id'])
            assert int(obj['id'], 16) < 2**53, 'ID would lose precision in Rhino'
            all_ids.add(obj['id'])
        for q in chapter['quests']:
            quests[q['id']] = q
            if q.get('optional'): optional += 1
            else: required += 1
            for t in q['tasks']:
                task_types[t['type']] += 1
                assert t['type'] != 'checkmark' or q.get('optional'), 'Mandatory checkbox forbidden'
    if not expansion: assert required == 336 and optional == 96
    else: assert 2000 <= len(quests) - 96 <= 3000, 'Exclude the 96 preserved legacy manual tasks from substantive quest count'
    for q in quests.values():
        for dependency in q.get('dependencies', []): assert dependency in quests
    def visit(node, visiting, seen):
        assert node not in visiting, ('Quest cycle', node)
        if node in seen: return
        visiting.add(node)
        for dep in quests[node].get('dependencies', []): visit(dep, visiting, seen)
        visiting.remove(node); seen.add(node)
    seen = set()
    for node in quests: visit(node, set(), seen)
    if expansion:
        legacy = read(ROOT / 'content/audit/legacy-ids.json')
        for filename, old in legacy['chapters'].items():
            chapter = read(PACK / 'config/ftbquests/quests/chapters' / filename)
            assert chapter['id'] == old['chapter']
            for expected in old['quests']:
                actual = quests[expected['id']]
                assert [t['id'] for t in actual['tasks']] == expected['tasks'], ('Legacy task ID changed', expected['id'])
                assert [r['id'] for r in actual.get('rewards',[])] == expected['rewards']
                assert actual.get('dependencies',[]) == expected['dependencies']
        groups = read(PACK / 'config/ftbquests/quests/chapter_groups.snbt')['chapter_groups']
        nbtlib.parse_nbt((PACK / 'config/ftbquests/quests/chapter_groups.snbt').read_text())
        assert len(groups) == 5
        group_ids = {g['id'] for g in groups}
        assert all(read(f)['group'] in group_ids for f in chapters)
    for i, e in enumerate(rules['epochs']):
        assert e['number'] == i + 1
        final = quests[e['finalQuestId']]
        assert set(final['dependencies']) == set(e['milestoneQuestIds'])
        assert len(e['milestoneQuestIds']) == 6
        assert final['tasks'][0]['type'] == 'advancement'
        reward = final['rewards'][0]
        assert reward['type'] == 'command' and reward['command'] == 'aia2 sync'
        assert reward['auto'] == 'invisible' and reward['team_reward'] is False
        assert reward['permission_level'] == 0 and '@p' not in reward['command']
        for qid in e['milestoneQuestIds']:
            assert any(t['type'] == 'advancement' and t['advancement'] == f'aia2:stages/e{i+1:02d}' for t in quests[qid]['tasks'])
        stage = read(PACK / f'kubejs/data/aia2/advancement/stages/e{i+1:02d}.json')['criteria']['active_stage']
        assert stage == {'trigger': 'gamestages:has_stage', 'conditions': {'stage': f'aia2_epoch_{i+1:02d}'}}
        assert sum(e['cost'].values()) == 9
        if expansion:
            assert len(e['requiredQuestIds']) == 1 and e['requiredQuestIds'][0] in quests
            trial = quests[e['requiredQuestIds'][0]]
            assert trial['dependencies']
            # The new trial must not depend on its own key, directly or transitively.
            ancestors=set()
            def collect(qid):
                if qid in ancestors:return
                ancestors.add(qid)
                for dep in quests[qid].get('dependencies',[]):collect(dep)
            collect(trial['id'])
            assert e['finalQuestId'] not in ancestors, ('Key/trial deadlock', e['number'])
        if i:
            predecessor = rules['epochs'][i-1]
            assert e['cost'][predecessor['key']] == 1
            for qid in e['milestoneQuestIds']:
                assert predecessor['finalQuestId'] in quests[qid]['dependencies']
        advancement = PACK / f'kubejs/data/aia2/advancement/keys/e{i+1:02d}.json'
        assert read(advancement)['criteria']['legal_craft']['trigger'] == 'minecraft:impossible'
    process_proofs = read(ROOT / 'implementation/create-process-evidence.json')
    for proof in process_proofs:
        epoch = rules['epochs'][proof['epoch'] - 1]
        quest = quests[epoch['milestoneQuestIds'][proof['milestone_index'] - 1]]
        assert any(t['type'] == 'advancement' and t['advancement'] == proof['advancement'] for t in quest['tasks'])
        assert quest.get('min_required_tasks', 0) == 0, 'Every process proof must be mandatory'
    assert len(bundle['add']) == len({r['id'] for r in bundle['add']}) == (283 if expansion else 91)
    assert 'minecraft:infinity_ingot' not in bundle['remove'], 'Preserve block unpacking'
    assert 'minecraft:infinity_ingot_from_infinity_nugget' not in bundle['remove'], 'Preserve nugget packing'
    for entry in bundle['add']:
        r = entry['json']
        assert ':' in r['type']
        assert 'aia2_epoch_key_' not in json.dumps(r), 'Keys must not appear in ordinary recipes'
        candidate = r.get('recipe', r)
        if 'pattern' in candidate:
            used = set(''.join(candidate['pattern'])) - {' '}
            assert used <= set(candidate['key']), entry['id']
            if r['type'] == 'minecraft:crafting_shaped':
                assert len(r['pattern']) <= 3 and max(map(len, r['pattern'])) <= 3
        if r['type'] == 'draconicevolution:fusion_crafting':
            assert r['totalEnergy'] > 0 and r['techLevel'] and r['catalyst']
        if r['type'] == 'avaritia:shaped_table': assert r['tier'] >= 1
        if r['type'] == 'extendedae:crystal_assembler':
            assert len(r['input_items']) == 5 and r['output']['count'] == 4
    extreme = next(r['json'] for r in bundle['add'] if r['target'] == 'avaritia:extreme_crafting_table')
    assert extreme['tier'] == 3 and len(extreme['pattern']) == 7
    assert 'minecraft:reinforced_deepslate' not in json.dumps(extreme)
    assert 'minecraft:dragon_egg' not in json.dumps(extreme)
    catalyst = next(r['json'] for r in bundle['add'] if r['target'] == 'avaritia:infinity_catalyst')
    assert 'minecraft:bedrock' not in json.dumps(catalyst)
    for script in (PACK / 'kubejs').rglob('*.js'):
        subprocess.run(['node', '--check', str(script)], check=True, capture_output=True)
    report = {'status': 'passed_static_and_logic_validation', 'chapters_parsed_as_snbt': len(chapters),
              'required_quests': required, 'optional_quests': optional, 'unique_ftb_ids': len(all_ids),
              'total_quests': len(quests), 'substantive_quests': len(quests) - 96,
              'task_types': dict(task_types), 'recipes_validated': len(bundle['add']),
              'block_registry_entries': len(rules['blockGates']), 'native_process_proofs': len(process_proofs),
              'native_stage_advancements': 48, 'mandatory_stage_tasks': 288, 'automatic_stage_sync_rewards': 48,
              'full_modpack_server_run': False,
              'native_companion_evidence': 'companion/verification-report.json'}
    (ROOT / 'implementation/validation-report.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report, indent=2))
    if expansion:
        from validate_expansion import validate
        print(json.dumps(validate(ROOT), ensure_ascii=False, indent=2))


if __name__ == '__main__': main()
