"""Three source-reviewed AA entry machines; preserve existing custom recipes/reset paths."""
import copy
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CATALOG = 'content/recipes/v5_aa_core.json'
PREFIX = 'aia2:v5/aa_core/'
REPORT = 'implementation/aa-core-balance-v5-audit.json'
TARGETS = {'actuallyadditions:canola_press', 'actuallyadditions:fermenting_barrel', 'actuallyadditions:oil_generator'}


def read(path): return json.loads(Path(path).read_text(encoding='utf-8'))
def write(path, value): Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
def canonical(value): return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def validate(root, catalog, bundle, rules, compiled=False):
    root = Path(root)
    assert catalog['schema'] == 1 and len(catalog['recipes']) == 3, 'Expected three reviewed AA machines'
    assert {r['target'] for r in catalog['recipes']} == TARGETS, 'AA target scope changed'
    actual = {r['id']: r for r in bundle['add']}
    assert len(actual) == len(bundle['add']), 'Duplicate recipe IDs'
    for ident, digest in catalog['baseline_recipe_hashes'].items():
        assert ident in actual and canonical(actual[ident]) == digest, ('Published recipe changed', ident)
    removals, preserved = set(), set()
    for entry in catalog['recipes']:
        ident, target, recipe = entry['id'], entry['target'], entry['json']
        assert ident == PREFIX+target.split(':')[1] and entry['epoch'] == 16
        assert len(entry['purpose_uk']) >= 30
        assert recipe['type'] == 'minecraft:crafting_shaped' and recipe['result'] == {'id': target, 'count': 1}
        pattern, keys = recipe['pattern'], recipe['key']
        assert 1 <= len(pattern) <= 3 and len({len(row) for row in pattern}) == 1
        assert all(1 <= len(row) <= 3 for row in pattern) and set(''.join(pattern))-{' '} == set(keys)
        assert all(set(v) == {'item'} for v in keys.values()), 'Only explicit reviewed ingredients supported'
        for ingredient in keys.values():
            item = ingredient['item']
            assert item in rules['itemGates'] and rules['itemGates'][item] <= 16, ('Future/unknown AA ingredient', item)
            assert item not in TARGETS and not item.startswith('kubejs:aia2_'), ('AA bootstrap cycle/key ingredient', item)
        assert rules['itemGates'][target] == rules['blockGates'][target] == 16
        assert entry['remove_recipe_ids'] == [target] and entry['preserve_recipe_ids'] == ['actuallyadditions:reset/'+target.split(':')[1]]
        sources = {}
        for spec in entry['sources']:
            path = Path(spec['path']);assert not path.is_absolute() and '..' not in path.parts
            data = (root/path).read_bytes();assert hashlib.sha256(data).hexdigest() == spec['sha256'], 'Stale AA source'
            sources[spec['recipe_id']] = json.loads(data)
        original, reset = sources[target], sources[entry['preserve_recipe_ids'][0]]
        assert original['result']['id'] == target
        assert reset['result']['id'] == target and any(i.get('item') == target for i in reset['ingredients']), 'Reset route could bootstrap machine'
        removals.update(entry['remove_recipe_ids']);preserved.update(entry['preserve_recipe_ids'])
        if compiled:
            expected = {k:copy.deepcopy(entry[k]) for k in ['id','epoch','target','category','json']}
            assert actual.get(ident) == expected and rules['recipeGates'].get(ident) == 16, 'Compiled AA recipe differs'
    assert not removals & set(catalog['baseline_recipe_hashes']), 'AA patch removes a published custom recipe'
    assert not preserved & set(bundle['remove']), 'AA reset recipe removed'
    if compiled: assert removals <= set(bundle['remove']), 'Cheap AA producers remain active'
    return {'status':'passed', 'recipes':3, 'native_producers_replaced':len(removals),
            'reset_routes_preserved':sorted(preserved), 'baseline_custom_recipes_preserved':len(catalog['baseline_recipe_hashes']),
            'full_pack_execution':False}


def apply(root=ROOT):
    root = Path(root);catalog=read(root/CATALOG)
    bundle=read(root/'kubejs/config/aia2_recipes.json');rules=read(root/'kubejs/config/aia2_runtime.json')
    validate(root,catalog,bundle,rules)
    owned={r['id'] for r in catalog['recipes']}
    bundle['add']=[r for r in bundle['add'] if r['id'] not in owned]+[
        {k:copy.deepcopy(r[k]) for k in ['id','epoch','target','category','json']} for r in catalog['recipes']]
    bundle['remove']=sorted(set(bundle['remove'])|{rid for r in catalog['recipes'] for rid in r['remove_recipe_ids']})
    for ident in sorted(owned): rules['recipeGates'][ident]=16
    report=validate(root,catalog,bundle,rules,compiled=True)
    write(root/'kubejs/config/aia2_recipes.json',bundle);write(root/'kubejs/config/aia2_runtime.json',rules)
    write(root/REPORT,report);return report
