#!/usr/bin/env python3
"""Independent, read-only validation of v5 authored content and migration safety.

Counts describe files actually present. Research maps can document gaps; only
claims marked verified require portable, hash-matched evidence. No Minecraft
runtime or TPS certification is inferred from these static checks.
"""
from collections import Counter
import hashlib
import importlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
HEX = re.compile(r'^[0-9A-Fa-f]{16}$')
SHA = re.compile(r'^[0-9a-f]{64}$')
UK = re.compile(r'[А-Яа-яІіЇїЄєҐґ]')
MACHINE = re.compile(r'(?:^|_)(?:generator|reactor|machine|furnace|infuser|assembler|quarry|miner|crusher|smelter|compressor|controller|workbench|altar|apothecary|spawner|jetpack|creative|press|mixer|millstone|deployer|drill|saw|basin)(?:_|$)')
MECHANIC_CONTRACT = {
    'andesite_mixing': (4, 'create:mixing', 'create:andesite_alloy',
                        {'create:mixing/andesite_alloy', 'create:mixing/andesite_alloy_from_zinc'}),
    # The heated native route needs a Blaze Burner (epoch15). The existing
    # mana-assisted unheated bootstrap is the attainable epoch10 route.
    'brass_mixing': (10, 'create:mixing', 'create:brass_ingot',
                      {'create:mixing/brass_ingot', 'aia2:bootstrap/epoch_10_1'}),
    'infused_alloy': (16, 'mekanism:metallurgic_infusing', 'mekanism:alloy_infused',
                      {'mekanism:metallurgic_infusing/alloy/infused'}),
    'reinforced_alloy': (23, 'mekanism:metallurgic_infusing', 'mekanism:alloy_reinforced',
                         {'mekanism:metallurgic_infusing/alloy/reinforced'}),
}


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))



def import_tool(name):
    try:
        return importlib.import_module('tools.' + name)
    except ModuleNotFoundError as error:
        if error.name != 'tools':
            raise
        return importlib.import_module(name)


def uid(logical):
    return hashlib.sha256(('aia2-runtime-v1:' + logical).encode()).hexdigest()[:12].upper().rjust(16, '0')


def quest_id(value):
    return value if HEX.fullmatch(value) else uid(value)


def require(condition, *context):
    if not condition:
        raise AssertionError(context)


def validate_preservation(snapshot, chapters, recipe_ids, migrations=()):
    """Old dependency order and task/reward identity are part of the save contract."""
    actual = {q['id']: q for c in chapters.values() for q in c['quests']}
    chapter_ids = {c['id'] for c in chapters.values()}
    changes = {change['quest_id']: change for change in migrations}
    require(len(changes) == len(migrations), 'Duplicate migration entry')
    checked = 0
    for filename, chapter in snapshot['chapters'].items():
        require(chapter['id'] in chapter_ids, 'Existing chapter lost', filename)
        for old in chapter['quests']:
            qid = old['id']
            require(qid in actual, 'Existing quest lost', qid)
            q = actual[qid]
            expected = {k: old.get(k, []) for k in ('tasks', 'rewards', 'dependencies')}
            current = {'tasks': [t['id'] for t in q['tasks']],
                       'rewards': [r['id'] for r in q.get('rewards', [])],
                       'dependencies': q.get('dependencies', [])}
            if expected != current:
                migration = changes.get(qid, {})
                require(len(migration.get('reason_uk', '').strip()) >= 30,
                        'Undocumented existing quest migration', qid)
                require(migration.get('old') == expected and migration.get('new') == current,
                        'Migration does not match exact old/new contract', qid)
            checked += 1
    require(set(snapshot['recipes']) <= set(recipe_ids), 'Existing native recipe removed')
    return {'preserved_quests': checked, 'preserved_chapters': len(snapshot['chapters']),
            'preserved_recipes': len(snapshot['recipes']), 'explicit_migrations': len(changes)}


def validate_graph(quests):
    seen, active = set(), set()
    def visit(qid):
        require(qid in quests, 'Missing quest dependency', qid)
        require(qid not in active, 'Quest dependency cycle', qid)
        if qid in seen:
            return
        active.add(qid)
        for parent in quests[qid].get('dependencies', []):
            visit(parent)
        active.remove(qid)
        seen.add(qid)
    for qid in quests:
        visit(qid)
    return len(seen)


