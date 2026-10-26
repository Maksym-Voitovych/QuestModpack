#!/usr/bin/env python3
"""Render reviewed research maps and explicit coverage gaps without inventing facts."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTENT_CATEGORIES = {'technology_core', 'technology_addon', 'storage_logistics',
                      'magic_core', 'magic_addon', 'resources_equipment', 'exploration_worldgen'}


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def strings(value):
    if isinstance(value, str): return [value]
    if isinstance(value, list): return [str(item) for item in value]
    return []


def render(root=ROOT):
    root = Path(root)
    documents = [(path, read(path)) for path in sorted((root/'content/research').glob('*v5*.json'))]
    maps = [(path, mod) for path, document in documents for mod in document.get('mods', [])]
    versions = {}; records = read(root/'design/mod-catalog.json')['mods']
    for record in records:
        for metadata in record.get('exported_metadata', []): versions[metadata['id']] = metadata['version']
    full, mapped, actual_sources = set(), set(), {}
    lines = ['# Карти механік AIA2 — робоча версія 0.5', '',
             'Джерело цих карт — перевірені JSON у `content/research/`. Статус карти',
             'описує охоплення механік; він не означає запуск повного модпаку або тест TPS.',
             'Відомі прогалини збережено явно. [Індекс джерел](SOURCE_INDEX.md) ·',
             '[Моди без завершених карт](REMAINING_COVERAGE.md).', '']
    for path, mod in maps:
        mid = mod.get('mod_id', mod.get('mod')); mapped.add(mid)
        if mod.get('complete') is True or mod.get('status') in {'complete', 'fully_implemented'}: full.add(mid)
        title = mod.get('name_uk', mod.get('name', mid))
        version = mod.get('installed_version', mod.get('version', versions.get(mid, '?')))
        lines += ['## '+title, '', f"Версія експорту: **{version}**. Статус: `{mod.get('status', 'partial')}`.",
                  f'[Структурована карта](../../{path.relative_to(root).as_posix()}).', '']
        lines += strings(mod.get('entry_uk')) + ['']
        for index, stage in enumerate(mod.get('stages', []), 1):
            epochs = stage.get('epochs', [stage.get('epoch')])
            period = ', '.join(map(str, epochs))
            if stage.get('post_completion'): period += ' — після завершення всіх 48 епох'
            lines += [f"### {index}. {stage['title_uk']}", '', 'Епохи: '+period+'.', '']
            lines += strings(stage.get('mechanic_uk'))
            lines += strings(stage.get('why_next_uk'))
            if stage.get('prerequisites'): lines += ['Попередні кроки: '+', '.join(stage['prerequisites'])+'.']
            for label, field in [('Машини', 'machine_ids'), ('Ресурси й результати', 'item_ids')]:
                if stage.get(field): lines += [label+': '+', '.join('`'+item+'`' for item in stage[field])+'.']
            refs = stage.get('existing_quest_ids', []) + stage.get('new_quest_ids', [])
            if refs: lines += ['Квести: '+', '.join('`'+ref+'`' for ref in dict.fromkeys(refs))+'.']
            lines += strings(stage.get('verification_uk')) + strings(stage.get('limitations_uk')) + ['']
        goals = mod.get('final_goals_uk', mod.get('final_goals'))
        if goals: lines += ['Фінальні цілі:'] + ['- '+text for text in strings(goals)] + ['']
        links = mod.get('intermod_links', [])
        if links: lines += ['Міжмодові зв’язки:'] + ['- '+(text if isinstance(text, str) else json.dumps(text, ensure_ascii=False)) for text in links] + ['']
        gaps = (strings(mod.get('uncertainties_uk')) + strings(mod.get('unconfirmed_mechanics_uk')) +
                strings(mod.get('uncertainties')))
        if gaps: lines += ['Прогалини та межі перевірки:'] + ['- '+text for text in gaps] + ['']
        lines += ['Джерела:', '']
        for source in mod.get('sources', []):
            url = source.get('url', source.get('source_url', ''))
            local = source.get('local_path', source.get('path'))
            digest = source.get('sha256')
            checked = bool(local and digest and (root/local).is_file() and
                           hashlib.sha256((root/local).read_bytes()).hexdigest() == digest)
            label = source.get('title_uk', source.get('kind', source.get('type', 'джерело')))
            target = url if url.startswith(('https://', 'http://')) else ('../../'+local if local else '')
            detail = '['+str(label)+']('+target+')' if target else str(label)
            detail += ' — SHA перевірено' if checked else ' — контекст, без заяви про перевірений вміст'
            if source.get('version_match') is False: detail += '; upstream-версія відрізняється'
            lines.append('- '+detail)
            if target: actual_sources.setdefault(target, {'verified_file': checked, 'mods': set()})['mods'].add(mid)
        lines += ['']
    native_lines = ['# Перевірені джерела без звичайного crafting-рецепта', '',
                    'Нативне джерело, торгівля або boss-drop не означають пропущений рецепт.',
                    'Наведені висновки перевірені за конкретними версіями й SHA файлів;',
                    'повне Survival-проходження та сторонні overrides ще не тестувалися.', '']
    for path in sorted((root/'content/audit').glob('v5-source-gaps-*.json')):
        native_lines += [f'[Структуровані докази](../../{path.relative_to(root).as_posix()}).', '']
        for row in read(path).get('items', []):
            native_lines += ['## `'+row['item']+'`', '',
                             'Статус: `'+row['status']+'`; версія: '+row['installed_version']+'.', '',
                             row['description_uk'], '']
            for source in row.get('sources', []):
                url = source.get('url', '')
                local = source.get('path', source.get('local_path'))
                checked = bool(local and (root/local).is_file() and
                               hashlib.sha256((root/local).read_bytes()).hexdigest() == source.get('sha256'))
                target = url if url.startswith(('http://','https://')) else ('../../'+local if local else '')
                if target:
                    native_lines.append('- '+target+(' — SHA перевірено' if checked else ' — контекст'))
                    entry = actual_sources.setdefault(target, {'verified_file':False, 'mods':set()})
                    entry['verified_file'] |= checked; entry['mods'].add(row['item'].split(':')[0])
            native_lines += ['']
    # Action contracts and component guards have independent codec/dispatch
    # evidence in addition to the mod maps. Include them in the public index.
    extra_sources = []
    action_path = root/'content/audit/v5-native-advancement-contracts.json'
    if action_path.is_file():
        extra_sources += [(row['mod_id'], source) for row in read(action_path)['advancements'] for source in row['sources']]
    for relative, owner, field in [('content/recipes/v5_component_variants.json', 'botania', 'source_evidence'),
                                    ('content/audit/v5-creative-mana-guard.json', 'botania', 'sources')]:
        if (root/relative).is_file():
            extra_sources += [(owner, source) for source in read(root/relative).get(field, [])]
    for relative in ['content/audit/v5-industrial-native-guard.json', 'content/audit/v5-roots-mutation-fix.json', 'content/audit/v5-energy-native-guard.json', 'content/audit/v5-fire-worksites.json', 'content/audit/v5-projecte-native-guard.json']:
        if (root/relative).is_file():
            audit = read(root/relative)
            extra_sources += [(source.get('mod_id', audit.get('mod_id')), source) for source in audit.get('sources', [])]
    for owner, source in extra_sources:
        local = source.get('path', source.get('local_path'))
        url = source.get('url', '')
        target = url if url.startswith(('http://','https://')) else ('../../'+local if local else '')
        checked = bool(local and (root/local).is_file() and
                       hashlib.sha256((root/local).read_bytes()).hexdigest() == source.get('sha256'))
        if target:
            entry = actual_sources.setdefault(target, {'verified_file':False, 'mods':set()})
            entry['verified_file'] |= checked; entry['mods'].add(owner)
    gap_lines = ['# Охоплення каталогу модів', '',
                 'Відсутня або часткова карта не прирівнюється до завершеного дослідження.',
                 'Невеликі аддони можуть мати тематичні цілі; бібліотеки й оптимізації',
                 'не потребують окремих квестів. Таблиця нижче охоплює контентні категорії',
                 'початкового каталогу, тому також містить worldgen і невеликі допоміжні моди.', '',
                 '| Мод | Категорія | Статус карти |', '|---|---|---|']
    missing = []
    for record in records:
        if record['category'] not in CONTENT_CATEGORIES: continue
        ids = set(record.get('mod_ids', []))
        status = 'DONE — основна карта' if ids & full else ('IN_PROGRESS — часткова карта' if ids & mapped else 'TODO — карта не досліджена')
        gap_lines.append('| '+record['name'].replace('|', '/')+' | '+record['category']+' | '+status+' |')
        if not ids & mapped: missing.append({'name':record['name'], 'mod_ids':sorted(ids), 'category':record['category']})
    source_lines = ['# Індекс джерел механік', '',
                    'SHA означає перевірку збереженого файла. Відповідність встановленій',
                    'версії та межі upstream-контексту наведені в самих JSON-картах.', '']
    for url, source in sorted(actual_sources.items()):
        source_lines += ['- '+url+' — '+', '.join(sorted(source['mods']))+
                         ('; є перевірений файл' if source['verified_file'] else '; лише контекст')]
    folder = root/'docs/research'; folder.mkdir(parents=True, exist_ok=True)
    for name, content in [('MOD_MECHANICS.md', lines), ('REMAINING_COVERAGE.md', gap_lines),
                          ('SOURCE_INDEX.md', source_lines), ('OBTAINABILITY.md', native_lines)]:
        (folder/name).write_text('\n'.join(content).rstrip()+'\n', encoding='utf-8')
    summary = {'map_documents':len(documents), 'map_records':len(maps), 'mapped_mods':len(mapped),
               'complete_core_maps':len(full), 'complete_core_mod_ids':sorted(full),
               'partial_mod_ids':sorted(mapped-full), 'source_links':len(actual_sources),
               'content_records_without_map':missing, 'full_pack_run':False,
               'scope':'Documentation rendered from reviewed data; no claim of full modpack acceptance'}
    (root/'implementation/research-v5-summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2)+'\n')
    return summary


if __name__ == '__main__':
    print(json.dumps(render(), ensure_ascii=False, indent=2))
