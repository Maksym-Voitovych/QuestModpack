#!/usr/bin/env python3
"""Audit explicit sources for important items; absence is never an invented recipe."""
import argparse
from collections import Counter, defaultdict
import csv
import hashlib
import json
from pathlib import Path
try:
    from item_normalization import normalize
except ImportError:
    from tools.item_normalization import normalize

ROOT = Path(__file__).resolve().parents[1]
OUTPUT_FIELDS = {'result', 'results', 'output', 'outputs', 'item_output', 'item_outputs',
                 'main_output', 'secondary_output', 'secondaryOutput', 'bonusOutput'}


def outputs(recipe):
    def stack_items(stack):
        if isinstance(stack, str) and ':' in stack:
            yield stack
        elif isinstance(stack, dict):
            ident = stack.get('id', stack.get('item'))
            if isinstance(ident, str) and ':' in ident: yield ident
            for nested in ['item', 'resource']:
                if isinstance(stack.get(nested), dict): yield from stack_items(stack[nested])
    for field in OUTPUT_FIELDS:
        value = recipe.get(field, [])
        for stack in value if isinstance(value, list) else [value]:
            yield from stack_items(stack)
    for field in ['recipe', 'base', 'gog', 'baseRecipe']:
        if isinstance(recipe.get(field), dict): yield from outputs(recipe[field])


def loot_items(value):
    if isinstance(value, dict):
        if value.get('type') in {'minecraft:item', 'item'} and isinstance(value.get('name'), str):
            yield value['name']
        for child in value.values(): yield from loot_items(child)
    elif isinstance(value, list):
        for child in value: yield from loot_items(child)


def source_context(root):
    """Accept native-source claims only with exact metadata and portable SHA proofs."""
    root = Path(root)
    read = lambda p: json.loads(p.read_text(encoding='utf-8'))
    versions = {m['id']:m['version'] for row in read(root/'design/mod-catalog.json')['mods']
                for m in row.get('exported_metadata', [])}
    known = set(read(root/'content/audit/registries.json')['registries']['item'])
    result = {}
    for path in sorted((root/'content/audit').glob('v5-source-gaps-*.json')):
        data = read(path); assert data['schema'] == 1
        for row in data['items']:
            item = row['item']; assert item in known, ('Unknown native source item', item)
            assert versions[item.split(':')[0]] == row['installed_version'], ('Native source version mismatch', item)
            assert row.get('sources'), ('Missing native source evidence', item)
            for source in row['sources']:
                local = Path(source['path'])
                assert not local.is_absolute() and '..' not in local.parts, ('Nonportable native evidence', item)
                assert hashlib.sha256((root/local).read_bytes()).hexdigest() == source['sha256'], ('Stale native evidence', item)
            if row['status'] == 'source_verified_native_path':
                assert any(s.get('version_match') is True for s in row['sources']), ('Unverified native source version', item)
            assert item not in result, ('Duplicate native source classification', item)
            result[item] = row
    return result


def audit(export, root=ROOT):
    root, export = Path(root), Path(export)
    if not (export/'recipes').is_dir():
        raise FileNotFoundError('Original recipe/loot export is required; do not treat its absence as missing recipes')
    read = lambda p: json.loads(p.read_text(encoding='utf-8'))
    rules, bundle = read(root/'kubejs/config/aia2_runtime.json'), read(root/'kubejs/config/aia2_recipes.json')
    registry = set(read(root/'content/audit/registries.json')['registries']['item']) | set(rules['itemGates'])
    removed = set(bundle['remove']); producers, loot, uses = defaultdict(set), defaultdict(set), defaultdict(list)
    implicit_targets = defaultdict(set)
    scanned = 0
    for path in (export/'recipes').rglob('*.json'):
        parts = path.relative_to(export/'recipes').with_suffix('').parts
        rid = parts[0]+':'+('/'.join(parts[1:])); scanned += 1
        if rid in removed: continue
        for item in outputs(read(path)):
            if item in registry: producers[item].add(rid)
    for entry in bundle['add']:
        explicit = set(outputs(entry['json']))
        for item in explicit:
            if item in registry: producers[item].add(entry['id'])
        if entry.get('target') and entry['target'] not in explicit:
            implicit_targets[entry['target']].add(entry['id'])
    loot_root = export/'minecraft/loot_table'; loot_scanned = 0
    if loot_root.exists():
        for path in loot_root.rglob('*.json'):
            loot_scanned += 1
            for item in loot_items(read(path)):
                if item in registry: loot[item].add(path.relative_to(loot_root).with_suffix('').as_posix())
    for path in (root/'content/quests').glob('*.json'):
        data = normalize(read(path))
        for quest in data if isinstance(data, list) else data.get('quests', []):
            for task in quest['tasks']:
                if task['type'] == 'item': uses[task['item']].append(quest['id'])
    for entry in bundle['add']:
        if entry.get('target'): uses[entry['target']].append('recipe:'+entry['id'])
    findings = {row['item']: row for row in read(root/'content/audit/quest-obtainability.json')['findings']}
    context = source_context(root)
    rows = []
    for item in sorted(uses):
        recipes, tables = sorted(producers[item]), sorted(loot[item])
        if recipes: status = 'explicit_recipe_source'
        elif implicit_targets[item]: status = 'declared_native_target_requires_codec_review'
        elif tables: status = 'loot_source_not_a_recipe_gap'
        elif context.get(item, {}).get('status') == 'source_verified_native_path': status = 'verified_native_source_not_a_recipe_gap'
        elif item in findings: status = 'previous_native_context_requires_runtime'
        else: status = 'unresolved_no_explicit_static_source'
        rows.append({'item':item, 'gate':rules['itemGates'].get(item, 100), 'status':status,
                     'recipe_sources':len(recipes), 'loot_sources':len(tables),
                     'recipe_examples':' | '.join(recipes[:5]), 'loot_examples':' | '.join(tables[:3]),
                     'implicit_native_recipes':' | '.join(sorted(implicit_targets[item])),
                     'quest_uses':len(set(uses[item])), 'context':context.get(item, {}).get('description_uk', findings.get(item, {}).get('note', ''))})
    folder = root/'implementation'; folder.mkdir(parents=True, exist_ok=True)
    with (folder/'obtainability-v5-items.csv').open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)
    report = {'status':'explicit_source_audit_complete_unresolved_items_retained',
              'exported_recipes_scanned':scanned, 'compiled_recipes':len(bundle['add']),
              'loot_tables_scanned':loot_scanned, 'important_items':len(rows),
              'classification':dict(Counter(row['status'] for row in rows)),
              'source_verified_native_items':sum(row['status']=='source_verified_native_path' for row in context.values()),
              'confirmed_canonical_mismatches':sum(row.get('replacement_evidence_verified') is True for row in context.values()),
              'unresolved':[row['item'] for row in rows if row['status']=='unresolved_no_explicit_static_source'],
              'creative_essence_producers':sorted(producers['mysticalagradditions:creative_essence']),
              'creative_pool_producers':sorted(producers['botania:creative_pool']),
              'automatic_recipes_added':0,
              'limits':['Explicit recipe and loot references do not prove Survival reachability or probability.',
                        'Unknown native/dynamic/tag-output serializers, hardcoded conversions and world interactions require separate source or runtime checks.',
                        'Boss/structure loot is preserved; unresolved items are not automatically given crafting recipes.'],
              'full_pack_run':False}
    (folder/'obtainability-v5-audit.json').write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--export-root', type=Path, default=Path('/workspace/aia2-reference/export'))
    args = parser.parse_args(); print(json.dumps(audit(args.export_root), ensure_ascii=False, indent=2))
