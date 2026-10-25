"""Run the actual Roots proof helper/mixin in a modeled host, not optional Roots."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class RootsRitualObserverTests(unittest.TestCase):
    def test_pinned_sources_distinguish_temporary_and_actual_input_clear(self):
        audit = json.loads((ROOT/'content/audit/v5-roots-ritual-observer.json').read_text())
        sources = {}
        for source in audit['sources']:
            data = (ROOT/source['path']).read_bytes()
            self.assertEqual(hashlib.sha256(data).hexdigest(), source['sha256'])
            for token in source.get('required_source_tokens', []):
                self.assertIn(token, data.decode())
            sources[Path(source['path']).name] = data.decode()
        altar = sources['AltarBlockEntity.java']
        tick = altar.split('public static void serverTick(', 1)[1].split('public static void clientTick(', 1)[0]
        self.assertLess(tick.index('.value().doEffect('), tick.index('tile.setCurrentRitual(null)'))
        self.assertLess(tick.index('tile.setCurrentRitual(null)'), tick.index('tile.emptyAltar()'))
        self.assertIn('inventory.setStackInSlot(i, ItemStack.EMPTY)', altar.split('public void emptyAltar()', 1)[1])
        self.assertIn('CustomInventory inventory = new CustomInventory(itemHandler.getSlots())', sources['InventoryUtil.java'])
        self.assertIn('inventory.setItem(i, itemHandler.getStackInSlot(i))', sources['InventoryUtil.java'])
        self.assertIn('this.itemStacks.clear()', sources['CustomInventory.java'])
        self.assertIn('levelAccessor.addFreshEntity(item);', sources['RitualCrafting.java'])
        self.assertIn('return effect.getResult(effectConfig, provider).copy()', sources['RitualRecipe.java'])
        mixin = (ROOT/'companion/src/main/java/ua/aia2/guard/mixin/RootsAltarMixin.java').read_text()
        self.assertIn('AltarBlockEntity;emptyAltar()V", shift = At.Shift.AFTER', mixin)
        self.assertIn('access.aia2$setAttempt(null)', mixin)
        self.assertNotIn('ThreadLocal', mixin)

    def test_actual_helper_and_mixin_handlers_with_real_stage_policy(self):
        jdk = Path(os.environ.get('JAVA_HOME', '/workspace/aia2-toolchains/jdk-21.0.9'))
        if not (jdk/'bin/javac').is_file(): self.skipTest('External JDK21 unavailable')
        fixtures = {
            'net/minecraft/world/level/Level.java': 'package net.minecraft.world.level; public class Level {}',
            'net/minecraft/server/level/ServerLevel.java': 'package net.minecraft.server.level; public final class ServerLevel extends net.minecraft.world.level.Level {}',
            'net/minecraft/core/BlockPos.java': 'package net.minecraft.core; public final class BlockPos {}',
            'net/minecraft/world/level/block/state/BlockState.java': 'package net.minecraft.world.level.block.state; public final class BlockState {}',
            # Interface host executes the real mixin handlers directly. Gradle
            # separately compiles production sources against actual Minecraft.
            'net/minecraft/world/level/block/entity/BlockEntity.java': '''package net.minecraft.world.level.block.entity;
                import net.minecraft.world.level.Level;
                public interface BlockEntity {Level getLevel(); String team();}''',
            'net/minecraft/world/item/ItemStack.java': '''package net.minecraft.world.item;
                public final class ItemStack {
                  public static final ItemStack EMPTY=new ItemStack("empty",0);
                  public final String id;private int count;
                  public ItemStack(String id,int count){this.id=id;this.count=count;}
                  public boolean isEmpty(){return count<=0;}public int getCount(){return count;}
                }''',
            'net/minecraft/world/item/crafting/Ingredient.java': '''package net.minecraft.world.item.crafting;
                import java.util.Set;import net.minecraft.world.item.ItemStack;
                public final class Ingredient {
                  private final Set<String> accepted;public Ingredient(String...ids){accepted=Set.of(ids);}
                  public boolean test(ItemStack stack){return !stack.isEmpty()&&accepted.contains(stack.id);}
                }''',
            'net/minecraft/world/item/crafting/RecipeInput.java': 'package net.minecraft.world.item.crafting; public interface RecipeInput {}',
            'net/minecraft/world/item/crafting/Recipe.java': '''package net.minecraft.world.item.crafting;
                import java.util.List;
                public interface Recipe<I extends RecipeInput>{List<Ingredient> getIngredients();int stage();}''',
            'net/minecraft/world/item/crafting/RecipeHolder.java': 'package net.minecraft.world.item.crafting; public record RecipeHolder<T extends Recipe<?>>(T value) {}',
            'net/neoforged/neoforge/items/IItemHandler.java': '''package net.neoforged.neoforge.items;
                import net.minecraft.world.item.ItemStack;
                public interface IItemHandler {int getSlots();ItemStack getStackInSlot(int slot);}''',
            'net/neoforged/neoforge/items/ItemStackHandler.java': '''package net.neoforged.neoforge.items;
                import net.minecraft.world.item.ItemStack;import java.util.Arrays;
                public final class ItemStackHandler implements IItemHandler {
                  private final ItemStack[] stacks;public ItemStackHandler(int slots){stacks=new ItemStack[slots];clear();}
                  public int getSlots(){return stacks.length;}public ItemStack getStackInSlot(int slot){return stacks[slot];}
                  public void setStackInSlot(int slot,ItemStack stack){stacks[slot]=stack;}
                  public void clear(){Arrays.fill(stacks,ItemStack.EMPTY);}
                }''',
            'org/spongepowered/asm/mixin/Mixin.java': 'package org.spongepowered.asm.mixin; public @interface Mixin {String[] targets();boolean remap();}',
            'org/spongepowered/asm/mixin/Pseudo.java': 'package org.spongepowered.asm.mixin; public @interface Pseudo {}',
            'org/spongepowered/asm/mixin/Final.java': 'package org.spongepowered.asm.mixin; public @interface Final {}',
            'org/spongepowered/asm/mixin/Unique.java': 'package org.spongepowered.asm.mixin; public @interface Unique {}',
            'org/spongepowered/asm/mixin/Shadow.java': 'package org.spongepowered.asm.mixin; public @interface Shadow {boolean remap() default true;}',
            'org/spongepowered/asm/mixin/injection/Coerce.java': 'package org.spongepowered.asm.mixin.injection; public @interface Coerce {}',
            'org/spongepowered/asm/mixin/injection/At.java': '''package org.spongepowered.asm.mixin.injection;
                public @interface At {String value();String target() default "";Shift shift() default Shift.NONE;enum Shift{NONE,BEFORE,AFTER}}''',
            'org/spongepowered/asm/mixin/injection/Inject.java': '''package org.spongepowered.asm.mixin.injection;
                public @interface Inject {String method();At at();boolean cancellable() default false;boolean remap();int require();}''',
            'org/spongepowered/asm/mixin/injection/callback/CallbackInfo.java': '''package org.spongepowered.asm.mixin.injection.callback;
                public final class CallbackInfo {public boolean canceled;public void cancel(){canceled=true;}}''',
            'ua/aia2/guard/Aia2MachineGuard.java': '''package ua.aia2.guard;
                import net.minecraft.world.level.block.entity.BlockEntity;import net.minecraft.world.item.crafting.Recipe;
                public final class Aia2MachineGuard {
                  public static final GuardPolicy policy=new GuardPolicy();public static int calls;
                  public static String getOwner(BlockEntity altar){return altar.team();}
                  public static boolean mayProcessRecipe(BlockEntity altar,Recipe<?> recipe){
                    calls++;return policy.isReady()&&policy.mayUseStage(4,altar.team())&&policy.mayUseStage(recipe.stage(),altar.team());
                  }
                }''',
            # This fixture deliberately rechecks policy/identity/proof stage.
            # Actual SavedData and registry identity are tested elsewhere.
            'ua/aia2/guard/ProductionMilestoneBridge.java': '''package ua.aia2.guard;
                import java.util.IdentityHashMap;import java.util.Map;
                import net.minecraft.world.item.crafting.Recipe;import net.minecraft.world.level.block.entity.BlockEntity;
                public final class ProductionMilestoneBridge {
                  public static final Map<Recipe<?>,Integer> curated=new IdentityHashMap<>();public static int calls,receipts;
                  public static void finishedMachine(BlockEntity altar,Recipe<?> recipe){
                    calls++;Integer epoch=curated.get(recipe);
                    if(epoch!=null&&Aia2MachineGuard.mayProcessRecipe(altar,recipe)&&
                       Aia2MachineGuard.policy.mayUseStage(epoch,Aia2MachineGuard.getOwner(altar)))receipts++;
                  }
                }''',
            'ua/aia2/guard/mixin/RootsRitualHarness.java': '''package ua.aia2.guard.mixin;
                import java.util.List;import java.lang.reflect.Method;
                import net.minecraft.core.BlockPos;import net.minecraft.world.level.Level;
                import net.minecraft.server.level.ServerLevel;import net.minecraft.world.level.block.state.BlockState;
                import net.minecraft.world.level.block.entity.BlockEntity;import net.minecraft.world.item.ItemStack;
                import net.minecraft.world.item.crafting.*;import net.neoforged.neoforge.items.ItemStackHandler;
                import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;
                import ua.aia2.guard.*;
                public final class RootsRitualHarness {
                  record Input() implements RecipeInput {}
                  record Ritual(int stage,List<Ingredient> getIngredients) implements Recipe<Input> {}
                  static int assertions;static Method head,after;
                  static void check(boolean condition,String message){assertions++;if(!condition)throw new AssertionError(message);}
                  static ItemStack stack(String id){return new ItemStack(id,1);}
                  static final class Altar extends RootsAltarMixin implements BlockEntity {
                    Level level=new ServerLevel();String owner="a";int progress=1,outputs;RecipeHolder<?> holder;
                    Altar(Recipe<?> recipe){inventory=new ItemStackHandler(3);fill();holder=new RecipeHolder<>(recipe);}
                    void fill(){inventory.setStackInSlot(0,stack("pick"));inventory.setStackInSlot(1,stack("sprig"));inventory.setStackInSlot(2,stack("modded:gold_nugget"));}
                    public Level getLevel(){return level;}public String team(){return owner;}
                    public RecipeHolder<?> getCurrentRitual(){return holder;}public void setCurrentRitual(RecipeHolder<?> next){holder=next;}
                    public int getProgress(){return progress;}public void setProgress(int next){progress=next;}
                    CallbackInfo beginTick()throws Exception {var callback=new CallbackInfo();head.invoke(null,level,new BlockPos(),new BlockState(),this,callback);return callback;}
                    void afterEmpty()throws Exception {after.invoke(null,level,new BlockPos(),new BlockState(),this,new CallbackInfo());}
                    boolean tick()throws Exception {
                      var callback=beginTick();if(callback.canceled)return false;
                      if(progress>0&&holder!=null){progress--;if(progress==0){outputs++;holder=null;inventory.clear();afterEmpty();}}return true;
                    }
                  }
                  static void ready(int completed){
                    var policy=Aia2MachineGuard.policy;policy.clear();policy.setRules(java.util.Map.of("rootsclassic:altar",4));
                    policy.setTeamProgress("a",completed);policy.setTeamProgress("b",48);policy.setReady();
                  }
                  public static void main(String[] args)throws Exception {
                    head=RootsAltarMixin.class.getDeclaredMethod("aia2$beginRitualTick",Level.class,BlockPos.class,BlockState.class,Object.class,CallbackInfo.class);head.setAccessible(true);
                    after=RootsAltarMixin.class.getDeclaredMethod("aia2$recordConsumedRitual",Level.class,BlockPos.class,BlockState.class,Object.class,CallbackInfo.class);after.setAccessible(true);
                    var pick=new Ingredient("pick");var sprig=new Ingredient("sprig");var goldTag=new Ingredient("minecraft:gold_nugget","modded:gold_nugget");
                    Ritual living=new Ritual(1,List.of(pick,sprig,goldTag));Ritual charged=new Ritual(4,List.of(pick,sprig,goldTag));
                    ProductionMilestoneBridge.curated.put(living,4);ProductionMilestoneBridge.curated.put(charged,15);ready(3);
                    Altar altar=new Altar(living);var attempt=RootsRitualProof.begin(altar,living,altar.inventory);
                    check(attempt!=null&&attempt.inputUnits()==3,"three real slot inputs and tag match begin a paid attempt");
                    check(attempt.recipe()==living&&attempt.team().equals("a"),"attempt binds actual recipe identity and owning team");
                    RootsRitualProof.finish(altar,altar.inventory,attempt);check(ProductionMilestoneBridge.calls==0,"temporary doEffect container clear cannot prove actual altar consumption");
                    altar.inventory.clear();RootsRitualProof.finish(altar,altar.inventory,attempt);check(ProductionMilestoneBridge.receipts==1,"actual empty inventory permits bridge receipt after live checks");
                    altar.fill();altar.inventory.setStackInSlot(0,stack("modded:gold_nugget"));altar.inventory.setStackInSlot(2,stack("pick"));
                    check(RootsRitualProof.begin(altar,living,altar.inventory)!=null,"ingredient matching ignores slot order");
                    Ritual overlap=new Ritual(4,List.of(new Ingredient("pick","sprig"),pick,goldTag));altar.fill();
                    check(RootsRitualProof.begin(altar,overlap,altar.inventory)!=null,"overlapping ingredient choices use one-to-one backtracking");
                    Ritual reuse=new Ritual(4,List.of(pick,pick,goldTag));check(RootsRitualProof.begin(altar,reuse,altar.inventory)==null,"one physical stack cannot satisfy duplicate ingredients twice");
                    altar.inventory.setStackInSlot(2,stack("wrong"));check(RootsRitualProof.begin(altar,living,altar.inventory)==null,"unmatched tag/item denied");
                    altar.fill();altar.inventory.setStackInSlot(2,ItemStack.EMPTY);check(RootsRitualProof.begin(altar,living,altar.inventory)==null,"missing native input denied");
                    altar.fill();Ritual fewer=new Ritual(4,List.of(pick,sprig));check(RootsRitualProof.begin(altar,fewer,altar.inventory)==null,"extra input slot cannot disguise wrong recipe");
                    check(RootsRitualProof.begin(altar,new Ritual(4,List.of()),altar.inventory)==null,"zero-ingredient recipe cannot produce proof");
                    check(RootsRitualProof.begin(altar,new Ritual(4,List.of(pick,sprig,goldTag,pick)),altar.inventory)==null,"unsupported ingredient count denied");
                    altar.inventory.clear();check(RootsRitualProof.begin(altar,living,altar.inventory)==null,"empty altar cannot begin");
                    altar.fill();check(RootsRitualProof.begin(altar,living,new ItemStackHandler(4))==null,"wrong inventory size denied");
                    check(RootsRitualProof.begin(altar,living,null)==null,"null inventory denied");
                    check(RootsRitualProof.begin(altar,null,altar.inventory)==null,"null recipe denied");
                    altar.owner="";check(RootsRitualProof.begin(altar,living,altar.inventory)==null,"unowned altar denied");altar.owner="a";
                    altar.level=new Level();check(RootsRitualProof.begin(altar,living,altar.inventory)==null,"client never begins server proof");altar.level=new ServerLevel();
                    Aia2MachineGuard.policy.clear();check(RootsRitualProof.begin(altar,living,altar.inventory)==null,"unready guard cannot begin proof");ready(3);
                    attempt=RootsRitualProof.begin(altar,living,altar.inventory);altar.inventory.clear();altar.owner="b";int receipts=ProductionMilestoneBridge.receipts;
                    RootsRitualProof.finish(altar,altar.inventory,attempt);check(ProductionMilestoneBridge.receipts==receipts,"owner change between begin/finish cannot move paid proof");altar.owner="a";
                    Aia2MachineGuard.policy.setTeamProgress("a",2);RootsRitualProof.finish(altar,altar.inventory,attempt);check(ProductionMilestoneBridge.receipts==receipts,"stage revoked after begin is rechecked by authoritative bridge");ready(3);
                    altar.fill();attempt=RootsRitualProof.begin(altar,charged,altar.inventory);altar.inventory.clear();RootsRitualProof.finish(altar,altar.inventory,attempt);
                    check(ProductionMilestoneBridge.receipts==receipts,"recipe gate4 does not bypass independent proof epoch15");
                    Aia2MachineGuard.policy.setTeamProgress("a",14);RootsRitualProof.finish(altar,altar.inventory,attempt);check(ProductionMilestoneBridge.receipts==receipts+1,"proof epoch15 opens with legitimate stage");ready(3);
                    altar=new Altar(living);receipts=ProductionMilestoneBridge.receipts;check(altar.tick(),"native final tick runs when recipe authorized");
                    check(altar.outputs==1&&altar.inventory.getStackInSlot(0).isEmpty(),"modeled native effect and actual clear execute");
                    check(ProductionMilestoneBridge.receipts==receipts+1,"real mixin after-empty handler records once");
                    check(altar.aia2$getAttempt()==null,"after-empty handler clears attempt token");altar.afterEmpty();
                    check(ProductionMilestoneBridge.receipts==receipts+1,"duplicate after-empty callback cannot replay proof");
                    altar=new Altar(living);altar.progress=199;check(altar.tick(),"nonfinal native progress continues");
                    check(altar.progress==198&&altar.aia2$getAttempt()==null,"nonfinal tick does not prepare receipt");
                    check(altar.outputs==0&&!altar.inventory.getStackInSlot(0).isEmpty(),"nonfinal tick has no output/consumption");
                    altar=new Altar(new Ritual(100,List.of(pick,sprig,goldTag)));check(!altar.tick(),"unknown cached recipe canceled before effect");
                    check(altar.progress==0&&altar.holder==null&&altar.outputs==0,"denied cached process is stopped");
                    check(!altar.inventory.getStackInSlot(0).isEmpty(),"unknown recipe denial retains actual inputs");
                    altar=new Altar(living);Aia2MachineGuard.policy.clear();check(!altar.tick(),"unready cache is canceled");
                    check(altar.outputs==0&&!altar.inventory.getStackInSlot(0).isEmpty(),"unready cancellation has no input loss");ready(3);
                    altar=new Altar(charged);Aia2MachineGuard.policy.setTeamProgress("a",2);check(!altar.tick(),"owner before altar epoch cannot finish cached ritual");
                    check(altar.outputs==0&&!altar.inventory.getStackInSlot(0).isEmpty(),"early cancellation retains inputs");ready(3);
                    altar=new Altar(living);altar.owner=null;check(!altar.tick(),"unowned cached recipe cannot complete");
                    check(altar.outputs==0&&!altar.inventory.getStackInSlot(0).isEmpty(),"unowned denial retains inputs");
                    altar=new Altar(living);altar.progress=0;check(altar.tick()&&altar.outputs==0,"idle altar does not produce");
                    altar=new Altar(living);altar.holder=null;check(altar.tick()&&altar.outputs==0,"missing cached holder preserves native idle behavior");
                    altar=new Altar(living);altar.beginTick();check(altar.aia2$getAttempt()!=null,"final native tick prepares attempt before effect");
                    // Model an effect throwing before emptyAltar. The next HEAD
                    // must clear the per-instance token even if progress is0.
                    altar.progress=0;altar.beginTick();check(altar.aia2$getAttempt()==null,"next HEAD discards exception-stale attempt");
                    receipts=ProductionMilestoneBridge.receipts;altar.inventory.clear();altar.afterEmpty();check(ProductionMilestoneBridge.receipts==receipts,"later clear cannot replay failed effect receipt");
                    altar=new Altar(living);altar.beginTick();altar.level=new Level();altar.inventory.clear();altar.afterEmpty();check(ProductionMilestoneBridge.receipts==receipts,"client finish never records");
                    altar=new Altar(living);altar.inventory.clear();altar.afterEmpty();check(ProductionMilestoneBridge.receipts==receipts,"give or pickup with no attempt cannot record");
                    altar=new Altar(living);altar.beginTick();altar.owner="b";altar.inventory.clear();altar.afterEmpty();check(ProductionMilestoneBridge.receipts==receipts,"mixin cannot transfer receipt to changed owner");
                    altar=new Altar(living);altar.beginTick();Aia2MachineGuard.policy.clear();altar.inventory.clear();altar.afterEmpty();check(ProductionMilestoneBridge.receipts==receipts,"policy reset at finish fails closed");ready(3);
                    System.out.println("RootsRitualHarness: "+assertions+" actual-helper/actual-handler/real-policy assertions passed; modeled host, bridge fixture, no optional Roots dispatch or SavedData claim");
                  }
                }''',
        }
        with tempfile.TemporaryDirectory(prefix='aia2-roots-ritual-') as destination:
            files = []
            for name, text in fixtures.items():
                path = Path(destination)/name;path.parent.mkdir(parents=True, exist_ok=True);path.write_text(text);files.append(str(path))
            files += [str(ROOT/'companion/src/main/java/ua/aia2/guard/GuardPolicy.java'),
                      str(ROOT/'companion/src/main/java/ua/aia2/guard/RootsAltarAccess.java'),
                      str(ROOT/'companion/src/main/java/ua/aia2/guard/RootsRitualProof.java'),
                      str(ROOT/'companion/src/main/java/ua/aia2/guard/mixin/RootsAltarMixin.java')]
            result = subprocess.run([str(jdk/'bin/javac'),'-encoding','UTF-8','-d',destination,*files],capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stdout+result.stderr)
            result = subprocess.run([str(jdk/'bin/java'),'-cp',destination,'ua.aia2.guard.mixin.RootsRitualHarness'],capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stdout+result.stderr)
            self.assertIn('actual-helper/actual-handler/real-policy assertions passed',result.stdout)
            print(result.stdout.strip())
