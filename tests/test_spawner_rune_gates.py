"""Exact-source application order and real native handler in a modeled host."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from tools import build_spawner_gates_v5 as G

ROOT=Path(__file__).resolve().parents[1]

class SpawnerRuneGuardTests(unittest.TestCase):
    def test_effective_export_matches_tier_proofs_and_native_apply_order(self):
        data=G.read(ROOT/G.CATALOG)
        for s in data['sources']:
            self.assertEqual(hashlib.sha256((ROOT/s['path']).read_bytes()).hexdigest(),s['sha256'])
        source=(ROOT/data['sources'][-1]['path']).read_text()
        use=source.split('public ItemInteractionResult useItemOn(',1)[1]
        self.assertLess(use.index('SpawnerModifier.findMatch'),use.index('match.apply(tile)'))
        self.assertLess(use.index('match.apply(tile)'),use.index('stack.shrink(1)'))
        base=ROOT/'content/research/evidence/apothic_split_modules_next_v5/effective_export/spawner_modifiers/tier'
        for tier,key,value in [('ascent','req_player_range',32),('summit','spawn_count',13),('pinnacle','min_delay',20)]:
            recipe=G.read(base/(tier+'.json'))
            self.assertEqual(next(s['value'] for s in recipe['stat_changes'] if s['type']=='apothic_spawners:'+key),value)
        for proof,field,value in [('ascent_range','req_player_range',32),('summit_count','spawn_count',13)]:
            a=G.read(ROOT/f'kubejs/data/aia2/advancement/spawners/{proof}.json')
            self.assertEqual(a['criteria']['modified']['conditions'][field],{'min':value})

    def test_real_handler_checks_imported_runes_both_hands_and_live_team_before_effect(self):
        jdk=Path(os.environ.get('JAVA_HOME','/workspace/aia2-toolchains/jdk-21.0.9'))
        if not (jdk/'bin/javac').is_file():self.skipTest('JDK21 unavailable')
        fixtures={
          'net/minecraft/world/level/Level.java':'package net.minecraft.world.level; public class Level {}',
          'net/minecraft/server/level/ServerLevel.java':'package net.minecraft.server.level; public class ServerLevel extends net.minecraft.world.level.Level {}',
          'net/minecraft/core/BlockPos.java':'package net.minecraft.core; public class BlockPos {}',
          'net/minecraft/world/level/block/state/BlockState.java':'package net.minecraft.world.level.block.state; public class BlockState {}',
          'net/minecraft/world/phys/BlockHitResult.java':'package net.minecraft.world.phys; public class BlockHitResult {}',
          'net/minecraft/world/InteractionHand.java':'package net.minecraft.world; public enum InteractionHand {MAIN_HAND,OFF_HAND}',
          'net/minecraft/world/ItemInteractionResult.java':'package net.minecraft.world; public enum ItemInteractionResult {FAIL,SUCCESS}',
          'net/minecraft/world/item/ItemStack.java':'''package net.minecraft.world.item; public class ItemStack {public final String id;public int count=1;public ItemStack(String s){id=s;}public String getItem(){return id;}}''',
          'net/minecraft/resources/ResourceLocation.java':'''package net.minecraft.resources; public record ResourceLocation(String value){public String getNamespace(){return value.split(":")[0];}public String getPath(){return value.split(":")[1];}}''',
          'net/minecraft/core/registries/BuiltInRegistries.java':'''package net.minecraft.core.registries; import net.minecraft.resources.ResourceLocation; public class BuiltInRegistries {public static final Registry ITEM=new Registry();public static class Registry {public ResourceLocation getKey(String id){return new ResourceLocation(id);}}}''',
          'net/minecraft/world/entity/player/Player.java':'''package net.minecraft.world.entity.player; import net.minecraft.world.item.ItemStack;import net.minecraft.world.InteractionHand;public class Player {public String team="a",synced="a";public boolean fake;public ItemStack main=new ItemStack("minecraft:quartz"),off=new ItemStack("minecraft:air");public ItemStack getItemInHand(InteractionHand hand){return hand==InteractionHand.MAIN_HAND?main:off;}}''',
          'org/spongepowered/asm/mixin/Mixin.java':'package org.spongepowered.asm.mixin; public @interface Mixin {String[] targets();boolean remap();}',
          'org/spongepowered/asm/mixin/Pseudo.java':'package org.spongepowered.asm.mixin; public @interface Pseudo {}',
          'org/spongepowered/asm/mixin/Unique.java':'package org.spongepowered.asm.mixin; public @interface Unique {}',
          'org/spongepowered/asm/mixin/injection/At.java':'package org.spongepowered.asm.mixin.injection; public @interface At {String value();}',
          'org/spongepowered/asm/mixin/injection/Inject.java':'package org.spongepowered.asm.mixin.injection; public @interface Inject {String method();At at();boolean cancellable();boolean remap();int require();}',
          'org/spongepowered/asm/mixin/injection/callback/CallbackInfoReturnable.java':'''package org.spongepowered.asm.mixin.injection.callback; public class CallbackInfoReturnable<T>{public boolean canceled;public T result;public void setReturnValue(T value){canceled=true;result=value;}}''',
          'ua/aia2/guard/Aia2MachineGuard.java':'''package ua.aia2.guard;import net.minecraft.world.entity.player.Player;import net.minecraft.world.item.ItemStack;public class Aia2MachineGuard {public static final GuardPolicy policy=new GuardPolicy();public static int calls;public static boolean mayCraft(Player p,ItemStack s){calls++;return !p.fake&&p.team!=null&&p.team.equals(p.synced)&&policy.mayTick(s.id,p.team);}}''',
          'ua/aia2/guard/mixin/SpawnerRuneHarness.java':'''package ua.aia2.guard.mixin;
            import java.lang.reflect.Method;import net.minecraft.world.*;import net.minecraft.world.item.ItemStack;import net.minecraft.world.entity.player.Player;import net.minecraft.world.level.Level;import net.minecraft.server.level.ServerLevel;import net.minecraft.world.level.block.state.BlockState;import net.minecraft.core.BlockPos;import net.minecraft.world.phys.BlockHitResult;import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;import ua.aia2.guard.Aia2MachineGuard;
            public class SpawnerRuneHarness extends ApothicSpawnerMixin {
              static int assertions;int effects;static void check(boolean b,String s){assertions++;if(!b)throw new AssertionError(s);}
              boolean activate(Method hook,Player p,Level world,InteractionHand hand)throws Exception{var cb=new CallbackInfoReturnable<ItemInteractionResult>();hook.invoke(this,p.getItemInHand(hand),new BlockState(),world,new BlockPos(),p,hand,new BlockHitResult(),cb);if(!cb.canceled){effects++;p.getItemInHand(hand).count--;}return cb.canceled;}
              public static void main(String[] args)throws Exception {
                var policy=Aia2MachineGuard.policy;policy.setRules(java.util.Map.of("apotheosis:pinnacle_spawner_upgrade_rune",41,"apotheosis:no_ai_spawner_rune",31));policy.setTeamProgress("a",19);policy.setReady();
                var h=new SpawnerRuneHarness();var p=new Player();var world=new ServerLevel();p.main=new ItemStack("apotheosis:pinnacle_spawner_upgrade_rune");var hook=ApothicSpawnerMixin.class.getDeclaredMethod("aia2$guardRune",ItemStack.class,BlockState.class,Level.class,BlockPos.class,Player.class,InteractionHand.class,BlockHitResult.class,CallbackInfoReturnable.class);hook.setAccessible(true);
                check(h.activate(hook,p,world,InteractionHand.MAIN_HAND),"imported late rune denied before native apply");check(h.effects==0&&p.main.count==1,"no effect or ingredient loss");
                policy.setTeamProgress("a",40);check(!h.activate(hook,p,world,InteractionHand.MAIN_HAND),"epoch41 permits Pinnacle");check(h.effects==1&&p.main.count==0,"native behavior after authorization");
                p.main.count=1;p.synced="old";check(h.activate(hook,p,world,InteractionHand.MAIN_HAND),"stale team cannot borrow old stage");p.synced="a";p.fake=true;check(h.activate(hook,p,world,InteractionHand.MAIN_HAND),"fake player cannot apply rune");p.fake=false;
                policy.setTeamProgress("a",29);p.main=new ItemStack("minecraft:quartz");p.off=new ItemStack("apotheosis:no_ai_spawner_rune");check(h.activate(hook,p,world,InteractionHand.MAIN_HAND),"inverse rune in opposite hand also checked");check(p.main.count==1&&p.off.count==1,"inverse denied without consuming either hand");
                policy.setTeamProgress("a",30);check(!h.activate(hook,p,world,InteractionHand.OFF_HAND),"authorized offhand rune allowed");
                p.off=new ItemStack("minecraft:air");p.main=new ItemStack("minecraft:quartz");int calls=Aia2MachineGuard.calls;check(!h.activate(hook,p,world,InteractionHand.MAIN_HAND),"ordinary interaction unchanged");check(calls==Aia2MachineGuard.calls,"ordinary item avoids policy queries");
                p.main=new ItemStack("other:pinnacle_spawner_upgrade_rune");check(!h.activate(hook,p,world,InteractionHand.MAIN_HAND),"foreign namespace unaffected");
                p.main=new ItemStack("apotheosis:pinnacle_spawner_upgrade_rune");calls=Aia2MachineGuard.calls;check(!h.activate(hook,p,new Level(),InteractionHand.MAIN_HAND),"client preview unchanged");check(calls==Aia2MachineGuard.calls,"client avoids server policy");
                policy.clear();check(h.activate(hook,p,world,InteractionHand.MAIN_HAND),"unready policy fails closed");
                System.out.println("SpawnerRuneHarness: "+assertions+" actual-handler/real-policy assertions passed; modeled host, no optional Spawners dispatch");
              }
            }'''}
        with tempfile.TemporaryDirectory(prefix='aia2-spawner-rune-') as folder:
            files=[]
            for name,text in fixtures.items():
                p=Path(folder)/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(text);files.append(str(p))
            files += [str(ROOT/'companion/src/main/java/ua/aia2/guard/GuardPolicy.java'),str(ROOT/'companion/src/main/java/ua/aia2/guard/mixin/ApothicSpawnerMixin.java')]
            result=subprocess.run([str(jdk/'bin/javac'),'-encoding','UTF-8','-d',folder,*files],text=True,capture_output=True);self.assertEqual(result.returncode,0,result.stdout+result.stderr)
            result=subprocess.run([str(jdk/'bin/java'),'-cp',folder,'ua.aia2.guard.mixin.SpawnerRuneHarness'],text=True,capture_output=True);self.assertEqual(result.returncode,0,result.stdout+result.stderr);self.assertIn('15 actual-handler/real-policy assertions passed',result.stdout);print(result.stdout.strip())
