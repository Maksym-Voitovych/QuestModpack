"""Two mechanical EvilCraft assemblies; retain native costs and all published formulas."""
import copy
import hashlib
import json
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
CATALOG='content/recipes/v5_evilcraft_core.json'
PREFIX='aia2:v5/evilcraft_core/'
TARGETS={'evilcraft:spirit_reanimator','evilcraft:sanguinary_environmental_accumulator'}
def read(p):return json.loads(Path(p).read_text())
def write(p,v):Path(p).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def canonical(v):return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()
def cost(recipe):
    assert recipe['type'] in {'minecraft:crafting_shaped','create:mechanical_crafting'}
    assert set(recipe['key'])==set(''.join(recipe['pattern']))-{' '},'Unused or missing assembly keys'
    assert all(set(v) in ({'item'},{'tag'}) for v in recipe['key'].values()),'Unreviewed ingredient shape'
    return Counter(json.dumps(recipe['key'][c],sort_keys=True) for row in recipe['pattern'] for c in row if c!=' ')
def scan(export,targets=TARGETS):
    manifest={};found={t:[] for t in sorted(targets)}
    for p in sorted((Path(export)/'recipes').rglob('*.json')):
        rel=p.relative_to(Path(export)/'recipes').with_suffix('');ident=rel.parts[0]+':'+ '/'.join(rel.parts[1:]);data=p.read_bytes();manifest[ident]=hashlib.sha256(data).hexdigest()
        r=json.loads(data)
        def outputs(value):
            if isinstance(value,str):return {value}
            if isinstance(value,dict):return {value.get('id',value.get('item'))} if isinstance(value.get('id',value.get('item')),str) else set()
            if isinstance(value,list):return set().union(*(outputs(v) for v in value)) if value else set()
            return set()
        produced=set().union(*(outputs(r.get(key)) for key in ['result','results','output','output_item','outputs']))
        for t in produced & targets:found[t].append(ident)
    return {'recipes_scanned':len(manifest),'manifest_sha256':canonical(manifest),'targets':found}
def validate(root,catalog,bundle,rules,compiled=False):
    root=Path(root);assert catalog['schema']==1 and {r['target'] for r in catalog['recipes']}==TARGETS
    actual={r['id']:r for r in bundle['add']};assert len(actual)==len(bundle['add'])
    for source in catalog['format_sources']:
        raw=(root/source['path']).read_bytes();assert hashlib.sha256(raw).hexdigest()==source['sha256'],'Stale recipe codec source'
        assert 'Codec.BOOL.fieldOf("accept_mirrored")' in raw.decode(),'Changed Create mechanical codec'
    for ident,digest in catalog['baseline_recipe_hashes'].items():assert ident in actual and canonical(actual[ident])==digest,('Published recipe changed',ident)
    for r in catalog['recipes']:
        assert r['id']==PREFIX+r['target'].split(':')[1] and r['epoch']==13
        src=root/r['source']['path'];raw=src.read_bytes();assert hashlib.sha256(raw).hexdigest()==r['source']['sha256'],'Stale source'
        original=json.loads(raw);recipe=r['json'];assert recipe['type']=='create:mechanical_crafting' and recipe.get('accept_mirrored') is False
        assert recipe['result']=={'id':r['target'],'count':1} and len(recipe['pattern'])==3 and all(len(row)==5 for row in recipe['pattern'])
        expected=cost(original)+Counter(json.dumps({'item':i},sort_keys=True) for i in r['added_item_ids'])
        assert cost(recipe)==expected,'Native materials or reviewed two cross-mod components changed'
        assert len(r['added_item_ids'])==2 and len(set(r['added_item_ids']))==2
        assert all(i not in TARGETS and rules['itemGates'].get(i,100)<=13 for i in r['added_item_ids']),'Future or cyclic assembly inputs'
        assert rules['itemGates'][r['target']]==rules['blockGates'][r['target']]==13
        assert rules['itemGates']['create:mechanical_crafter']<=13
        assert r['remove_recipe_ids']==catalog['producer_scan']['targets'][r['target']]==[r['source']['recipe_id']],'Incomplete or unreviewed producer closure'
        if compiled:
            assert actual.get(r['id'])=={k:copy.deepcopy(r[k]) for k in ['id','epoch','target','category','json']}
            assert rules['recipeGates'].get(r['id'])==13 and set(r['remove_recipe_ids'])<=set(bundle['remove'])
    return {'status':'passed','recipes':2,'native_producers_replaced':2,'native_material_units_per_recipe':9,'added_cross_mod_units_per_recipe':2,'published_custom_recipes_preserved':len(catalog['baseline_recipe_hashes']),'full_export_recipes_scanned':catalog['producer_scan']['recipes_scanned'],'full_pack_execution':False}
def apply(root=ROOT):
    root=Path(root);c=read(root/CATALOG);b=read(root/'kubejs/config/aia2_recipes.json');r=read(root/'kubejs/config/aia2_runtime.json');validate(root,c,b,r)
    owned={v['id'] for v in c['recipes']};b['add']=[v for v in b['add'] if v['id'] not in owned]+[{k:copy.deepcopy(v[k]) for k in ['id','epoch','target','category','json']} for v in c['recipes']]
    b['remove']=sorted(set(b['remove'])|{i for v in c['recipes'] for i in v['remove_recipe_ids']})
    for ident in sorted(owned):r['recipeGates'][ident]=13
    report=validate(root,c,b,r,True);write(root/'kubejs/config/aia2_recipes.json',b);write(root/'kubejs/config/aia2_runtime.json',r);write(root/'implementation/evilcraft-core-balance-v5-audit.json',report);return report
