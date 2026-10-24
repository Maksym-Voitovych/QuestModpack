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


def validate_dual_keys(root, rules, bundle, quests):
    """Check the native manufacture protocol, separately from possession tasks."""
    if rules.get('progressionVersion', 3) < 4:
        return {'enabled': False, 'keys': 0}
    epochs = rules['epochs']
    assert len(epochs) == 48, 'Dual-key progression must retain all48epochs'
    protocol = rules.get('dualKeys', [])
    assert len(protocol) == 96, 'Every epoch needs two actual native recipes'
    by_pair = {(r['epoch'], r['branch']): r for r in protocol}
    assert len(by_pair) == len(protocol), 'Duplicate epoch/branch manufacture rule'
    assert len({r['recipeId'] for r in protocol}) == len(protocol), 'Duplicate manufacture recipe ID'
    assert len({r['output'] for r in protocol}) == len(protocol), 'Duplicate branch-key output'
    recipes = {r['id']: r for r in bundle['add']}
    assert len(recipes) == len(bundle['add']), 'Duplicate native recipe ID'
    key_items = {r['output'] for r in protocol}
    allowed = {'minecraft:crafting_shaped', 'create:mixing', 'create:compacting',
               'mekanism:metallurgic_infusing'}
    process_counts = Counter()
    for i, epoch in enumerate(epochs):
        n = i+1
        assert epoch['number'] == n
        assert set(epoch['branchKeys']) == {'tech', 'arcane'}
        assert set(epoch['branchQuestIds']) == {'tech', 'arcane'}
        assert set(epoch['branchKeyQuestIds']) == {'tech', 'arcane'}
        expected_cost = {epoch['branchKeys']['tech']: 1, epoch['branchKeys']['arcane']: 1,
                         epochs[i-1]['key'] if i else 'minecraft:crafting_table': 1}
        assert epoch['transitionCost'] == expected_cost, ('Invalid transition cost', n)
        assert sum(epoch['transitionCost'].values()) == 3
        assert sum(epoch['cost'].values()) == 9, ('Legacy recovery formula changed', n)
        assert epoch['branchKeys']['tech'] != epoch['branchKeys']['arcane']
        for branch in ['tech', 'arcane']:
            spec = by_pair[(n, branch)]
            item = epoch['branchKeys'][branch]
            assert spec['output'] == item
            assert item == f'kubejs:aia2_{branch}_key_{n:02d}'
            assert rules['itemGates'][item] == n
            assert rules['recipeGates'][spec['recipeId']] == n
            entry = recipes[spec['recipeId']]
            recipe = entry['json']
            assert entry['target'] == item and entry['epoch'] == n and entry['category'] == 'dual_key'
            assert spec['serializer'] == recipe['type'] and recipe['type'] in allowed
            process_counts[recipe['type']] += 1
            if recipe['type'] == 'minecraft:crafting_shaped':
                assert n < 4
                result = recipe['result']
                inputs = [ingredient['item'] for ingredient in recipe['key'].values()]
                assert set(''.join(recipe['pattern']))-{' '} == set(recipe['key'])
                assert 1 <= len(recipe['pattern']) <= 3 and all(1 <= len(row) <= 3 for row in recipe['pattern'])
            elif recipe['type'].startswith('create:'):
                assert n >= 4
                assert recipe['type'] == ('create:mixing' if branch == 'tech' else 'create:compacting')
                assert len(recipe['results']) == 1
                result = recipe['results'][0]
                inputs = [ingredient['item'] for ingredient in recipe['ingredients']]
                assert 1 <= len(inputs) <= 9
            else:
                assert branch == 'tech' and n >= 16
                result = recipe['output']
                inputs = [recipe['item_input']['item']]
                assert recipe['item_input']['count'] > 0
                assert recipe['chemical_input']['amount'] > 0 and recipe['chemical_input']['tag'] == 'mekanism:redstone'
                assert recipe['per_tick_usage'] is False
            assert result == {'id': item, 'count': 1}, ('Wrong branch-key output', spec['recipeId'])
            assert not set(inputs)&key_items, ('Branch keys must not manufacture other branch keys', spec['recipeId'])
            assert all(rules['itemGates'][ingredient] <= n for ingredient in inputs), ('Future key ingredient', spec['recipeId'])
            requirements = epoch['branchQuestIds'][branch]
            assert requirements and len(set(requirements)) == len(requirements)
            qid = epoch['branchKeyQuestIds'][branch]
            quest = quests[qid]
            assert set(quest['dependencies']) == set(requirements)
            assert not quest.get('optional') and quest.get('hide_until_deps_complete')
            assert quest['icon']['id'] == item
            adv = f'aia2:production/{branch}_{n:02d}'
            assert len(quest['tasks']) == 1
            assert quest['tasks'][0]['type'] == 'advancement' and quest['tasks'][0]['advancement'] == adv
            proof = read(root/f'kubejs/data/aia2/advancement/production/{branch}_{n:02d}.json')
            assert proof == {'criteria': {'native_manufacture': {'trigger': 'minecraft:impossible'}}}, ('Possession must not grant manufacturing proof', adv)
            # Neither branch may depend on its own manufactured key, its sibling,
            # or the final transition it is meant to unlock.
            forbidden = set(epoch['branchKeyQuestIds'].values())|{epoch['finalQuestId']}
            ancestors = set()
            def collect(node):
                assert node in quests, ('Missing branch quest', n, branch, node)
                if node in ancestors:return
                ancestors.add(node)
                for parent in quests[node].get('dependencies', []):collect(parent)
            for node in requirements:collect(node)
            assert not ancestors&forbidden, ('Manufacture/transition deadlock', n, branch, ancestors&forbidden)
    # No alternative recipe can mint a key without the declared native receipt route.
    for entry in bundle['add']:
        recipe = entry['json']
        for field in ['output', 'outputs', 'result', 'results']:
            values = recipe.get(field, [])
            for value in values if isinstance(values,list) else [values]:
                if isinstance(value,dict) and value.get('id',value.get('item')) in key_items:
                    assert entry['id'] in {r['recipeId'] for r in protocol}, ('Untracked manufacture route', entry['id'])
    return {'enabled': True, 'keys': len(protocol), 'native_processes': dict(process_counts),
            'manufacture_advancements': len(protocol), 'transition_costs_checked': len(epochs)}


