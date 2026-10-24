#!/usr/bin/env python3
"""Apply a curated, stage-safe reward policy without changing any quest/reward ID.

Runs after quest/layout compilation. Catalogs are immutable source material;
only compiled item payloads/counts change. No item reward is added to finals.
"""
import copy
import hashlib
import json
import os
import re
from collections import Counter, defaultdict
from pathlib import Path

try:
    from item_normalization import normalize
except ModuleNotFoundError:
    from tools.item_normalization import normalize

ROOT = Path(__file__).resolve().parents[1]
POLICY = 'content/rewards/v5_profiles.json'
REPORT = 'implementation/rewards-v5-audit.json'
FORBIDDEN = re.compile(r'(^|[:_/])(creative|singularity|chaotic|awakened_draconium|boss|trophy|spawn_egg)(_|/|$)|aia2_.*key|infinity_ingot|infinity_nugget|life_essence|gaia_ingot|dead_king|divine_soul|warden_tendril|pixie_dust')
MAGIC = {'botania','ars_nouveau','occultism','naturesaura','rootsclassic','totemic','enchanted',
         'evilcraft','forbidden_arcanus','goety','irons_spellbooks'}
SAFE_BLOCKS = {'minecraft:torch','minecraft:glass_pane','ars_nouveau:sourceberry_bush',
              'pneumaticcraft:plastic','naturesaura:gold_powder','totemic:cedar_planks',
              'productivemetalworks:fire_clay','integrateddynamics:crystalized_menril_block',
              'integrateddynamics:menril_log','justdirethings:charcoal','aether:skyroot_planks',
              'twilightforest:canopy_planks'}


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def write(path, data):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')


def uid(name):
    return hashlib.sha256(('aia2-runtime-v1:'+name).encode()).hexdigest()[:12].upper().rjust(16,'0')


def catalog_records(root):
    """All author catalogs, including future v5 technology/magic/endgame files."""
    for path in sorted((root/'content/quests').glob('*.json')):
        if not (path.name.startswith('epochs_') or re.match(r'v[45]_.*\.json$',path.name)):
            continue
        data=read(path)
        records=data if isinstance(data,list) else data.get('quests',[])
        for record in records:
            yield path,record


def validate_policy(root, policy, gates):
    registries=read(root/'content/audit/registries.json')['registries']
    registry=set(registries['item'])
    blocks=set(registries['block'])
    assert policy.get('schema')==1
    assert policy.get('profiles') and 'minecraft' in policy['profiles']
    allowed={}
    for name,profile in policy['profiles'].items():
        assert profile.get('description_uk') and profile.get('entries'),('Empty reward profile',name)
        seen=set()
        for entry in profile['entries']:
            item=entry['item']
            assert item in registry,('Unknown reward item',name,item)
            assert normalize(item)==item,('Noncanonical reward item',item)
            assert item not in seen,('Duplicate reward profile item',name,item)
            seen.add(item)
            assert not FORBIDDEN.search(item),('Forbidden reward',item)
            assert item not in blocks or item in SAFE_BLOCKS,('Machine or unaudited block reward',item)
            assert not re.search(r'_(helmet|chestplate|leggings|boots|sword|pickaxe|axe|bow|shield|wand)$',item),('Equipment reward',item)
            assert entry.get('role') in {'material','consumable'}
            assert type(entry.get('min_epoch')) is int and 1<=entry['min_epoch']<=48
            # The authored policy promises two to four materials, including
            # repeated course rewards; larger stacks need an explicit review.
            assert type(entry.get('count')) is int and 2<=entry['count']<=4
            assert entry['min_epoch']>=gates.get(item,100),('Reward precedes canonical gate',item)
            proof=entry.get('producer_evidence',{})
            assert proof.get('recipes') or proof.get('loot'),('Unverified producer',item)
            for recipe in proof.get('recipes',[]):
                assert recipe.get('recipe') and recipe.get('serializer') and recipe.get('output_field')
                assert re.fullmatch(r'[a-f0-9]{64}',recipe.get('source_sha256',''))
            for loot in proof.get('loot',[]):
                assert loot.get('loot_table') and re.fullmatch(r'[a-f0-9]{64}',loot.get('source_sha256',''))
            assert entry.get('reason_uk')
            allowed.setdefault(item,[]).append(entry)
    for name,entry in policy.get('aliases',{}).items():
        assert name not in policy['profiles'],('Shadowed profile alias',name)
        assert entry.get('profile') in policy['profiles'] and entry.get('reason_uk')
    # Explicit semantic boundary: Botania's namespace default is not an Alfheim unlock.
    for item,entries in allowed.items():
        if any(x in item for x in ('elementium','dragonstone','pixie')):
            assert all(entry['min_epoch']>=21 for entry in entries),('Premature Alfheim reward',item)
        if item.startswith('modern_industrialization:'):
            # The approved set intentionally contains only steam-age consumables;
            # broad namespace stage6 is not permission for higher circuit/material tiers.
            assert item in {'modern_industrialization:tin_plate','modern_industrialization:coke'},('Unaudited MI tier',item)
    return allowed


