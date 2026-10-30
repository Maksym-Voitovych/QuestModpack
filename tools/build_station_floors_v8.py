"""Narrow source-backed floors for Ad Astra's six orbit station recipes.

Frozen export bytes make normal generation portable. This module changes only
the six recipe access floors; it never creates recipes, pays inputs, constructs
structures, or claims optional-mod dispatch has been tested.
"""
import copy
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CATALOG = 'content/recipes/v8_station_floors.json'
RUNTIME = 'kubejs/config/aia2_runtime.json'
SERIALIZER = 'ad_astra:space_station_recipe'
FLOORS = {'ad_astra:' + orbit + '_orbit': epoch for orbit, epoch in (
    ('earth', 37), ('moon', 37), ('mars', 37),
    ('mercury', 38), ('venus', 38), ('glacio', 38))}
RECIPES = {dimension.replace(':', ':space_station/') + '_space_station': dimension
           for dimension in FLOORS}
RECIPE_SHA256 = {'ad_astra:space_station/earth_orbit_space_station': '535fdab424f99f35b30b218f73f012c04e938c33981a545b72f54afc9925bac5',
 'ad_astra:space_station/glacio_orbit_space_station': '7332aa3490d8986b54a69f056077e4c8f280d955aedd441984503ad86ddd05b9',
 'ad_astra:space_station/mars_orbit_space_station': '72ca901e36c17518230460e552977a847f1c783d7cef593c627a031adbc5d505',
 'ad_astra:space_station/mercury_orbit_space_station': 'b362a501c79ee9b7f3e8136d210503d0a8e34a8bccc9b5fff9191cec9f1a55a5',
 'ad_astra:space_station/moon_orbit_space_station': '824fbd8ba59ece2d71558e3fee9399f3de0413a96a7141e1d41344b891b82247',
 'ad_astra:space_station/venus_orbit_space_station': '78f824099febee1dea71af5724cf8126ac843d6d7e4e36d4de2181fa05183832'}
TAG_SHA256 = {'ad_astra:calorite_ingots': '1d5a2e8d6223c7d0f149a55bf7708881fe5a2de7143e2564740b9f589446a65c',
 'ad_astra:calorite_plates': '121a572ef6239e8073198b90d099177dcf5398961599152a8eb68b4127f944ec',
 'ad_astra:desh_ingots': '8921a80ec2998fd7bf15715301e93dba5b4da4d82390e169b811a21bce2e94ac',
 'ad_astra:desh_plates': '1b01c48159220b25bd8a90a52faf91b59e60b1918da8d72ba2c2b233af801ce1',
 'ad_astra:iron_plates': '4bc5422ea41078761953d65b8cddb18df35fef685c8aa33c1d33e51e9e995949',
 'ad_astra:ostrum_ingots': 'e6524a740fa8c894eaa15808a4f4139c5467d2016892c4713ea3fe82b5a3ae77',
 'ad_astra:ostrum_plates': 'f681230dc4feebe14101cde85be183f682f8a532ae217a80251777908945df80',
 'ad_astra:steel_ingots': 'bb5f46bf1e791f2471e836d85ac8ee9fc77fc951f1e7210b330951b1fd3e32cc',
 'ad_astra:steel_plates': '0ce4655f32fa25b319e36f4f021d4701b640062c9948a1a8c7dc28155907fb07',
 'c:ingots/calorite': '67c729500f414531fac2e5ed057839508bcb72880b51875e1631bcdf36271ef1',
 'c:ingots/desh': '52b4a5fab42ed98bbf80143c3e039d54ad6b67168b9f7ab68c7cd81831920510',
 'c:ingots/ostrum': 'a97adcd4699ebb4817bdc17c2fe78c6e22d70a9798129b78b9db5a5a0519b810',
 'c:ingots/steel': '37d1d8e8c380276dfff9ed0f83134aae1673105384de24b12124c972334e64a9',
 'c:plates/calorite': 'b9d602e582ebce110ac95eb97d6158c4d4778dbf5b6d4992206551780ec5ffda',
 'c:plates/desh': '7df8e4c11fecf342eb75d6b68c7c73017c3f23548246e12bc813fc442153eacf',
 'c:plates/iron': 'd0e121461a51be5f9af6561b0bfe0dd15866b113c1729f8cf6f3b235211c8817',
 'c:plates/ostrum': '3ace09338a88bcd5d2a945064cf8869458267f42967340f74feb51a2fe4a05c5',
 'c:plates/steel': '26b29a3a82af872f5df18c2f9d0f4bc61ef2af2a80349306785ae29c17a27f70'}


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def exact_integer(value, lower, upper):
    return type(value) is int and lower <= value <= upper