def objective_signature(tasks):
    """Amounts, observation duration and titles cannot disguise duplicate goals."""
    return tuple(sorted((t['type'], t.get('item', t.get('block', t.get('dimension',
        t.get('biome', t.get('entity', t.get('stat', t.get('advancement', ''))))))),
        bool(t.get('consume')), bool(t.get('craft'))) for t in tasks))



def validate_compiled_tasks(record, compiled):
    """A generated task must still prove the action declared by its author."""
    actual = {t['id']: t for t in compiled['tasks']}
    for index, task in enumerate(record['tasks']):
        qid = record['id']
        tid = uid(qid + ':task:' + str(index))
        require(tid in actual and actual[tid]['type'] == task['type'], 'Compiled task identity/type changed', qid, tid)
        result = actual[tid]
        kind = task['type']
        expected = {}
        if kind == 'item':
            expected = {'item': {'id': task['item'], 'count': 1}, 'count': task.get('count', 1),
                        'consume_items': task.get('consume', False), 'only_from_crafting': task.get('craft', False)}
        elif kind == 'observation':
            expected = {'observation_type': 'block', 'to_observe': task['block'], 'timer': task.get('ticks', 40)}
        elif kind == 'kill':
            expected = {'entity': task['entity'], 'value': task.get('count', 1)}
        elif kind == 'stat':
            expected = {'stat': task['stat'], 'value': task['value']}
        elif kind in {'dimension', 'biome', 'advancement'}:
            expected = {kind: task[kind]}
        require(all(result.get(k) == v for k,v in expected.items()), 'Compiled task semantics changed', qid, tid)
    proof = 'aia2:keys/e48' if record.get('post_completion') else f"aia2:stages/e{record['epoch']:02d}"
    gate = actual.get(uid(record['id'] + ':stage'), {})
    require(gate.get('type') == 'advancement' and gate.get('advancement') == proof,
            'Compiled quest lacks final completion proof' if record.get('post_completion') else 'Compiled quest lacks epoch gate', record['id'])


def verified_mechanic_advancements(root, rules, bundle=None):
    """Only the four audited native production contracts can count as actions.

    This checks the checked-in recipe/advancement protocol. Successful native
    dispatch still needs its separate Java/runtime tests; inventory triggers
    must never replace the native post-consumption record.
    """
    root = Path(root)
    config = root/'kubejs/config/aia2_mechanics.json'
    if not config.is_file():
        return frozenset()
    document = read(config)
    require(document.get('schema') == 1 and isinstance(document.get('rules'), list),
            'Unsupported native mechanics contract')
    specs = document['rules']
    by_id = {rule.get('id'): rule for rule in specs}
    require(len(specs) == len(by_id) and set(by_id) == set(MECHANIC_CONTRACT),
            'Only four audited native mechanics are supported')
    removed = set((bundle or {}).get('remove', []))
    compiled_recipes = {entry['id']: entry['json'] for entry in (bundle or {}).get('add', [])}
    allowed = set()
    for ident, (epoch, serializer, output, recipe_ids) in MECHANIC_CONTRACT.items():
        rule = by_id[ident]
        advancement = 'aia2:mechanics/' + ident
        require(type(rule.get('epoch')) is int and rule['epoch'] == epoch and
                rule.get('serializer') == serializer and rule.get('output') == output and
                rule.get('advancement') == advancement, 'Native mechanic identity changed', ident)
        ids = rule.get('recipeIds', [])
        require(len(ids) == len(set(ids)) and set(ids) == recipe_ids,
                'Native mechanic recipe identity changed', ident)
        require(output in rules['itemGates'] and rules['itemGates'][output] <= epoch,
                'Native mechanic has missing/future output', ident)
        evidence = rule.get('evidence', [])
        sources = {source.get('recipeId'): source for source in evidence}
        require(len(evidence) == len(sources) and set(sources) == recipe_ids,
                'Native mechanic lacks exact recipe evidence', ident)
        for recipe_id in ids:
            require(recipe_id in rules.get('recipeGates', {}) and rules['recipeGates'][recipe_id] <= epoch,
                    'Native mechanic has missing/future recipe', ident, recipe_id)
            require(recipe_id not in removed, 'Native mechanic producer was removed', ident, recipe_id)
            source = sources[recipe_id]
            recipe = source.get('json', {})
            digest = hashlib.sha256(json.dumps(recipe, ensure_ascii=False, sort_keys=True,
                                               separators=(',', ':')).encode()).hexdigest()
            require(source.get('canonical_sha256') == digest and
                    SHA.fullmatch(source.get('source_sha256', '')),
                    'Native mechanic frozen recipe hash mismatch', ident, recipe_id)
            require(recipe.get('type') == serializer, 'Native mechanic serializer changed', ident, recipe_id)
            if recipe_id.startswith('aia2:'):
                require(source.get('source_kind') == 'aia2_runtime' and
                        source.get('runtime_recipe_path') == 'kubejs/config/aia2_recipes.json',
                        'Native mechanic lacks runtime recipe provenance', ident, recipe_id)
                require(compiled_recipes.get(recipe_id) == recipe,
                        'Native mechanic runtime producer differs from frozen evidence', ident, recipe_id)
            outputs = recipe.get('results', []) if serializer == 'create:mixing' else [recipe.get('output', {})]
            require(any(result.get('id') == output and result.get('count', 1) > 0 for result in outputs),
                    'Native mechanic recipe does not produce its output', ident, recipe_id)
        path = root/'kubejs/data/aia2/advancement/mechanics'/(ident + '.json')
        require(path.is_file() and read(path) == {
            'criteria': {'native_process': {'trigger': 'minecraft:impossible'}}},
            'Native mechanic proof must use only its impossible trigger', ident)
        allowed.add(advancement)
    return frozenset(allowed)