def main():
    rules = read(PACK / 'kubejs/config/aia2_runtime.json')
    bundle = read(PACK / 'kubejs/config/aia2_recipes.json')
    assert len(rules['blockGates']) == 16003
    expansion = rules.get('expansionSchema') == 2
    dual = rules.get('progressionVersion', 3) >= 4
    assert len(rules['itemGates']) == 27964 + (390 if dual else 293 if expansion else 48)
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
    elif list((ROOT/'content/quests').glob('v5_*.json')):
        additions = sum(len(read(p)['quests']) for p in (ROOT/'content/quests').glob('v5_*.json'))
        assert len(quests) == 2784 + additions, 'Every reviewed v5 goal must compile once, preserving the v4 baseline'
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
        assert len(groups) == (6 if dual else 5)
        group_ids = {g['id'] for g in groups}
        assert all(read(f)['group'] in group_ids for f in chapters)
        if dual:
            golden = read(ROOT/'content/audit/v3-ids.json')
            preserved = 0
            chapter_ids = {read(f)['id'] for f in chapters}
            for filename, old in golden['chapters'].items():
                assert old['id'] in chapter_ids, ('v3 chapter ID lost', filename)
                for expected in old['quests']:
                    actual = quests[expected['id']]
                    assert [t['id'] for t in actual['tasks']] == expected['tasks'], ('v3 task ID changed', expected['id'])
                    assert [r['id'] for r in actual.get('rewards',[])] == expected['rewards'], ('v3 reward ID changed', expected['id'])
                    preserved += 1
            assert preserved == 2512, ('Wrong v3 preservation baseline', preserved)
            assert len(golden['recipes']) == 283, 'Wrong v3 native-recipe baseline'
            assert set(golden['recipes']) <= {entry['id'] for entry in bundle['add']}, 'An existing v3 native recipe was removed'
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
            for task in quests[qid]['tasks']:
                if task['type']=='item':
                    assert task['item']['id'] in rules['itemGates'], ('Unknown milestone item',qid,task['item'])
                    assert rules['itemGates'][task['item']['id']] <= i+1, ('Future milestone item',i+1,qid,task['item']['id'])
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
    assert len(bundle['add']) == len({r['id'] for r in bundle['add']})
    assert len(bundle['add']) >= (379 if dual else 283 if expansion else 91)
    if not dual:assert len(bundle['add']) == (283 if expansion else 91)
    dual_validation = validate_dual_keys(ROOT,rules,bundle,quests)
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
            assert r['input_items'] and r['output']['count'] > 0
        if entry['id'] == 'aia2:integration/epoch_39':
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
    report['dual_key_validation'] = dual_validation
    report['preserved_v3_quests'] = 2512 if dual else None
    (ROOT / 'implementation/validation-report.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report, indent=2))
    if expansion:
        from validate_expansion import validate
        print(json.dumps(validate(ROOT), ensure_ascii=False, indent=2))
    if list((ROOT/'content/quests').glob('v5_*.json')):
        from validate_v5 import validate as validate_v5
        result = validate_v5(ROOT)
        (ROOT/'implementation/v5-validation-report.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
        print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__': main()
