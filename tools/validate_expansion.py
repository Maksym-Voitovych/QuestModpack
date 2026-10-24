#!/usr/bin/env python3
"""Independent content/registry/graph/resource validation for the curated expansion."""
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
try:
    from item_normalization import normalize
except ModuleNotFoundError:
    from tools.item_normalization import normalize


def load(path):
    return json.loads(path.read_text(encoding='utf-8'))


def validate(root=ROOT):
    regs = {k: set(v) for k,v in load(root/'content/audit/registries.json')['registries'].items()}
    rules = load(root/'kubejs/config/aia2_runtime.json')
    bundle = load(root/'kubejs/config/aia2_recipes.json')
    components = load(root/'content/components/catalog.json')['items']
    dual = rules.get('progressionVersion', 3) >= 4
    custom = {e['key'] for e in rules['epochs']} | {e['id'] for e in components}
    custom |= {f'kubejs:aia2_epoch_icon_{n:02d}' for n in range(1,49)}
    custom |= {'kubejs:aia2_section_'+s for s in ['epochs','technology','magic','adventure','collection']}
    if dual:
        custom |= {r['output'] for r in rules['dualKeys']}
        custom.add('kubejs:aia2_section_automation')
    items = regs['item'] | custom
    assert set(rules['itemGates']) == items
    assert set(rules['blockGates']) == regs['block']
    authored = []
    for file in sorted((root/'content/quests').glob('epochs_*.json')):
        data = normalize(load(file)); authored += data if isinstance(data,list) else data['quests']
    audit=load(root/'content/audit/quest-obtainability.json')
    assert audit['quests_scanned']==len(authored)
    for catalog in audit['catalogs']:
        path=root/'content/quests'/catalog['file']
        assert hashlib.sha256(path.read_bytes()).hexdigest()==catalog['sha256'],('Obtainability audit is stale',catalog['file'])
    baseline_authored = len(authored)
    v4_path=root/'content/quests/v4_mod_depth.json'
    if dual:
        assert v4_path.is_file(), 'Missing authored v4 mod-depth catalog'
        data=normalize(load(v4_path))
        authored += data if isinstance(data,list) else data['quests']
        new_audit_path=root/'implementation/quests-v4-audit.json'
        assert new_audit_path.is_file(), 'Missing v4 quest source audit'
        new_audit=load(new_audit_path)
        assert new_audit['catalog_sha256']==hashlib.sha256(v4_path.read_bytes()).hexdigest(), 'v4 quest source audit is stale'
    assert len({q['id'] for q in authored}) == len(authored)
    v5_authored = []
    for path in sorted((root/'content/quests').glob('v5_*.json')):
        v5_authored.extend(normalize(load(path))['quests'])
    authored.extend(v5_authored)
    assert len({q['id'] for q in authored}) == len(authored)
    signatures = defaultdict(list)
    byepoch = Counter()
    tasktypes = Counter()
    allowed_advancements = {'minecraft:story/root','minecraft:story/mine_stone','minecraft:story/upgrade_tools',
        'minecraft:story/smelt_iron','minecraft:story/obtain_armor','minecraft:story/lava_bucket',
        'minecraft:story/iron_tools','minecraft:story/deflect_arrow','minecraft:story/form_obsidian',
        'minecraft:story/mine_diamond','minecraft:story/enter_the_nether','minecraft:story/shiny_gear',
        'minecraft:story/enchant_item','minecraft:story/cure_zombie_villager','minecraft:story/follow_ender_eye',
        'minecraft:story/enter_the_end','minecraft:nether/root','minecraft:nether/return_to_sender',
        'minecraft:nether/find_fortress','minecraft:nether/obtain_blaze_rod','minecraft:nether/brew_potion',
        'minecraft:nether/find_bastion','minecraft:nether/distract_piglin','minecraft:nether/get_wither_skull','minecraft:nether/summon_wither','minecraft:nether/create_beacon',
        'minecraft:end/root','minecraft:end/kill_dragon','minecraft:end/dragon_egg','minecraft:end/enter_end_gateway',
        'minecraft:end/find_end_city','minecraft:end/elytra','minecraft:end/respawn_dragon',
        'minecraft:adventure/root','minecraft:adventure/kill_a_mob','minecraft:adventure/trade',
        'minecraft:adventure/sleep_in_bed','minecraft:adventure/shoot_arrow',
        'minecraft:husbandry/root','minecraft:husbandry/plant_seed','minecraft:husbandry/breed_an_animal',
        'minecraft:husbandry/tame_an_animal','minecraft:husbandry/fishy_business',
        'create:water_wheel','create:mechanical_press','create:millstone','create:mechanical_mixer'}
    if (root/'kubejs/config/aia2_mechanics.json').is_file():
        try: from validate_v5 import verified_mechanic_advancements
        except ImportError: from tools.validate_v5 import verified_mechanic_advancements
        allowed_advancements.update(verified_mechanic_advancements(root, rules, bundle))
    for q in authored:
        n=q['epoch']; byepoch[n]+=1
        gate_limit = 99 if q.get('post_completion') else n
        assert q['title_uk'].strip() and len(' '.join(q['description_uk'])) >= 80, q['id']
        assert q['icon'] in items, (q['id'],'icon',q['icon'])
        assert q['tasks'] and any(t['type'] != 'advancement' or not t['advancement'].startswith('aia2:') for t in q['tasks'])
        assert rules['itemGates'][q['icon']] <= gate_limit, (q['id'],'future icon',q['icon'])
        signature=[]
        for t in q['tasks']:
            kind=t['type'];tasktypes[kind]+=1
            if kind=='item':
                assert t['item'] in items,(q['id'],t)
                assert rules['itemGates'][t['item']] <= gate_limit,(q['id'],'future item',t['item'],rules['itemGates'][t['item']])
                assert 1<=t.get('count',1)<=10000000,(q['id'],t)
                signature.append((kind,t['item'],t.get('consume',False),t.get('craft',False)))
            elif kind=='observation':
                assert t['block'] in regs['block'],(q['id'],t)
                assert rules['blockGates'][t['block']] <= gate_limit,(q['id'],'future block',t['block'],rules['blockGates'][t['block']])
                signature.append((kind,t['block']))
            elif kind=='dimension':
                assert t['dimension'] in regs['dimension'],(q['id'],t)
                assert rules['dimensionGates'].get(t['dimension'],0)<=n,(q['id'],'future dimension',t['dimension'])
                signature.append((kind,t['dimension']))
            elif kind=='biome':
                assert t['biome'] in regs['worldgen/biome'],(q['id'],t)
                signature.append((kind,t['biome']))
            elif kind=='kill':
                assert t['entity'] in regs['entity_type'],(q['id'],t)
                signature.append((kind,t['entity']))
            elif kind=='stat':
                assert t['stat'] in regs['custom_stat'],(q['id'],t)
                signature.append((kind,t['stat']))
            elif kind=='advancement':
                assert t['advancement'] in allowed_advancements,(q['id'],'unverified advancement',t['advancement'])
                signature.append((kind,t['advancement']))
            else: raise AssertionError((q['id'],'unverified task',kind))
        signatures[tuple(sorted(signature))].append(q['id'])
        for reward in q.get('reward',[]):
            assert reward['item'] in items,(q['id'],reward)
            assert rules['itemGates'][reward['item']] <= gate_limit,(q['id'],'future reward',reward)
            assert not reward['item'].startswith('kubejs:aia2_epoch_key_'),q['id']
            assert reward['item'] not in {r['output'] for r in rules.get('dualKeys',[])}, ('Free manufacture key reward',q['id'])
    # Identical item lists with only a larger amount do not create a new design goal.
    duplicates=[v for k,v in signatures.items() if len(v)>1]
    assert not duplicates,('Duplicate objectives differ only in quantity/title',duplicates[:20])
    assert set(byepoch)==set(range(1,49))
    all_custom_recipe_outputs=set()
    component_ids={e['id'] for e in components}
    component_graph={}
    recipe_types=Counter()
    def ingredients(value):
        if isinstance(value,dict):
            for k,v in value.items():
                if k in {'item','items'} and isinstance(v,str):yield v
                elif k not in {'output','outputs','result','results','item_output','item_outputs','main_output','secondary_output'}:yield from ingredients(v)
        elif isinstance(value,list):
            for v in value:yield from ingredients(v)
    def walk(value):
        if isinstance(value,dict):
            for k,v in value.items():
                if k in {'item','id'} and isinstance(v,str) and ':' in v:
                    # Recipe outputs and item ingredients only: no invented registry IDs.
                    assert v in items,('recipe item missing',v)
                if k=='items' and isinstance(v,str): assert v in items,v
                yield from walk(v)
        elif isinstance(value,list):
            for v in value: yield from walk(v)
        yield None
    for entry in bundle['add']:
        recipe=entry['json'];recipe_types[recipe['type']]+=1
        assert recipe['type'] in regs['recipe_serializer'],entry['id']
        list(walk(recipe))
        inputs=set(ingredients(recipe))
        # Custom v4 dependency claims and manufacturing stages must never rely
        # on a future item; untouched native conversions are reviewed separately.
        if entry['category'] in {'component_chain','dual_key','v4_crossmod_rebalance'}:
            for item in inputs:
                assert rules['itemGates'][item] <= entry['epoch'], (entry['id'],'future ingredient',item,rules['itemGates'][item])
        if entry['category']=='component_chain':
            assert entry['target'] in custom
            all_custom_recipe_outputs.add(entry['target'])
            # No future ingredient can make the current epoch unreachable.
            component_graph[entry['target']]=inputs & component_ids
            for item in inputs:
                assert rules['itemGates'][item]<=entry['epoch'],(entry['id'],'future ingredient',item,rules['itemGates'][item])
    assert all_custom_recipe_outputs == {e['id'] for e in components}
    visited=set()
    def check_component(node, path):
        assert node not in path, ('Component production cycle',node)
        if node in visited:return
        for dependency in component_graph[node]:check_component(dependency,path|{node})
        visited.add(node)
    for item in component_graph:check_component(item,set())
    v4_recipe_checks={}
    if dual:
        recipe_catalog_path=root/'content/recipes/v4_expansion.json'
        recipe_catalog=load(recipe_catalog_path)
        recipe_audit=load(root/'implementation/recipes-v4-audit.json')
        assert recipe_audit['catalog_sha256']==hashlib.sha256(recipe_catalog_path.read_bytes()).hexdigest(), 'v4 recipe audit is stale'
        expected={entry['id']:entry for entry in recipe_catalog['add']}
        actual={entry['id']:entry for entry in bundle['add'] if entry['id'].startswith('aia2:v4/')}
        assert actual==expected, 'Compiled v4 recipes differ from reviewed frozen templates'
        assert set(recipe_catalog['remove'])<=set(bundle['remove']), 'An unpatched native alternative was retained'
        try:
            from build_recipe_expansion import validate as validate_recipe_catalog
        except ModuleNotFoundError:
            from tools.build_recipe_expansion import validate as validate_recipe_catalog
        # Includes real native templates, slot limits and the introduced
        # component/machine prerequisite graph. It performs no mutations.
        v4_recipe_checks=validate_recipe_catalog(root,recipe_catalog,bundle,rules)
    from PIL import Image
    image_paths=list((root/'kubejs/assets/kubejs/textures/item/aia2').rglob('*.png'))
    assert len(image_paths)==(390 if dual else 293),len(image_paths)
    digests=set();key_shapes=set();dual_shapes=set()
    for path in image_paths:
        with Image.open(path) as im:
            assert im.size in {(32,32),(64,64)} and im.mode=='RGBA',str(path)
            alpha=im.getchannel('A');assert alpha.getextrema()==(0,255),str(path)
            assert alpha.getbbox() and sum(a>0 for a in alpha.getdata())>=40,str(path)
            if '/keys/' in path.as_posix():key_shapes.add(hashlib.sha256(bytes(1 if a else 0 for a in alpha.getdata())).hexdigest())
            if '/dual_keys/' in path.as_posix():dual_shapes.add(hashlib.sha256(bytes(1 if a else 0 for a in alpha.getdata())).hexdigest())
        digest=hashlib.sha256(path.read_bytes()).hexdigest();assert digest not in digests,('Duplicate texture',str(path));digests.add(digest)
    assert len(key_shapes)==48,('Key silhouettes must be unique',len(key_shapes))
    if dual:
        assert len(dual_shapes)==96, ('Dual-key silhouettes must be individually composed',len(dual_shapes))
        assert len(dual_shapes|key_shapes)==144, 'New key silhouettes must differ from old epoch artifacts'
        manifest=load(root/'content/resources/dual-keys.json')
        assert len(manifest['keys'])==96 and len(manifest['assets'])==97
        assert {entry['id'] for entry in manifest['keys']}=={r['output'] for r in rules['dualKeys']}
        assert len({entry['name_uk'] for entry in manifest['keys']})==96
    legacy_assets=load(root/'content/resources/manifest.json')['assets']
    assert len(legacy_assets)==293
    for entry in legacy_assets:
        assert hashlib.sha256((root/entry['png']).read_bytes()).hexdigest()==entry['sha256'], ('Legacy texture changed',entry['id'])
    for item in custom:
        model=root/'kubejs/assets/kubejs/models/item'/(item.split(':')[1]+'.json')
        data=load(model);texture=data['textures']['layer0'];ns,path=texture.split(':')
        assert (root/'kubejs/assets'/ns/'textures'/(path+'.png')).is_file(),str(model)
    report={'status':'passed','authored_quests':len(authored),'baseline_authored_quests':baseline_authored,
            'new_v4_authored_quests':len(authored)-baseline_authored,'quests_per_epoch':dict(sorted(byepoch.items())),
            'authored_task_types':dict(tasktypes),'duplicate_objectives':len(duplicates),
            'registered_custom_items':len(custom),'components':len(components),'native_recipe_types':dict(recipe_types),
            'component_dependency_edges':sum(map(len,component_graph.values())),
            'png_textures':len(image_paths),'unique_key_silhouettes':len(key_shapes),
            'unique_dual_key_silhouettes':len(dual_shapes),
            'preserved_legacy_textures':len(legacy_assets),
            'v4_recipe_validation':v4_recipe_checks,
            'registry_source':'content/audit/registries.json, user supplied export; snapshot is not runtime discovery',
            'full_pack_run':False,'tps_benchmark':'not run'}
    (root/'implementation/content-validation-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    return report

if __name__=='__main__':print(json.dumps(validate(),ensure_ascii=False,indent=2))