def validate_catalog(records, rules, registries, compiled=None, old_records=(), mechanic_advancements=(), native_action_advancements=()):
    ids = set()
    objectives = {objective_signature(q['tasks']): q['id'] for q in old_records}
    keys = {e['key'] for e in rules['epochs']} | {k['output'] for k in rules.get('dualKeys', [])}
    task_types, byepoch, mods = Counter(), Counter(), set()
    authored_by_id = {q['id']: q for q in list(old_records) + list(records)}
    for q in records:
        qid, epoch = q['id'], q['epoch']
        post = q.get('post_completion') is True
        require(not post or epoch == 48 and not q.get('required'), 'Post-completion quest must be optional and belong to epoch48', qid)
        gate_limit = 99 if post else epoch
        require(qid not in ids, 'Duplicate v5 logical quest ID', qid)
        ids.add(qid)
        require(type(epoch) is int and 1 <= epoch <= 48, 'Invalid quest epoch', qid)
        require(UK.search(q.get('title_uk', '')) and len(' '.join(q.get('description_uk', []))) >= 80,
                'Missing substantive Ukrainian quest text', qid)
        require(q.get('tasks'), 'Empty quest', qid)
        require(q['icon'] in rules['itemGates'] and rules['itemGates'][q['icon']] <= gate_limit,
                'Missing/future quest icon', qid)
        signature = objective_signature(q['tasks'])
        require(signature not in objectives, 'Duplicate objectives ignoring quantities', qid, objectives.get(signature))
        objectives[signature] = qid
        meaningful = False
        for task in q['tasks']:
            kind = task['type']; task_types[kind] += 1
            fields = {'item': ('item', rules['itemGates']), 'observation': ('block', rules['blockGates']),
                      'dimension': ('dimension', rules.get('dimensionGates', {}))}
            if kind in fields:
                field, gates = fields[kind]
                value = task[field]
                registry = 'block' if kind == 'observation' else 'dimension' if kind == 'dimension' else 'item'
                valid = set(gates) if kind == 'item' else set(registries[registry])
                require(value in valid, 'Unregistered quest target', qid, kind, value)
                require(gates.get(value, 0) <= gate_limit, 'Future quest target', qid, value)
                meaningful = True
            elif kind in {'kill', 'biome', 'stat'}:
                field, registry = {'kill': ('entity', 'entity_type'), 'biome': ('biome', 'worldgen/biome'),
                                   'stat': ('stat', 'custom_stat')}[kind]
                require(task[field] in registries[registry], 'Unregistered quest target', qid, task)
                if kind == 'stat':
                    require(type(task.get('value')) is int and task['value'] > 0, 'Invalid statistic goal', qid)
                meaningful = True
            elif kind == 'advancement':
                require(':' in task['advancement'], 'Invalid advancement', qid)
                if task['advancement'].startswith('aia2:mechanics/'):
                    require(task['advancement'] in mechanic_advancements,
                            'Unverified native mechanic proof', qid, task['advancement'])
                    mechanic_id = task['advancement'].split('/')[-1]
                    require(MECHANIC_CONTRACT[mechanic_id][0] <= gate_limit,
                            'Future native mechanic proof', qid, task['advancement'])
                meaningful |= task['advancement'] in mechanic_advancements or task['advancement'] in native_action_advancements or not task['advancement'].startswith('aia2:')
            else:
                require(False, 'Unsupported or manual-only new task', qid, kind)
            for number in ('count', 'ticks'):
                if number in task:
                    require(type(task[number]) is int and task[number] > 0, 'Invalid task amount', qid, task)
        require(meaningful, 'Quest only contains decorative stage proof', qid)
        for parent_id in q.get('after', []):
            parent = authored_by_id.get(parent_id)
            if parent is not None:
                parent_epoch = 99 if parent.get('post_completion') else parent['epoch']
                require(parent_epoch <= gate_limit, 'Quest requires a future authored goal', qid, parent_id)
        for reward in q.get('reward', []):
            item, count = reward['item'], reward.get('count', 1)
            require(item in rules['itemGates'] and rules['itemGates'][item] <= gate_limit, 'Missing/future reward', qid, item)
            require(item not in keys, 'Reward bypasses key manufacture', qid, item)
            require(not MACHINE.search(item.split(':', 1)[-1]), 'Free machine/overpowered reward', qid, item)
            require(type(count) is int and count > 0, 'Unbalanced reward stack', qid, count)
        if compiled is not None:
            require(uid(qid) in compiled, 'Authored quest not compiled', qid)
            cq = compiled[uid(qid)]
            require(cq.get('title') == q['title_uk'], 'Compiled quest title differs', qid)
            validate_compiled_tasks(q, cq)
            for parent in q.get('after', []):
                require(quest_id(parent) in cq.get('dependencies', []), 'Authored dependency not compiled', qid, parent)
        byepoch[epoch] += 1
        mods.add(q.get('mod', q['icon'].split(':', 1)[0]))
    return {'new_authored_quests': len(records), 'quest_mods': sorted(mods),
            'quests_per_epoch': dict(sorted(byepoch.items())), 'task_types': dict(task_types)}