def output_items(value):
    if isinstance(value,str):
        if ':' in value:yield value
    elif isinstance(value,list):
        for child in value:yield from output_items(child)
    elif isinstance(value,dict):
        if isinstance(value.get('id'),str):yield value['id']
        elif isinstance(value.get('item'),str):yield value['item']


def recipe_outputs(value):
    for key in ['result','results','output','outputs','item_output','item_outputs','main_output']:
        if key in value:yield from output_items(value[key])
    for key in ['base','gog','recipe']:
        if isinstance(value.get(key),dict):yield from recipe_outputs(value[key])


def loot_outputs(value):
    if isinstance(value,dict):
        if value.get('type')=='minecraft:item':yield value.get('name')
        for child in value.values():yield from loot_outputs(child)
    elif isinstance(value,list):
        for child in value:yield from loot_outputs(child)


def verify_producers(policy, export):
    """Recheck original byte hashes and semantic outputs when export is available."""
    export=Path(export)
    if not (export/'recipes').is_dir():return {'status':'external_export_unavailable','sources_verified':0}
    count=0
    for profile in policy['profiles'].values():
        for entry in profile['entries']:
            evidence=entry['producer_evidence']
            for kind,records in [('recipe',evidence.get('recipes',[])),('loot_table',evidence.get('loot',[]))]:
                for record in records:
                    relative=Path(record[kind]+'.json')
                    assert not relative.is_absolute() and '..' not in relative.parts
                    path=export/('recipes' if kind=='recipe' else 'minecraft/loot_table')/relative
                    content=path.read_bytes()
                    assert hashlib.sha256(content).hexdigest()==record['source_sha256'],('Changed producer source',entry['item'],relative)
                    outputs=recipe_outputs(json.loads(content)) if kind=='recipe' else loot_outputs(json.loads(content))
                    assert entry['item'] in {normalize(item) for item in outputs if item},('Not a semantic producer',entry['item'],relative)
                    count+=1
    return {'status':'semantic_outputs_and_exact_source_hashes_verified','sources_verified':count}


def describe_quests(root, chapters):
    records={uid(record['id']):record for _,record in catalog_records(root)}
    epochs=read(root/'design/progression.json')['epochs']
    descriptions={}
    for path,chapter in chapters:
        match=re.search(r'aia2_epoch_(\d+)',path.stem)
        for q in chapter['quests']:
            record=records.get(q['id'])
            stages=[int(re.search(r'e(\d+)$',t.get('advancement','')).group(1))
                    for t in q.get('tasks',[]) if re.fullmatch(r'aia2:stages/e\d+',t.get('advancement',''))]
            epoch=record['epoch'] if record else int(match.group(1)) if match else max(stages,default=0)
            assert 1<=epoch<=48,('Unknown quest epoch',q['id'])
            mod=(record.get('mod') or record['icon'].split(':')[0]) if record else q.get('icon',{}).get('id','minecraft:book').split(':')[0]
            if mod=='kubejs':
                mains=epochs[epoch-1]['main_mods']
                icon=q.get('icon',{}).get('id','')
                if 'arcane' in icon:
                    mod=next((m for m in mains if m in MAGIC),'botania' if epoch>=5 else 'rootsclassic')
                else: mod=next((m for m in mains if m not in MAGIC and m!='minecraft'),mains[0])
            types={t['type'] for t in q.get('tasks',[])}
            role='combat' if 'kill' in types else 'expedition' if 'dimension' in types or 'biome' in types else 'construction' if 'observation' in types else 'production'
            logical=record['id'] if record else q['id']
            course=logical.rsplit('_',1)[0] if record else path.stem
            descriptions[q['id']]={'epoch':epoch,'mod':mod,'role':role,'course':course}
    # Stable, meaningful per-course/goal-role ordinal. Registry ordering has no influence.
    groups=defaultdict(list)
    for qid,meta in descriptions.items():groups[(meta['course'],meta['role'])].append(qid)
    for ids in groups.values():
        for ordinal,qid in enumerate(sorted(ids)):descriptions[qid]['ordinal']=ordinal
    return descriptions


def choose_reward(policy,gates,meta,index):
    mod=meta['mod']; source='profile'
    key=mod
    if key not in policy['profiles']:
        if key in policy.get('aliases',{}):key=policy['aliases'][key]['profile'];source='parent_profile'
        else:key='minecraft';source='unverified_food_fallback'
    eligible=[entry for entry in policy['profiles'][key]['entries']
              if max(entry['min_epoch'],gates.get(entry['item'],100))<=meta['epoch']]
    if source=='unverified_food_fallback':eligible=[entry for entry in eligible if entry['item']=='minecraft:bread']
    if not eligible:
        source='early_food_fallback';key='minecraft'
        eligible=[entry for entry in policy['profiles'][key]['entries'] if entry['item']=='minecraft:bread']
    assert eligible,('No safe reward',meta)
    offset={'production':0,'construction':1,'expedition':2,'combat':3}[meta['role']]
    entry=eligible[(meta['ordinal']+index+offset)%len(eligible)]
    return entry,key,source


