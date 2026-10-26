"""Three fusion upgrades with exact native cost, tier, catalyst and conversion closure.

The installed export is authoritative for recipes. Official3.1.4 source verifies
codec/geometry; the catalog explicitly does not assert CI build633 provenance.
"""
import argparse
from collections import Counter
import copy
import json
from pathlib import Path
try:
    from build_energy_core_balance_v5 import canonical, frozen, read, write
    from audit_obtainability_v5 import outputs
except ModuleNotFoundError:
    from tools.build_energy_core_balance_v5 import canonical, frozen, read, write
    from tools.audit_obtainability_v5 import outputs

ROOT=Path(__file__).resolve().parents[1]
CATALOG='content/recipes/v5_draconic_power.json'
REPORT='implementation/draconic-power-balance-v5-audit.json'
PREFIX='aia2:v5/draconic_power/'
TARGETS={'draconicevolution:awakened_crafting_injector':41,'draconicevolution:chaotic_crafting_injector':42,'draconicevolution:draconic_relay_crystal':41}
FAMILY={**TARGETS,'draconicevolution:draconic_io_crystal':41}
CONVERSIONS={'draconicevolution:machines/draconic_relay_crystal_combine','draconicevolution:machines/draconic_io_crystal'}
TIER_PRODUCER={'wyvern':'draconicevolution:wyvern_crafting_injector','draconic':'draconicevolution:awakened_crafting_injector'}


def scan_export(export_recipes):
    import hashlib
    folder=Path(export_recipes);manifest=[];producers={item:[] for item in sorted(FAMILY)}
    for path in sorted(folder.rglob('*.json')):
        raw=path.read_bytes();rel=path.relative_to(folder)
        assert len(rel.parts)>=2,'Export namespace missing'
        manifest.append([rel.as_posix(),hashlib.sha256(raw).hexdigest()])
        ident=rel.parts[0]+':'+rel.with_suffix('').as_posix().split('/',1)[1]
        for target in set(outputs(json.loads(raw)))&FAMILY.keys():producers[target].append(ident)
    return {'recipes_scanned':len(manifest),'manifest_sha256':canonical(manifest),'targets':producers}


def ingredient(data):
    assert type(data) is dict,'Unreviewed fusion ingredient'
    if set(data)=={'item'} and type(data['item']) is str:return ('item',data['item'],1)
    if set(data)=={'tag'} and type(data['tag']) is str:return ('tag',data['tag'],1)
    assert set(data)=={'type','items','count'} and data['type']=='draconicevolution:stack','Unreviewed fusion ingredient codec'
    assert type(data['items']) is str and type(data['count']) is int and 1<=data['count']<=64,'Invalid stack catalyst count'
    return ('item',data['items'],data['count'])


def fusion_cost(recipe):
    assert recipe['type']=='draconicevolution:fusion_crafting'
    entries=[recipe['catalyst']]
    assert type(recipe['ingredients']) is list and 1<=len(recipe['ingredients'])<=11,'Unreviewed injector count'
    for entry in recipe['ingredients']:
        assert set(entry)=={'consume','ingredient'} and entry['consume'] is True,'Nonconsumed or malformed fusion input'
        entries.append(entry['ingredient'])
    return Counter((kind,ident) for value in entries for kind,ident,count in [ingredient(value)] for _ in range(count))


def craft_conflicts(root):
    conflicts=[]
    for path in (Path(root)/'content/quests').glob('*.json'):
        data=read(path)
        for quest in data if isinstance(data,list) else data.get('quests',[]):
            for task in quest.get('tasks',[]):
                if task.get('type')=='item' and task.get('item') in TARGETS and task.get('craft') is True:conflicts.append(quest['id'])
    return conflicts


