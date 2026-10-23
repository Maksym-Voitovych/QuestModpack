#!/usr/bin/env python3
"""Compile native dual-key recipes and receipt-backed quest conditions, preserving old IDs."""
import json
from pathlib import Path
try:
    from item_normalization import normalize
except ImportError:
    from tools.item_normalization import normalize

def apply(root):
    try:from build_expansion import uid,write,crafting
    except ImportError:from tools.build_expansion import uid,write,crafting
    load=lambda p:normalize(json.loads(p.read_text(encoding='utf-8')))
    rules=load(root/'kubejs/config/aia2_runtime.json')
    bundle=load(root/'kubejs/config/aia2_recipes.json')
    design=load(root/'design/progression.json')['epochs']
    assets_path=root/'content/resources/dual-keys.json'
    assets=load(assets_path) if assets_path.exists() else {}
    names={e['id']:e for e in assets.get('keys',[])}
    chapters={p:load(p)for p in (root/'config/ftbquests/quests/chapters').glob('*.snbt')}
    questmap={q['id']:q for ch in chapters.values() for q in ch['quests']}
    categories={}
    records=[]
    for p in (root/'content/quests').glob('*.json'):
        d=load(p);records+=d if isinstance(d,list)else d.get('quests',[])
    for q in records:categories[uid(q['id'])]=q['category']
    for e in rules['epochs']:
        n=e['number']
        for i,qid in enumerate(e['milestoneQuestIds']):categories[qid]='technology'if i in {0,1,4}else'magic'
        for kind in ['tech_matrix','convergence_core']:categories[uid(f'E{n:02d}_COMPONENT_{kind}')]='technology'
        for kind in ['arcane_catalyst','epoch_seal']:categories[uid(f'E{n:02d}_COMPONENT_{kind}')]='magic'
    recipes=[];key_rules=[];catalog=[]
    startup=['// Native manufacturing receipts are independent of possession or /give.',"StartupEvents.registry('item', function (event) {"]
    for e,d in zip(rules['epochs'],design):
        n=e['number'];tech=f'kubejs:aia2_tech_key_{n:02d}';arcane=f'kubejs:aia2_arcane_key_{n:02d}'
        matrix=f'kubejs:aia2_tech_matrix_{n:02d}';catalyst=f'kubejs:aia2_arcane_catalyst_{n:02d}'
        core=f'kubejs:aia2_convergence_core_{n:02d}';seal=f'kubejs:aia2_epoch_seal_{n:02d}'
        t,m,r,s=[d['key']['ingredients'][x]['id']for x in 'TMRS']
        e['branchKeys']={'tech':tech,'arcane':arcane}
        e['transitionCost']={tech:1,arcane:1,rules['epochs'][n-2]['key']if n>1 else'minecraft:crafting_table':1}
        closure=set()
        def ancestors(qid):
            if qid in closure:return
            closure.add(qid)
            for parent in questmap[qid].get('dependencies',[]):ancestors(parent)
        for qid in e['requiredQuestIds']+e['milestoneQuestIds']:ancestors(qid)
        # Ancestors in older epochs are already satisfied; only current stage goals
        # classify each independent branch. The seal trial excludes all key quests.
        current=set(e['milestoneQuestIds'])|{uid(q['id'])for q in records if q['epoch']==n}
        current|={uid(f'E{n:02d}_COMPONENT_{k}')for k in ['tech_matrix','convergence_core','arcane_catalyst','epoch_seal']}
        e['branchQuestIds']={
            'tech':sorted(q for q in closure&current if categories.get(q)in{'technology','automation'}),
            'arcane':sorted(q for q in closure&current if categories.get(q)in{'magic','adventure','collection'})}
        assert e['branchQuestIds']['tech'] and e['branchQuestIds']['arcane']
        for branch,item in [('tech',tech),('arcane',arcane)]:
            if branch=='tech':
                if n<4:recipe=crafting(['TMT','RCR',' S '],{'T':t,'M':matrix,'R':r,'C':core,'S':s},item)
                elif n<16:recipe={'type':'create:mixing','ingredients':[{'item':x}for x in[matrix,core,t,t,r,s]],'results':[{'id':item,'count':1}]}
                else:recipe={'type':'mekanism:metallurgic_infusing','chemical_input':{'amount':40+10*(n//8),'tag':'mekanism:redstone'},'item_input':{'count':2,'item':core},'output':{'id':item,'count':1},'per_tick_usage':False}
            else:
                if n<4:recipe=crafting(['MCM','RSR',' A '],{'M':m,'C':catalyst,'R':r,'S':seal,'A':s},item)
                else:recipe={'type':'create:compacting','ingredients':[{'item':x}for x in[catalyst,seal,m,m,r,s]],'results':[{'id':item,'count':1}]}
            rid=f'aia2:dual/e{n:02d}/{branch}'
            recipes.append({'id':rid,'json':recipe,'epoch':n,'target':item,'category':'dual_key'})
            key_rules.append({'recipeId':rid,'output':item,'epoch':n,'branch':branch,'serializer':recipe['type']})
            rules['itemGates'][item]=n;rules['recipeGates'][rid]=n
            name=names.get(item,{}).get('name_uk',('Технологічний ключ'if branch=='tech'else'Ключ магії та досліджень')+f' — {n:02d}')
            texture=f'kubejs:item/aia2/dual_keys/{branch}_{n:02d}'
            startup.append('  event.create('+json.dumps(item)+').displayName('+json.dumps(name,ensure_ascii=False)+').maxStackSize(1).fireResistant().texture('+json.dumps(texture)+');')
            lid=f'E{n:02d}_DUAL_{branch.upper()}';qid=uid(lid)
            adv=f'aia2:production/{branch}_{n:02d}'
            write(root/f'kubejs/data/aia2/advancement/production/{branch}_{n:02d}.json',{'criteria':{'native_manufacture':{'trigger':'minecraft:impossible'}}})
            q={'id':qid,'title':name,'description':[
                'Завершіть обов’язкову '+('технологічну гілку.'if branch=='tech'else'магічну й дослідницьку гілку.'),
                'Виготовте цей ключ за справжнім рецептом JEI. Завершення фіксує сервер після виконання рецепта й витрати інгредієнтів.',
                'Фінальне '+('технологічне складання'if branch=='tech'else'гравіювання магічної печатки')+' використовує '+recipe['type']+'. Магічні й промислові компоненти проходять власні попередні процеси.',
                'Отримання через /give, Creative або передачу іншої команди не створює виробничого запису для вашої команди. Обидва ключі потрібні для переходу.'],
                'icon':{'id':item,'count':1},'dependencies':e['branchQuestIds'][branch],
                'tasks':[{'id':uid(lid+':proof'),'type':'advancement','advancement':adv}],
                'hide_until_deps_complete':True,'optional':False,'x':float(8 if branch=='tech' else 10),'y':8.0,
                'rewards':[{'id':uid(lid+':reward'),'type':'item','item':{'id':'minecraft:torch'if branch=='tech'else'minecraft:paper','count':1},'count':8 if n<16 else 16}]}
            chapter=next(ch for ch in chapters.values()if ch['filename']==f'aia2_epoch_{n:02d}')
            chapter['quests']=[old for old in chapter['quests']if old['id']!=qid]+[q]
            e.setdefault('branchKeyQuestIds',{})[branch]=qid
            catalog.append({'id':item,'epoch':n,'branch':branch,'name_uk':name,'texture':texture,'recipeId':rid,'process':recipe['type']})
        final=questmap[e['finalQuestId']]
        final['description']=[
            'Завершіть обов’язкові віхи, підсумкове випробування та обидві гілки. Виготовте технологічний і магічний ключі у дозволених процесах.',
            'Біля верстака виконайте /aia2 key. Сервер перевіряє два нативні виробничі записи, витрачає два ключі та попередній артефакт, після чого підтверджує цей фінальний квест.',
            'Наступна епоха відкриється тільки після завершення цього квесту FTB. Виготовлення артефакту й очікування підтвердження зберігаються після перезапуску.',
            'Уже законно завершені епохи з попередніх версій залишаються завершеними. /aia2 recover відновлює останній старий артефакт за попередньою платною формулою.']
    startup+=['});','']
    # Automation icon is registered once by component_chains(GROUPS).
    bundle['add']=[r for r in bundle['add']if not r['id'].startswith('aia2:dual/')]+recipes
    rules['dualKeys']=key_rules;rules['progressionVersion']=4
    for p,ch in chapters.items():write(p,ch)
    write(root/'kubejs/startup_scripts/aia2/20_dual_keys.js','\n'.join(startup))
    write(root/'kubejs/config/aia2_dual_keys.json',{'items':catalog,'transition':'native proof -> paid pending artifact -> final FTB quest -> next stage'})
    write(root/'kubejs/config/aia2_recipes.json',bundle);write(root/'kubejs/config/aia2_runtime.json',rules)
    for locale in ['uk_ua','en_us']:
        p=root/f'kubejs/assets/kubejs/lang/{locale}.json';lang=json.loads(p.read_text())if p.exists()else{}
        for item in catalog:lang['item.kubejs.'+item['id'].split(':')[1]]=item['name_uk']
        lang['item.kubejs.aia2_section_automation']='Автоматизація';write(p,lang)
    total=sum(len(ch['quests'])for ch in chapters.values())
    report={'dual_keys':96,'dual_key_recipes':96,'dual_key_quests':96,'total_quests':total,'progression_version':4,
            'epoch1_start':'Both branches start at stage1; no previous epoch key. Crafting-table transition anchor only.',
            'provenance':'Native post-consumption receipts in SavedData, team-bound; item possession never counts',
            'legacy_migration':'completed0..48 unchanged; previous epoch artifacts retained; recovery uses old9-unit cost'}
    write(root/'implementation/dual-key-report.json',report)
    return report
