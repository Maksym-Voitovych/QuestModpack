"""Exact Roots 1.5.10 source and actual redirect handler; no Roots mod launch."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class RootsMortarGuardTests(unittest.TestCase):
    def test_exact_interaction_has_no_ticker_context_and_consumes_after_lookup(self):
        audit = json.loads((ROOT/'content/audit/v5-roots-mortar-guard.json').read_text())
        text = (ROOT/audit['source']['path']).read_bytes()
        self.assertEqual(hashlib.sha256(text).hexdigest(), audit['source']['sha256'])
        source = text.decode()
        method = source.split('private ItemInteractionResult tryActivateRecipe(', 1)[1].split('public void dropItem', 1)[0]
        self.assertIn('return tryActivateRecipe(player, state);', source)
        self.assertIn('getRecipeFor(RootsRecipes.COMPONENT_RECIPE_TYPE.get()', method)
        self.assertLess(method.index('if (recipeHolder == null)'), method.index('level.addFreshEntity('))
        self.assertLess(method.index('level.addFreshEntity('), method.index('InventoryUtil.clearInventory(inventory)'))
        self.assertNotIn('serverTick', method)
        rules = json.loads((ROOT/'kubejs/config/aia2_runtime.json').read_text())
        for recipe, stage in audit['confirmed_recipe_gates'].items():
            self.assertEqual(rules['recipeGates'][recipe], stage)
            self.assertGreater(stage, rules['blockGates']['rootsclassic:mortar'])
        mixins = json.loads((ROOT/'companion/src/main/resources/aia2_machine_guard.mixins.json').read_text())
        self.assertIn('RootsMortarMixin', mixins['mixins'])

    def test_real_redirect_filters_before_native_consumption_with_real_policy(self):
        jdk = Path(os.environ.get('JAVA_HOME', '/workspace/aia2-toolchains/jdk-21.0.9'))
        if not (jdk/'bin/javac').exists(): self.skipTest('External JDK21 unavailable')
        fixtures = {
            'net/minecraft/world/level/Level.java': 'package net.minecraft.world.level; public class Level {}',
            'net/minecraft/server/level/ServerLevel.java': 'package net.minecraft.server.level; public class ServerLevel extends net.minecraft.world.level.Level {}',
            'net/minecraft/world/level/block/entity/BlockEntity.java': '''package net.minecraft.world.level.block.entity;
                public interface BlockEntity { String team(); }''',
            'net/minecraft/world/item/crafting/RecipeInput.java': 'package net.minecraft.world.item.crafting; public interface RecipeInput {}',
            'net/minecraft/world/item/crafting/Recipe.java': 'package net.minecraft.world.item.crafting; public interface Recipe<I extends RecipeInput> {int stage();}',
            'net/minecraft/world/item/crafting/RecipeType.java': 'package net.minecraft.world.item.crafting; public class RecipeType<T extends Recipe<?>> {}',
            'net/minecraft/world/item/crafting/RecipeHolder.java': 'package net.minecraft.world.item.crafting; public record RecipeHolder<T extends Recipe<?>>(T value) {}',
            'net/minecraft/world/item/crafting/RecipeManager.java': '''package net.minecraft.world.item.crafting;
                import java.util.Optional;import net.minecraft.world.level.Level;
                public class RecipeManager {
                  public RecipeHolder<?> selected; public int calls;
                  @SuppressWarnings("unchecked") public <I extends RecipeInput,T extends Recipe<I>> Optional<RecipeHolder<T>> getRecipeFor(RecipeType<T> type,I input,Level level){calls++;return Optional.ofNullable((RecipeHolder<T>)selected);}
                }''',
            'org/spongepowered/asm/mixin/Mixin.java': 'package org.spongepowered.asm.mixin; public @interface Mixin {String[] targets(); boolean remap();}',
            'org/spongepowered/asm/mixin/Pseudo.java': 'package org.spongepowered.asm.mixin; public @interface Pseudo {}',
            'org/spongepowered/asm/mixin/injection/At.java': 'package org.spongepowered.asm.mixin.injection; public @interface At {String value(); String target();}',
            'org/spongepowered/asm/mixin/injection/Redirect.java': 'package org.spongepowered.asm.mixin.injection; public @interface Redirect {String method(); At at(); boolean remap(); int require();}',
            'ua/aia2/guard/Aia2MachineGuard.java': '''package ua.aia2.guard;
                import net.minecraft.world.level.block.entity.BlockEntity;import net.minecraft.world.item.crafting.Recipe;
                public final class Aia2MachineGuard {
                  public static final GuardPolicy policy=new GuardPolicy(); public static int calls;
                  public static boolean mayProcessRecipe(BlockEntity owner,Recipe<?> recipe){calls++;return policy.mayUseStage(recipe.stage(),owner.team());}
                }''',
            'ua/aia2/guard/mixin/RootsMortarHarness.java': '''package ua.aia2.guard.mixin;
                import java.lang.reflect.Method;import java.util.Optional;
                import net.minecraft.world.item.crafting.*;import net.minecraft.world.level.Level;
                import net.minecraft.server.level.ServerLevel;import net.minecraft.world.level.block.entity.BlockEntity;
                import ua.aia2.guard.Aia2MachineGuard;
                public final class RootsMortarHarness {
                  record Input() implements RecipeInput {} record Component(int stage) implements Recipe<Input> {}
                  static int assertions;static void check(boolean ok,String message){assertions++;if(!ok)throw new AssertionError(message);}
                  static final class Mortar extends RootsMortarMixin implements BlockEntity {
                    String owner="a"; int inputs=4,outputs;public String team(){return owner;}
                    Optional<?> activate(Method hook,RecipeManager manager,Level level)throws Exception {
                      Optional<?> result=(Optional<?>)hook.invoke(this,manager,new RecipeType<Component>(),new Input(),level);
                      if(result.isPresent()&&level instanceof ServerLevel){inputs=0;outputs++;}return result;
                    }
                  }
                  public static void main(String[] args)throws Exception {
                    var policy=Aia2MachineGuard.policy;policy.setRules(java.util.Map.of("rootsclassic:late",30));policy.setTeamProgress("a",13);policy.setReady();
                    Method hook=RootsMortarMixin.class.getDeclaredMethod("aia2$guardPestleLookup",RecipeManager.class,RecipeType.class,RecipeInput.class,Level.class);hook.setAccessible(true);
                    var manager=new RecipeManager();var late=new RecipeHolder<>(new Component(15));manager.selected=late;var mortar=new Mortar();var server=new ServerLevel();
                    check(mortar.activate(hook,manager,server).isEmpty(),"early player interaction denied outside ticker");
                    check(mortar.inputs==4&&mortar.outputs==0,"denied lookup retains ingredients and spawns nothing");
                    check(manager.calls==1&&Aia2MachineGuard.calls==1,"native lookup called once and authoritative policy consulted");
                    policy.setTeamProgress("a",14);check(mortar.activate(hook,manager,server).orElseThrow()==late,"open epoch15 permits exact native holder");
                    check(mortar.inputs==0&&mortar.outputs==1,"allowed native operation executes");
                    manager.selected=new RecipeHolder<>(new Component(30));mortar.inputs=4;
                    check(mortar.activate(hook,manager,server).isEmpty(),"epoch30 component still locked after15");
                    check(mortar.inputs==4&&mortar.outputs==1,"second recipe denial does not consume");
                    policy.setTeamProgress("a",29);check(mortar.activate(hook,manager,server).isPresent(),"open epoch30 permits component");
                    policy.setTeamProgress("a",28);mortar.inputs=4;check(mortar.activate(hook,manager,server).isEmpty(),"access loss rechecked on every interaction");
                    check(mortar.inputs==4&&mortar.outputs==2,"revocation cannot mint output");
                    mortar.owner=null;check(mortar.activate(hook,manager,server).isEmpty(),"unowned mortar denied");mortar.owner="a";
                    manager.selected=new RecipeHolder<>(new Component(100));check(mortar.activate(hook,manager,server).isEmpty(),"unknown recipe quarantined");
                    manager.selected=null;int calls=Aia2MachineGuard.calls;check(mortar.activate(hook,manager,server).isEmpty(),"native no-match preserved");
                    check(calls==Aia2MachineGuard.calls,"empty native result does not query policy");
                    manager.selected=late;check(mortar.activate(hook,manager,new Level()).orElseThrow()==late,"client preview preserved");
                    check(calls==Aia2MachineGuard.calls,"client does not query server policy");
                    policy.clear();check(mortar.activate(hook,manager,server).isEmpty(),"unready server policy fails closed");
                    check(mortar.inputs==4&&mortar.outputs==2,"unready policy preserves input state");
                    System.out.println("RootsMortarHarness: "+assertions+" actual-handler/real-policy assertions passed; modeled host, no Roots dispatch");
                  }
                }''',
        }
        with tempfile.TemporaryDirectory(prefix='aia2-roots-mortar-') as destination:
            files = []
            for name, text in fixtures.items():
                path = Path(destination)/name;path.parent.mkdir(parents=True, exist_ok=True);path.write_text(text);files.append(str(path))
            files += [str(ROOT/'companion/src/main/java/ua/aia2/guard/GuardPolicy.java'),
                      str(ROOT/'companion/src/main/java/ua/aia2/guard/mixin/RootsMortarMixin.java')]
            result = subprocess.run([str(jdk/'bin/javac'),'-encoding','UTF-8','-d',destination,*files],capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stdout+result.stderr)
            result = subprocess.run([str(jdk/'bin/java'),'-cp',destination,'ua.aia2.guard.mixin.RootsMortarHarness'],capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stdout+result.stderr)
            self.assertIn('18 actual-handler/real-policy assertions passed',result.stdout)
            print(result.stdout.strip())