def frozen_text(row, expected_path, expected_sha):
    """A coordinated JSON/text/hash edit is not a new verified native source."""
    assert row.get('export_path') == expected_path, 'Changed station source export path'
    assert row.get('source_sha256') == expected_sha, 'Unreviewed station source SHA'
    assert isinstance(row.get('source_text'), str), 'Missing station source text'
    raw = row['source_text'].encode('utf-8')
    assert hashlib.sha256(raw).hexdigest() == expected_sha, 'Station exact source SHA mismatch'
    return json.loads(raw)


def tag_members(evidence):
    assert isinstance(evidence, list), 'Station tag evidence must be a list'
    by_id = {row['tag']: row for row in evidence}
    assert len(by_id) == len(evidence) and set(by_id) == set(TAG_SHA256), 'Incomplete or duplicate station tag evidence'
    resolved, active = {}, set()

    def visit(tag):
        assert tag not in active, 'Cyclic station tag evidence'
        if tag in resolved:
            return resolved[tag]
        active.add(tag)
        row = by_id[tag]
        values = frozen_text(row, 'tags/minecraft/item/' + tag.replace(':', '/') + '.json', TAG_SHA256[tag])
        assert isinstance(values, list) and 1 <= len(values) <= 64, 'Unbounded station tag values'
        items = set()
        for value in values:
            assert isinstance(value, str) and ':' in value, 'Unsupported station tag value'
            if value.startswith('#'):
                child = value[1:].removesuffix('?')
                assert child in by_id, 'Missing nested station tag evidence'
                items.update(visit(child))
            else:
                assert not value.endswith('?'), 'Unreviewed optional station item'
                items.add(value)
            assert len(items) <= 16384, 'Unbounded station tag membership'
        active.remove(tag)
        assert sorted(items) == row.get('resolved_item_ids'), 'Station tag membership differs from export'
        resolved[tag] = items
        return items

    for tag in by_id:
        visit(tag)
    return resolved


def recipe_inputs(recipe, dimension):
    """Validate the real count-bearing IngredientHolder JSON shape, not a guess."""
    assert isinstance(recipe, dict) and set(recipe) == {'type', 'dimension', 'ingredients', 'structure'}, 'Unsupported station recipe shape'
    assert recipe['type'] == SERIALIZER, 'Wrong station recipe serializer'
    assert recipe['dimension'] == dimension and dimension in FLOORS, 'Wrong station recipe dimension'
    assert recipe['structure'] == 'ad_astra:space_station', 'Unreviewed station structure'
    ingredients = recipe['ingredients']
    assert isinstance(ingredients, list) and 1 <= len(ingredients) <= 64, 'Unbounded station ingredient count'
    total = 0
    for holder in ingredients:
        assert isinstance(holder, dict) and set(holder) == {'count', 'ingredient'}, 'Unsupported station holder shape'
        assert exact_integer(holder['count'], 1, 4096), 'Invalid station material count'
        total += holder['count']
        assert total <= 16384, 'Unbounded station material total'
        ingredient = holder['ingredient']
        assert isinstance(ingredient, dict) and set(ingredient) in ({'item'}, {'tag'}), 'Unsupported station ingredient shape'
        assert isinstance(next(iter(ingredient.values())), str), 'Unsupported station ingredient ID'
    return ingredients


