"""Pinned lookup/commit contracts plus real handlers in a modeled Minecraft host."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class OritechNativeGuardTests(unittest.TestCase):
    def test_exact_sources_and_all_mixin_target_methods(self):
        audit = json.loads((ROOT/'content/audit/v5-industrial-native-guard.json').read_text())
        sources = {}
        for row in audit['sources']:
            data = (ROOT/row['path']).read_bytes()
            self.assertEqual(hashlib.sha256(data).hexdigest(), row['sha256'])
            sources[Path(row['path']).name] = data.decode()
        self.assertIn('version=1.2.13', sources['gradle.properties'].replace(' ', ''))
        base = sources['MachineBlockEntity.java']
        self.assertIn('new RecipeHolder<>(currentRecipe.getOriType().getIdentifier(), currentRecipe)', base)
        self.assertLess(base.index('var recipeCandidate = getRecipe()'), base.index('useEnergy();'))
        for name in ['Centrifuge', 'Refinery', 'Cooler', 'TaintedRefinery']:
            text = sources[name+'BlockEntity.java']
            self.assertIn('protected Optional<RecipeHolder<OritechRecipe>> getRecipe()', text)
            self.assertIn('.getRecipesFor(', text)
            self.assertIn('protected void craftItem(OritechRecipe activeRecipe, List<ItemStack> outputInventory, List<ItemStack> inputInventory)', text)
        for name in ['Centrifuge', 'Refinery', 'TaintedRefinery']:
            self.assertIn('private void craftFluids(OritechRecipe activeRecipe)', sources[name+'BlockEntity.java'])
        self.assertIn('super.getRecipe()', sources['AtomicForgeBlockEntity.java'])
        self.assertIn('.getRecipesFor(RecipeType.CRAFTING', sources['PulverizerBlockEntity.java'])
        registered = json.loads((ROOT/'companion/src/main/resources/aia2_machine_guard.mixins.json').read_text())['mixins']
        for name in ['OritechMachineMixin', 'OritechFluidMachineMixin', 'OritechDustMixin', 'OritechRecipeLookupMixin', 'OritechBaseTickMixin']:
            self.assertIn(name, registered)
            text = (ROOT/f'companion/src/main/java/ua/aia2/guard/mixin/{name}.java').read_text()
            self.assertNotIn('processing/', text)  # A slash in a dotted target silently skips @Pseudo.
            self.assertNotIn('util/recipes/OritechRecipe', text)

    def test_actual_lookup_commit_and_compaction_handlers(self):
        jdk = Path(os.environ.get('JAVA_HOME', '/workspace/aia2-toolchains/jdk-21.0.9'))
        if not (jdk/'bin/javac').is_file(): self.skipTest('External JDK21 unavailable')
        fixtures = {
            'net/minecraft/world/level/Level.java': 'package net.minecraft.world.level; public class Level {}',
            'net/minecraft/world/level/block/entity/BlockEntity.java': 'package net.minecraft.world.level.block.entity; public interface BlockEntity {String team();}',
            'net/minecraft/world/item/ItemStack.java': 'package net.minecraft.world.item; public class ItemStack {public int count=1;}',
            'net/minecraft/world/item/crafting/RecipeInput.java': 'package net.minecraft.world.item.crafting; public interface RecipeInput {}',
            'net/minecraft/world/item/crafting/Recipe.java': 'package net.minecraft.world.item.crafting; public interface Recipe<T extends RecipeInput> {}',
            'net/minecraft/world/item/crafting/RecipeType.java': 'package net.minecraft.world.item.crafting; public class RecipeType<T extends Recipe<?>> {}',
            'net/minecraft/world/item/crafting/RecipeHolder.java': 'package net.minecraft.world.item.crafting; public record RecipeHolder<T extends Recipe<?>>(String id,T value) {}',
            'net/minecraft/world/item/crafting/RecipeManager.java': '''package net.minecraft.world.item.crafting;
              import java.util.List;import net.minecraft.world.level.Level;
              public class RecipeManager {public List<RecipeHolder<?>> rows=List.of();
              @SuppressWarnings("unchecked") public <I extends RecipeInput,T extends Recipe<I>> List<RecipeHolder<T>> getRecipesFor(RecipeType<T> type,I input,Level level){return (List)rows;}}''',
            'org/spongepowered/asm/mixin/Mixin.java': 'package org.spongepowered.asm.mixin; public @interface Mixin {String[] targets();boolean remap();}',
            'org/spongepowered/asm/mixin/Shadow.java': 'package org.spongepowered.asm.mixin; public @interface Shadow {boolean remap();}',
            'org/spongepowered/asm/mixin/Pseudo.java': 'package org.spongepowered.asm.mixin; public @interface Pseudo {}',
            'org/spongepowered/asm/mixin/injection/At.java': 'package org.spongepowered.asm.mixin.injection; public @interface At {String value();String target() default "";}',
            'org/spongepowered/asm/mixin/injection/Coerce.java': 'package org.spongepowered.asm.mixin.injection; public @interface Coerce {}',
            'org/spongepowered/asm/mixin/injection/Inject.java': 'package org.spongepowered.asm.mixin.injection; public @interface Inject {String method();At at();boolean cancellable();boolean remap();int require();}',
            'org/spongepowered/asm/mixin/injection/Redirect.java': 'package org.spongepowered.asm.mixin.injection; public @interface Redirect {String method();At at();boolean remap();int require();}',
            'org/spongepowered/asm/mixin/injection/callback/CallbackInfo.java': 'package org.spongepowered.asm.mixin.injection.callback; public class CallbackInfo {public boolean canceled;public void cancel(){canceled=true;}}',
            'org/spongepowered/asm/mixin/injection/callback/CallbackInfoReturnable.java': '''package org.spongepowered.asm.mixin.injection.callback;
              public class CallbackInfoReturnable<T> extends CallbackInfo {private T value;public CallbackInfoReturnable(T v){value=v;}public T getReturnValue(){return value;}public void setReturnValue(T v){canceled=true;value=v;}}''',
            'ua/aia2/guard/Aia2MachineGuard.java': '''package ua.aia2.guard;
              import java.util.IdentityHashMap;import net.minecraft.world.item.crafting.Recipe;import net.minecraft.world.level.block.entity.BlockEntity;
              public class Aia2MachineGuard {
                public static final GuardPolicy policy=new GuardPolicy();public static final IdentityHashMap<Object,Integer> index=new IdentityHashMap<>();public static BlockEntity current;
                public static boolean mayProcessRecipe(BlockEntity owner,Recipe<?> recipe){return policy.mayUseStage(index.getOrDefault(recipe,100),owner.team());}
                public static boolean mayProcessRecipeInCurrentTick(Recipe<?> recipe){return current!=null&&mayProcessRecipe(current,recipe);}
              }''',
            'ua/aia2/guard/mixin/OritechGuardHarness.java': '''package ua.aia2.guard.mixin;
              import java.util.*;import java.lang.reflect.Method;import net.minecraft.world.level.Level;import net.minecraft.world.level.block.entity.BlockEntity;
              import net.minecraft.world.item.ItemStack;import net.minecraft.world.item.crafting.*;import ua.aia2.guard.Aia2MachineGuard;
              import org.spongepowered.asm.mixin.injection.callback.*;
              public class OritechGuardHarness {
                static int checks;static void check(boolean b,String s){checks++;if(!b)throw new AssertionError(s);}
                static class R implements Recipe<RecipeInput> {}
                static class Machine extends OritechMachineMixin implements BlockEntity {String owner="a";public String team(){return owner;}}
                static class Lookup extends OritechRecipeLookupMixin implements BlockEntity {String owner="a";public String team(){return owner;}}
                static class Tick extends OritechBaseTickMixin implements BlockEntity {String owner="a";Optional<RecipeHolder<?>> selected;int energy=100;public String team(){return owner;}protected Optional<RecipeHolder<?>> getRecipe(){energy=100;return selected;}}
                static class Fluid extends OritechFluidMachineMixin implements BlockEntity {String owner="a";public String team(){return owner;}}
                static Method hook(Class<?> c,String name,Class<?>... types)throws Exception{var m=c.getDeclaredMethod(name,types);m.setAccessible(true);return m;}
                public static void main(String[] args)throws Exception {
                  var p=Aia2MachineGuard.policy;p.setRules(Map.of("oritech:centrifuge_block",25));p.setTeamProgress("a",24);p.setReady();
                  var machine=new Machine();var fluid=new Fluid();var lookupHost=new Lookup();var low=new R();var high=new R();Aia2MachineGuard.index.put(low,25);Aia2MachineGuard.index.put(high,32);
                  var lookup=hook(OritechRecipeLookupMixin.class,"aia2$guardCachedLookup",CallbackInfoReturnable.class);
                  var commit=hook(OritechMachineMixin.class,"aia2$guardItemCommit",Object.class,List.class,List.class,CallbackInfo.class);
                  var fluidCommit=hook(OritechFluidMachineMixin.class,"aia2$guardFluidCommit",Object.class,CallbackInfo.class);
                  var cb=new CallbackInfoReturnable<>(Optional.of(new RecipeHolder<>("oritech:centrifuge",high)));lookup.invoke(lookupHost,cb);
                  check(cb.getReturnValue().isEmpty(),"type-like holder ID cannot disguise future cached recipe");
                  var lowCb=new CallbackInfoReturnable<>(Optional.of(new RecipeHolder<>("forged:late_id",low)));lookup.invoke(lookupHost,lowCb);
                  check(lowCb.getReturnValue().isPresent(),"canonical value identity wins over holder ID");
                  var inputs=new ArrayList<>(List.of(new ItemStack()));var outputs=new ArrayList<ItemStack>();int energy=100;
                  var denied=new CallbackInfo();commit.invoke(machine,high,outputs,inputs,denied);if(!denied.canceled){inputs.clear();outputs.add(new ItemStack());energy--;}
                  check(denied.canceled&&inputs.size()==1&&outputs.isEmpty()&&energy==100,"item commit denied without side effects");
                  var fc=new CallbackInfo();fluidCommit.invoke(fluid,high,fc);check(fc.canceled,"subclass fluid commit independently denied");
                  p.setTeamProgress("a",31);var allowed=new CallbackInfo();commit.invoke(machine,high,outputs,inputs,allowed);check(!allowed.canceled,"recipe opens at epoch32");
                  fc=new CallbackInfo();fluidCommit.invoke(fluid,high,fc);check(!fc.canceled,"authorized fluid operation unchanged");
                  lookupHost.owner="b";var changed=new CallbackInfoReturnable<>(Optional.of(new RecipeHolder<>("oritech:centrifuge",high)));lookup.invoke(lookupHost,changed);check(changed.getReturnValue().isEmpty(),"unsynchronized owner fails closed");lookupHost.owner="a";
                  var unknown=new CallbackInfo();commit.invoke(machine,new R(),outputs,inputs,unknown);check(unknown.canceled,"unknown or retired identity denied");
                  var wrong=new CallbackInfo();commit.invoke(machine,new Object(),outputs,inputs,wrong);check(wrong.canceled,"non recipe object denied");
                  var tick=new Tick();tick.selected=Optional.of(new RecipeHolder<>("type",high));p.setTeamProgress("a",24);var tickHook=hook(OritechBaseTickMixin.class,"aia2$guardTickSelection",Object.class);check(((Optional<?>)tickHook.invoke(tick,tick)).isEmpty()&&tick.energy==100,"filter after native capacity adjustment retains stored energy");p.setTeamProgress("a",31);check(((Optional<?>)tickHook.invoke(tick,tick)).isPresent(),"authorized polymorphic selection retained");
                  var empty=new CallbackInfoReturnable<>(Optional.empty());lookup.invoke(lookupHost,empty);check(empty.getReturnValue().isEmpty(),"native empty selection retained");
                  var dust=hook(OritechDustMixin.class,"aia2$guardCompaction",RecipeManager.class,RecipeType.class,RecipeInput.class,Level.class);
                  var manager=new RecipeManager();manager.rows=List.of(new RecipeHolder<>("low",low),new RecipeHolder<>("late",high),new RecipeHolder<>("unknown",new R()));
                  Aia2MachineGuard.current=machine;p.setTeamProgress("a",24);
                  var selected=(List<?>)dust.invoke(null,manager,new RecipeType<>(),new RecipeInput(){},new Level());check(selected.size()==1,"dust list filters late and unknown candidates");
                  Aia2MachineGuard.current=null;check(((List<?>)dust.invoke(null,manager,new RecipeType<>(),new RecipeInput(){},new Level())).isEmpty(),"contextless static conversion denied");
                  Aia2MachineGuard.current=machine;p.setTeamProgress("a",31);check(((List<?>)dust.invoke(null,manager,new RecipeType<>(),new RecipeInput(){},new Level())).size()==2,"authorized candidates retained");
                  p.clear();var reload=new CallbackInfo();commit.invoke(machine,high,outputs,inputs,reload);check(reload.canceled,"unready reload cannot process");
                  System.out.println("OritechGuardHarness: "+checks+" actual-handler/real-policy assertions; modeled host, no optional mod dispatch");
                }
              }'''
        }
        with tempfile.TemporaryDirectory(prefix='aia2-oritech-guard-') as folder:
            files = []
            for name, text in fixtures.items():
                p = Path(folder)/name;p.parent.mkdir(parents=True, exist_ok=True);p.write_text(text);files.append(str(p))
            files += [str(ROOT/'companion/src/main/java/ua/aia2/guard/GuardPolicy.java')]
            files += [str(ROOT/f'companion/src/main/java/ua/aia2/guard/mixin/{name}.java') for name in ['OritechMachineMixin','OritechFluidMachineMixin','OritechDustMixin','OritechRecipeLookupMixin','OritechBaseTickMixin']]
            result = subprocess.run([str(jdk/'bin/javac'),'-d',folder,*files],capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stdout+result.stderr)
            result = subprocess.run([str(jdk/'bin/java'),'-cp',folder,'ua.aia2.guard.mixin.OritechGuardHarness'],capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stdout+result.stderr)
            self.assertIn('16 actual-handler/real-policy assertions',result.stdout)
            print(result.stdout.strip())
