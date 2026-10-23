#!/usr/bin/env python3
"""Merge the curated, source-backed v4 recipe catalog into generated runtime files.

This compiler does not discover or invent recipes. The catalog stores the exact
native input/output template, its exported source hash, the specific earlier
component used, and an explanation for every deliberately selected target.
"""
import copy
import hashlib
import json
from collections import Counter
from pathlib import Path
try:
    from item_normalization import normalize
except ModuleNotFoundError:
    from tools.item_normalization import normalize

ROOT = Path(__file__).resolve().parents[1]
PREFIX = 'aia2:v4/'
CATALOG = 'content/recipes/v4_expansion.json'
MACHINE_FOR_COMPONENT_PROCESS = {
    'create:mixing': ['create:mechanical_mixer', 'create:basin'],
    'create:compacting': ['create:mechanical_press', 'create:basin'],
    'botania:mana_infusion': ['botania:mana_pool'],
    'botania:runic_altar': ['botania:runic_altar', 'botania:mana_pool', 'botania:mana_spreader'],
    'mekanism:metallurgic_infusing': ['mekanism:metallurgic_infuser'],
    'oritech:foundry': ['oritech:foundry_block'],
    'oritech:assembler': ['oritech:assembler_block'],
    'draconicevolution:fusion_crafting': ['draconicevolution:crafting_core'],
}


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def write(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')


def item_inputs(value):
    if isinstance(value, dict):
        for key, child in value.items():
            if key in {'result','results','output','outputs','item_output','item_outputs','ritual_dummy',
                       'neoforge:conditions','conditions'}:
                continue
            if key in {'item','items'} and isinstance(child,str):
                yield child
            else:
                yield from item_inputs(child)
    elif isinstance(value, list):
        for child in value:
            yield from item_inputs(child)


def native_metadata(recipe):
    """Ignore only the input fields this catalog is allowed to modify."""
    recipe=copy.deepcopy(recipe)
    kind=recipe.get('type','')
    if ':' not in kind: recipe['type']='minecraft:'+kind; kind=recipe['type']
    fields={
        'minecraft:crafting_shaped':['pattern','key'],
        'minecraft:crafting_shapeless':['ingredients'],
        'mekanism:mek_data':['pattern','key'],
        'enderio:shaped_entity_storage':['pattern','key'],
        'actuallyadditions:copy_nbt':['pattern','key'],
        'actuallyadditions:copy_nbt_shapeless':['ingredients'],
        'immersiveengineering:blueprint':['inputs'],
        'modern_industrialization:assembler':['item_inputs'],
        'industrialforegoing:dissolution_chamber':['input'],
        'powah:energizing':['ingredients'],
        'ars_nouveau:enchanting_apparatus':['pedestalItems'],
        'occultism:ritual':['ingredients'],
        'oritech:assembler':['ingredients'],
    }
    for key in fields.get(kind,[]):recipe.pop(key,None)
    for key in ['base','gog','recipe']:
        if isinstance(recipe.get(key),dict):recipe[key]=native_metadata(recipe[key])
    return recipe


def validate(root, catalog, bundle, rules):
    registry = read(root/'content/audit/registries.json')['registries']
    items = set(registry['item']) | set(rules['itemGates'])
    serializers = set(registry['recipe_serializer'])
    entries = catalog['add']
    ids = [entry['id'] for entry in entries]
    assert len(ids) == len(set(ids)), 'Duplicate v4 recipe ID'
    assert all(ident.startswith(PREFIX) for ident in ids), 'Unexpected recipe namespace'
    assert len(catalog['remove']) == len(set(catalog['remove']))
    assert not set(catalog['remove']) & set(catalog.get('preserved_free_conversions',[])), 'Free form conversion removed'
    base = [entry for entry in bundle['add'] if not entry['id'].startswith(PREFIX)]
    base_targets = {entry.get('target') for entry in base}
    evidence = {row['id']:row for row in catalog['evidence']}
    assert set(evidence) == set(ids)
    targets = set(catalog['targets'])
    assert not targets & base_targets, ('Existing recipe target modified', sorted(targets & base_targets))
    component_graph = {}
    for entry in base:
        if entry.get('category') == 'component_chain':
            component_graph[entry['target']] = set(item_inputs(entry['json']))
            component_graph[entry['target']].update(MACHINE_FOR_COMPONENT_PROCESS.get(entry['json']['type'],[]))
    graph = {target:set() for target in targets}
    protected_fields = ['result','results','output','outputs','item_outputs','energy','eu','duration',
                        'processingTime','inputFluid','sourceCost','reagent','activation_item',
                        'pentacle_id','ritual_type','ritual_dummy']
    for entry in entries:
        recipe = entry['json']; proof = evidence[entry['id']]
        assert entry['target'] in items and entry['target'] in targets, entry['id']
        assert recipe['type'] in serializers, (entry['id'],recipe['type'])
        assert 1 <= proof['component_epoch'] < entry['epoch'] <= 48, entry['id']
        assert proof['component'] in items, entry['id']
        assert proof['component'] in set(item_inputs(recipe)), entry['id']
        assert proof['source_recipe'] in catalog['remove'], entry['id']
        assert proof['source_recipe'] not in {row['id'] for row in base}, entry['id']
        source = proof['source_json']
        canonical_hash = hashlib.sha256(json.dumps(source,sort_keys=True,separators=(',',':')).encode()).hexdigest()
        assert canonical_hash == proof['source_canonical_sha256'], ('Source template changed',entry['id'])
        assert native_metadata(normalize(source))==native_metadata(recipe), ('Native recipe metadata changed',entry['id'])
        for field in protected_fields:
            assert recipe.get(field) == source.get(field), ('Native output/energy/core metadata changed',entry['id'],field)
        for item in item_inputs(recipe):
            assert item in items, ('Unknown recipe ingredient',entry['id'],item)
            assert not (item.startswith('kubejs:') and 'key' in item), ('Progression key in ordinary recipe',entry['id'])
            assert rules['itemGates'].get(item,100) <= entry['epoch'], ('Future ingredient',entry['id'],item)
            if item in targets or item in component_graph:
                graph[entry['target']].add(item)
        for branch in [recipe] + [recipe[key] for key in ['base','gog','recipe'] if isinstance(recipe.get(key),dict)]:
            if 'pattern' in branch:
                assert 1 <= len(branch['pattern']) <= 3
                assert max(map(len,branch['pattern'])) <= 3
                assert set(''.join(branch['pattern']))-{' '} == set(branch['key'])
        kind=recipe['type']
        if kind=='modern_industrialization:assembler': assert len(recipe['item_inputs'])<=6
        elif kind=='industrialforegoing:dissolution_chamber': assert len(recipe['input'])==8
        elif kind=='powah:energizing': assert len(recipe['ingredients'])<=6
        elif kind=='ars_nouveau:enchanting_apparatus': assert len(recipe['pedestalItems'])<=8
        elif kind=='occultism:ritual': assert len(recipe['ingredients'])<=8
    for item,deps in component_graph.items(): graph[item] = deps & (targets | set(component_graph))
    visited=set()
    def visit(node,path):
        assert node not in path, ('New component/machine dependency cycle',node,sorted(path))
        if node in visited:return
        for child in graph.get(node,[]):visit(child,path|{node})
        visited.add(node)
    for node in graph:visit(node,set())
    return {'recipes':len(entries),'targets':len(targets),'graph_nodes':len(graph),
            'graph_edges':sum(map(len,graph.values())),
            'graph_scope':'Explicit native item inputs and custom-component machine prerequisites; not all hardcoded/native/world producers',
            'serializers':dict(Counter(entry['json']['type'] for entry in entries))}


def apply(root=ROOT):
    root=Path(root)
    catalog=read(root/CATALOG)
    bundle=read(root/'kubejs/config/aia2_recipes.json')
    rules=read(root/'kubejs/config/aia2_runtime.json')
    checks=validate(root,catalog,bundle,rules)
    # Repeated rebuilds replace only this compiler's IDs; no duplicate append.
    bundle['add']=[entry for entry in bundle['add'] if not entry['id'].startswith(PREFIX)]
    bundle['add'].extend(copy.deepcopy(catalog['add']))
    prior_owned=set(bundle.get('aia2_v4_source_removals',[]))
    bundle['remove']=sorted((set(bundle['remove'])-prior_owned) | set(catalog['remove']))
    bundle['aia2_v4_source_removals']=list(catalog['remove'])
    for item,spec in catalog['targets'].items():
        rules['itemGates'][item]=max(rules['itemGates'][item],spec['epoch'])
        if item in rules['blockGates']:
            rules['blockGates'][item]=max(rules['blockGates'][item],spec['epoch'])
    # An AE2 part and its full block perform the same function. Keep the free
    # conversion, while sharing access rules rather than creating a part bypass.
    for target,forms in catalog.get('equivalent_functional_forms',{}).items():
        for item in forms:
            assert item in rules['itemGates'],item
            rules['itemGates'][item]=max(rules['itemGates'][item],catalog['targets'][target]['epoch'])
            if item in rules['blockGates']:
                rules['blockGates'][item]=max(rules['blockGates'][item],catalog['targets'][target]['epoch'])
    for entry in catalog['add']:
        rules.setdefault('recipeGates',{})[entry['id']]=entry['epoch']
    write(root/'kubejs/config/aia2_recipes.json',bundle)
    write(root/'kubejs/config/aia2_runtime.json',rules)
    report=read(root/'implementation/recipes-v4-audit.json')
    report.update(checks,catalog_file=CATALOG,
                  catalog_sha256=hashlib.sha256((root/CATALOG).read_bytes()).hexdigest(),
                  add_count=len(catalog['add']),remove_count=len(catalog['remove']),
                  explicit_dependency_graph_acyclic=True,
                  baseline_native_recipe_ids_preserved=True,
                  full_pack_execution=False)
    write(root/'implementation/recipes-v4-audit.json',report)
    return report


if __name__=='__main__':
    print(json.dumps(apply(),ensure_ascii=False,indent=2))