def verify_evidence(root, evidence, claimed=False):
    """Only repository-relative files make a verified claim portable and reproducible."""
    claimed = claimed or evidence.get('verified') is True or evidence.get('version_match') is True
    path = evidence.get('local_path', evidence.get('path'))
    digest = evidence.get('sha256')
    if not path or not digest:
        require(not claimed, 'Verified source lacks portable path/hash', evidence)
        return False
    candidate = Path(path)
    require(not candidate.is_absolute() and '..' not in candidate.parts, 'Nonportable evidence path', path)
    target = (root / candidate).resolve()
    require(target.is_relative_to(root.resolve()), 'Evidence escapes project', path)
    require(SHA.fullmatch(digest) and target.is_file(), 'Missing or invalid evidence', path)
    require(hashlib.sha256(target.read_bytes()).hexdigest() == digest, 'Stale source evidence hash', path)
    return True


def installed_versions(root):
    versions = {}
    for mod in read(root/'design/mod-catalog.json')['mods']:
        for item in mod.get('exported_metadata', []):
            versions[item['id']] = item['version']
    extra = root/'design/export-mods-not-matched-to-user-list.json'
    for item in read(extra) if extra.is_file() else []:
        versions[item['id']] = item['version']
    return versions


def validate_research(root, documents, versions, rules, registries, authored, compiled):
    counts = Counter()
    mod_ids, verified_paths = set(), set()
    complete_mod_ids, partial_mod_ids = set(), set()
    for document in documents:
        require(document.get('schema') == 1 and document.get('mods'), 'Empty/unsupported research document')
        for mod in document['mods']:
            name = mod.get('mod_id', mod.get('mod'))
            version = mod.get('installed_version', mod.get('version'))
            require(name in versions and version == versions[name], 'Research installed version mismatch', name, version)
            mod_ids.add(name)
            counts['research_mod_records'] += 1
            sources = mod.get('sources', [])
            require(sources, 'Research mod has no evidence or context', name)
            for source in sources:
                if verify_evidence(root, source):
                    verified_paths.add(source.get('local_path', source.get('path')))
                    counts['hash_verified_source_references'] += 1
                else:
                    counts['unverified_context_sources'] += 1
            if isinstance(mod.get('installed_evidence'), dict):
                verify_evidence(root, mod['installed_evidence'], claimed=True)
            stages = mod.get('stages', [])
            require(stages, 'Research map has no stages', name)
            stage_ids = {stage['id'] for stage in stages}
            require(len(stage_ids) == len(stages), 'Duplicate research stage ID', name)
            graph = {stage['id']: {'dependencies': stage.get('prerequisites', [])} for stage in stages}
            validate_graph(graph)
            stage_by_id = {s['id']: s for s in stages}
            for stage in stages:
                epochs = stage.get('epochs', [stage.get('epoch')])
                require(epochs and all(type(n) is int and 1 <= n <= 48 for n in epochs), 'Invalid research epochs', name, stage['id'])
                maximum = max(epochs)
                if stage.get('post_completion') is True:
                    require(maximum == 48, 'Post-completion research belongs to epoch48', name, stage['id'])
                    maximum = 99
                require(UK.search(stage.get('title_uk', '')), 'Missing Ukrainian stage title', name, stage['id'])
                for dep in stage.get('prerequisites', []):
                    parent = stage_by_id[dep]
                    parent_maximum = max(parent.get('epochs', [parent.get('epoch')]))
                    if parent.get('post_completion') is True:
                        parent_maximum = 99
                    require(parent_maximum <= maximum, 'Research stage requires future stage', name, stage['id'], dep)
                for field in ('item_ids', 'output_ids', 'machine_ids'):
                    for item in stage.get(field, []):
                        gate = rules['blockGates'] if field == 'machine_ids' else rules['itemGates']
                        require(item in gate and gate[item] <= maximum, 'Missing/future research item', name, stage['id'], item)
                for evidence in stage.get('recipe_evidence', []):
                    require(verify_evidence(root, evidence, claimed=True), 'Missing recipe evidence', name, stage['id'])
                refs = stage.get('existing_quest_ids', []) + stage.get('new_quest_ids', [])
                for ref in refs:
                    require(quest_id(ref) in compiled, 'Research references missing compiled quest', name, stage['id'], ref)
                    if ref in authored:
                        require(authored[ref]['epoch'] <= maximum, 'Research references future quest', name, stage['id'], ref)
                counts['research_stages'] += 1
                counts['research_quest_links'] += len(refs)
            completed = mod.get('complete') is True or mod.get('status') in {'complete', 'fully_implemented'}
            if completed:
                require(len(stages) >= 8 and all(s.get('existing_quest_ids') or s.get('new_quest_ids') for s in stages),
                        'Unsupported claim of complete mod progression', name)
                counts['claimed_complete_mod_records'] += 1
                complete_mod_ids.add(name)
            else:
                counts['partial_or_gap_documented_mod_records'] += 1
                partial_mod_ids.add(name)
    if complete_mod_ids:
        counts['claimed_complete_mods'] = len(complete_mod_ids)
    if partial_mod_ids:
        counts['mods_with_partial_records'] = len(partial_mod_ids)
        counts['partial_or_gap_documented_mods'] = len(partial_mod_ids - complete_mod_ids)
    return {**dict(counts), 'research_mods': len(mod_ids), 'research_mod_ids': sorted(mod_ids),
            'hash_verified_source_files': len(verified_paths)}


