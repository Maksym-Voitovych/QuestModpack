"""Pinned MI contracts and real cache/proxy handlers in a modeled Minecraft host.

The executable test uses the real Gson/DFU codecs and GuardPolicy. It does not
launch MI, exercise optional mixin dispatch, or claim full-pack Survival coverage.
"""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


def method_body(text, marker):
    start = text.index('{', text.index(marker))
    depth = 0
    for end in range(start, len(text)):
        depth += (text[end] == '{') - (text[end] == '}')
        if depth == 0:
            return text[start:end+1]
    raise AssertionError('Unclosed method: '+marker)


class ModernCacheGuardTests(unittest.TestCase):
    def test_exact_mi_input_cache_and_codec_contracts(self):
        audit = json.loads((ROOT/'content/audit/v5-industrial-native-guard.json').read_text())
        sources = {}
        for row in audit['sources']:
            if row['mod_id'] != 'modern_industrialization':
                continue
            data = (ROOT/row['path']).read_bytes()
            self.assertEqual(hashlib.sha256(data).hexdigest(), row['sha256'])
            sources[Path(row['path']).name] = data.decode()
        crafter = sources['CrafterComponent.java']
        start = method_body(crafter, 'private boolean tryStartRecipe(')
        self.assertLess(start.index('canStartRecipe('), start.index('takeItemInputs('))
        tick = method_body(crafter, 'public boolean tickRecipe()')
        self.assertLess(tick.index('loadDelayedActiveRecipe();'), tick.index('updateActiveRecipe()'))
        self.assertLess(tick.index('loadDelayedActiveRecipe();'), tick.index('usedEnergy += eu'))
        self.assertLess(tick.index('usedEnergy += eu'), tick.index('putItemOutputs('))
        self.assertIn('efficiencyTicks == 0 && usedEnergy == 0', method_body(crafter, 'private void clearActiveRecipeIfPossible()'))
        self.assertIn('Collections.singletonList(activeRecipe)', method_body(crafter, 'private Iterable<RecipeHolder<MachineRecipe>> getRecipes()'))
        self.assertIn('if (delayedActiveRecipe != null)', method_body(crafter, 'private void loadDelayedActiveRecipe()'))
        codec = method_body(sources['MachineRecipe.java'], 'public static MapCodec<MachineRecipe> codec(')
        for field in ['eu', 'duration', 'item_inputs', 'fluid_inputs', 'item_outputs', 'fluid_outputs', 'process_conditions']:
            self.assertIn('"'+field+'"', codec)
        self.assertIn('DataComponentPatch.CODEC', sources['MachineRecipe.java'])
        self.assertIn('probability', sources['MachineRecipe.java'])
        conversions = sources['RecipeConversions.java']
        for suffix in ['_exported_mi_furnace', '_exported_mi_cutting_machine', '_to_plant_oil']:
            self.assertIn(suffix, conversions)
        registered = json.loads((ROOT/'companion/src/main/resources/aia2_machine_guard.mixins.json').read_text())['mixins']
        for name in ['ModernCrafterMixin', 'ModernRecipeConversionsMixin', 'ModernReplicatorMixin']:
            self.assertIn(name, registered)

    def test_actual_cache_rebind_and_generated_recipe_provenance(self):
        jdk = Path(os.environ.get('JAVA_HOME', '/workspace/aia2-toolchains/jdk-21.0.9'))
        cache = Path(os.environ.get('GRADLE_USER_HOME', '/workspace/aia2-toolchains/gradle-home'))/'caches/modules-2/files-2.1'
        if not (jdk/'bin/javac').is_file():
            self.skipTest('External JDK21 unavailable')
        artifacts = [
            ('com.google.code.gson/gson', 'gson-2.10.1.jar'),
            ('com.mojang/datafixerupper', 'datafixerupper-8.0.16.jar'),
            ('com.google.guava/guava', 'guava-*.jar'),
            ('org.slf4j/slf4j-api', 'slf4j-api-*.jar'),
            ('it.unimi.dsi/fastutil', 'fastutil-*.jar'),
        ]
        jars = []
        for group, pattern in artifacts:
            matches = sorted((cache/group).glob('**/'+pattern))
            if not matches:
                self.skipTest('External codec dependency unavailable: '+group)
            jars.append(str(matches[-1]))
        fixtures = {
            'net/minecraft/core/RegistryAccess.java': 'package net.minecraft.core; public final class RegistryAccess {}',
            # Real codecs use JSON ops. The modeled host has no dynamic registries;
            # Gradle independently checks RegistryOps against actual Minecraft.
            'net/minecraft/resources/RegistryOps.java': '''package net.minecraft.resources;
              import com.google.gson.JsonElement;import com.mojang.serialization.*;import net.minecraft.core.RegistryAccess;
              public final class RegistryOps {public static DynamicOps<JsonElement> create(JsonOps ops,RegistryAccess access){return ops;}}''',
            'net/minecraft/resources/ResourceLocation.java': '''package net.minecraft.resources;
              public record ResourceLocation(String namespace,String path) {
                public static ResourceLocation parse(String text){int split=text.indexOf(':');return new ResourceLocation(text.substring(0,split),text.substring(split+1));}
                public String getNamespace(){return namespace;}public String getPath(){return path;}public String toString(){return namespace+":"+path;}}''',
            'net/minecraft/core/registries/BuiltInRegistries.java': '''package net.minecraft.core.registries;
              import net.minecraft.world.item.Item;import net.minecraft.resources.ResourceLocation;
              public final class BuiltInRegistries {public static final ItemRegistry ITEM=new ItemRegistry();
                public static final class ItemRegistry {public ResourceLocation getKey(Item item){return ResourceLocation.parse(item.id);}}}''',
            'net/minecraft/world/level/ItemLike.java': 'package net.minecraft.world.level; import net.minecraft.world.item.Item; public interface ItemLike {Item asItem();}',
            'net/minecraft/world/item/Item.java': '''package net.minecraft.world.item;
              public class Item implements net.minecraft.world.level.ItemLike {public final String id;public Item(String id){this.id=id;}public Item asItem(){return this;}}''',
            'net/minecraft/world/item/ItemStack.java': '''package net.minecraft.world.item;
              public class ItemStack {public final Item item;public boolean creative;public ItemStack(String id){item=id==null?null:new Item(id);}public boolean isEmpty(){return item==null;}public Item getItem(){return item;}}''',
            'net/minecraft/world/item/crafting/RecipeInput.java': 'package net.minecraft.world.item.crafting; public interface RecipeInput {}',
            'net/minecraft/world/item/crafting/Recipe.java': '''package net.minecraft.world.item.crafting;
              import net.minecraft.world.item.ItemStack;import net.minecraft.core.RegistryAccess;
              public interface Recipe<T extends RecipeInput> {RecipeSerializer<?> getSerializer();RecipeType<?> getType();ItemStack getResultItem(RegistryAccess registry);}''',
            'net/minecraft/world/item/crafting/RecipeSerializer.java': '''package net.minecraft.world.item.crafting;
              import com.mojang.serialization.MapCodec;public interface RecipeSerializer<T extends Recipe<?>> {MapCodec<T> codec();}''',
            'net/minecraft/world/item/crafting/RecipeType.java': 'package net.minecraft.world.item.crafting; public class RecipeType<T extends Recipe<?>> {}',
            'net/minecraft/world/item/crafting/RecipeHolder.java': '''package net.minecraft.world.item.crafting;
              import net.minecraft.resources.ResourceLocation;public record RecipeHolder<T extends Recipe<?>>(ResourceLocation id,T value) {}''',
            'net/minecraft/world/item/crafting/RecipeManager.java': '''package net.minecraft.world.item.crafting;
              import java.util.*;import net.minecraft.resources.ResourceLocation;
              public class RecipeManager {public final Map<ResourceLocation,RecipeHolder<?>> rows=new HashMap<>();public Optional<RecipeHolder<?>> byKey(ResourceLocation id){return Optional.ofNullable(rows.get(id));}}''',
            'net/minecraft/world/item/crafting/BaseRecipe.java': '''package net.minecraft.world.item.crafting;
              import com.google.gson.*;import com.mojang.serialization.*;import net.minecraft.world.item.ItemStack;import net.minecraft.core.RegistryAccess;
              public class BaseRecipe implements Recipe<RecipeInput> {
                public static int encodings;
                public static final MapCodec<BaseRecipe> CODEC=Codec.PASSTHROUGH.fieldOf("payload").xmap(
                  data->new BaseRecipe(data.convert(JsonOps.INSTANCE).getValue().getAsJsonObject()),
                  recipe->{encodings++;if(recipe.invalid)throw new IllegalArgumentException("bad model codec");return new Dynamic<>(JsonOps.INSTANCE,recipe.data);});
                public static final RecipeSerializer<BaseRecipe> SERIALIZER=()->CODEC;
                public static final RecipeType<BaseRecipe> TYPE=new RecipeType<>();
                public JsonObject data;public boolean invalid;public RecipeSerializer<?> serializer=SERIALIZER;public RecipeType<?> type=TYPE;
                public ItemStack output=new ItemStack("minecraft:iron_ingot");
                public BaseRecipe(JsonObject data){this.data=data;}public RecipeSerializer<?> getSerializer(){return serializer;}public RecipeType<?> getType(){return type;}public ItemStack getResultItem(RegistryAccess registry){return output;}
              }''',
            'net/minecraft/world/item/crafting/SmeltingRecipe.java': '''package net.minecraft.world.item.crafting;
              public class SmeltingRecipe extends BaseRecipe {public SmeltingRecipe(){super(new com.google.gson.JsonObject());}}''',
            'net/minecraft/world/item/crafting/StonecutterRecipe.java': '''package net.minecraft.world.item.crafting;
              public class StonecutterRecipe extends BaseRecipe {public StonecutterRecipe(){super(new com.google.gson.JsonObject());}}''',
            'aztech/modern_industrialization/machines/recipe/MachineRecipe.java': '''package aztech.modern_industrialization.machines.recipe;
              public class MachineRecipe extends net.minecraft.world.item.crafting.BaseRecipe {public MachineRecipe(com.google.gson.JsonObject data){super(data);}}''',
            'net/minecraft/server/level/ServerLevel.java': '''package net.minecraft.server.level;
              import net.minecraft.core.RegistryAccess;import net.minecraft.world.item.crafting.RecipeManager;
              public final class ServerLevel {public final RecipeManager recipes=new RecipeManager();public RecipeManager getRecipeManager(){return recipes;}public RegistryAccess registryAccess(){return new RegistryAccess();}}''',
            'org/spongepowered/asm/mixin/Mixin.java': 'package org.spongepowered.asm.mixin; public @interface Mixin {String[] targets();boolean remap();}',
            'org/spongepowered/asm/mixin/Pseudo.java': 'package org.spongepowered.asm.mixin; public @interface Pseudo {}',
            'org/spongepowered/asm/mixin/Shadow.java': 'package org.spongepowered.asm.mixin; public @interface Shadow {boolean remap();}',
            'org/spongepowered/asm/mixin/injection/At.java': '''package org.spongepowered.asm.mixin.injection;
              public @interface At {String value();String target() default "";Shift shift() default Shift.NONE;enum Shift{NONE,AFTER}}''',
            'org/spongepowered/asm/mixin/injection/Coerce.java': 'package org.spongepowered.asm.mixin.injection; public @interface Coerce {}',
            'org/spongepowered/asm/mixin/injection/Inject.java': '''package org.spongepowered.asm.mixin.injection;
              public @interface Inject {String method();At at();boolean cancellable();boolean remap();int require();}''',
            'org/spongepowered/asm/mixin/injection/callback/CallbackInfoReturnable.java': '''package org.spongepowered.asm.mixin.injection.callback;
              public class CallbackInfoReturnable<T> {public boolean canceled;public T value;public void setReturnValue(T v){value=v;canceled=true;}}''',
            'ua/aia2/guard/CreativeManaGuard.java': '''package ua.aia2.guard;
              public final class CreativeManaGuard {public static boolean isCreativeTablet(net.minecraft.world.item.ItemStack stack){return stack.creative;}}''',
            'ua/aia2/guard/Aia2MachineGuard.java': '''package ua.aia2.guard;
              import java.util.*;import net.minecraft.server.level.ServerLevel;import net.minecraft.world.item.crafting.Recipe;
              public final class Aia2MachineGuard {
                public static final GuardPolicy policy=new GuardPolicy();public static final IdentityHashMap<Object,Integer> index=new IdentityHashMap<>();
                public static final Map<String,Integer> items=new HashMap<>();public static ServerLevel level;public static String team="a";
                public static ServerLevel currentTickServerLevel(){return level;}
                public static int stage(Object recipe){return index.getOrDefault(recipe,100);}
                public static int item(String id){return items.getOrDefault(id,id.startsWith("minecraft:")?0:100);}
                public static boolean mayProcessRecipeInCurrentTick(Recipe<?> recipe){
                  if(level==null)return false;int stage=stage(recipe);
                  if(stage==100)stage=ModernRecipeProxyAccess.requiredStage(recipe,level,Aia2MachineGuard::stage,Aia2MachineGuard::item);
                  return policy.mayUseStage(stage,team);
                }
              }''',
            'ua/aia2/guard/mixin/ModernCacheHarness.java': '''package ua.aia2.guard.mixin;
              import java.lang.reflect.*;import java.util.*;import com.google.gson.*;
              import aztech.modern_industrialization.machines.recipe.MachineRecipe;
              import net.minecraft.resources.ResourceLocation;import net.minecraft.server.level.ServerLevel;
              import net.minecraft.world.item.*;import net.minecraft.world.item.crafting.*;
              import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;
              import ua.aia2.guard.*;
              public final class ModernCacheHarness {
                static int checks;static void check(boolean b,String s){checks++;if(!b)throw new AssertionError(s);}
                static final class Crafter extends ModernCrafterMixin {}
                static Field field(String name)throws Exception{var f=ModernCrafterMixin.class.getDeclaredField(name);f.setAccessible(true);return f;}
                static Method hook(String name,Class<?>... types)throws Exception{var m=ModernCrafterMixin.class.getDeclaredMethod(name,types);m.setAccessible(true);return m;}
                static void state(Crafter c,RecipeHolder<?> recipe,long eu,int efficiency)throws Exception{field("activeRecipe").set(c,recipe);field("usedEnergy").setLong(c,eu);field("efficiencyTicks").setInt(c,efficiency);}
                static RecipeHolder<?> active(Crafter c)throws Exception{return (RecipeHolder<?>)field("activeRecipe").get(c);}
                static long eu(Crafter c)throws Exception{return field("usedEnergy").getLong(c);}
                static int efficiency(Crafter c)throws Exception{return field("efficiencyTicks").getInt(c);}
                static JsonObject document(){return JsonParser.parseString("{\\"eu\\":4,\\"duration\\":600,\\"item_inputs\\":[{\\"item\\":\\"minecraft:iron_ingot\\",\\"amount\\":1,\\"probability\\":0.04}],\\"fluid_inputs\\":[{\\"fluid\\":\\"minecraft:water\\",\\"amount\\":100}],\\"item_outputs\\":[{\\"item\\":\\"minecraft:gold_ingot\\",\\"amount\\":2,\\"probability\\":1,\\"components\\":{\\"minecraft:custom_data\\":{\\"a\\":1}}}],\\"fluid_outputs\\":[{\\"fluid\\":\\"minecraft:water\\",\\"amount\\":10,\\"probability\\":0.5}],\\"process_conditions\\":[{\\"type\\":\\"modern_industrialization:biome\\",\\"biome\\":\\"minecraft:plains\\"}]}").getAsJsonObject();}
                static MachineRecipe recipe(){return new MachineRecipe(document());}
                static RecipeHolder<?> holder(String id,Recipe<?> r){return new RecipeHolder<>(ResourceLocation.parse(id),r);}
                static RecipeHolder<?> install(String id,Recipe<?> r,int stage){var h=holder(id,r);Aia2MachineGuard.level.recipes.rows.put(h.id(),h);Aia2MachineGuard.index.put(r,stage);return h;}
                static CallbackInfoReturnable<Boolean> tick(Method hook,Crafter c)throws Exception{var cb=new CallbackInfoReturnable<Boolean>();hook.invoke(c,cb);return cb;}
                static boolean mayStart(Method start,Object recipe)throws Exception{var cb=new CallbackInfoReturnable<Boolean>();start.invoke(new Crafter(),recipe,cb);return !cb.canceled;}
                static int proxyStage(Recipe<?> recipe){return ModernRecipeProxyAccess.requiredStage(recipe,Aia2MachineGuard.level,Aia2MachineGuard::stage,Aia2MachineGuard::item);}
                public static void main(String[] args)throws Exception{
                  Aia2MachineGuard.level=new ServerLevel();var p=Aia2MachineGuard.policy;
                  p.setRules(Map.of("modern_industrialization:steam_quarry",6));p.setTeamProgress("a",5);p.setReady();
                  Method start=hook("aia2$guardStart",Object.class,CallbackInfoReturnable.class),tick=hook("aia2$guardPaidRecipe",CallbackInfoReturnable.class);
                  var low=recipe();var lowHolder=install("modern_industrialization:low",low,6);
                  var high=recipe();var highHolder=install("modern_industrialization:quarry/bronze",high,16);
                  check(mayStart(start,low),"current epoch recipe starts");
                  int input=4;if(mayStart(start,high))input--;check(input==4,"future recipe denied before native input consumption");
                  check(!mayStart(start,new Object()),"non Recipe input denied");
                  Aia2MachineGuard.level=null;check(!mayStart(start,low),"contextless native machine lookup denied");Aia2MachineGuard.level=new ServerLevel();
                  install("modern_industrialization:quarry/bronze",high,16);
                  var c=new Crafter();state(c,highHolder,30,12);
                  check(tick(tick,c).canceled&&eu(c)==30&&efficiency(c)==12&&active(c)==highHolder,"paid future work paused without loss");
                  p.setTeamProgress("a",15);check(!tick(tick,c).canceled&&active(c)==highHolder,"paid work continues after legitimate unlock");
                  p.setTeamProgress("a",5);check(tick(tick,c).canceled&&eu(c)==30,"revoked progress closes existing cache");
                  state(c,highHolder,0,30);check(!tick(tick,c).canceled&&active(c)==null&&efficiency(c)==0,"unpaid locked efficiency cache released for fresh native selection");
                  state(c,null,0,0);check(!tick(tick,c).canceled,"empty cache leaves native lookup alone");
                  Aia2MachineGuard.index.remove(low);var fresh=recipe();var freshHolder=install("modern_industrialization:low",fresh,6);
                  state(c,lowHolder,0,20);check(!tick(tick,c).canceled&&active(c)==null,"unpaid retired cache cannot freeze native rescan");
                  state(c,lowHolder,45,22);int encoded=BaseRecipe.encodings;
                  check(!tick(tick,c).canceled&&active(c)==freshHolder,"unchanged paid native recipe rebound after reload");
                  check(eu(c)==45&&efficiency(c)==22,"safe rebind preserves paid energy and efficiency");
                  check(BaseRecipe.encodings==encoded+2,"comparison encodes both complete native recipes");
                  encoded=BaseRecipe.encodings;check(ModernRecipeProxyAccess.rebindUnchanged(lowHolder,Aia2MachineGuard.level)==freshHolder&&BaseRecipe.encodings==encoded,"same replacement identity reuses successful comparison");
                  for(String field:List.of("eu","duration","item_inputs","fluid_inputs","item_outputs","fluid_outputs","process_conditions")){
                    var changed=recipe();changed.data.addProperty(field,"changed");var replacement=install("modern_industrialization:low",changed,6);
                    state(c,lowHolder,45,22);check(tick(tick,c).canceled&&eu(c)==45&&active(c)==lowHolder,"changed "+field+" cannot rewrite paid work");
                    encoded=BaseRecipe.encodings;check(ModernRecipeProxyAccess.rebindUnchanged(lowHolder,Aia2MachineGuard.level)==null&&BaseRecipe.encodings==encoded,"unchanged denied identity is not serialized every server tick");
                  }
                  var components=recipe();components.data.getAsJsonArray("item_outputs").get(0).getAsJsonObject().getAsJsonObject("components").addProperty("aia2:forged",true);install("modern_industrialization:low",components,6);
                  check(ModernRecipeProxyAccess.rebindUnchanged(lowHolder,Aia2MachineGuard.level)==null,"output component changes also reject paid rebind");
                  Aia2MachineGuard.level.recipes.rows.remove(lowHolder.id());state(c,lowHolder,45,22);
                  check(tick(tick,c).canceled&&eu(c)==45&&active(c)==lowHolder,"removed paid recipe preserved and quarantined");
                  var restored=recipe();var restoredHolder=install("modern_industrialization:low",restored,6);check(!tick(tick,c).canceled&&active(c)==restoredHolder,"later identical restoration recovers paid native work");
                  var late=recipe();var lateHolder=install("modern_industrialization:low",late,16);state(c,lowHolder,45,22);
                  check(tick(tick,c).canceled&&active(c)==lowHolder&&eu(c)==45,"equivalent fresh object still obeys current recipe stage");p.setTeamProgress("a",15);
                  check(!tick(tick,c).canceled&&active(c)==lateHolder,"current stage unlock permits previously equivalent paid rebind");p.setTeamProgress("a",5);
                  var wrongSerializer=recipe();wrongSerializer.serializer=(RecipeSerializer<BaseRecipe>)()->BaseRecipe.CODEC;install("modern_industrialization:low",wrongSerializer,6);
                  check(ModernRecipeProxyAccess.rebindUnchanged(lowHolder,Aia2MachineGuard.level)==null,"serializer identity cannot change under same ID");
                  var wrongType=recipe();wrongType.type=new RecipeType<>();install("modern_industrialization:low",wrongType,6);
                  check(ModernRecipeProxyAccess.rebindUnchanged(lowHolder,Aia2MachineGuard.level)==null,"machine process type cannot change under same ID");
                  install("modern_industrialization:low",new SmeltingRecipe(),6);check(ModernRecipeProxyAccess.rebindUnchanged(lowHolder,Aia2MachineGuard.level)==null,"non MI replacement rejected");
                  var invalid=recipe();invalid.invalid=true;install("modern_industrialization:low",invalid,6);state(c,lowHolder,45,22);
                  check(tick(tick,c).canceled&&eu(c)==45,"codec failure pauses without crashing or losing paid inputs");
                  encoded=BaseRecipe.encodings;check(ModernRecipeProxyAccess.rebindUnchanged(lowHolder,Aia2MachineGuard.level)==null&&BaseRecipe.encodings==encoded,"invalid codec failure is cached per replacement identity");
                  check(ModernRecipeProxyAccess.rebindUnchanged(lowHolder,null)==null,"no server level cannot rebind");
                  install("modern_industrialization:low",low,6);encoded=BaseRecipe.encodings;
                  check(ModernRecipeProxyAccess.rebindUnchanged(lowHolder,Aia2MachineGuard.level).value()==low&&BaseRecipe.encodings==encoded,"current object uses no codec work");
                  var source=new SmeltingRecipe();var sourceHolder=install("minecraft:iron",source,6);var generated=recipe();var generatedHolder=holder("minecraft:/iron_exported_mi_furnace",generated);
                  Aia2MachineGuard.items.put("minecraft:iron_ingot",16);ModernRecipeProxyAccess.registerConversion(sourceHolder,generatedHolder,"smelting");
                  check(proxyStage(generated)==16,"smelting conversion inherits source and output policy");
                  check(proxyStage(recipe())==100,"lookalike MachineRecipe without native provenance quarantined");
                  var forged=recipe();ModernRecipeProxyAccess.registerConversion(sourceHolder,holder("minecraft:iron_exported_mi_furnace",forged),"smelting");check(proxyStage(forged)==100,"forged suffix without exact native ID rejected");
                  var wrongKind=recipe();ModernRecipeProxyAccess.registerConversion(sourceHolder,holder("minecraft:/iron_exported_mi_cutting_machine",wrongKind),"stonecutting");check(proxyStage(wrongKind)==100,"conversion requires actual vanilla recipe class");
                  source.output=new ItemStack("kubejs:aia2_tech_key_01");check(proxyStage(generated)==100,"native conversion cannot mint epoch keys");
                  source.output=new ItemStack("botania:mana_tablet");source.output.creative=true;Aia2MachineGuard.items.put("botania:mana_tablet",15);check(proxyStage(generated)==99,"component-bearing creative tablet remains postgame");source.output=new ItemStack("minecraft:iron_ingot");
                  var stone=new StonecutterRecipe();var stoneHolder=install("minecraft:stone",stone,6);var cutting=recipe();ModernRecipeProxyAccess.registerConversion(stoneHolder,holder("minecraft:/stone_exported_mi_cutting_machine",cutting),"stonecutting");check(proxyStage(cutting)==16,"stonecutting conversion preserves output floor");
                  var compost=recipe();ModernRecipeProxyAccess.registerCompost(new Item("minecraft:wheat"),holder("modern_industrialization:/wheat_to_plant_oil",compost));
                  Aia2MachineGuard.items.put("minecraft:wheat",12);Aia2MachineGuard.items.put("modern_industrialization:plant_oil_bucket",14);check(proxyStage(compost)==14,"compost provenance obeys input and fluid output floors");
                  Aia2MachineGuard.index.remove(source);var newSource=new SmeltingRecipe();var newSourceHolder=install("minecraft:iron",newSource,6);
                  check(proxyStage(generated)==100,"retired original never restored by generated ID alone");
                  state(c,generatedHolder,40,11);check(tick(tick,c).canceled&&eu(c)==40&&active(c)==generatedHolder,"paid stale generated conversion pauses rather than guessing original provenance");
                  state(c,generatedHolder,0,11);check(!tick(tick,c).canceled&&active(c)==null,"unpaid stale conversion can be replaced through native fresh lookup");
                  var freshGenerated=recipe();ModernRecipeProxyAccess.registerConversion(newSourceHolder,holder("minecraft:/iron_exported_mi_furnace",freshGenerated),"smelting");check(proxyStage(freshGenerated)==16,"fresh native conversion after reload remains supported");
                  p.clear();state(c,lowHolder,40,11);check(tick(tick,c).canceled&&eu(c)==40,"unready guard cannot resume work through rebind");
                  System.out.println("ModernCacheHarness: "+checks+" actual-handler/proxy/real-policy assertions; real DFU/Gson, modeled host, no MI optional dispatch");
                }
              }''',
        }
        with tempfile.TemporaryDirectory(prefix='aia2-modern-cache-') as folder:
            files = []
            for name, text in fixtures.items():
                path = Path(folder)/name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(text)
                files.append(str(path))
            files += [str(ROOT/'companion/src/main/java/ua/aia2/guard/GuardPolicy.java'),
                      str(ROOT/'companion/src/main/java/ua/aia2/guard/ModernRecipeProxyAccess.java'),
                      str(ROOT/'companion/src/main/java/ua/aia2/guard/mixin/ModernCrafterMixin.java')]
            classpath = os.pathsep.join([folder, *jars])
            result = subprocess.run([str(jdk/'bin/javac'), '-encoding', 'UTF-8', '-cp', classpath, '-d', folder, *files], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stdout+result.stderr)
            result = subprocess.run([str(jdk/'bin/java'), '-cp', classpath, 'ua.aia2.guard.mixin.ModernCacheHarness'], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stdout+result.stderr)
            self.assertIn('actual-handler/proxy/real-policy assertions', result.stdout)
            print(result.stdout.strip())


if __name__ == '__main__':
    unittest.main()
