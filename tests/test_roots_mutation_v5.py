"""Execute pinned Roots predicates and actual mixin handlers in a modeled host."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT/'content/research/evidence/roots_core_next_v5/official/src/main/java'


class RootsMutationFixTests(unittest.TestCase):
    def test_exact_native_sources_and_consumption_boundary(self):
        audit = json.loads((ROOT/'content/audit/v5-roots-mutation-fix.json').read_text())
        sources = {}
        for spec in audit['sources']:
            data = (ROOT/spec['path']).read_bytes()
            self.assertEqual(hashlib.sha256(data).hexdigest(), spec['sha256'])
            sources[Path(spec['path']).name] = data.decode()
        self.assertIn('mod_version=1.5.10', sources['gradle.properties'])
        self.assertIn('mc_version=1.21.1', sources['gradle.properties'])
        base = sources['MutagenRecipe.java']
        self.assertIn('final List<ItemStack> inputs = new ArrayList<>()', base)
        self.assertIn('ItemStack.isSameItem(input, tempItems.get(j))', base)
        self.assertIn('tempItems.remove(j)', base)
        self.assertIn('return tempItems.size() == 0', base)
        self.assertNotIn('items.size() == inputs.size()', base)
        radiant = sources['MutagenRadiantDaisyRecipe.java']
        self.assertEqual(radiant.count('getDayTime()'), 2)
        self.assertIn('getDayTime() > 5000', radiant)
        self.assertIn('getDayTime() < 7000', radiant)
        self.assertIn('Level.OVERWORLD', radiant)
        self.assertIn('MobEffects.NIGHT_VISION', radiant)
        self.assertIn('Level.NETHER', sources['MutagenFlareOrchidRecipe.java'])
        self.assertIn('MobEffects.FIRE_RESISTANCE', sources['MutagenFlareOrchidRecipe.java'])
        self.assertIn('Level.END', sources['MutagenMidnightBloomRecipe.java'])
        self.assertIn('MobEffects.MOVEMENT_SLOWDOWN', sources['MutagenMidnightBloomRecipe.java'])
        self.assertEqual(sources['MutagenManager.java'].count('recipes.add(new '), 3)
        powder = sources['MutatingPowderItem.java']
        self.assertLess(powder.index('if (recipe != null)'), powder.index('itemEntity.discard()'))
        self.assertLess(powder.index('recipe.onCrafted('), powder.index('stack.shrink(1)'))
        # Failed attempts still pay the native powder cost. The fix does not
        # promise zero-cost attempts or modify dropped-stack consumption.
        self.assertIn('if (!player.getAbilities().instabuild)', powder)

    def test_actual_handlers_with_original_unmodified_predicates(self):
        jdk = Path(os.environ.get('JAVA_HOME', '/workspace/aia2-toolchains/jdk-21.0.9'))
        if not (jdk/'bin/javac').is_file(): self.skipTest('External JDK21 unavailable')
        fixtures = {
            'net/minecraft/core/BlockPos.java': '''package net.minecraft.core;
                public record BlockPos(int x,int y,int z) {
                  public BlockPos east(){return new BlockPos(x+1,y,z);}public BlockPos west(){return new BlockPos(x-1,y,z);}
                  public BlockPos north(){return new BlockPos(x,y,z-1);}public BlockPos south(){return new BlockPos(x,y,z+1);}
                  public BlockPos below(int n){return new BlockPos(x,y-n,z);}
                }''',
            'net/minecraft/resources/ResourceLocation.java': '''package net.minecraft.resources;
                public record ResourceLocation(String namespace,String path) {}''',
            'net/minecraft/world/level/block/Block.java': '''package net.minecraft.world.level.block;
                import net.minecraft.world.level.block.state.BlockState;
                public record Block(String name){public BlockState defaultBlockState(){return new BlockState(this);}}''',
            'net/minecraft/world/level/block/state/BlockState.java': '''package net.minecraft.world.level.block.state;
                import net.minecraft.world.level.block.Block;
                public record BlockState(Block block){public boolean is(Block b){return block==b;}public Block getBlock(){return block;}}''',
            'net/minecraft/world/level/block/Blocks.java': '''package net.minecraft.world.level.block;
                public final class Blocks {
                  public static final Block AIR=new Block("air"),OXEYE_DAISY=new Block("oxeye_daisy"),GLOWSTONE=new Block("glowstone"),
                    BLUE_ORCHID=new Block("blue_orchid"),NETHERRACK=new Block("netherrack"),POPPY=new Block("poppy"),
                    COAL_BLOCK=new Block("coal_block"),OBSIDIAN=new Block("obsidian");
                }''',
            'net/minecraft/world/item/Items.java': '''package net.minecraft.world.item;
                public final class Items {public static final Object PRISMARINE_CRYSTALS=new Object(),BLAZE_ROD=new Object(),LAVA_BUCKET=new Object(),QUARTZ=new Object();}''',
            'net/minecraft/world/item/ItemStack.java': '''package net.minecraft.world.item;
                public final class ItemStack {
                  public final Object item;public int count;public String components="";
                  public ItemStack(Object item,int count){this.item=item;this.count=count;}
                  public static boolean isSameItem(ItemStack a,ItemStack b){return a.item==b.item;}
                }''',
            'net/minecraft/world/level/Level.java': '''package net.minecraft.world.level;
                import java.util.HashMap;import java.util.Map;import net.minecraft.core.BlockPos;
                import net.minecraft.world.level.block.Blocks;import net.minecraft.world.level.block.state.BlockState;
                public class Level {
                  public static final Object OVERWORLD=new Object(),NETHER=new Object(),END=new Object();
                  public Object dimension=OVERWORLD;public long time;public int clockReads;
                  public final Map<BlockPos,BlockState> blocks=new HashMap<>();
                  public Object dimension(){return dimension;}public long getDayTime(){clockReads++;return time;}
                  public BlockState getBlockState(BlockPos pos){return blocks.getOrDefault(pos,Blocks.AIR.defaultBlockState());}
                }''',
            'net/minecraft/world/effect/MobEffects.java': '''package net.minecraft.world.effect;
                public final class MobEffects {public static final Object NIGHT_VISION=new Object(),FIRE_RESISTANCE=new Object(),MOVEMENT_SLOWDOWN=new Object(),BLINDNESS=new Object();}''',
            'net/minecraft/world/effect/MobEffectInstance.java': '''package net.minecraft.world.effect;
                public record MobEffectInstance(Object effect,int duration,int amplifier) {}''',
            'net/minecraft/nbt/CompoundTag.java': '''package net.minecraft.nbt;import java.util.HashMap;
                public class CompoundTag {private final HashMap<String,Integer> values=new HashMap<>();public void putInt(String k,int v){values.put(k,v);}public int getInt(String k){return values.getOrDefault(k,0);}}''',
            'net/minecraft/world/entity/player/Player.java': '''package net.minecraft.world.entity.player;
                import java.util.HashMap;import java.util.Map;import net.minecraft.world.level.Level;import net.minecraft.world.effect.MobEffectInstance;import net.minecraft.nbt.CompoundTag;
                public class Player {public Level world;public int fireSeconds;public final Map<Object,MobEffectInstance> effects=new HashMap<>();private final CompoundTag data=new CompoundTag();
                  public Player(Level world){this.world=world;}public Level getCommandSenderWorld(){return world;}
                  public MobEffectInstance getEffect(Object key){return effects.get(key);}public void addEffect(MobEffectInstance e){effects.put(e.effect(),e);}
                  public void igniteForSeconds(int n){fireSeconds=n;}public CompoundTag getPersistentData(){return data;}
                }''',
            'elucent/rootsclassic/Const.java': '''package elucent.rootsclassic;import net.minecraft.resources.ResourceLocation;
                public final class Const {public static final String NBT_SKIP_TICKS="skipTicks";public static ResourceLocation modLoc(String path){return new ResourceLocation("rootsclassic",path);}}''',
            'elucent/rootsclassic/registry/RootsRegistry.java': '''package elucent.rootsclassic.registry;
                import java.util.function.Supplier;import net.minecraft.world.level.block.Block;
                public final class RootsRegistry {
                  private static final Block R=new Block("radiant"),F=new Block("flare"),M=new Block("midnight");
                  public static final Supplier<Block> RADIANT_DAISY=()->R,FLARE_ORCHID=()->F,MIDNIGHT_BLOOM=()->M;
                }''',
            'org/spongepowered/asm/mixin/Mixin.java': 'package org.spongepowered.asm.mixin; public @interface Mixin {String[] targets();boolean remap();}',
            'org/spongepowered/asm/mixin/Pseudo.java': 'package org.spongepowered.asm.mixin; public @interface Pseudo {}',
            'org/spongepowered/asm/mixin/Final.java': 'package org.spongepowered.asm.mixin; public @interface Final {}',
            'org/spongepowered/asm/mixin/Shadow.java': 'package org.spongepowered.asm.mixin; public @interface Shadow {boolean remap();}',
            'org/spongepowered/asm/mixin/injection/At.java': 'package org.spongepowered.asm.mixin.injection; public @interface At {String value();String target() default "";}',
            'org/spongepowered/asm/mixin/injection/Inject.java': 'package org.spongepowered.asm.mixin.injection; public @interface Inject {String method();At at();boolean cancellable();boolean remap();int require();}',
            'org/spongepowered/asm/mixin/injection/Redirect.java': 'package org.spongepowered.asm.mixin.injection; public @interface Redirect {String method();At at();boolean remap();int require();int expect();int allow();}',
            'org/spongepowered/asm/mixin/injection/callback/CallbackInfoReturnable.java': '''package org.spongepowered.asm.mixin.injection.callback;
                public class CallbackInfoReturnable<T>{public boolean canceled;public T value;public void setReturnValue(T v){canceled=true;value=v;}}''',
            'ua/aia2/guard/mixin/RootsMutationHarness.java': '''package ua.aia2.guard.mixin;
                import java.lang.reflect.Method;import java.lang.reflect.Field;import java.util.List;
                import net.minecraft.core.BlockPos;import net.minecraft.resources.ResourceLocation;import net.minecraft.world.item.*;
                import net.minecraft.world.level.Level;import net.minecraft.world.level.block.Blocks;import net.minecraft.world.effect.*;
                import net.minecraft.world.entity.player.Player;import elucent.rootsclassic.mutation.MutagenRecipe;
                import elucent.rootsclassic.mutation.mutations.*;import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;
                public final class RootsMutationHarness {
                  static int assertions;static final BlockPos POS=new BlockPos(0,64,0);
                  static final Method INPUT_HOOK,TIME_HOOK;static final Field EXPECTED;
                  static {try {INPUT_HOOK=RootsMutationIngredientsMixin.class.getDeclaredMethod("aia2$requireAllMutationInputs",List.class,Level.class,BlockPos.class,Player.class,CallbackInfoReturnable.class);INPUT_HOOK.setAccessible(true);
                    TIME_HOOK=RootsMutationRadiantMixin.class.getDeclaredMethod("aia2$mutationTimeOfDay",Level.class);TIME_HOOK.setAccessible(true);EXPECTED=MutagenRecipe.class.getDeclaredField("inputs");EXPECTED.setAccessible(true);
                  }catch(Exception e){throw new ExceptionInInitializerError(e);}}
                  static void check(boolean b,String message){assertions++;if(!b)throw new AssertionError(message);}
                  static ItemStack stack(Object item){return new ItemStack(item,1);}
                  static class InputHost extends RootsMutationIngredientsMixin {}
                  static class TimeHost extends RootsMutationRadiantMixin {}
                  static long normalize(Level raw)throws Exception{return (Long)TIME_HOOK.invoke(new TimeHost(),raw);}
                  static class RoutedClock extends Level {final Level raw;RoutedClock(Level raw){this.raw=raw;}@Override public long getDayTime(){try{return normalize(raw);}catch(Exception e){throw new RuntimeException(e);}}}
                  @SuppressWarnings("unchecked") static boolean patched(MutagenRecipe recipe,List<ItemStack> items,Level level,Player player)throws Exception {
                    InputHost host=new InputHost();host.inputs=(List<ItemStack>)EXPECTED.get(recipe);
                    var callback=new CallbackInfoReturnable<Boolean>();INPUT_HOOK.invoke(host,items,level,POS,player,callback);
                    return callback.canceled?callback.value:recipe.matches(items,level,POS,player);
                  }
                  static void effect(Player player,Object effect){player.effects.put(effect,new MobEffectInstance(effect,1200,0));}
                  public static void main(String[] args)throws Exception {
                    Level level=new Level();level.blocks.put(POS,Blocks.OXEYE_DAISY.defaultBlockState());Player player=new Player(level);
                    MutagenRecipe base=new MutagenRecipe(new ResourceLocation("test","two"),Blocks.OXEYE_DAISY.defaultBlockState(),Blocks.POPPY.defaultBlockState());
                    base.addIngredient(stack(Blocks.GLOWSTONE));base.addIngredient(stack(Items.PRISMARINE_CRYSTALS));
                    var glow=stack(Blocks.GLOWSTONE);var prism=stack(Items.PRISMARINE_CRYSTALS);var full=List.of(glow,prism);
                    check(base.matches(List.of(glow),level,POS,player),"unmodified source reproduces missing ingredient bug");
                    check(base.matches(List.of(),level,POS,player),"unmodified base accepts empty subset");
                    check(patched(base,full,level,player),"full native input remains valid");
                    check(!patched(base,List.of(glow),level,player),"missing ingredient blocked");check(!patched(base,List.of(),level,player),"empty subset blocked");
                    check(!patched(base,List.of(glow,stack(Items.QUARTZ)),level,player),"wrong same-cardinality input blocked by native matcher");
                    check(!patched(base,List.of(glow,prism,stack(Items.QUARTZ)),level,player),"extra input rejected");
                    check(patched(base,List.of(prism,glow),level,player),"native unordered matching preserved");
                    check(full.size()==2&&glow.count==1&&prism.count==1,"predicates do not consume submitted stacks");
                    check(((List<?>)EXPECTED.get(base)).size()==2,"recipe ingredient list retained");
                    check(!patched(base,null,level,player),"invalid null input fails closed");
                    level.blocks.put(POS,Blocks.BLUE_ORCHID.defaultBlockState());check(!patched(base,full,level,player),"native source plant still required");level.blocks.put(POS,Blocks.OXEYE_DAISY.defaultBlockState());
                    MutagenRecipe dup=new MutagenRecipe(new ResourceLocation("test","duplicates"),Blocks.OXEYE_DAISY.defaultBlockState(),Blocks.POPPY.defaultBlockState());dup.addIngredient(stack(Items.QUARTZ));dup.addIngredient(stack(Items.QUARTZ));
                    var large=stack(Items.QUARTZ);large.count=64;large.components="non-native-extra-data";
                    check(!patched(dup,List.of(large),level,player),"one large ItemEntity stack cannot replace two ingredient entries");
                    check(patched(dup,List.of(large,stack(Items.QUARTZ)),level,player),"two native entries match regardless of stack amount/components");
                    check(!patched(dup,List.of(stack(Items.QUARTZ),prism),level,player),"one matching entry cannot be reused");
                    var radiant=new MutagenRadiantDaisyRecipe();level.time=6000;effect(player,MobEffects.NIGHT_VISION);
                    check(radiant.matches(full,level,POS,player),"first-day native noon works");level.time=30000;check(!radiant.matches(full,level,POS,player),"unmodified source reproduces later-day failure");
                    player.world=new RoutedClock(level);
                    for(long day:new long[]{0,1,2,100,1000000}){level.time=day*24000+6000;check(patched(radiant,full,level,player),"noon works on day"+day);}
                    for(long time:new long[]{4999,5000,7000,7001,18000}){level.time=24000+time;check(!patched(radiant,full,level,player),"strict original window retained at"+time);}
                    level.time=29001;check(patched(radiant,full,level,player),"strict lower bound plus one accepted");level.time=30999;check(patched(radiant,full,level,player),"strict upper bound minus one accepted");
                    level.time=30000;level.dimension=Level.NETHER;check(!patched(radiant,full,level,player),"Radiant still requires Overworld");level.dimension=Level.OVERWORLD;
                    player.effects.clear();check(!patched(radiant,full,level,player),"Radiant still requires Night Vision");effect(player,MobEffects.NIGHT_VISION);
                    level.blocks.put(POS,Blocks.POPPY.defaultBlockState());check(!patched(radiant,full,level,player),"Radiant still requires Oxeye Daisy");level.blocks.put(POS,Blocks.OXEYE_DAISY.defaultBlockState());
                    check(!patched(radiant,List.of(glow),level,player),"later-day noon cannot bypass full ingredient check");
                    level.time=Long.MIN_VALUE;long t=normalize(level);check(t>=0&&t<24000&&t==Math.floorMod(Long.MIN_VALUE,24000L),"negative extreme time normalizes without overflow");
                    level.time=-18000;check(normalize(level)==6000,"negative day times use floor modulus");
                    radiant.onCrafted(level,POS,player);check(player.getEffect(MobEffects.BLINDNESS)!=null,"native crafting effect preserved");
                    var flare=new MutagenFlareOrchidRecipe();var flame=List.of(stack(Items.BLAZE_ROD),stack(Items.LAVA_BUCKET));level.dimension=Level.NETHER;level.blocks.put(POS,Blocks.BLUE_ORCHID.defaultBlockState());effect(player,MobEffects.FIRE_RESISTANCE);
                    var ring=List.of(POS.east(),POS.west(),POS.north(),POS.south(),POS.east().north(),POS.west().south(),POS.north().west(),POS.south().east());for(var pos:ring)level.blocks.put(pos,Blocks.NETHERRACK.defaultBlockState());
                    check(patched(flare,flame,level,player),"complete Flare recipe remains valid");
                    level.dimension=Level.OVERWORLD;check(!patched(flare,flame,level,player),"Flare still requires Nether");level.dimension=Level.NETHER;
                    player.effects.remove(MobEffects.FIRE_RESISTANCE);check(!patched(flare,flame,level,player),"Flare still requires fire resistance");effect(player,MobEffects.FIRE_RESISTANCE);
                    level.blocks.remove(POS.east());check(!patched(flare,flame,level,player),"Flare still requires entire Netherrack ring");level.blocks.put(POS.east(),Blocks.NETHERRACK.defaultBlockState());
                    check(!patched(flare,List.of(flame.get(0)),level,player),"Flare cannot omit lava bucket");flare.onCrafted(level,POS,player);check(player.fireSeconds==20,"native Flare onCrafted fire effect preserved");
                    var midnight=new MutagenMidnightBloomRecipe();var coal=List.of(stack(Blocks.COAL_BLOCK));level.dimension=Level.END;level.blocks.put(POS,Blocks.POPPY.defaultBlockState());level.blocks.put(POS.below(2),Blocks.OBSIDIAN.defaultBlockState());effect(player,MobEffects.MOVEMENT_SLOWDOWN);
                    check(patched(midnight,coal,level,player),"native one-input Midnight recipe remains valid");
                    level.dimension=Level.OVERWORLD;check(!patched(midnight,coal,level,player),"Midnight still requires End");level.dimension=Level.END;
                    player.effects.remove(MobEffects.MOVEMENT_SLOWDOWN);check(!patched(midnight,coal,level,player),"Midnight still requires Movement Slowness");effect(player,MobEffects.MOVEMENT_SLOWDOWN);
                    level.blocks.remove(POS.below(2));check(!patched(midnight,coal,level,player),"Midnight still requires obsidian below");level.blocks.put(POS.below(2),Blocks.OBSIDIAN.defaultBlockState());
                    check(!patched(midnight,List.of(),level,player),"empty Midnight input rejected");midnight.onCrafted(level,POS,player);check(player.getPersistentData().getInt("skipTicks")==200,"native Midnight crafting side effect retained");
                    System.out.println("RootsMutationHarness: "+assertions+" actual-handler/pinned-native-predicate assertions passed; modeled Minecraft host, no optional Roots dispatch");
                  }
                }''',
        }
        with tempfile.TemporaryDirectory(prefix='aia2-roots-mutation-') as folder:
            files = []
            for name, text in fixtures.items():
                p = Path(folder)/name;p.parent.mkdir(parents=True, exist_ok=True);p.write_text(text);files.append(str(p))
            files += [str(SOURCE/'elucent/rootsclassic/mutation/MutagenRecipe.java'),
                      *[str(SOURCE/'elucent/rootsclassic/mutation/mutations'/name) for name in ['MutagenRadiantDaisyRecipe.java','MutagenFlareOrchidRecipe.java','MutagenMidnightBloomRecipe.java']],
                      str(ROOT/'companion/src/main/java/ua/aia2/guard/mixin/RootsMutationIngredientsMixin.java'),
                      str(ROOT/'companion/src/main/java/ua/aia2/guard/mixin/RootsMutationRadiantMixin.java')]
            result = subprocess.run([str(jdk/'bin/javac'),'-encoding','UTF-8','-d',folder,*files],capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stdout+result.stderr)
            result = subprocess.run([str(jdk/'bin/java'),'-cp',folder,'ua.aia2.guard.mixin.RootsMutationHarness'],capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stdout+result.stderr)
            self.assertIn('actual-handler/pinned-native-predicate assertions passed',result.stdout)
            print(result.stdout.strip())