def validate(root=ROOT, catalog=None, runtime=None, compiled=False):
    root = Path(root)
    catalog = copy.deepcopy(catalog if catalog is not None else read(root / CATALOG))
    runtime = runtime if runtime is not None else read(root / RUNTIME)
    assert catalog.get('schema') == 1 and catalog.get('mod_id') == 'ad_astra', 'Unsupported station catalog schema'
    assert catalog.get('installed_version') == '1.16.26' and catalog.get('minecraft') == '1.21.1', 'Unreviewed station source version'
    assert catalog.get('serializer') == SERIALIZER, 'Wrong station catalog serializer'
    assert catalog.get('new_recipes') == 0 and catalog.get('changed_native_recipe_floors') == 6, 'Station floors must not add recipes'
    assert catalog.get('full_modpack_dispatch_tested') is False, 'Static station source validation cannot certify native dispatch'
    assert catalog.get('baseline_recipe_floors') == {key: 0 for key in RECIPES}, 'Changed station baseline scope'
    recipes = catalog.get('recipes')
    assert isinstance(recipes, list), 'Station recipe evidence must be a list'
    by_id = {row['recipe_id']: row for row in recipes}
    assert len(by_id) == len(recipes) == 6 and set(by_id) == set(RECIPES), 'Exactly six native station recipe sources required'
    tags = tag_members(catalog.get('input_tag_evidence'))
    recipe_gates, dimension_gates, item_gates = (runtime.get(key, {}) for key in ('recipeGates', 'dimensionGates', 'itemGates'))
    alternatives, late_alternatives = set(), set()
    for ident, dimension in RECIPES.items():
        row, epoch = by_id[ident], FLOORS[dimension]
        assert row.get('dimension') == dimension and row.get('stage') == epoch, 'Wrong station floor/dimension evidence'
        assert type(dimension_gates.get(dimension)) is int and dimension_gates[dimension] == epoch, 'Station dimension floor missing or changed'
        assert ident in recipe_gates and exact_integer(recipe_gates[ident], 0, 100), 'Station recipe floor missing or invalid'
        if compiled:
            assert recipe_gates[ident] >= epoch, 'Station recipe floor below destination dimension'
        recipe = frozen_text(row, 'recipes/' + ident.replace(':', '/') + '.json', RECIPE_SHA256[ident])
        assert recipe == row.get('json'), 'Station recipe JSON differs from frozen native source'
        for holder in recipe_inputs(recipe, dimension):
            ingredient = holder['ingredient']
            if 'tag' in ingredient:
                assert ingredient['tag'] in tags, 'Missing station ingredient tag evidence'
                members = tags[ingredient['tag']]
            else:
                members = {ingredient['item']}
            assert members and all(item in item_gates and exact_integer(item_gates[item], 0, 100) for item in members), 'Unknown station ingredient item or floor'
            assert any(item_gates[item] <= epoch for item in members), 'Future-only station ingredient strands construction'
            alternatives.update(members)
            late_alternatives.update(item for item in members if item_gates[item] > epoch)
    return {'status': 'passed', 'native_recipe_floors': 6, 'new_recipes': 0,
            'destination_floors': dict(FLOORS), 'frozen_recipe_sources': 6,
            'frozen_input_tag_sources': len(tags), 'input_item_alternatives': len(alternatives),
            'future_tag_alternatives_retained': len(late_alternatives),
            'native_costs_and_structures_preserved': True, 'full_modpack_dispatch_tested': False}


def apply(root=ROOT):
    """Validate first and only raise six already existing recipe access floors."""
    root = Path(root)
    before = read(root / RUNTIME)
    report = validate(root, runtime=before)
    after = copy.deepcopy(before)
    for ident, dimension in RECIPES.items():
        after['recipeGates'][ident] = max(after['recipeGates'][ident], FLOORS[dimension])
    validate(root, runtime=after, compiled=True)
    untouched_before = {key: value for key, value in before.items() if key != 'recipeGates'}
    untouched_after = {key: value for key, value in after.items() if key != 'recipeGates'}
    assert untouched_before == untouched_after
    assert {key: value for key, value in before['recipeGates'].items() if key not in RECIPES} == {
        key: value for key, value in after['recipeGates'].items() if key not in RECIPES}
    if after != before:
        write(root / RUNTIME, after)
    return {**report, 'changed_recipe_floors': sum(before['recipeGates'][key] != after['recipeGates'][key] for key in RECIPES)}