def validate(root,catalog,bundle,rules,compiled=False,export_recipes=None):
    root=Path(root)
    assert catalog['schema']==1 and catalog['installed_versions']=={'draconicevolution':'3.1.4.633'},'Installed DE contract changed'
    assert len(catalog['recipes'])==3 and {s['target']:s['epoch'] for s in catalog['recipes']}==TARGETS,'Target scope changed'
    baseline=catalog['baseline_recipe_hashes'];assert len(baseline)==618,'Published618 baseline required'
    actual={row['id']:row for row in bundle['add']};assert len(actual)==len(bundle['add']),'Duplicate custom recipe'
    for ident,digest in baseline.items():assert ident in actual and canonical(actual[ident])==digest,('Published baseline changed',ident)
    assert not [row['id'] for row in bundle['add'] if not row['id'].startswith(PREFIX) and set(outputs(row['json']))&FAMILY.keys()],'Unreviewed custom family producer'
    texts={Path(s['path']).name:frozen(root,s).decode() for s in catalog['sources']}
    assert 'mod_version=3.1.4' in texts['gradle.properties'] and 'mc_version=1.21.1' in texts['gradle.properties']
    assert 'BUILD_NUMBER' in texts['build.gradle'],'Source build suffix missing'
    for token in ['Codec.LONG.fieldOf("totalEnergy")','TechLevel.CODEC.fieldOf("techLevel")','Codec.list(FusionIngredient.CODEC).fieldOf("ingredients")']:
        assert token in texts['FusionRecipe.java'],('Unverified fusion codec',token)
    assert 'getCustomIngredient() instanceof StackIngredient' in texts['IFusionRecipe.java'] and 'catalyst.shrink(catCount)' in texts['IFusionRecipe.java']
    assert 'Codec.INT.optionalFieldOf("count", 1)' in texts['StackIngredient.java']
    assert 'int radius = 1' in texts['TileFusionCraftingCore.java'] and 'fusionInjectorRange' in texts['TileFusionCraftingCore.java']
    assert '.setDefaultInt(16)' in texts['DEConfig.java'] and '.setDefaultInt(2)' in texts['DEConfig.java']
    witness=catalog['injector_layout_witness']['positions'];assert len(witness)==11 and len({tuple(x) for x in witness})==11
    assert all(abs(x)==4 and abs(y)<=1 and abs(z)<=1 for x,y,z in witness),'Injector witness outside source scan arms'
    assert all((x//abs(x),y,z)!=(a//abs(a),b,c) for i,(x,y,z) in enumerate(witness) for a,b,c in witness[i+1:]),'Collinear injector witness'
    scan=json.loads(frozen(root,catalog['producer_scan']))
    assert scan['recipes_scanned']==42064 and set(scan['targets'])==set(FAMILY) and not scan['existing_custom_family_producers'],'Incomplete producer closure'
    if export_recipes is not None:
        reproduced=scan_export(export_recipes)
        assert all(scan[k]==v for k,v in reproduced.items()),'Full producer scan differs'
    registry=json.loads(frozen(root,catalog['registry_evidence']))
    assert registry['registry_entries']==27964 and len(registry['source_sha256'])==64
    assert not craft_conflicts(root),'Fusion output cannot use vanilla craft:true task'
    removed=set();seen=set()
    for spec in catalog['recipes']:
        ident,target,epoch,recipe=spec['id'],spec['target'],spec['epoch'],spec['json']
        assert ident==PREFIX+target.split(':',1)[1] and ident not in seen,'Invalid or duplicate DE recipe ID';seen.add(ident)
        assert spec['category']=='integration' and spec['producer']=='draconicevolution:crafting_core'
        assert rules['itemGates'].get(target)==epoch and rules['blockGates'].get(target)==epoch,'DE target floor drift'
        assert rules['blockGates'].get(spec['producer'],100)<=epoch,'Future fusion core'
        assert set(recipe)=={'type','catalyst','ingredients','result','techLevel','totalEnergy'},'Unreviewed fusion fields'
        source_id='draconicevolution:machines/'+target.split(':',1)[1]
        assert spec['remove_recipe_ids']==[source_id] and len(spec['sources'])==1,'Unexpected producer removal'
        source=spec['sources'][0];assert source['recipe_id']==source_id
        original=json.loads(frozen(root,source));expected=copy.deepcopy(original)
        expected['ingredients'] += [{'consume':True,'ingredient':{'item':spec['magic_input']}},{'consume':True,'ingredient':{'item':spec['tech_input']}}]
        assert recipe==expected,'Native catalyst/materials/energy/tier/output changed'
        assert type(recipe['totalEnergy']) is int and recipe['totalEnergy']>0,'Invalid energy quantity'
        assert type(recipe['result']['count']) is int and recipe['result']['id']==target,'Invalid output quantity'
        assert recipe['techLevel']==spec['required_injector_tier'] and recipe['techLevel'] in TIER_PRODUCER
        injector=TIER_PRODUCER[recipe['techLevel']]
        assert injector!=target and rules['blockGates'].get(injector,100)<=epoch,'Future or self-dependent tier producer'
        assert len(recipe['ingredients'])==spec['injectors_needed']<=11
        assert spec['magic_input'].startswith('botania:') and spec['tech_input'].split(':')[0] in {'ae2','mekanism'}
        assert spec['magic_input']!=spec['tech_input']
        for kind,item in fusion_cost(recipe):
            if kind=='tag':
                assert item in catalog['tag_evidence'],'Missing native tag evidence'
                members=json.loads(frozen(root,catalog['tag_evidence'][item]['source']))
                assert members==catalog['tag_evidence'][item]['members']
                members=[m for m in members if not m.startswith('#')]
                assert any(m in registry['items'] and rules['itemGates'].get(m,100)<=epoch for m in members),'No reachable native tag member'
            else:
                assert item in registry['items'] and rules['itemGates'].get(item,100)<=epoch,('Future or unknown input',item)
                assert (item not in TARGETS or TARGETS[item]<epoch) and not item.startswith('kubejs:'),'Bootstrap/key dependency'
        assert set(spec['remove_recipe_ids'])<=set(scan['targets'][target]);removed.add(source_id)
        if compiled:
            expected_row={k:copy.deepcopy(spec[k]) for k in ['id','epoch','target','category','json']}
            assert actual.get(ident)==expected_row and rules['recipeGates'].get(ident)==epoch,'Compiled fusion record/gate differs'
    preserved=catalog['preserved_producer_contracts'];assert set(preserved)==CONVERSIONS
    units=scan['family_units'];assert units=={'draconicevolution:draconic_relay_crystal':2,'draconicevolution:draconic_io_crystal':1}
    for rid,contract in preserved.items():
        recipe=json.loads(frozen(root,contract['source']));assert recipe['type']=='minecraft:crafting_shapeless'
        assert sum(units[x['item']] for x in recipe['ingredients'])==units[recipe['result']['id']]*recipe['result']['count'],'Lossy/gaining crystal conversion'
        assert rid not in bundle['remove'] and rules['recipeGates'].get(rid)==41,'Lossless conversion was removed or ungated'
    assert {rid for ids in scan['targets'].values() for rid in ids}==removed|set(preserved),'Unclassified primary/alternate producer'
    if compiled:assert removed<=set(bundle['remove']),'Cheap native fusion producer remains'
    return {'status':'passed','recipes':3,'serializers':{'draconicevolution:fusion_crafting':3},'native_producers_replaced':3,'lossless_conversion_routes_preserved':2,'published_custom_recipes_preserved':618,'maximum_injector_inputs':11,'native_tier_energy_catalyst_output_preserved':True,'full_export_recipes_scanned':42064,'full_export_verified_this_run':export_recipes is not None,'source_ci_build633_verified':False,'full_pack_execution':False}


def apply(root=ROOT):
    root=Path(root);catalog=read(root/CATALOG);bundle=read(root/'kubejs/config/aia2_recipes.json');rules=read(root/'kubejs/config/aia2_runtime.json')
    validate(root,catalog,bundle,rules)
    owned={r['id'] for r in catalog['recipes']}
    bundle['add']=[r for r in bundle['add'] if r['id'] not in owned]+[{k:copy.deepcopy(r[k]) for k in ['id','epoch','target','category','json']} for r in catalog['recipes']]
    removed=sorted({rid for r in catalog['recipes'] for rid in r['remove_recipe_ids']})
    bundle['remove']=sorted(set(bundle['remove'])|set(removed));bundle['aia2_v5_draconic_power_source_removals']=removed
    for row in sorted(catalog['recipes'],key=lambda r:r['id']):rules['recipeGates'][row['id']]=row['epoch']
    report=validate(root,catalog,bundle,rules,compiled=True)
    write(root/'kubejs/config/aia2_recipes.json',bundle);write(root/'kubejs/config/aia2_runtime.json',rules);write(root/REPORT,report)
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('command',choices=['apply','validate']);parser.add_argument('--root',type=Path,default=ROOT);parser.add_argument('--compiled',action='store_true');parser.add_argument('--export-recipes',type=Path);args=parser.parse_args()
    result=apply(args.root) if args.command=='apply' else validate(args.root,read(args.root/CATALOG),read(args.root/'kubejs/config/aia2_recipes.json'),read(args.root/'kubejs/config/aia2_runtime.json'),compiled=args.compiled,export_recipes=args.export_recipes)
    print(json.dumps(result,ensure_ascii=False,indent=2))