def plan(root):
    root=Path(root)
    policy=read(root/POLICY)
    gates=read(root/'kubejs/config/aia2_runtime.json')['itemGates']
    validate_policy(root,policy,gates)
    producers=verify_producers(policy,os.environ.get('AIA2_EXPORT_ROOT','/workspace/aia2-reference/export'))
    source_records=list(catalog_records(root))
    catalog_counts=Counter(str(path.relative_to(root)) for path,record in source_records for reward in record.get('reward',[]))
    catalog_hashes={str(path.relative_to(root)):hashlib.sha256(path.read_bytes()).hexdigest() for path,record in source_records}
    chapters=[(path,read(path)) for path in sorted((root/'config/ftbquests/quests/chapters').glob('aia2_*.snbt'))]
    meta=describe_quests(root,chapters)
    changed=0;count=0;commands=0;profiles=Counter();namespaces=Counter();modes=Counter();reasons=Counter()
    quest_ids=[];reward_ids=[];commands_before=[];decisions=[]
    for path,chapter in chapters:
        for q in chapter['quests']:
            quest_ids.append(q['id'])
            for i,reward in enumerate(q.get('rewards',[])):
                reward_ids.append(reward['id'])
                if reward['type']!='item':
                    commands+=reward['type']=='command'
                    commands_before.append(copy.deepcopy(reward))
                    continue
                count+=1
                choice,key,source=choose_reward(policy,gates,meta[q['id']],i)
                before=(reward['item']['id'],reward.get('count',1),reward['item'].get('count',1))
                after=(choice['item'],choice['count'],1)
                changed+=before!=after
                reward['item']={'id':choice['item'],'count':1}
                reward['count']=choice['count']
                profiles[key]+=1;namespaces[meta[q['id']]['mod']]+=1;modes[source]+=1
                if source.endswith('fallback'):reasons[meta[q['id']]['mod']]+=1
                decisions.append({'quest':q['id'],'reward':reward['id'],'epoch':meta[q['id']]['epoch'],
                                  'mod':meta[q['id']]['mod'],'profile':key,'source':source,
                                  'item':choice['item'],'count':choice['count'],'min_epoch':choice['min_epoch']})
    assert len(reward_ids)==len(set(reward_ids)), 'Duplicate reward IDs'
    assert len(quest_ids)==len(set(quest_ids)), 'Duplicate quest IDs'
    report={'schema':1,'status':'compiled_reward_policy_verified_full_pack_economy_not_run',
            'item_rewards_audited':count,'item_rewards_changed':changed,'command_rewards_preserved':commands,
            'quest_count':len(quest_ids),'namespace_count':len(namespaces),'quests_by_namespace':dict(sorted(namespaces.items())),
            'reward_profiles_used':dict(sorted(profiles.items())),'selection_modes':dict(sorted(modes.items())),
            'fallback_namespaces':dict(sorted(reasons.items())),
            'policy_profiles':len(policy['profiles']),'parent_profile_aliases':len(policy.get('aliases',{})),
            'curated_entries':sum(len(p['entries']) for p in policy['profiles'].values()),
            'source_catalog_rewards_audited':sum(catalog_counts.values()),
            'source_catalog_reward_counts':dict(sorted(catalog_counts.items())),
            'source_catalog_sha256':dict(sorted(catalog_hashes.items())),
            'all_reward_ids_preserved':True,'all_command_payloads_preserved':True,'catalogs_unchanged':True,
            'future_or_banned_rewards':0,'new_final_item_rewards':0,
            'selection':'Stable course/goal-role ordinal over explicit authored material lists; never registry sampling',
            'producer_scope':'Exported semantic outputs or explicitly documented common crop/world source; not full in-game reachability',
            'producer_verification':producers,
            'fallback_reason':policy['unverified_fallback']['reason_uk'],
            'decisions':decisions}
    return chapters,report,commands_before


def validate(root=ROOT):
    root=Path(root)
    planned,report,commands=plan(root)
    actual_commands=[]
    for path,chapter in planned:
        actual=read(path)
        assert len(actual['quests'])==len(chapter['quests'])
        for before,after in zip(actual['quests'],chapter['quests']):
            for original,expected in zip(before.get('rewards',[]),after.get('rewards',[])):
                assert original==expected,('Reward policy mismatch',before['id'],original['id'])
                if original['type']!='item':actual_commands.append(original)
    assert actual_commands==commands
    return report


def apply(root=ROOT):
    root=Path(root)
    chapters,report,commands=plan(root)
    # Complete validation precedes the first write. Preserve all non-reward data.
    originals={str(path):read(path) for path,_ in chapters}
    for path,chapter in chapters:
        stripped=copy.deepcopy(chapter)
        before=copy.deepcopy(originals[str(path)])
        for document in (stripped,before):
            for quest in document['quests']:quest.pop('rewards',None)
        assert stripped==before,('Non-reward quest data changed',path)
    for path,chapter in chapters:write(path,chapter)
    validate(root)
    write(root/REPORT,report)
    return report


if __name__=='__main__':
    report=apply()
    print(json.dumps({k:v for k,v in report.items() if k!='decisions'},ensure_ascii=False,indent=2))
