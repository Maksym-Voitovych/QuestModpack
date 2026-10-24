#!/usr/bin/env python3
"""Close component-based creative tablet recipes without gating ordinary tablets.

An Item ID does not distinguish Botania's finite and creative mana tablets.
This compiler addresses only frozen recipes whose actual output carries the
creative component, leaving the ordinary item gate and recipes untouched.
"""
import copy
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CATALOG = 'content/recipes/v5_component_variants.json'
REPORT = 'implementation/component-variants-v5-audit.json'
PREFIX = 'aia2:v5/variants/'
TABLET = 'botania:mana_tablet'
ESSENCE = 'mysticalagradditions:creative_essence'
RECIPE = PREFIX + 'creative_mana_tablet'


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def write(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')


def canonical(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def check(condition, *context):
    if not condition:
        raise ValueError(' '.join(map(str, context)))


def frozen(root, spec):
    relative = Path(spec['path'])
    check(not relative.is_absolute() and '..' not in relative.parts, 'Nonportable variant evidence:', relative)
    path = (root/relative).resolve()
    check(path.is_relative_to(root.resolve()) and path.is_file(), 'Missing variant evidence:', relative)
    content = path.read_bytes()
    check(hashlib.sha256(content).hexdigest() == spec['sha256'], 'Changed variant source:', relative)
    return content


def result_stacks(recipe):
    """Read semantic output positions, never arbitrary input component data."""
    for key in ('result', 'results', 'output', 'outputs', 'item_output', 'item_outputs'):
        value = recipe.get(key, [])
        for stack in value if isinstance(value, list) else [value]:
            if isinstance(stack, dict):
                yield stack
    for key in ('recipe', 'base', 'baseRecipe', 'gog'):
        if isinstance(recipe.get(key), dict):
            yield from result_stacks(recipe[key])


def is_creative_tablet(stack):
    if stack.get('id', stack.get('item')) != TABLET:
        return False
    flag = stack.get('components', {}).get('minecraft:custom_data', {}).get('creative')
    return flag is True or type(flag) is int and flag == 1


def validate(root, catalog, bundle, rules):
    root = Path(root)
    check(catalog.get('schema') == 1 and catalog.get('prefix') == PREFIX, 'Unsupported variant catalog')
    entries = catalog['add']
    check(len(entries) == 1 and entries[0]['id'] == RECIPE, 'Unexpected variant recipe set')
    entry = entries[0]
    check(entry.get('epoch') == 99 and entry.get('post_completion') is True,
          'Creative tablet requires completed48, not current epoch48')
    recipe = entry['json']
    check(recipe.get('type') == 'botania:terra_plate', 'Creative tablet must use its reviewed Terra Plate codec')
    check(type(recipe.get('mana')) is int and 0 < recipe['mana'] <= 2147483647,
          'Invalid Terra Plate mana cost')
    registry = read(root/'content/audit/registries.json')['registries']
    check(recipe['type'] in registry['recipe_serializer'], 'Unregistered Terra Plate serializer')
    check(rules['itemGates'].get(TABLET) == catalog['ordinary_item_gate'] < 99,
          'Ordinary tablet item gate was changed')
    check(TABLET in registry['item'], 'Unregistered ordinary tablet')
    routes = catalog['route_evidence']
    check(len({s['id'] for s in routes}) == len(routes), 'Duplicate tablet route evidence')
    creative, ordinary, source_json = set(), set(), {}
    for spec in routes:
        source = json.loads(frozen(root, spec))
        source_json[spec['id']] = source
        outputs = [s for s in result_stacks(source) if s.get('id', s.get('item')) == TABLET]
        check(outputs, 'Frozen route does not produce a tablet:', spec['id'])
        if any(is_creative_tablet(stack) for stack in outputs):
            check(spec['kind'] == 'creative_variant', 'Creative route misclassified:', spec['id'])
            creative.add(spec['id'])
        else:
            check(spec['kind'] == 'ordinary_tablet', 'Ordinary tablet misclassified:', spec['id'])
            ordinary.add(spec['id'])
    check(len(catalog['remove']) == len(set(catalog['remove'])) and set(catalog['remove']) == creative,
          'A creative producer remains active or an ordinary recipe was removed')
    check(set(catalog['preserved_normal_routes']) == ordinary and
          not ordinary & set(bundle['remove']), 'Ordinary tablet recipe removed')
    scan_spec = {'path': catalog['audit_scope']['scan_path'], 'sha256': catalog['audit_scope']['scan_sha256']}
    scan = json.loads(frozen(root, scan_spec))
    check(scan['exported_recipes_scanned'] == catalog['audit_scope']['exported_recipes_scanned'] == 42064,
          'Variant export scan scope changed')
    check({row['id'] for row in scan['creative_routes']} == creative and
          {row['id'] for row in scan['normal_routes']} == ordinary,
          'Variant routes differ from full-export scan')
    for proof in catalog['source_evidence']:
        frozen(root, proof)
    # Native Terra Plate ItemStack.STRICT_CODEC retains the exact reviewed
    # custom_data and rarity, including creative:1's numeric representation.
    original = source_json['botania:cre/terra_plate/creative_mana_tablet']['result']
    check(recipe.get('result') == original and is_creative_tablet(recipe['result']),
          'Creative output components/count differ from native result')
    ingredients = recipe.get('ingredients', [])
    check(ingredients and all(isinstance(i, dict) and set(i) == {'item'} for i in ingredients),
          'Only reviewed explicit Terra Plate ingredients are supported')
    items = [i['item'] for i in ingredients]
    check(ESSENCE in items and items.count(TABLET) == 1, 'Missing Creative Essence or ordinary tablet input')
    check(items.count(ESSENCE) >= 1 and entry.get('target') == TABLET, 'Invalid creative tablet target')
    keys = {e['key'] for e in rules['epochs']} | {k['output'] for k in rules.get('dualKeys', [])}
    for item in items:
        check(item in rules['itemGates'], 'Unknown variant ingredient:', item)
        check(rules['itemGates'][item] <= 99, 'Unavailable variant ingredient:', item)
        check(item not in keys and not (item.startswith('kubejs:') and 'key' in item),
              'Epoch key in variant recipe:', item)
    actual = {r['id']: r for r in bundle['add']}
    for identifier, digest in catalog['baseline_recipe_hashes'].items():
        check(identifier in actual and canonical(actual[identifier]) == digest,
              'Existing recipe changed by variant patch:', identifier)
    check(not set(catalog['remove']) & set(actual), 'Variant removal targets a custom existing recipe')
    for row in bundle['add']:
        if row['id'] == 'aia2:v5/synthesis/creative_essence':
            # The essence's established recipe must not use this creative
            # variant (or any tablet); this patch cannot bootstrap its own cost.
            check(TABLET not in json.dumps(row['json']), 'Creative Essence bootstraps from its tablet')
    return {'recipes': 1, 'source_removals': len(creative), 'preserved_normal_routes': sorted(ordinary),
            'baseline_recipes_preserved': len(catalog['baseline_recipe_hashes']),
            'minimum_completed_epochs': 48, 'ordinary_item_gate': rules['itemGates'][TABLET],
            'component_aware_output_verified': True}


def apply(root=ROOT):
    root = Path(root)
    catalog = read(root/CATALOG)
    bundle = read(root/'kubejs/config/aia2_recipes.json')
    rules = read(root/'kubejs/config/aia2_runtime.json')
    checks = validate(root, catalog, bundle, rules)
    bundle['add'] = [r for r in bundle['add'] if not r['id'].startswith(PREFIX)] + copy.deepcopy(catalog['add'])
    previous = set(bundle.get('aia2_v5_variant_source_removals', []))
    bundle['remove'] = sorted((set(bundle['remove']) - previous) | set(catalog['remove']))
    bundle['aia2_v5_variant_source_removals'] = sorted(catalog['remove'])
    rules.setdefault('recipeGates', {})[RECIPE] = 99
    # Intentionally no itemGates or blockGates mutation: ordinary tablets stay
    # available. The server recipe ID, not the base Item ID, gates this variant.
    write(root/'kubejs/config/aia2_recipes.json', bundle)
    write(root/'kubejs/config/aia2_runtime.json', rules)
    report = dict(checks, catalog_file=CATALOG,
                  catalog_sha256=hashlib.sha256((root/CATALOG).read_bytes()).hexdigest(),
                  creative_tablet_removed_native_routes=sorted(catalog['remove']),
                  retained_producer=RECIPE, full_pack_execution=False,
                  limitations=catalog['limitations_uk'])
    write(root/REPORT, report)
    return report


if __name__ == '__main__':
    print(json.dumps(apply(), ensure_ascii=False, indent=2))
