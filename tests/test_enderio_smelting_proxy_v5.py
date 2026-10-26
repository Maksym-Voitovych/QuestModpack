"""Frozen EnderIO converter contract and actual proxy helper with real GuardPolicy.

The executable fixture models Minecraft and EnderIO accessors. It does not launch
Minecraft, exercise mixin dispatch or claim full-pack Survival coverage.
"""
import hashlib
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
JAVA = ROOT/'companion/src/main/java/ua/aia2/guard'
FROZEN = ROOT/'content/research/evidence/energy_guard_next_v5/enderio/enderio/src/main/java/com/enderio/enderio'


class EnderSmeltingProxyTests(unittest.TestCase):
    def test_frozen_native_converter_provenance_contract(self):
        contracts = {
            'content/machines/alloy/AlloySmeltingRecipe.java': '5b628d5b804e910cd62346b90a1d348224c67a8282428bc6b1fd9c362dbf6f89',
            'mixin/RecipeManagerMixin.java': '8fbc8c8be7fd5d73bb457bc09f4b18b4d13f273f845e970331a3eac1465bd984',
            'foundation/MachineRecipe.java': '595d677907f739621ac67f835409a7c43504ba5d10b34c670e4289085c1e7907',
        }
        sources = {}
        for path, expected in contracts.items():
            data = (FROZEN/path).read_bytes()
            self.assertEqual(hashlib.sha256(data).hexdigest(), expected)
            sources[Path(path).name] = data.decode()
        alloy = sources['AlloySmeltingRecipe.java']
        converter = sources['RecipeManagerMixin.java']
        machine = sources['MachineRecipe.java']
        self.assertIn('Codec.BOOL.optionalFieldOf("is_smelting", false)', alloy)
        self.assertIn('public ItemStack output()', alloy)
        self.assertIn('public float experience()', alloy)
        self.assertIn('new SizedIngredient(accessor.getIngredient(), 1)', converter)
        self.assertIn('ALLOY_SMELTER_VANILLA_ITEM_ENERGY.get()', converter)
        self.assertIn('new AlloySmeltingRecipe(List.of(input), accessor.getResult(), energy,', converter)
        self.assertIn('accessor.getExperience(), true)', converter)
        self.assertIn('"smelting/" + originalId.getNamespace() + "/" + originalId.getPath()', converter)
        self.assertIn('byName.put(convertedHolder.id(), convertedHolder)', converter)
        self.assertIn('byType.put(EIORecipes.ALLOY_SMELTING.type().get(), convertedHolder)', converter)
        self.assertIn('default ItemStack getResultItem(HolderLookup.Provider lookupProvider) {\n        return ItemStack.EMPTY;', machine)

    def test_actual_proxy_and_real_policy(self):
        jdk = Path(os.environ.get('JAVA_HOME', '/workspace/aia2-toolchains/jdk-21.0.9'))
        if not (jdk/'bin/javac').is_file():
            self.skipTest('External JDK21 unavailable')
        fixtures = {
            'net/minecraft/core/RegistryAccess.java': 'package net.minecraft.core; public final class RegistryAccess {}',
            'net/minecraft/resources/ResourceLocation.java': '''package net.minecraft.resources;
              public record ResourceLocation(String namespace, String path) {
                public ResourceLocation {
                  if(!namespace.matches("[a-z0-9_.-]+") || !path.matches("[a-z0-9_./-]+"))
                    throw new IllegalArgumentException("Invalid resource location");
                }
                public static ResourceLocation fromNamespaceAndPath(String namespace,String path){return new ResourceLocation(namespace,path);}
                public static ResourceLocation parse(String text){int i=text.indexOf(':');return fromNamespaceAndPath(text.substring(0,i),text.substring(i+1));}
                public String getNamespace(){return namespace;} public String getPath(){return path;}
                public String toString(){return namespace+":"+path;}
              }''',
            'net/minecraft/core/registries/BuiltInRegistries.java': '''package net.minecraft.core.registries;
              import net.minecraft.resources.ResourceLocation; import net.minecraft.world.item.Item;
              public final class BuiltInRegistries {
                public static final ItemRegistry ITEM=new ItemRegistry();
                public static final class ItemRegistry {public ResourceLocation getKey(Item item){return ResourceLocation.parse(item.id);}}
              }''',
            'net/minecraft/world/item/Item.java': '''package net.minecraft.world.item;
              import java.util.*;
              public final class Item {
                private static final Map<String,Item> ITEMS=new HashMap<>();
                public final String id; private Item(String id){this.id=id;}
                public static Item get(String id){return ITEMS.computeIfAbsent(id,Item::new);}
              }''',
            'net/minecraft/world/item/ItemStack.java': '''package net.minecraft.world.item;
              import java.util.*;
              public final class ItemStack {
                public static final ItemStack EMPTY=new ItemStack(null,0,Map.of());
                public final Item item; public int count; public final Map<String,Object> components;
                public ItemStack(String id,int count,Map<String,Object> components){this.item=id==null?null:Item.get(id);this.count=count;this.components=new HashMap<>(components);}
                public boolean isEmpty(){return item==null||count<=0;} public Item getItem(){return item;} public int getCount(){return count;}
                public ItemStack copy(){return new ItemStack(item==null?null:item.id,count,components);}
                public static boolean isSameItemSameComponents(ItemStack a,ItemStack b){return a.item==b.item&&a.components.equals(b.components);}
              }''',
            'net/minecraft/world/item/crafting/Ingredient.java': '''package net.minecraft.world.item.crafting;
              public record Ingredient(String item) {public boolean isEmpty(){return item==null;}}''',
            'net/neoforged/neoforge/common/crafting/SizedIngredient.java': '''package net.neoforged.neoforge.common.crafting;
              import net.minecraft.world.item.crafting.Ingredient;
              public record SizedIngredient(Ingredient ingredient,int count) {}''',
            'net/minecraft/world/item/crafting/Recipe.java': '''package net.minecraft.world.item.crafting;
              import net.minecraft.core.RegistryAccess; import net.minecraft.world.item.ItemStack;
              public interface Recipe<T> {ItemStack getResultItem(RegistryAccess access);}''',
            'net/minecraft/world/item/crafting/RecipeHolder.java': '''package net.minecraft.world.item.crafting;
              import net.minecraft.resources.ResourceLocation;
              public record RecipeHolder<T extends Recipe<?>>(ResourceLocation id,T value) {}''',
            'net/minecraft/world/item/crafting/SmeltingRecipe.java': '''package net.minecraft.world.item.crafting;
              import java.util.*; import net.minecraft.core.RegistryAccess; import net.minecraft.world.item.ItemStack;
              public class SmeltingRecipe implements Recipe<Object> {
                public List<Ingredient> inputs; public ItemStack output; public float xp;
                public SmeltingRecipe(List<Ingredient> inputs,ItemStack output,float xp){this.inputs=inputs;this.output=output;this.xp=xp;}
                public List<Ingredient> getIngredients(){return inputs;}
                public ItemStack getResultItem(RegistryAccess access){return output;}
                public float getExperience(){return xp;}
              }''',
            'net/minecraft/world/item/crafting/RecipeManager.java': '''package net.minecraft.world.item.crafting;
              import java.util.*; import net.minecraft.resources.ResourceLocation;
              public final class RecipeManager {
                public final Map<ResourceLocation,RecipeHolder<?>> rows=new HashMap<>();
                public Optional<RecipeHolder<?>> byKey(ResourceLocation id){return Optional.ofNullable(rows.get(id));}
              }''',
            'net/minecraft/server/level/ServerLevel.java': '''package net.minecraft.server.level;
              import net.minecraft.core.RegistryAccess; import net.minecraft.world.item.crafting.RecipeManager;
              public final class ServerLevel {
                public final RecipeManager recipes=new RecipeManager();
                public RecipeManager getRecipeManager(){return recipes;} public RegistryAccess registryAccess(){return new RegistryAccess();}
              }''',
            'ua/aia2/guard/CreativeManaGuard.java': '''package ua.aia2.guard;
              import net.minecraft.world.item.ItemStack;
              public final class CreativeManaGuard {
                public static boolean isCreativeTablet(ItemStack stack){return !stack.isEmpty()&&stack.getItem().id.equals("botania:mana_tablet")&&Boolean.TRUE.equals(stack.components.get("creative"));}
              }''',
            'ua/aia2/guard/KeyProductionBridge.java': '''package ua.aia2.guard;
              import java.util.*;
              public final class KeyProductionBridge {
                public static final Set<String> KEYS=new HashSet<>();
                public static boolean isKeyOutput(String id){return KEYS.contains(id);}
              }''',
            'com/enderio/enderio/content/machines/alloy/AlloySmeltingRecipe.java': '''package com.enderio.enderio.content.machines.alloy;
              import java.util.*; import net.minecraft.core.RegistryAccess; import net.minecraft.world.item.ItemStack;
              import net.minecraft.world.item.crafting.Recipe; import net.neoforged.neoforge.common.crafting.SizedIngredient;
              public class AlloySmeltingRecipe implements Recipe<Object> {
                public List<SizedIngredient> inputs; public ItemStack output; public int energy; public float xp; public boolean smelting,broken;
                public AlloySmeltingRecipe(List<SizedIngredient> inputs,ItemStack output,int energy,float xp,boolean smelting){this.inputs=inputs;this.output=output;this.energy=energy;this.xp=xp;this.smelting=smelting;}
                public boolean isSmelting(){if(broken)throw new IllegalStateException("modeled incompatible accessor");return smelting;}
                public List<SizedIngredient> inputs(){return inputs;} public ItemStack output(){return output;} public float experience(){return xp;}
                // Matches EnderIO's MachineRecipe default; using this accessor would reject all native conversions.
                public ItemStack getResultItem(RegistryAccess access){return ItemStack.EMPTY;}
              }''',
            'ua/aia2/guard/EnderSmeltingHarness.java': '''package ua.aia2.guard;
              import java.util.*; import net.minecraft.resources.ResourceLocation; import net.minecraft.server.level.ServerLevel;
              import net.minecraft.world.item.ItemStack; import net.minecraft.world.item.crafting.*;
              import net.neoforged.neoforge.common.crafting.SizedIngredient;
              import com.enderio.enderio.content.machines.alloy.AlloySmeltingRecipe;
              public final class EnderSmeltingHarness {
                static int checks; static ServerLevel level=new ServerLevel();
                static final GuardPolicy recipePolicy=new GuardPolicy(),itemPolicy=new GuardPolicy(),progress=new GuardPolicy();
                record Native(RecipeHolder<SmeltingRecipe> source,RecipeHolder<AlloySmeltingRecipe> converted) {}
                static void check(boolean value,String message){checks++;if(!value)throw new AssertionError(message);}
                static ItemStack stack(String id){return new ItemStack(id,1,Map.of());}
                static SmeltingRecipe source(String output){return new SmeltingRecipe(List.of(new Ingredient("minecraft:iron_ore")),stack(output),0.7f);}
                static <T extends Recipe<?>> RecipeHolder<T> install(String id,T recipe){var holder=new RecipeHolder<>(ResourceLocation.parse(id),recipe);level.recipes.rows.put(holder.id(),holder);return holder;}
                static Native nativeRecipe(String id,SmeltingRecipe source){
                  var original=install(id,source);
                  var converted=new AlloySmeltingRecipe(List.of(new SizedIngredient(source.getIngredients().getFirst(),1)),source.output,3200,source.getExperience(),true);
                  return new Native(original,install("enderio:smelting/"+original.id().getNamespace()+"/"+original.id().getPath(),converted));
                }
                static int stage(RecipeHolder<?> holder){return EnderSmeltingProxyAccess.requiredStage(holder,level,recipePolicy::getRequiredStage,itemPolicy::getRequiredStage);}
                static int stage(Native recipe){return stage(recipe.converted());}
                static void denied(Native recipe,String message){check(stage(recipe)==100,message);}
                static void recipeRules(int stage){recipePolicy.setRules(Map.of("example:protected/smelting",stage));}
                static void itemRules(String id,int stage){itemPolicy.setRules(Map.of(id,stage));}
                static final class AlloySubclass extends AlloySmeltingRecipe {
                  AlloySubclass(AlloySmeltingRecipe original){super(original.inputs,original.output,original.energy,original.xp,true);}
                }
                public static void main(String[] args){
                  progress.setRules(Map.of("enderio:alloy_smelter",6));progress.setTeamProgress("team",5);progress.setReady();
                  recipeRules(16);itemRules("example:protected_ingot",18);
                  var normal=nativeRecipe("minecraft:iron_ingot_from_smelting_raw_iron",source("minecraft:iron_ingot"));
                  check(stage(normal)==0,"normal native vanilla smelting stays usable");
                  check(normal.converted.value().getResultItem(level.registryAccess()).isEmpty(),"fixture retains native empty MachineRecipe result");
                  check(progress.mayUseStage(stage(normal),null),"normal furnace conversion does not need owner inference");
                  var protectedSource=nativeRecipe("example:protected/smelting",source("minecraft:iron_ingot"));
                  check(stage(protectedSource)==16,"source recipe ID floor survives conversion");
                  check(!progress.mayUseStage(stage(protectedSource),"team"),"future source denied by real GuardPolicy");
                  progress.setTeamProgress("team",15);check(progress.mayUseStage(stage(protectedSource),"team"),"legitimate source unlock permits conversion");
                  progress.setTeamProgress("team",5);check(!progress.mayUseStage(stage(protectedSource),"team"),"revoked source unlock closes conversion");
                  var protectedOutput=nativeRecipe("minecraft:protected_output",source("example:protected_ingot"));
                  check(stage(protectedOutput)==18,"protected output retains item floor even for vanilla source ID");
                  check(!progress.mayUseStage(stage(protectedOutput),"team"),"protected output cannot be laundered through inherited smelting");
                  var both=nativeRecipe("example:protected/smelting",source("example:protected_ingot"));
                  check(stage(both)==18,"source and item floors combine by maximum");
                  recipeRules(24);check(stage(both)==24,"current source policy can increase converted floor");recipeRules(16);
                  var unknown=nativeRecipe("unclassified:smelting",source("minecraft:iron_ingot"));denied(unknown,"unknown modded source recipe is quarantined");
                  var unknownOutput=nativeRecipe("minecraft:unknown_output",source("unclassified:ingot"));denied(unknownOutput,"unknown output is quarantined");
                  for(String kind:List.of("tech","arcane","epoch"))for(int i=1;i<=48;i++){
                    var key=nativeRecipe("minecraft:key",source("kubejs:aia2_"+kind+"_key_"+String.format("%02d",i)));
                    itemRules(key.source.value().output.getItem().id,0);denied(key,"AIA2 key conversion always denied: "+kind+i);
                  }
                  KeyProductionBridge.KEYS.add("example:bridge_key");itemRules("example:bridge_key",0);
                  var bridgeKey=nativeRecipe("minecraft:bridge_key",source("example:bridge_key"));denied(bridgeKey,"key bridge outputs denied independently of namespace and policy");
                  itemRules("botania:mana_tablet",15);var finite=nativeRecipe("minecraft:finite_tablet",source("botania:mana_tablet"));
                  check(stage(finite)==15,"finite tablet retains ordinary policy");
                  var creativeSource=source("botania:mana_tablet");creativeSource.output.components.put("creative",true);
                  var creative=nativeRecipe("minecraft:creative_tablet",creativeSource);check(stage(creative)==99,"creative component imposes postgame floor");
                  progress.setTeamProgress("team",47);check(!progress.mayUseStage(stage(creative),"team"),"creative output closed before completed postgame");
                  progress.setTeamProgress("team",48);check(progress.mayUseStage(stage(creative),"team"),"creative output opens at completed postgame");
                  itemRules("botania:mana_tablet",100);denied(creative,"creative marker does not weaken unknown output quarantine");

                  var componentsSource=source("minecraft:iron_ingot");componentsSource.output.count=3;
                  componentsSource.output.components.put("minecraft:custom_data",Map.of("aia2",7));
                  var components=nativeRecipe("minecraft:components",componentsSource);
                  check(stage(components)==0,"native full output count and components survive");
                  components.converted.value().output=componentsSource.output.copy();check(stage(components)==0,"full equivalent stack need not share object identity");
                  components.converted.value().output.count=2;denied(components,"changed output count rejected");
                  components.converted.value().output=componentsSource.output.copy();components.converted.value().output.components.clear();denied(components,"stripped output components rejected");
                  components.converted.value().output=componentsSource.output.copy();components.converted.value().output.components.put("minecraft:custom_data",Map.of("aia2",8));denied(components,"changed output components rejected");
                  components.converted.value().output=stack("minecraft:gold_ingot");denied(components,"changed output item rejected");
                  components.converted.value().output=ItemStack.EMPTY;denied(components,"empty converted output rejected");
                  components.converted.value().output=componentsSource.output.copy();componentsSource.output=ItemStack.EMPTY;denied(components,"empty source output rejected");

                  var forged=nativeRecipe("minecraft:forged",source("minecraft:iron_ingot"));var alloy=forged.converted.value();
                  alloy.smelting=false;denied(forged,"ordinary alloy recipe does not inherit smelting policy");alloy.smelting=true;
                  var ingredient=forged.source.value().inputs.getFirst();
                  alloy.inputs=List.of(new SizedIngredient(new Ingredient(ingredient.item()),1));
                  check(alloy.inputs.getFirst().ingredient().equals(ingredient),"forged ingredient is semantically identical to source");
                  denied(forged,"JSON is_smelting flag plus prefix cannot forge native ingredient identity");
                  alloy.inputs=List.of(new SizedIngredient(ingredient,2));denied(forged,"native input count must be one");
                  alloy.inputs=List.of();denied(forged,"missing sized input denied");
                  alloy.inputs=List.of(new SizedIngredient(ingredient,1),new SizedIngredient(ingredient,1));denied(forged,"multiple sized inputs denied");
                  alloy.inputs=List.of(new SizedIngredient(ingredient,1));alloy.xp=1.1f;denied(forged,"changed experience rejected");
                  alloy.xp=forged.source.value().getExperience();check(stage(forged)==0,"exact native conversion restored");
                  alloy.broken=true;denied(forged,"reflection accessor failure is fail closed");alloy.broken=false;
                  forged.source.value().inputs=List.of();denied(forged,"source without ingredients rejected");
                  forged.source.value().inputs=List.of(new Ingredient(null));alloy.inputs=List.of(new SizedIngredient(forged.source.value().inputs.getFirst(),1));denied(forged,"empty source ingredient rejected");

                  var identity=nativeRecipe("minecraft:identity",source("minecraft:iron_ingot"));
                  check(stage(new RecipeHolder<>(identity.converted.id(),identity.converted.value()))==0,"holder wrapper may change while registered recipe identity stays exact");
                  var clone=new AlloySmeltingRecipe(identity.converted.value().inputs,identity.converted.value().output,3200,0.7f,true);
                  check(stage(new RecipeHolder<>(identity.converted.id(),clone))==100,"unregistered clone under valid ID denied");
                  var subclass=install("enderio:smelting/minecraft/identity",new AlloySubclass(identity.converted.value()));
                  check(stage(subclass)==100,"alloy subclass cannot use exact class exception");
                  level.recipes.rows.put(identity.converted.id(),identity.converted);
                  var generic=install("enderio:smelting/minecraft/generic",source("minecraft:iron_ingot"));check(stage(generic)==100,"other recipe class denied");
                  for(String invalid:List.of("example:smelting/minecraft/identity","enderio:identity","enderio:smelting/identity","enderio:smelting//identity","enderio:smelting/minecraft/")){
                    var wrongId=install(invalid,identity.converted.value());check(stage(wrongId)==100,"malformed or wrong namespace conversion denied: "+invalid);
                  }
                  var nested=nativeRecipe("example:protected/smelting",source("minecraft:iron_ingot"));check(stage(nested)==16,"source path may contain slashes");
                  var minecraftNamed=nativeRecipe("minecraft:smelting/minecraft/identity",source("minecraft:iron_ingot"));check(stage(minecraftNamed)==0,"nested native source name is decoded exactly");

                  var reload=nativeRecipe("minecraft:reload",source("minecraft:iron_ingot"));
                  level.recipes.rows.remove(reload.source.id());denied(reload,"removed source cannot survive on converted ID alone");
                  install("minecraft:reload",source("minecraft:iron_ingot"));denied(reload,"same source ID and semantic ingredients after reload cannot restore old identity");
                  var replacement=nativeRecipe("minecraft:reload",source("minecraft:iron_ingot"));denied(reload,"retired converted object is rejected after manager replacement");
                  check(stage(replacement)==0,"new native converter objects work after reload");
                  level.recipes.rows.remove(replacement.converted.id());denied(replacement,"removed converted manager entry denied");
                  level.recipes.rows.put(replacement.converted.id(),replacement.converted);
                  install("minecraft:reload",replacement.converted.value());denied(replacement,"source must remain actual SmeltingRecipe");
                  level=new ServerLevel();denied(normal,"a different manager cannot inherit old registered conversion");

                  check(EnderSmeltingProxyAccess.requiredStage(null,level,recipePolicy::getRequiredStage,itemPolicy::getRequiredStage)==100,"null holder fails closed");
                  check(EnderSmeltingProxyAccess.requiredStage(normal.converted,null,recipePolicy::getRequiredStage,itemPolicy::getRequiredStage)==100,"null level fails closed");
                  check(EnderSmeltingProxyAccess.requiredStage(normal.converted,level,null,itemPolicy::getRequiredStage)==100,"missing source policy fails closed");
                  check(EnderSmeltingProxyAccess.requiredStage(normal.converted,level,recipePolicy::getRequiredStage,null)==100,"missing item policy fails closed");
                  var throwing=nativeRecipe("minecraft:throwing",source("minecraft:iron_ingot"));
                  check(EnderSmeltingProxyAccess.requiredStage(throwing.converted,level,id->{throw new IllegalStateException("policy reload");},itemPolicy::getRequiredStage)==100,"policy failure fails closed");
                  var protectedAgain=nativeRecipe("example:protected/smelting",source("minecraft:iron_ingot"));
                  progress.clear();check(!progress.mayUseStage(stage(protectedAgain),"team"),"unready real policy cannot authorize protected conversion");
                  System.out.println("EnderSmeltingHarness: "+checks+" actual-proxy/real-policy assertions; modeled Minecraft and EnderIO, no optional mixin dispatch");
                }
              }''',
            'ua/aia2/guard/NoEnderHarness.java': '''package ua.aia2.guard;
              import java.util.*; import net.minecraft.server.level.ServerLevel; import net.minecraft.resources.ResourceLocation;
              import net.minecraft.world.item.ItemStack; import net.minecraft.world.item.crafting.*;
              public final class NoEnderHarness {
                public static void main(String[] args){
                  var recipe=new SmeltingRecipe(List.of(new Ingredient("minecraft:iron_ore")),new ItemStack("minecraft:iron_ingot",1,Map.of()),0.7f);
                  var holder=new RecipeHolder<>(ResourceLocation.parse("minecraft:iron"),recipe);
                  if(EnderSmeltingProxyAccess.requiredStage(holder,new ServerLevel(),id->0,id->0)!=100)throw new AssertionError("optional EnderIO absence");
                  System.out.println("NoEnderHarness: helper loads without EnderIO classes");
                }
              }''',
        }
        with tempfile.TemporaryDirectory(prefix='aia2-ender-smelting-') as folder:
            folder = Path(folder)
            files = []
            optional = []
            for name, text in fixtures.items():
                path = folder/name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(text)
                (optional if name.startswith('com/enderio/') or name.endswith('EnderSmeltingHarness.java') else files).append(str(path))
            files += [str(JAVA/'GuardPolicy.java'), str(JAVA/'EnderSmeltingProxyAccess.java')]
            # Compile and run the real helper before any EnderIO class is available.
            result = subprocess.run([str(jdk/'bin/javac'), '-encoding', 'UTF-8', '-d', str(folder), *files], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stdout+result.stderr)
            result = subprocess.run([str(jdk/'bin/java'), '-cp', str(folder), 'ua.aia2.guard.NoEnderHarness'], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stdout+result.stderr)
            self.assertIn('helper loads without EnderIO classes', result.stdout)
            result = subprocess.run([str(jdk/'bin/javac'), '-encoding', 'UTF-8', '-cp', str(folder), '-d', str(folder), *optional], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stdout+result.stderr)
            result = subprocess.run([str(jdk/'bin/java'), '-cp', str(folder), 'ua.aia2.guard.EnderSmeltingHarness'], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stdout+result.stderr)
            self.assertIn('actual-proxy/real-policy assertions', result.stdout)
            print(result.stdout.strip())


if __name__ == '__main__':
    unittest.main()