def validate(root=ROOT, include_layout=True):
    root = Path(root)
    paths = sorted((root/'content/quests').glob('v5*.json'))
    maps = sorted((root/'content/research').glob('*v5*.json'))
    if not paths and not maps:
        return {'enabled': False, 'reason': 'No authored v5 catalogs or research maps exist yet'}
    registries = {k: set(v) for k,v in read(root/'content/audit/registries.json')['registries'].items()}
    rules = read(root/'kubejs/config/aia2_runtime.json')
    bundle = read(root/'kubejs/config/aia2_recipes.json')
    require([e['number'] for e in rules['epochs']] == list(range(1,49)), '48 epoch structure changed')
    import nbtlib
    chapters = {}
    object_ids = set()
    for path in sorted((root/'config/ftbquests/quests/chapters').glob('*.snbt')):
        nbtlib.parse_nbt(path.read_text(encoding='utf-8'))
        chapter = read(path); chapters[path.name] = chapter
        for obj in [chapter, *chapter['quests'], *[t for q in chapter['quests'] for t in q['tasks']],
                    *[r for q in chapter['quests'] for r in q.get('rewards', [])]]:
            require(HEX.fullmatch(obj['id']) and int(obj['id'],16) < 2**53, 'Unsafe FTB ID', obj['id'])
            require(obj['id'] not in object_ids, 'Duplicate FTB object ID', obj['id'])
            object_ids.add(obj['id'])
    compiled = {q['id']: q for c in chapters.values() for q in c['quests']}
    validate_graph(compiled)
    snapshot = read(root/'content/audit/v4-ids.json')
    migration_file = root/'content/audit/v5-migrations.json'
    migrations = read(migration_file).get('quests', []) if migration_file.is_file() else []
    preservation = validate_preservation(snapshot, chapters, [r['id'] for r in bundle['add']], migrations)
    checkpoint_preservation = []
    for path in sorted((root/'content/audit').glob('v5-checkpoint-*-ids.json')):
        checkpoint_preservation.append({'snapshot': path.name,
            **validate_preservation(read(path), chapters, [r['id'] for r in bundle['add']], migrations)})
    records, old = [], []
    normalize = import_tool('item_normalization').normalize
    for path in paths:
        data = normalize(read(path))
        require(data.get('quests'), 'Empty v5 authored catalog', str(path))
        if 'quest_count' in data:
            require(data['quest_count'] == len(data['quests']), 'Misreported catalog count', str(path))
        records += data['quests']
    for path in sorted((root/'content/quests').glob('*.json')):
        if path not in paths:
            data = normalize(read(path))
            old += data if isinstance(data,list) else data.get('quests', [])
    migrate = import_tool('quest_content_migrations').apply
    migrated = migrate(old + records, root)
    old, records = migrated[:len(old)], migrated[len(old):]
    mechanic_advancements = verified_mechanic_advancements(root, rules, bundle)
    native_actions = import_tool('validate_native_advancements_v5').validate(root, records, rules, installed_versions(root))
    catalog = validate_catalog(records, rules, registries, compiled, old, mechanic_advancements,
                               native_actions['approved_advancements'])
    research = validate_research(root, [read(p) for p in maps], installed_versions(root), rules,
                                 registries, {q['id']:q for q in old+records}, compiled)
    layout = {'status': 'not_requested'}
    if include_layout:
        module = import_tool('layout_quests')
        metrics = [module.chapter_metrics(c) for c in chapters.values()]
        require(all(not m['overlaps'] and not m['backwards_edges'] and not m['vertical_edges'] for m in metrics), 'Quest layout overlaps or is not strictly left-to-right')
        layout = {'status': 'passed', 'chapters': len(metrics)}
    reward_details = import_tool('build_rewards_v5').validate(root)
    rewards = {key: value for key, value in reward_details.items() if key != 'decisions'}
    rewards['detailed_audit'] = 'implementation/rewards-v5-audit.json'
    return {'enabled': True, 'status': 'passed', 'catalogs': [p.name for p in paths],
            'compiled_quests': len(compiled), **preservation, **catalog, **research,
            'layout': layout, 'reward_validation': rewards,
            'native_mechanic_proofs': sorted(mechanic_advancements),
            'native_action_proofs': native_actions,
            'checkpoint_preservation': checkpoint_preservation,
            'full_pack_run': False, 'tps_benchmark': 'not run'}


if __name__ == '__main__':
    print(json.dumps(validate(),ensure_ascii=False,indent=2))
