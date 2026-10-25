"""Keep rune acquisition, native modifier recipes and native use at the same stage."""
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
CATALOG='content/audit/v5-spawner-rune-gates.json'
FLOORS={name:stage for name,stage in [
    ('apotheosis:ascent_spawner_upgrade_rune',31),('apotheosis:summit_spawner_upgrade_rune',31),
    ('apotheosis:pinnacle_spawner_upgrade_rune',41),('apotheosis:no_ai_spawner_rune',31),
    ('apotheosis:ignore_conditions_spawner_rune',31),('apotheosis:ignore_players_spawner_rune',31)]}

def read(p):return json.loads(Path(p).read_text())
def write(p,v):Path(p).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')

def validate(root,rules,compiled=True):
    root=Path(root);data=read(root/CATALOG)
    assert data['schema']==1 and data['item_floors']==FLOORS, 'Unreviewed spawner floor scope'
    for source in data['sources']:
        p=Path(source['path']);assert not p.is_absolute() and '..' not in p.parts
        assert hashlib.sha256((root/p).read_bytes()).hexdigest()==source['sha256'], 'Stale spawner source'
    for item,floor in FLOORS.items():
        assert item in rules['itemGates'], 'Unregistered spawner rune'
        if compiled:assert rules['itemGates'][item]==floor, 'Rune use floor differs'
    assert len(data['recipe_floors'])>=12
    if compiled:
        for rid,floor in data['recipe_floors'].items():assert floor<=rules['recipeGates'][rid]<=48, ('Rune recipe early or quarantined',rid)
    return {'status':'passed','item_floors':len(FLOORS),'recipe_floors':len(data['recipe_floors']),
            'native_use_hook':'ApothicSpawnerMixin.useItemOn HEAD before findMatch/apply/consume',
            'full_pack_dispatch':'not_run'}

def apply(root=ROOT):
    root=Path(root);rules=read(root/'kubejs/config/aia2_runtime.json');data=read(root/CATALOG)
    validate(root,rules,compiled=False)
    for item,floor in FLOORS.items():rules['itemGates'][item]=max(rules['itemGates'][item],floor)
    for rid,floor in data['recipe_floors'].items():
        assert rid in rules['recipeGates'], ('Unregistered native rune recipe',rid)
        rules['recipeGates'][rid]=max(rules['recipeGates'][rid],floor)
    report=validate(root,rules);write(root/'kubejs/config/aia2_runtime.json',rules)
    write(root/'implementation/spawner-rune-gates-v5-audit.json',report);return report
