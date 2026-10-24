#!/usr/bin/env python3
"""Compile source-backed postgame recipes and close their native alternatives.

The catalog is portable: frozen source JSON, canonical hashes, source-route
classifications, recipe IDs and the pre-v5 baseline are committed together.
No installed instance, recipe export, network or Minecraft process is required
for deterministic rebuilding and structural validation.
"""
import copy
import hashlib
import json
from collections import Counter
from pathlib import Path
try:
    from item_normalization import normalize
    from build_recipe_expansion import item_inputs, MACHINE_FOR_COMPONENT_PROCESS
except ModuleNotFoundError:
    from tools.item_normalization import normalize
    from tools.build_recipe_expansion import item_inputs, MACHINE_FOR_COMPONENT_PROCESS

ROOT = Path(__file__).resolve().parents[1]
CATALOG = 'content/recipes/v5_balance.json'
PREFIX = 'aia2:v5/'
ESSENCE = 'mysticalagradditions:creative_essence'
REPORT = 'implementation/balance-v5-audit.json'


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def write(path, obj):
    Path(path).write_text(json.dumps(obj, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')


def canonical_sha256(obj):
    return hashlib.sha256(json.dumps(obj, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def item_outputs(recipe):
    """Semantic item output fields only; never mistake input stacks for output."""
    for key in ('result', 'results', 'output', 'outputs', 'item_output', 'item_outputs'):
        value = recipe.get(key, [])
        for stack in value if isinstance(value, list) else [value]:
            if isinstance(stack, str):
                yield stack
            elif isinstance(stack, dict):
                item = stack.get('id', stack.get('item'))
                if isinstance(item, str):
                    yield item
    for key in ('base', 'gog', 'recipe'):
        if isinstance(recipe.get(key), dict):
            yield from item_outputs(recipe[key])


def tags(value):
    if isinstance(value, dict):
        if isinstance(value.get('tag'), str):
            yield value['tag']
        for key, child in value.items():
            if key not in {'result', 'results', 'output', 'outputs', 'neoforge:conditions'}:
                yield from tags(child)
    elif isinstance(value, list):
        for child in value:
            yield from tags(child)


def check(condition, *details):
    if not condition:
        raise ValueError(' '.join(map(str, details)))


def validate(root, catalog, bundle, rules):
    registry = read(root/'content/audit/registries.json')['registries']
    items = set(registry['item']) | set(rules['itemGates'])
    serializers = set(registry['recipe_serializer'])
    native_source = catalog['native_source_evidence']
    check(hashlib.sha256((root/native_source['file']).read_bytes()).hexdigest() == native_source['sha256'],
          'Native Hephaestus source evidence changed')
    codec_source = catalog['native_codec_evidence']
    check(hashlib.sha256((root/codec_source['file']).read_bytes()).hexdigest() == codec_source['sha256'],
          'Native codec source evidence changed')
    entries = catalog['add']
    ids = [entry['id'] for entry in entries]
    check(len(ids) == len(set(ids)), 'Duplicate v5 recipe ID')
    check(all(i.startswith(PREFIX) for i in ids), 'Unexpected v5 recipe ID')
    check(len(catalog['remove']) == len(set(catalog['remove'])), 'Duplicate removal')
    preserved = set(catalog['preserved_free_conversions'])
    check(not preserved.intersection(catalog['remove']), 'Free conversion removed')
    base = {entry['id']: entry for entry in bundle['add'] if not entry['id'].startswith(PREFIX)}
    # This intentionally pins all 569 recipes that predate this compiler, not
    # only their IDs: a regenerated patch may not silently alter old native law.
    for ident, digest in catalog['baseline_recipe_hashes'].items():
        check(ident in base, 'Baseline recipe deleted:', ident)
        check(canonical_sha256(base[ident]) == digest, 'Baseline recipe changed:', ident)
    check(not set(base).intersection(catalog['remove']), 'Existing AIA2 recipe removed')
    evidence = {row['id']: row for row in catalog['evidence']}
    check(set(evidence) == set(ids), 'Evidence must cover every new recipe')
    baseline_targets = {row['target'] for row in base.values()}
    check(not baseline_targets.intersection(catalog['targets']), 'A pre-v5 custom target was replaced')
    removed = set(catalog['remove'])
    covered_sources = set()
    target_producers = {}
    for target, audit in catalog['alternative_audit'].items():
        for row in audit['routes']:
            if row['action'] == 'replace_native_producer':
                check(row['id'] in removed, 'Live alternate producer:', row['id'])
    tag_items = catalog['audit_scope']['tag_evidence']
    graph = {target: set() for target in catalog['targets']}
    for entry in base.values():
        if entry.get('category') == 'component_chain':
            graph[entry['target']] = set(item_inputs(entry['json']))
            graph[entry['target']].update(MACHINE_FOR_COMPONENT_PROCESS.get(entry['json']['type'], []))
    for row in entries:
        ident, recipe, epoch, target = row['id'], row['json'], row['epoch'], row['target']
        proof = evidence[ident]
        check(target in items, 'Unknown target:', ident, target)
        check(target in set(item_outputs(recipe)), 'Recipe does not produce target:', ident)
        check(recipe['type'] in serializers, 'Unknown serializer:', ident, recipe['type'])
        post = row.get('post_completion', False)
        check((post and epoch == 99) or (not post and 1 <= epoch <= 48), 'Bad stage semantics:', ident)
        check(proof['minimum_completed'] == (48 if post else epoch-1), 'Bad completion floor:', ident)
        check(proof['actual_key_ingredient'] is False, 'Epoch key ingredient forbidden:', ident)
        target_producers.setdefault(target, []).append(ident)
        for src in proof['sources']:
            check(canonical_sha256(src['json']) == src['canonical_sha256'], 'Source hash changed:', ident, src['id'])
            if src.get('template_only'):
                check(src['json']['type'] == recipe['type'], 'Serializer changed from template:', ident)
            if not src.get('template_only'):
                check(target in set(item_outputs(src['json'])), 'Removed source had different output:', ident, src['id'])
                check(src['id'] in removed, 'Old source still active:', ident, src['id'])
                covered_sources.add(src['id'])
                # Preserve native output components/charges, yield and process
                # limits for a patch; new processes deliberately set their own.
                if src['json']['type'] == recipe['type']:
                    for key in ('result', 'output', 'results', 'outputs', 'tier', 'techLevel',
                                'inputFluid', 'processingTime', 'mana'):
                        check(recipe.get(key) == src['json'].get(key), 'Native output/process changed:', ident, key)
        ingredients = set(item_inputs(recipe))
        for tag in tags(recipe):
            ingredients.update(tag_items.get(tag, []))
        for item in ingredients:
            check(item in items, 'Unknown ingredient:', ident, item)
            check(not (item.startswith('kubejs:') and 'key' in item), 'Epoch key in ordinary recipe:', ident)
            check(rules['itemGates'].get(item, 100) <= epoch, 'Future ingredient:', ident, item)
        graph[target].update(ingredients)
        if recipe['type'] == 'draconicevolution:fusion_crafting':
            check(isinstance(recipe.get('catalyst'), dict) and recipe['catalyst']
                  and isinstance(recipe.get('ingredients'), list) and recipe['ingredients'],
                  'Missing native fusion inputs:', ident)
            check(all(isinstance(value, dict) and type(value.get('consume')) is bool
                      and isinstance(value.get('ingredient'), dict) and value['ingredient']
                      for value in recipe['ingredients']), 'Invalid native fusion ingredient:', ident)
            check(recipe['techLevel'] == 'chaotic', 'Capstone fusion tier:', ident)
            check(type(recipe.get('totalEnergy')) is int and 0 < recipe['totalEnergy'] <= 2147483647,
                  'Fusion energy outside reviewed range:', ident)
            check(len(recipe['ingredients']) <= 12, 'Fusion injector limit:', ident)
            graph[target].add('draconicevolution:crafting_core')
        if 'pattern' in recipe:
            width = max(map(len, recipe['pattern']))
            max_grid = 9 if recipe['type'] in {'avaritia:shaped_table', 'create:mechanical_crafting'} else 3
            check(0 < width <= max_grid and len(recipe['pattern']) <= max_grid, 'Grid dimensions:', ident)
            check(len({len(r) for r in recipe['pattern']}) == 1, 'Ragged shape:', ident)
            check(set(''.join(recipe['pattern']))-{' '} == set(recipe['key']), 'Shape symbols:', ident)
        if recipe['type'] == 'industrialforegoing:dissolution_chamber':
            check(len(recipe['input']) == 8, 'Dissolution chamber slot count:', ident)
            check(type(recipe.get('processingTime')) is int and recipe['processingTime'] > 0
                  and isinstance(recipe.get('inputFluid'), dict)
                  and type(recipe['inputFluid'].get('amount')) is int and recipe['inputFluid']['amount'] > 0,
                  'Invalid native dissolution timing/fluid:', ident)
        elif recipe['type'] == 'powah:energizing':
            check(len(recipe['ingredients']) <= 6, 'Powah slot count:', ident)
            check(type(recipe.get('energy')) is int and 0 < recipe['energy'] <= 9223372036854775807,
                  'Invalid native energizing energy:', ident)
        elif recipe['type'] == 'pneumaticcraft:pressure_chamber':
            check(0 < recipe['pressure'] < 5.0, 'Ordinary pressure chamber safety:', ident)
            check(isinstance(recipe.get('inputs'), list) and recipe['inputs']
                  and all(isinstance(value, dict) and type(value.get('count')) is int and value['count'] > 0
                          and bool(value.get('item') or value.get('tag')) for value in recipe['inputs']),
                  'Invalid native pressure-chamber inputs:', ident)
        elif recipe['type'] == 'botania:terra_plate':
            check(type(recipe.get('mana')) is int and recipe['mana'] > 0
                  and isinstance(recipe.get('ingredients'), list) and recipe['ingredients'],
                  'Invalid native terra-plate mana/inputs:', ident)
    check(covered_sources == removed, 'Missing source evidence for removals:', removed-covered_sources)
    nodes = set(graph)
    graph = {item: deps & nodes for item, deps in graph.items()}
    visited = set()
    def visit(item, ancestors):
        check(item not in ancestors, 'Creative/component cycle:', item, sorted(ancestors))
        if item in visited:
            return
        for child in graph[item]:
            visit(child, ancestors | {item})
        visited.add(item)
    for item in graph:
        visit(item, set())
    # Closed source targets must have no remaining primary route. Dyes,
    # container conversions and creative-alloy unpacking are expressly kept.
    for target in catalog['targets']:
        for route in catalog['alternative_audit'].get(target, {}).get('routes', []):
            check(route['id'] in removed or route['id'] in preserved,
                  'Unpatched native alternative:', target, route['id'])
    essence_recipe = next(e for e in entries if e['target'] == ESSENCE)
    check(not any('creative' in i for i in item_inputs(essence_recipe['json'])), 'Essence bootstraps itself')
    for base_recipe in base.values():
        if base_recipe.get('category') in {'component_chain', 'dual_key'} or 'epoch_key' in base_recipe.get('target', ''):
            check(ESSENCE not in set(item_inputs(base_recipe['json'])), 'Main progression requires Creative Essence')
    return {'recipes': len(entries), 'targets': len(catalog['targets']), 'source_removals': len(removed),
            'baseline_recipes_preserved': len(catalog['baseline_recipe_hashes']),
            'serializers': dict(Counter(r['json']['type'] for r in entries)),
            'post_completion_recipes': sum(r.get('post_completion', False) for r in entries),
            'creative_essence_direct_consumers': sum(ESSENCE in set(item_inputs(r['json'])) for r in entries),
            'explicit_graph_nodes': len(graph), 'explicit_graph_edges': sum(map(len, graph.values())),
            'explicit_graph_acyclic': True,
            'graph_scope': 'Explicit custom-component/selected-target ingredients plus creative-alloy tags and component-machine prerequisites; native code/world producers require in-game testing.'}


def apply(root=ROOT):
    root = Path(root)
    catalog = read(root/CATALOG)
    bundle = read(root/'kubejs/config/aia2_recipes.json')
    rules = read(root/'kubejs/config/aia2_runtime.json')
    checks = validate(root, catalog, bundle, rules)
    bundle['add'] = [r for r in bundle['add'] if not r['id'].startswith(PREFIX)] + copy.deepcopy(catalog['add'])
    previous = set(bundle.get('aia2_v5_source_removals', []))
    bundle['remove'] = sorted((set(bundle['remove'])-previous) | set(catalog['remove']))
    bundle['aia2_v5_source_removals'] = list(catalog['remove'])
    for item, spec in catalog['targets'].items():
        rules['itemGates'][item] = max(rules['itemGates'][item], spec['epoch'])
        if item in rules['blockGates']:
            rules['blockGates'][item] = max(rules['blockGates'][item], spec['epoch'])
    # Native Hephaestus rituals replace the block in place and yield no item.
    # Both item and block floors must be monotonic; no native ritual is removed.
    for tier, floor in ((1,15), (2,21), (3,21), (4,21), (5,31)):
        block = 'forbidden_arcanus:hephaestus_forge_tier_'+str(tier)
        check(block in rules['itemGates'] and block in rules['blockGates'], 'Unknown forge tier:', block)
        rules['itemGates'][block] = max(rules['itemGates'][block], floor)
        rules['blockGates'][block] = max(rules['blockGates'][block], floor)
    for row in catalog['add']:
        rules.setdefault('recipeGates', {})[row['id']] = row['epoch']
    write(root/'kubejs/config/aia2_recipes.json', bundle)
    write(root/'kubejs/config/aia2_runtime.json', rules)
    report = dict(checks, add_count=len(catalog['add']), remove_count=len(catalog['remove']), catalog_file=CATALOG,
                  catalog_sha256=hashlib.sha256((root/CATALOG).read_bytes()).hexdigest(),
                  exported_recipes_scanned=catalog['audit_scope']['exported_recipes_scanned'],
                  audited_named_targets=len(catalog['alternative_audit']),
                  audited_named_native_routes=sum(len(a['routes']) for a in catalog['alternative_audit'].values()),
                  creative_pool_removed_native_routes=['avaritia:botania_creative_pool','botania:cre/creative_pool_extreme','botania:cre/terra_plate/creative_pool'],
                  preserved_free_conversions=catalog['preserved_free_conversions'],
                  native_ritual_audit=catalog['native_ritual_audit'],
                  native_codec_evidence=catalog['native_codec_evidence'],
                  forge_gate_floors=[15,21,21,21,31],
                  full_pack_execution=False,
                  manual_checks=['Complete48 then craft every new Creative capstone using its real native process.',
                                 'Check JEI has one Creative Pool producer; all three original source IDs absent.',
                                 'Exercise native Hephaestus upgrades at tier2/3/4/5; check inherited ownership and inaccessible upgraded block at epoch below floor.',
                                 'IF tools retain zero charge and need ordinary fuel/energy; validate no automatic Infinite tier.',
                                 'Verify import/fake-player/machine processing under Machine Guard; no blanket TPS claim.'],
                  limitations=['Source output audit does not enumerate commands, loot tables, hardcoded recipes, or arbitrary external datapacks.',
                               'Native Hephaestus ritual creation is not intercepted by a ritual-specific permission hook; Machine Guard must block use/ticking of the transformed block.'])
    write(root/REPORT, report)
    return report


if __name__ == '__main__':
    print(json.dumps(apply(), ensure_ascii=False, indent=2))
