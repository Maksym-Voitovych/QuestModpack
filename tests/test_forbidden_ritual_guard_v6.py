"""Actual ritual helpers and handlers, modeled optional host, real GuardPolicy.

This is deliberately not a claim of Forbidden Arcanus weaving or Minecraft execution.
"""
import json
import hashlib
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class ForbiddenRitualGuardTests(unittest.TestCase):
    def test_pinned_native_cost_enhancer_and_pedestal_contracts(self):
        folder = ROOT / 'content/research/evidence/forbidden_ritual_guard_v6'
        manifest = json.loads((folder / 'manifest.json').read_text())
        sources = {}
        for row in manifest['sources']:
            raw = (ROOT / row['path']).read_bytes()
            self.assertEqual(hashlib.sha256(raw).hexdigest(), row['sha256'])
            sources[Path(row['repository_path']).name] = raw.decode()
        self.assertEqual(len(sources), 6)
        self.assertIn('public void reduce(EssencesDefinition', sources['EssencesStorage.java'])
        self.assertIn('getEnhancerHolder(HolderLookup.Provider', sources['EnhancerHelper.java'])
        self.assertIn('stack.get(ModDataComponents.ENHANCER)', sources['EnhancerHelper.java'])
        self.assertIn('public ItemStack getStack()', sources['PedestalBlockEntity.java'])
        self.assertIn('pos, 4, PoiManager.Occupancy.ANY', sources['UpdateForgeIngredientsEffect.java'])
        self.assertIn('public static final Codec<EnhancerDefinition> CODEC', sources['EnhancerDefinition.java'])

    def test_actual_helpers_handlers_payment_reload_pause_commit_and_scope(self):
        jdk = Path(os.environ.get('JAVA_HOME', '/workspace/aia2-toolchains/jdk-21.0.9'))
        if not (jdk / 'bin/javac').is_file():
            self.skipTest('External JDK21 unavailable')
        gson = sorted(Path('/workspace/aia2-toolchains/gradle-home/caches/modules-2/files-2.1/com.google.code.gson/gson').glob('*/*/gson-*.jar'))
        if not gson:
            self.skipTest('External Gson test dependency unavailable')
        fixture = json.loads((ROOT / 'tests/fixtures/forbidden-paid-state-host.json').read_text())
        fixture.update(json.loads((ROOT / 'tests/fixtures/forbidden-ritual-host.json').read_text()))
        nbt = fixture['net/minecraft/nbt/CompoundTag.java']
        nbt = nbt.replace('public int getId(){return TAG_COMPOUND;}', 'public boolean isEmpty(){return map.isEmpty();}public void putLong(String k,long v){map.put(k,new Value(4,v));}public ListTag getList(String k,int type){return map.get(k) instanceof ListTag l&&(l.size()==0||l.getElementType()==type)?l:new ListTag();}public int getId(){return TAG_COMPOUND;}')
        fixture['net/minecraft/nbt/CompoundTag.java'] = nbt
        fixture['net/minecraft/nbt/Tag.java'] = fixture['net/minecraft/nbt/Tag.java'].replace('TAG_COMPOUND=10', 'TAG_LIST=9,TAG_COMPOUND=10')
        fixture['net/minecraft/nbt/ListTag.java'] = 'package net.minecraft.nbt;import java.util.*;public final class ListTag extends Tag {private final List<Tag> tags=new ArrayList<>();public int getId(){return TAG_LIST;}public int getElementType(){return tags.isEmpty()?0:tags.getFirst().getId();}public int size(){return tags.size();}public Tag get(int index){return tags.get(index);}public void add(Tag tag){tags.add(tag);}public Tag copy(){ListTag copy=new ListTag();tags.forEach(t->copy.add(t.copy()));return copy;}public boolean equals(Object value){return value instanceof ListTag list&&tags.equals(list.tags);}public int hashCode(){return tags.hashCode();}}'
        with tempfile.TemporaryDirectory(prefix='aia2-forbidden-ritual-') as tmp:
            files = []
            for name, text in fixture.items():
                path = Path(tmp) / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(text)
                files.append(str(path))
            files.append(str(ROOT / 'tests/fixtures/ForbiddenRitualHarness.java'))
            files.extend(str(ROOT / f'companion/src/main/java/ua/aia2/guard/{name}.java') for name in ['GuardPolicy', 'ForbiddenPaidState', 'ForbiddenRitualAccess'])
            files.extend(str(ROOT / f'companion/src/main/java/ua/aia2/guard/mixin/{name}.java') for name in ['ForbiddenRitualMixin', 'ForbiddenEssencePaymentMixin', 'ForbiddenForgeInputMixin'])
            run = subprocess.run([str(jdk / 'bin/javac'), '-encoding', 'UTF-8', '-cp', str(gson[-1]), '-d', tmp, *files], capture_output=True, text=True)
            self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
            run = subprocess.run([str(jdk / 'bin/java'), '-cp', os.pathsep.join([tmp, str(gson[-1])]), 'ua.aia2.guard.ForbiddenRitualHarness'], capture_output=True, text=True)
            self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
            self.assertIn('modeled assertions PASS', run.stdout)
            print(run.stdout.strip())
