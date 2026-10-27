#!/usr/bin/env python3
"""Compile curated quest data and native component chains without changing legacy IDs."""
import copy
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path
try:
    from item_normalization import normalize
except ModuleNotFoundError:
    from tools.item_normalization import normalize

ROOT = Path(__file__).resolve().parents[1]


def read(path):
    return normalize(json.loads(Path(path).read_text(encoding='utf-8')))


def write(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(data if isinstance(data, str) else json.dumps(data, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')


def uid(name):
    return hashlib.sha256(('aia2-runtime-v1:' + name).encode()).hexdigest()[:12].upper().rjust(16, '0')


def compile_description(record, migration=None):
    description = list(record['description_uk'])
    if migration:
        description = [line.replace(migration['from'], migration['to']) for line in description]
        if migration.get('description_note_uk'):
            description.append(migration['description_note_uk'])
    return description


def component_id(kind, n):
    return f'kubejs:aia2_{kind}_{n:02d}'


KINDS = ('tech_matrix', 'arcane_catalyst', 'convergence_core', 'epoch_seal')
KIND_NAMES = {'tech_matrix': 'Матриця ремесла', 'arcane_catalyst': 'Арканний каталізатор',
              'convergence_core': 'Осередок узгодження', 'epoch_seal': 'Печатка випробування'}
GROUPS = {'epochs': 'Епохи', 'technology': 'Технології', 'magic': 'Магія',
          'adventure': 'Пригоди', 'collection': 'Колекції', 'automation': 'Автоматизація'}


def crafting(pattern, keys, output, count=1):
    return {'type': 'minecraft:crafting_shaped', 'pattern': pattern,
            'key': {k: {'item': v} for k, v in keys.items()}, 'result': {'id': output, 'count': count}}


def component_chains(root=ROOT):
    epochs = read(root/'design/progression.json')['epochs']
    runtime = read(root/'kubejs/config/aia2_runtime.json')
    bundle = read(root/'kubejs/config/aia2_recipes.json')
    # Re-running the expansion replaces only its own recipe namespace.
    bundle['add'] = [x for x in bundle['add'] if not x['id'].startswith('aia2:components/')]
    components = []
    recipes = []
    startup = ['// priority: 9000', '// Component IDs are stable; changing registrations requires a full restart.',
               "StartupEvents.registry('item', function (event) {"]
    for epoch in epochs:
        n = epoch['number']
        base = {symbol: entry['id'] for symbol, entry in epoch['key']['ingredients'].items()}
        t, m, r, s = [base[x] for x in 'TMRS']
        matrix, catalyst, core, seal = [component_id(kind, n) for kind in KINDS]
        if n in {25, 26}:
            tech = {'type': 'oritech:foundry', 'ingredients': [{'item': t}, {'item': 'oritech:raw_biopolymer'}],
                    'results': [{'id': matrix, 'count': 2}], 'time': 160}
        elif n < 4:
            tech = crafting(['TRT', 'RMR', 'STS'], {'T': t, 'R': r, 'M': m, 'S': s}, matrix, 2)
        elif n >= 16 and n % 3 == 1:
            tech = {'type': 'mekanism:metallurgic_infusing',
                    'chemical_input': {'amount': 20, 'tag': 'mekanism:redstone'},
                    'item_input': {'count': 2, 'item': t}, 'output': {'count': 2, 'id': matrix},
                    'per_tick_usage': False}
        else:
            tech = {'type': 'create:mixing', 'ingredients': [{'item': x} for x in [t,t,t,r,r,m,m,s]],
                    'results': [{'id': matrix, 'count': 2}]}
        if n < 5:
            magic = crafting(['MRM', 'SXS', 'MR '], {'M': m, 'R': r, 'S': s, 'X': matrix}, catalyst)
        elif n < 9:
            magic = {'type': 'botania:mana_infusion', 'input': {'item': matrix},
                     'mana': 2000 + 250*n, 'output': {'id': catalyst, 'count': 1}}
        else:
            magic = {'type': 'botania:runic_altar',
                     'ingredients': [{'item': x} for x in [matrix,m,m,r,s]],
                     'mana': 2000 + 250*n, 'output': {'id': catalyst, 'count': 1}}
        if n < 25:
            convergence = crafting(['XMX', 'TRS', ' C '],
                                   {'X': matrix, 'M': m, 'T': t, 'R': r, 'S': s, 'C': catalyst}, core)
        elif n < 40:
            convergence = {'type': 'oritech:assembler',
                           'ingredients': [{'item': x} for x in [matrix,catalyst,t,m]],
                           'results': [{'id': core, 'count': 1}], 'time': 600 + n*20}
        else:
            convergence = {'type': 'draconicevolution:fusion_crafting',
                           'catalyst': {'type': 'draconicevolution:stack', 'count': 1, 'items': matrix},
                           'ingredients': [{'consume': True, 'ingredient': {'item': x}} for x in
                                           [catalyst,t,m,r,s,component_id('convergence_core', n-1)]],
                           'result': {'id': core, 'count': 1},
                           'techLevel': 'wyvern' if n == 40 else 'draconic' if n <= 42 else 'chaotic',
                           'totalEnergy': 1000000*(n-39)**2}
        if n < 4:
            sealing = crafting(['XAX', 'TRT', 'SMS'],
                               {'X': matrix, 'A': catalyst, 'T': t, 'R': r, 'S': s, 'M': core}, seal)
        else:
            sealing = {'type': 'create:compacting',
                       'ingredients': [{'item': x} for x in [core,catalyst,matrix,m,s]],
                       'results': [{'id': seal, 'count': 1}]}
        for kind, recipe in zip(KINDS, [tech, magic, convergence, sealing]):
            item = component_id(kind, n)
            rid = f'aia2:components/e{n:02d}/{kind}'
            name = KIND_NAMES[kind] + ': ' + epoch['title']
            entry = {'id': item, 'epoch': n, 'kind': kind, 'name_uk': name,
                     'texture': f'kubejs:item/aia2/components/{kind}_{n:02d}',
                     'description_uk': 'Компонент епохи ' + str(n) + '. ' + {
                         'tech_matrix': 'Матеріальна основа: поєднайте технічну сировину з доступним магічним ресурсом.',
                         'arcane_catalyst': 'Насичує технічну основу магією; потрібний для осередку та печатки.',
                         'convergence_core': 'Узгоджує технічну матрицю й магічний каталізатор.',
                         'epoch_seal': 'Виготовляється наприкінці виробничого ланцюга та входить до складу ключа.'}[kind],
                     'recipe_id': rid, 'process': recipe['type']}
            components.append(entry)
            recipes.append({'id': rid, 'json': recipe, 'epoch': n, 'target': item, 'category': 'component_chain'})
            runtime['itemGates'][item] = n
            startup.append('  event.create(' + json.dumps(item) + ').displayName(' + json.dumps(name, ensure_ascii=False)
                           + ').maxStackSize(64).texture(' + json.dumps(entry['texture']) + ');')
        # The native key transaction still has nine input units, and only it uses the previous key.
        cost = {}
        for symbol, value in epoch['key']['ingredients'].items():
            cost[value['id']] = value['count'] - (1 if symbol == 'S' else 0)
        cost[seal] = 1
        assert sum(cost.values()) == 9
        runtime['epochs'][n-1]['cost'] = cost
        for item, texture in [(f'kubejs:aia2_epoch_icon_{n:02d}', f'kubejs:item/aia2/chapters/epoch_{n:02d}')]:
            startup.append('  event.create(' + json.dumps(item) + ').displayName(' + json.dumps('Епоха '+str(n)+': '+epoch['title'], ensure_ascii=False)
                           + ').maxStackSize(1).texture(' + json.dumps(texture) + ');')
            runtime['itemGates'][item] = 0
    for group, title in GROUPS.items():
        item = 'kubejs:aia2_section_' + group
        startup.append('  event.create(' + json.dumps(item) + ').displayName(' + json.dumps(title, ensure_ascii=False)
                       + ').maxStackSize(1).texture(' + json.dumps('kubejs:item/aia2/sections/' + group) + ');')
        runtime['itemGates'][item] = 0
    startup += ['});', '']
    bundle['add'] += recipes
    runtime.setdefault('recipeGates', {}).update({r['id']: r['epoch'] for r in recipes})
    runtime['expansionSchema'] = 2
    write(root/'kubejs/startup_scripts/aia2/10_components.js', '\n'.join(startup))
    write(root/'kubejs/config/aia2_runtime.json', runtime)
    write(root/'kubejs/config/aia2_recipes.json', bundle)
    write(root/'content/components/catalog.json', {'schema': 1, 'items': components})
    write(root/'kubejs/config/aia2_components.json', {'schema': 1, 'items': components})
    return components, recipes


def compile_task(record, logical_id, index):
    task = {'id': uid(logical_id + ':task:' + str(index)), 'type': record['type']}
    kind = record['type']
    if kind == 'item':
        task.update(item={'id': record['item'], 'count': 1}, count=record.get('count', 1),
                    consume_items=record.get('consume', False), only_from_crafting=record.get('craft', False))
    elif kind == 'kill':
        task.update(entity=record['entity'], value=record.get('count', 1))
    elif kind == 'advancement':
        task['advancement'] = record['advancement']
    elif kind == 'observation':
        task.update(observation_type='block', to_observe=record['block'], timer=record.get('ticks', 40))
    elif kind == 'dimension': task['dimension'] = record['dimension']
    elif kind == 'biome': task['biome'] = record['biome']
    elif kind == 'stat': task.update(stat=record['stat'], value=record['value'])
    else: raise ValueError('Unverified task type: ' + kind)
    return task


def compile_quests(root=ROOT):
    paths = sorted((root/'content/quests').glob('epochs_*.json'))
    if len(paths) != 4: raise ValueError('Four curated epoch catalogs are required before compiling the full expansion')
    records = []
    for path in paths:
        data = read(path)
        records.extend(data if isinstance(data, list) else data['quests'])
    v4 = root/'content/quests/v4_mod_depth.json'
    if v4.exists(): records.extend(read(v4)['quests'])
    for path in sorted((root/'content/quests').glob('v5_*.json')):
        records.extend(read(path)['quests'])
    try:
        from quest_content_migrations import apply as migrate_quest_content
    except ImportError:
        from tools.quest_content_migrations import apply as migrate_quest_content
    records = migrate_quest_content(records, root)
    epochs = read(root/'design/progression.json')['epochs']
    runtime = read(root/'kubejs/config/aia2_runtime.json')
    components = read(root/'content/components/catalog.json')['items']
    baseline = {}
    core_chapters = {}
    for e in epochs:
        n = e['number']; path = root/f'config/ftbquests/quests/chapters/aia2_epoch_{n:02d}.snbt'
        chapter = read(path)
        # Own extra nodes are rebuilt; all nine legacy IDs remain unchanged.
        legacy_ids = {*runtime['epochs'][n-1]['milestoneQuestIds'], runtime['epochs'][n-1]['finalQuestId'],
                      uid(f'E{n:02d}_O1'), uid(f'E{n:02d}_O2')}
        chapter['quests'] = [q for q in chapter['quests'] if q['id'] in legacy_ids]
        if len(chapter['quests']) != 9:
            raise ValueError('Run the base generator before rebuilding expanded chapters: '+str(path))
        baseline.update({f'E{n:02d}_M{j}': q['id'] for j,q in enumerate(chapter['quests'][:6],1)})
        baseline[f'E{n:02d}_KEY'] = runtime['epochs'][n-1]['finalQuestId']
        chapter['group'] = uid('GROUP:epochs')
        chapter['icon'] = {'id': f'kubejs:aia2_epoch_icon_{n:02d}', 'count': 1}
        for q in chapter['quests']:
            q['icon'] = {'id': next((t['item']['id'] for t in q['tasks'] if t['type'] == 'item'), e['key']['id']), 'count': 1}
        core_chapters[n] = chapter
    logical = {record['id']: uid(record['id']) for record in records}
    migration_path = root/'content/audit/v5-item-normalization-migrations.json'
    # Keep the raw 'from' ID: read() would normalize it before text migration.
    material_migrations = {row['id']: row for row in json.loads(migration_path.read_text(encoding='utf-8')).get('quests', [])} if migration_path.exists() else {}
    if len(logical) != len(records): raise ValueError('Duplicate authored logical IDs')
    all_logical = dict(baseline, **logical)
    mods = defaultdict(list)
    required = defaultdict(list)
    for r in records:
        n = r['epoch']; group = r['category']
        assert 1 <= n <= 48 and group in GROUPS and group != 'epochs'
        deps = [all_logical[x] for x in r.get('after', [])]
        if n > 1: deps.append(runtime['epochs'][n-2]['finalQuestId'])
        if r.get('post_completion'):
            assert n == 48 and not r.get('required'), 'Post-completion goals must remain optional'
            deps.append(runtime['epochs'][47]['finalQuestId'])
        tasklist = [compile_task(t, r['id'], i) for i,t in enumerate(r['tasks'])]
        tasklist.append({'id': uid(r['id']+':stage'), 'type': 'advancement',
                         'advancement': 'aia2:keys/e48' if r.get('post_completion') else f'aia2:stages/e{n:02d}'})
        rewards = [{'id': uid(r['id']+':reward:'+str(i)), 'type': 'item', 'item': {'id': reward['item'], 'count': 1},
                    'count': reward['count']} for i,reward in enumerate(r.get('reward', []))]
        description = compile_description(r, material_migrations.get(r['id']))
        q = {'id': logical[r['id']], 'title': r['title_uk'], 'description': description,
             'icon': {'id': r['icon'], 'count': 1}, 'dependencies': list(dict.fromkeys(deps)),
             'hide_until_deps_complete': True, 'tasks': tasklist, 'optional': not r.get('required', False), 'rewards': rewards}
        primary = r.get('mod') or r['icon'].split(':')[0]
        mods[(group, primary)].append((n, q))
        if r.get('required'): required[n].append(q['id'])
    for component in components:
        n = component['epoch']; kind = component['kind']; lid = f'E{n:02d}_COMPONENT_{kind}'
        index = KINDS.index(kind)
        deps = [] if index == 0 else [uid(f'E{n:02d}_COMPONENT_{KINDS[index-1]}')]
        if n > 1: deps.append(runtime['epochs'][n-2]['finalQuestId'])
        core_chapters[n]['quests'].append({'id': uid(lid), 'title': component['name_uk'],
            'description': [component['description_uk'], 'Процес: '+component['process']+'. Точний склад дивіться в JEI.',
                            'Предметне завдання підтверджує наявність компонента, а не кількість циклів машини.'],
            'icon': {'id': component['id'], 'count': 1}, 'dependencies': deps,
            'hide_until_deps_complete': True,
            'tasks': [{'id': uid(lid+':item'), 'type': 'item', 'item': {'id': component['id'], 'count': 1},
                       'count': 1, 'consume_items': False},
                      {'id': uid(lid+':stage'), 'type': 'advancement', 'advancement': f'aia2:stages/e{n:02d}'}],
            'rewards': [{'id': uid(lid+':reward'), 'type': 'item', 'item': {'id': 'minecraft:bread', 'count': 1}, 'count': 4}]})
    quest_objects = {q['id']: q for chapter in core_chapters.values() for q in chapter['quests']}
    quest_objects.update({q['id']:q for entries in mods.values() for n,q in entries})
    effective_required = set()
    def mark_required(qid):
        if qid in effective_required: return
        effective_required.add(qid)
        q = quest_objects[qid]
        q['optional'] = False
        for dep in q.get('dependencies', []): mark_required(dep)
    for n, chapter in core_chapters.items():
        lid = f'E{n:02d}_EXPANSION_TRIAL'
        gate = {'id': uid(lid), 'title': 'Підсумкове випробування: '+epochs[n-1]['title'],
                'description': ['Завершіть обов’язкові модові гілки цієї епохи та виготовте печатку випробування.',
                                'Нові перевірки потрібні для наступного законного крафту ключа. Уже завершені старі епохи не скидаються.'],
                'icon': {'id': component_id('epoch_seal', n), 'count': 1},
                'dependencies': list(dict.fromkeys(required[n]+[uid(f'E{n:02d}_COMPONENT_epoch_seal')])),
                'hide_until_deps_complete': True,
                'tasks': [{'id': uid(lid+':item'), 'type': 'item', 'item': {'id': component_id('epoch_seal',n), 'count': 1},
                           'count': 1, 'consume_items': False}],
                'rewards': [{'id': uid(lid+':reward'), 'type': 'item', 'item': {'id': 'minecraft:golden_carrot','count':1},'count':8}]}
        chapter['quests'].append(gate)
        quest_objects[gate['id']] = gate
        mark_required(gate['id'])
        runtime['epochs'][n-1]['requiredQuestIds'] = [gate['id']]
        # Preserve every legacy dependency and ID; new server checks enforce the trial.
        final = chapter['quests'][6]
        final['description'] = [line for line in final['description'] if not line.startswith('Склад: ')
                                and line != 'Нове проходження також потребує підсумкового випробування епохи.']
        final['description'] += ['Нове проходження також потребує підсумкового випробування епохи.',
                                'Склад: '+'; '.join(f'{count} × {item}' for item,count in runtime['epochs'][n-1]['cost'].items())]
        for i,q in enumerate(chapter['quests']):
            if i >= 9: q.update(x=float((i-9)%3*2), y=float(8+(i-9)//3*2))
        write(root/f'config/ftbquests/quests/chapters/aia2_epoch_{n:02d}.snbt', chapter)
    # Small addon/cross-mod fragments share a readable chapter rather than dozens
    # of one-node chapters. Every quest keeps its own stable ID and stage proof.
    grouped = defaultdict(list)
    old_locations = {}
    snapshots = [root/'content/audit/v4-ids.json', *sorted((root/'content/audit').glob('v5-checkpoint-*-ids.json'))]
    for snapshot_path in snapshots:
        if not snapshot_path.exists(): continue
        for filename, old in read(snapshot_path)['chapters'].items():
            if filename.startswith('aia2_branch_'):
                for quest in old['quests']: old_locations[quest['id']] = filename
    for (group, mod), entries in mods.items():
        for entry in entries:
            old_filename = old_locations.get(entry[1]['id'])
            # New courses must not empty/retire a published chapter or move its
            # old quests when a small addon grows past the grouping threshold.
            target = old_filename[len('aia2_branch_'+group+'_'):-5] if old_filename else (
                mod if len(entries) >= 6 else 'shared_studies')
            grouped[(group, target)].append(entry)
    mods = grouped
    chapter_files = set()
    mod_names = {m: n for m, n in [('shared_studies','Спільні дослідження'), ('minecraft','Ремесло й дослідження'), ('create','Create'),
                 ('mekanism','Mekanism'), ('modern_industrialization','Modern Industrialization'),
                 ('botania','Botania'), ('ars_nouveau','Ars Nouveau'), ('occultism','Occultism'),
                 ('draconicevolution','Draconic Evolution'), ('avaritia','Re-Avaritia')]}
    for order, ((group, mod), entries) in enumerate(sorted(mods.items())):
        filename = 'aia2_branch_'+group+'_'+mod.replace('-','_').replace('.','_')
        chapters = {'id': uid('CHAPTER:'+filename), 'filename': filename, 'title': mod_names.get(mod, mod)+' — '+GROUPS[group],
                    'group': uid('GROUP:'+group), 'order_index': order,
                    'icon': {'id': entries[0][1]['icon']['id'], 'count':1},
                    'hide_quest_details_until_startable':True,'hide_quest_until_deps_complete':True,
                    'quests':[]}
        chapter_ids = {q['id'] for n,q in entries}
        levels = {}
        def level(qid, visiting=None):
            if qid in levels: return levels[qid]
            visiting = set() if visiting is None else visiting
            if qid in visiting: raise ValueError('Quest cycle: '+qid)
            visiting.add(qid)
            q = next(q for n,q in entries if q['id'] == qid)
            levels[qid] = 1 + max((level(dep, visiting) for dep in q['dependencies'] if dep in chapter_ids), default=-1)
            visiting.remove(qid)
            return levels[qid]
        rows = Counter()
        for n,q in sorted(entries, key=lambda pair:(pair[0],level(pair[1]['id']),pair[1]['id'])):
            depth = level(q['id'])
            q.update(x=float(depth*2), y=float(rows[depth]*2))
            rows[depth] += 1
            chapters['quests'].append(q)
        chapter_files.add(filename+'.snbt')
        write(root/f'config/ftbquests/quests/chapters/{filename}.snbt',chapters)
    # Only retire this compiler's unpublished generated chapter containers;
    # authored quest IDs remain unchanged and the installer preserves foreign nodes.
    for path in (root/'config/ftbquests/quests/chapters').glob('aia2_branch_*.snbt'):
        if path.name not in chapter_files and read(path)['id'] == uid('CHAPTER:'+path.stem):
            path.unlink()
    write(root/'config/ftbquests/quests/chapter_groups.snbt', {'chapter_groups':[
        {'id':uid('GROUP:'+group),'title':title} for group,title in GROUPS.items()]})
    write(root/'kubejs/config/aia2_runtime.json', runtime)
    report = {'authored_quests':len(records),'legacy_quests_preserved':432,'component_quests':len(components),
              'new_final_trials':48,'total_quests':432+len(records)+len(components)+48,
              'epoch_chapters':48,'mod_chapters':len(mods),'groups':len(GROUPS),
              'chapter_files':sorted(chapter_files),
              'task_types':dict(Counter(t['type'] for r in records for t in r['tasks'])),
              'required_authored_quests':sum(bool(r.get('required')) for r in records),
              'effective_required_authored_quests':sum(logical[r['id']] in effective_required for r in records),
              'legacy_id_migration':'No legacy IDs or dependencies changed; new trials checked only when forging future keys.'}
    write(root/'implementation/expansion-report.json',report)
    return report


def apply(root=ROOT):
    components, recipes = component_chains(root)
    report = compile_quests(root)
    report.update(new_components=len(components),new_component_recipes=len(recipes))
    try:
        from build_dual_keys import apply as dual_apply
    except ImportError:
        from tools.build_dual_keys import apply as dual_apply
    dual_report=dual_apply(root)
    report.update(dual_report)
    recipe_module=root/'tools/build_recipe_expansion.py'
    if recipe_module.exists() and (root/'content/recipes/v4_expansion.json').exists():
        try:
            from build_recipe_expansion import apply as recipe_apply
        except ImportError:
            from tools.build_recipe_expansion import apply as recipe_apply
        recipe_apply(root)
    for module_name, source in [('build_balance_v5', 'content/recipes/v5_balance.json'),
                                ('build_variant_balance_v5', 'content/recipes/v5_component_variants.json'),
                                ('build_core_balance_v5', 'content/recipes/v5_aa_core.json'),
                                ('build_spawner_gates_v5', 'content/audit/v5-spawner-rune-gates.json'),
                                ('build_industrial_core_balance_v5', 'content/recipes/v5_mi_oritech_core.json'),
                                ('build_industrial_controller_gates_v5', 'content/audit/v5-industrial-controller-floors.json'),
                                ('build_energy_core_balance_v5', 'content/recipes/v5_enderio_powah_core.json'),
                                ('build_powah_generators_balance_v5', 'content/recipes/v5_powah_generators.json'),
                                ('build_draconic_power_v5', 'content/recipes/v5_draconic_power.json'),
                                ('build_evilcraft_core_balance_v5', 'content/recipes/v5_evilcraft_core.json'),
                                ('build_rewards_v5', 'content/rewards/v5_profiles.json')]:
        if (root/source).exists():
            import importlib
            try: module = importlib.import_module(module_name)
            except ModuleNotFoundError: module = importlib.import_module('tools.'+module_name)
            module.apply(root)
    if (root/'tools/layout_quests.py').exists():
        try: from layout_quests import apply as layout_apply
        except ImportError: from tools.layout_quests import apply as layout_apply
        layout_apply(root)
    report['native_recipes'] = len(read(root/'kubejs/config/aia2_recipes.json')['add'])
    write(root/'implementation/expansion-report.json',report)
    print(json.dumps(report,ensure_ascii=False,indent=2))


if __name__ == '__main__': apply()
