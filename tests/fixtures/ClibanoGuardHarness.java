package ua.aia2.guard;

import java.util.*;
import net.minecraft.core.*;
import net.minecraft.nbt.*;
import net.minecraft.resources.*;
import net.minecraft.server.level.*;
import net.minecraft.world.item.*;
import net.minecraft.world.item.crafting.*;
import com.stal111.forbidden_arcanus.common.block.entity.clibano.*;
import com.stal111.forbidden_arcanus.common.block.entity.clibano.logic.*;
import com.stal111.forbidden_arcanus.common.block.entity.clibano.residue.*;
import com.stal111.forbidden_arcanus.common.item.crafting.*;
import com.stal111.forbidden_arcanus.common.item.enhancer.*;
import com.stal111.forbidden_arcanus.core.registry.*;

/** Actual adapters and exact native lane logic; the MC/container host is deliberately modeled. */
public final class ClibanoGuardHarness {
    private static int checks;
    private static final String PREFIX = "forbidden_arcanus:clibano_combustion/";
    private static final String DUST = PREFIX + "arcane_crystal_dust_from_clibano_combustion";
    private static final String RUNE = PREFIX + "rune_from_clibano_combustion";
    private static final String ALLOY = PREFIX + "obsidiansteel_ingot_from_clibano_combustion";
    private static void check(boolean value, String why) { checks++; if (!value) throw new AssertionError(why); }
    private static Object nativeField(Object object,String name){try{var field=object.getClass().getDeclaredField(name);field.setAccessible(true);return field.get(object);}catch(ReflectiveOperationException failure){throw new RuntimeException(failure);}}
    private static ItemStack item(String id, int count) { return new ItemStack(id, count); }
    private static ItemStack item(String id) { return item(id, 1); }
    private static void policy(GuardPolicy policy, Map<String, Integer> rules) {
        policy.clear(); policy.setRules(rules); policy.setTeamProgress("a", 20); policy.setTeamProgress("b", 0); policy.setReady();
    }
    private static void policies() {
        Aia2MachineGuard.ready = true; ClibanoOwnership.valid = true; KeyProductionBridge.KEYS.clear();
        EnhancerHelper.ITEMS.clear(); ProductionMilestoneBridge.PROOFS.clear();
        policy(Aia2MachineGuard.BLOCKS, Map.of("forbidden_arcanus:clibano_main_part", 15));
        policy(Aia2MachineGuard.ITEMS, Map.ofEntries(
                Map.entry("minecraft:coal", 0), Map.entry("minecraft:diamond", 0),
                Map.entry("minecraft:iron_ingot", 0), Map.entry("minecraft:copper_ingot", 0),
                Map.entry("minecraft:gold_ingot", 0), Map.entry("minecraft:emerald", 0),
                Map.entry("forbidden_arcanus:arcane_crystal_dust", 15), Map.entry("forbidden_arcanus:rune", 15),
                Map.entry("forbidden_arcanus:obsidiansteel_ingot", 15), Map.entry("forbidden_arcanus:artisan_relic", 21),
                Map.entry("forbidden_arcanus:enchanted_soul", 21), Map.entry("fixture:future", 44),
                Map.entry("kubejs:aia2_tech_key_15", 1)));
        policy(Aia2MachineGuard.RECIPES, Map.of(DUST, 15, RUNE, 15, ALLOY, 21, "fixture:late_recipe", 44));
    }
    private record Snapshot(int ticks, int burn, int soul, int finishes, List<String> slots, List<Integer> progress, int residues, int proofs) {}
    private static Snapshot snapshot(ClibanoMainBlockEntity m) {
        return new Snapshot(m.nativeTicks, m.burnTime, m.soulTime, m.nativeFinishes,
                Arrays.stream(m.slots).map(ItemStack::toString).toList(),
                Arrays.stream(m.logic.cookingProgress).boxed().toList(), m.residues.totalAmount, ProductionMilestoneBridge.PROOFS.size());
    }
    private static final class Scene {
        final ServerLevel level = new ServerLevel();
        final ClibanoMainBlockEntity machine = new ClibanoMainBlockEntity();
        final ServerPlayer player = new ServerPlayer(level);
        final Registry<Object> enhancers = new Registry<>(), residueTypes = new Registry<>();
        RecipeHolder<ClibanoRecipe> first, second;
        Scene() {
            policies(); machine.level = level; level.tiles.put(machine.pos, machine);
            level.access.registries.put(FARegistries.ENHANCER_DEFINITION, enhancers);
            level.access.registries.put(FARegistries.RESIDUE_TYPE, residueTypes);
            first = recipe(DUST, "minecraft:diamond", null, "forbidden_arcanus:arcane_crystal_dust");
            second = recipe(RUNE, "minecraft:iron_ingot", null, "forbidden_arcanus:rune");
            machine.slots[2] = item("minecraft:coal", 3);
            machine.slots[3] = item("minecraft:diamond");
            level.recipes.replace(first, second);
        }
        RecipeHolder<ClibanoRecipe> recipe(String id, String a, String b, String result) {
            return new RecipeHolder<>(ResourceLocation.parse(id), new ClibanoRecipe(a, b, item(result)));
        }
        void tick() { ClibanoMainBlockEntity.serverTick(level, machine.pos, machine.getBlockState(), machine); }
        void steps(int count) { for (int i = 0; i < count; i++) tick(); }
        void paid() {
            tick(); check(machine.burnTime > 0 && machine.slots[2].getCount() == 2, "cold tick acquires one actual native fuel");
            check(machine.logic.cookingProgress[0] == 0 && machine.nativeFinishes == 0, "cold tick never cooks or finishes");
            tick(); check(machine.logic.cookingProgress[0] == 1, "lit native logic actually advances");
            check(ClibanoPaidState.lane(machine, 0).isPresent(), "actual progress records first lane receipt");
        }
        void paused(String why) {
            Snapshot before = snapshot(machine); tick();
            check(snapshot(machine).equals(before), why + ": preflight leaves native ticks/costs/inputs/progress/output/proofs unchanged");
            check(!ClibanoAccess.inTick(machine), why + ": scoped native context cleaned");
        }
        void oneResult(String output) {
            check(machine.nativeFinishes == 1, "one native recipe finishes");
            check(machine.slots[3].isEmpty(), "native finish consumed exactly one first-slot unit");
            check(machine.slots[5].item.id.equals(output) && machine.slots[5].getCount() == 1, "actual accepted output correct");
            check(ProductionMilestoneBridge.PROOFS.size() == 1, "one observed post-consumption proof recorded");
            check(ClibanoPaidState.lane(machine, 0).isEmpty(), "completion clears only the completed receipt");
        }
    }

    private static void normalProductionAndEnergy() {
        Scene scene = new Scene(); scene.paid(); scene.steps(2); scene.oneResult("forbidden_arcanus:arcane_crystal_dust");
        Scene fast = new Scene(); fast.first.value().duration = 1; fast.tick();
        check(fast.machine.nativeFinishes == 0 && ProductionMilestoneBridge.PROOFS.isEmpty(), "duration1 cannot finish during cold prepayment tick");
        check(fast.machine.burnTime > 0 && fast.machine.slots[2].getCount() == 2, "duration1 cold path really pays fuel first");
        fast.tick(); fast.oneResult("forbidden_arcanus:arcane_crystal_dust");
        Scene empty = new Scene(); empty.first.value().duration = 1; empty.machine.slots[2] = ItemStack.EMPTY; empty.steps(4);
        check(empty.machine.nativeFinishes == 0 && empty.machine.slots[3].getCount() == 1, "no-fuel duration1 cannot produce free output");
        check(empty.machine.logic.cookingProgress[0] == 0 && ProductionMilestoneBridge.PROOFS.isEmpty(), "unlit logic cannot manufacture progress/proof");
        Scene carry = new Scene(); carry.paid(); carry.machine.burnTime = 0; carry.machine.slots[2] = ItemStack.EMPTY;
        int progress = carry.machine.logic.cookingProgress[0]; carry.steps(3);
        check(carry.machine.logic.cookingProgress[0] == progress && ClibanoPaidState.lane(carry.machine, 0).isPresent(), "temporarily unlit paid lane retains progress and receipt");
    }
    private static void prepaymentDenials() {
        Scene off = new Scene(); Aia2MachineGuard.ready = false; off.paused("bridge not ready");
        Scene unknown = new Scene(); unknown.machine.team = ""; unknown.paused("unowned controller");
        Scene early = new Scene(); early.machine.team = "b"; early.paused("owner has not unlocked machine");
        Scene canonical = new Scene(); ClibanoOwnership.valid = false; canonical.paused("missing canonical shell");
        Scene removed = new Scene(); removed.machine.removed = true; removed.paused("removed controller");
        Scene swapped = new Scene(); swapped.level.tiles.put(swapped.machine.pos, new ClibanoMainBlockEntity()); swapped.paused("controller replaced at same position");
        Scene unloaded = new Scene(); unloaded.level.loaded = false; unloaded.paused("unloaded canonical position");
        Scene thread = new Scene(); thread.level.server.sameThread = false; thread.paused("off-server thread");
        Scene futureOutput = new Scene(); futureOutput.first = futureOutput.recipe(DUST, "minecraft:diamond", null, "fixture:future"); futureOutput.level.recipes.replace(futureOutput.first); futureOutput.paused("future output");
        Scene futureInput = new Scene(); futureInput.machine.slots[3] = item("fixture:future"); futureInput.first = futureInput.recipe(DUST, "fixture:future", null, "minecraft:emerald"); futureInput.level.recipes.replace(futureInput.first); futureInput.paused("future input");
        Scene futureFuel = new Scene(); futureFuel.machine.slots[2] = item("fixture:future"); futureFuel.paused("future fuel");
        Scene futureSoul = new Scene(); futureSoul.machine.slots[1] = item("fixture:future"); futureSoul.paused("future soul");
        Scene keyOutput = new Scene(); keyOutput.first = keyOutput.recipe(DUST, "minecraft:diamond", null, "kubejs:aia2_tech_key_15"); keyOutput.level.recipes.replace(keyOutput.first); keyOutput.paused("key copy output");
        Scene dynamicKey = new Scene(); KeyProductionBridge.KEYS.add("forbidden_arcanus:arcane_crystal_dust"); dynamicKey.paused("registered manufactured key cannot be copied");
        Scene keyInput = new Scene(); keyInput.machine.slots[3] = item("kubejs:aia2_tech_key_15"); keyInput.first = keyInput.recipe(DUST, "kubejs:aia2_tech_key_15", null, "minecraft:emerald"); keyInput.level.recipes.replace(keyInput.first); keyInput.paused("key input");
        Scene stagedRecipe = new Scene(); stagedRecipe.first = stagedRecipe.recipe("fixture:late_recipe", "minecraft:diamond", null, "minecraft:emerald"); stagedRecipe.level.recipes.replace(stagedRecipe.first); stagedRecipe.paused("future recipe despite low output");
        Scene unregistered = new Scene(); unregistered.first = unregistered.recipe("fixture:unknown", "minecraft:diamond", null, "minecraft:emerald"); unregistered.level.recipes.replace(unregistered.first); unregistered.paused("unknown recipe policy");
        Scene components = new Scene(); components.first.value().result.components.put("creative", true); components.paused("component-aware output gate");
        Scene merge = new Scene(); merge.machine.slots[5] = item("forbidden_arcanus:arcane_crystal_dust", 2); merge.machine.slots[5].components.put("foreign", "different"); merge.paused("native isSameItem would merge into different components");
    }
    private static void lanesAndCurrentIdentities() {
        Scene lanes = new Scene(); lanes.machine.slots[4] = item("minecraft:iron_ingot"); lanes.paid();
        check(ClibanoPaidState.lane(lanes.machine, 1).isPresent(), "second independent lane has real progress proof");
        lanes.steps(2); check(lanes.machine.nativeFinishes == 2, "both native lanes finish");
        check(lanes.machine.slots[3].isEmpty() && lanes.machine.slots[4].isEmpty(), "both actual inputs consumed independently");
        check(lanes.machine.slots[5].getCount() == 1 && lanes.machine.slots[6].getCount() == 1 && ProductionMilestoneBridge.PROOFS.size() == 2, "two accepted different outputs yield two observations");
        Scene reload = new Scene(); reload.paid();
        RecipeHolder<ClibanoRecipe> current = reload.recipe(DUST, "minecraft:diamond", null, "forbidden_arcanus:arcane_crystal_dust"); reload.level.recipes.replace(current, reload.second);
        reload.tick(); check(reload.machine.logic.cookingProgress[0] == 2, "equal full definition rebind preserves paid progress");
        check(nativeField(reload.machine.logic,"firstRecipe") == current, "native logic actually bound to current RecipeHolder");
        reload.tick(); reload.oneResult("forbidden_arcanus:arcane_crystal_dust");
        Scene changed = new Scene(); changed.paid(); RecipeHolder<ClibanoRecipe> changedDef = changed.recipe(DUST, "minecraft:diamond", null, "forbidden_arcanus:arcane_crystal_dust"); changedDef.value().duration = 4; changed.level.recipes.replace(changedDef); changed.paused("changed duration after payment");
        check(ClibanoPaidState.lane(changed.machine, 0).isPresent(), "changed definition keeps old paid receipt");
        changed.level.recipes.replace(changed.first, changed.second); changed.tick(); check(changed.machine.logic.cookingProgress[0] == 2, "restored original definition resumes without new fuel payment");
        Scene missing = new Scene(); missing.paid(); missing.level.recipes.replace(); missing.paused("removed paid producer");
        Scene changedInput = new Scene(); changedInput.paid(); changedInput.machine.slots[3].components.put("name", "changed"); changedInput.paused("changed input components during paid lane");
        Scene count = new Scene(); count.paid(); count.machine.slots[3].count = 8; count.tick(); check(count.machine.logic.cookingProgress[0] == 2, "extra identical feed units do not invalidate one-unit recipe progress"); count.tick(); check(count.machine.slots[3].getCount() == 7 && ProductionMilestoneBridge.PROOFS.size() == 1, "finish consumes one unit from replenished stack");
    }
    private static void alloyEnhancersAndLaneIndependence() {
        Scene alloy = new Scene();
        Holder<?> artisan = alloy.enhancers.put("forbidden_arcanus:artisan_relic", new EnhancerDefinition("allow_alloy"));
        EnhancerHelper.ITEMS.put("forbidden_arcanus:artisan_relic", artisan);
        alloy.machine.slots[0] = item("forbidden_arcanus:artisan_relic");
        alloy.machine.slots[3] = item("minecraft:iron_ingot"); alloy.machine.slots[4] = item("minecraft:copper_ingot");
        var combined = alloy.recipe(ALLOY, "minecraft:iron_ingot", "minecraft:copper_ingot", "forbidden_arcanus:obsidiansteel_ingot");
        combined.value().enhancer = artisan; alloy.level.recipes.replace(combined, alloy.first, alloy.second);
        alloy.paid(); check(alloy.machine.logic instanceof DoubleSmeltLogic, "actual native double logic selected");
        check(ClibanoPaidState.lane(alloy.machine, 0).orElseThrow().equals(ClibanoPaidState.lane(alloy.machine, 1).orElseThrow()), "alloy binds both selected lanes to one operation");
        alloy.steps(2);
        check(alloy.machine.nativeFinishes == 1 && alloy.machine.slots[3].isEmpty() && alloy.machine.slots[4].isEmpty(), "native alloy consumes both units once");
        check(alloy.machine.slots[5].item.id.equals("forbidden_arcanus:obsidiansteel_ingot") && ProductionMilestoneBridge.PROOFS.size() == 1, "alloy output accepted before one actual proof");
        check(ClibanoPaidState.lane(alloy.machine, 0).isEmpty() && ClibanoPaidState.lane(alloy.machine, 1).isEmpty(), "alloy completion clears both independent lane entries");
        Scene staggered = new Scene(); staggered.paid(); staggered.machine.slots[4] = item("minecraft:iron_ingot"); staggered.tick();
        check(staggered.machine.logic.cookingProgress[0] == 2 && staggered.machine.logic.cookingProgress[1] == 1, "new second lane starts without resetting first paid progress");
        staggered.tick();
        check(staggered.machine.nativeFinishes == 1 && ClibanoPaidState.lane(staggered.machine, 0).isEmpty() && ClibanoPaidState.lane(staggered.machine, 1).isPresent(), "first completion preserves still-active second-lane proof");
        staggered.tick(); check(staggered.machine.nativeFinishes == 2 && ProductionMilestoneBridge.PROOFS.size() == 2, "second lane completes independently on later tick");
        Scene enhanced = new Scene();
        Holder<?> original = enhanced.enhancers.put("forbidden_arcanus:artisan_relic", new EnhancerDefinition("original"));
        EnhancerHelper.ITEMS.put("forbidden_arcanus:artisan_relic", original); enhanced.machine.slots[0] = item("forbidden_arcanus:artisan_relic"); enhanced.paid();
        Holder<?> changed = enhanced.enhancers.put("forbidden_arcanus:artisan_relic", new EnhancerDefinition("changed"));
        EnhancerHelper.ITEMS.put("forbidden_arcanus:artisan_relic", changed); enhanced.paused("physical enhancer definition changed during paid work");
        Scene malformed = new Scene(); malformed.first.value().duration = 0; malformed.paused("zero native cooking duration");
        Scene negative = new Scene(); negative.first.value().duration = -1; negative.paused("negative native cooking duration");
        Scene huge = new Scene(); huge.first.value().duration = 1200001; huge.paused("unbounded native cooking duration");
    }
    private static void restartLegacyAndProofIntegrity() {
        Scene old = new Scene(); old.paid(); CompoundTag saved = old.machine.saved();
        Scene restored = new Scene(); restored.machine.loadRaw(saved); restored.tick(); check(restored.machine.logic.cookingProgress[0] == 2, "saved paid lane resumes in a fresh controller");
        restored.tick(); restored.oneResult("forbidden_arcanus:arcane_crystal_dust");
        Scene legacy = new Scene(); legacy.machine.logic.cookingProgress[0] = 1; legacy.machine.burnTime = 10; legacy.paused("legacy in-flight lane without original receipt");
        check(ClibanoPaidState.lane(legacy.machine, 0).isEmpty(), "legacy native progress never manufactures a receipt");
        Scene corrupt = new Scene(); CompoundTag root = new CompoundTag(); root.putString(ClibanoPaidState.TAG, "opaque corrupt payload"); root.putIntArray("cooking_times", new int[]{1, 0}); root.putIntArray("cooking_durations", new int[]{3, 0}); root.putInt("burn_time", 10); corrupt.machine.loadRaw(root); corrupt.paused("corrupt persisted ledger");
        check(corrupt.machine.saved().getString(ClibanoPaidState.TAG).equals("opaque corrupt payload"), "corrupt raw tag survives native save");
        Scene noInput = new Scene(); noInput.paid(); noInput.machine.skipConsumption = true; noInput.steps(2); check(noInput.machine.nativeFinishes == 1 && ProductionMilestoneBridge.PROOFS.isEmpty(), "native finish without observed input consumption cannot grant proof");
        Scene noOutput = new Scene(); noOutput.paid(); noOutput.machine.skipInsertion = true; noOutput.steps(2); check(noOutput.machine.nativeFinishes == 1 && ProductionMilestoneBridge.PROOFS.isEmpty(), "native finish without accepted output cannot grant proof");
        Scene stolen = new Scene(); stolen.paid(); stolen.machine.afterFinish = () -> stolen.machine.team = "b"; stolen.steps(2); check(ProductionMilestoneBridge.PROOFS.isEmpty(), "owner change during commit cannot award another team");
        Scene exception = new Scene(); exception.paid(); exception.machine.throwTick = true;
        boolean thrown = false; try { exception.tick(); } catch (IllegalStateException nativeFailure) { thrown = nativeFailure.getMessage().equals("native tick exception"); }
        check(thrown && !ClibanoAccess.inTick(exception.machine), "native tick exception propagates and restores scope");
        check(ClibanoPaidState.lane(exception.machine, 0).isPresent(), "exception does not silently delete paid receipt");
    }
    private static void residueConversions() {
        Scene safe = new Scene(); safe.machine.slots[3] = ItemStack.EMPTY;
        ResidueType type = new ResidueType(new ResidueType.CombineInfo(2, item("forbidden_arcanus:arcane_crystal_dust")));
        @SuppressWarnings("unchecked") Holder<ResidueType> holder = (Holder<ResidueType>)(Holder<?>)safe.residueTypes.put("forbidden_arcanus:test", type);
        safe.machine.residues.add(holder, 2); safe.tick();
        check(safe.machine.residues.totalAmount == 0 && safe.machine.slots[5].getCount() == 1, "current allowed residue definition converts actual residue amount");
        Scene future = new Scene(); future.machine.slots[3] = ItemStack.EMPTY; ResidueType later = new ResidueType(new ResidueType.CombineInfo(2, item("fixture:future")));
        @SuppressWarnings("unchecked") Holder<ResidueType> laterHolder = (Holder<ResidueType>)(Holder<?>)future.residueTypes.put("forbidden_arcanus:test", later);
        future.machine.residues.add(laterHolder, 2); future.tick(); check(future.machine.residues.totalAmount == 2 && future.machine.slots[5].isEmpty(), "future residue output does not spend residue or create item");
        Scene stale = new Scene(); stale.machine.slots[3] = ItemStack.EMPTY;
        @SuppressWarnings("unchecked") Holder<ResidueType> staleHolder = (Holder<ResidueType>)(Holder<?>)stale.residueTypes.put("forbidden_arcanus:test", type);
        stale.machine.residues.add(staleHolder, 2); stale.residueTypes.put("forbidden_arcanus:test", new ResidueType(new ResidueType.CombineInfo(2, item("minecraft:emerald")))); stale.tick();
        check(stale.machine.residues.totalAmount == 2 && stale.machine.slots[5].isEmpty(), "stale residue holder cannot bypass current registry identity");
        Scene merge = new Scene(); merge.machine.slots[3] = ItemStack.EMPTY; merge.machine.slots[5] = item("forbidden_arcanus:arcane_crystal_dust"); merge.machine.slots[5].components.put("foreign", "variant");
        @SuppressWarnings("unchecked") Holder<ResidueType> merging = (Holder<ResidueType>)(Holder<?>)merge.residueTypes.put("forbidden_arcanus:test", type);
        merge.machine.residues.add(merging, 2); merge.tick(); check(merge.machine.residues.totalAmount == 2 && merge.machine.slots[5].getCount() == 1, "residue native same-item component merge denied before spending");
        Scene filled = new Scene(); filled.paid();
        @SuppressWarnings("unchecked") Holder<ResidueType> gold = (Holder<ResidueType>)(Holder<?>)filled.residueTypes.put("forbidden_arcanus:gold", new ResidueType(new ResidueType.CombineInfo(1, item("minecraft:gold_ingot", 64))));
        @SuppressWarnings("unchecked") Holder<ResidueType> copper = (Holder<ResidueType>)(Holder<?>)filled.residueTypes.put("forbidden_arcanus:copper", new ResidueType(new ResidueType.CombineInfo(1, item("minecraft:copper_ingot", 64))));
        filled.machine.residues.add(gold, 1); filled.machine.residues.add(copper, 1); filled.tick();
        check(filled.machine.slots[5].getCount() == 64 && filled.machine.slots[6].getCount() == 64, "native residue pass fills both destinations before cooking");
        check(filled.machine.logic.cookingProgress[0] == 1 && ClibanoPaidState.lane(filled.machine, 0).isPresent(), "newly blocked output cannot make native lane reset paid progress");
        check(filled.machine.nativeFinishes == 0 && ProductionMilestoneBridge.PROOFS.isEmpty(), "full destinations produce neither recipe result nor proof");
        filled.machine.slots[5] = ItemStack.EMPTY; filled.machine.slots[6] = ItemStack.EMPTY; filled.steps(2); filled.oneResult("forbidden_arcanus:arcane_crystal_dust");
        Scene unknown = new Scene(); CompoundTag unknownSave = new CompoundTag(); unknownSave.putIntArray("cooking_times", new int[]{0, 0}); unknownSave.putIntArray("cooking_durations", new int[]{0, 0});
        CompoundTag missingDefinition = new CompoundTag(); missingDefinition.putInt("forbidden_arcanus:removed_type", 4); unknownSave.put("residues", missingDefinition); unknown.machine.loadRaw(unknownSave); unknown.paused("removed native residue registry definition during load");
        check(unknown.machine.saved().getCompound("residues").equals(missingDefinition), "native residue codec drop cannot erase original raw saved amounts");
        Scene opaque = new Scene(); CompoundTag opaqueSave = unknownSave.copy(); opaqueSave.putString("residues", "opaque format"); opaque.machine.loadRaw(opaqueSave); opaque.paused("unreadable residue payload");
        check(opaque.machine.saved().getString("residues").equals("opaque format"), "unreadable raw residue type survives save unchanged");
    }
    private static void explicitRecoveryAndScopes() {
        Scene recovery = new Scene(); recovery.paid(); List<String> items = Arrays.stream(recovery.machine.slots).map(ItemStack::toString).toList();
        int fuel = recovery.machine.burnTime, souls = recovery.machine.soulTime;
        String result = ClibanoAccess.cancelProgress(recovery.player, recovery.machine);
        check(result.contains("1/8"), "explicit nearby own-team operator recovery takes first persistent backup");
        check(Arrays.equals(recovery.machine.logic.cookingProgress, new int[]{0,0}) && ClibanoPaidState.lane(recovery.machine, 0).isEmpty(), "explicit recovery clears active counters/receipt only");
        check(Arrays.stream(recovery.machine.slots).map(ItemStack::toString).toList().equals(items), "recovery keeps every physical input/fuel/soul/enhancer/output");
        check(recovery.machine.burnTime == fuel && recovery.machine.soulTime == souls && ProductionMilestoneBridge.PROOFS.isEmpty(), "recovery grants no output, fuel refund or proof");
        check(recovery.machine.persistent.getList("aia2_clibano_cancel_backups_v1", Tag.TAG_COMPOUND).size() == 1, "recovery backup persisted on actual controller host");
        Scene nonOp = new Scene(); nonOp.paid(); Snapshot before = snapshot(nonOp.machine); nonOp.player.permissions = 0;
        check(ClibanoAccess.cancelProgress(nonOp.player, nonOp.machine).contains("не завершено") && snapshot(nonOp.machine).equals(before), "ordinary player cannot clear paid progress");
        check(!nonOp.machine.persistent.contains("aia2_clibano_cancel_backups_v1"), "denied recovery makes no persistent backup write");
        Scene visitor = new Scene(); visitor.paid(); visitor.player.team = "b";
        check(ClibanoAccess.cancelProgress(visitor.player, visitor.machine).contains("не завершено") && ClibanoPaidState.lane(visitor.machine, 0).isPresent(), "other team operator cannot clear owner's receipt");
        Scene far = new Scene(); far.paid(); far.player.pos = new BlockPos(20,0,0);
        check(ClibanoAccess.cancelProgress(far.player, far.machine).contains("не завершено") && ClibanoPaidState.lane(far.machine, 0).isPresent(), "distant operator cannot clear receipt");
        Scene capped = new Scene(); capped.paid();
        for (int i = 1; i <= 8; i++) check(ClibanoAccess.cancelProgress(capped.player, capped.machine).contains(i+"/8"), "explicit backup number " + i);
        CompoundTag previous = capped.machine.persistent.copy();
        check(ClibanoAccess.cancelProgress(capped.player, capped.machine).contains("не завершено") && capped.machine.persistent.equals(previous), "ninth explicit recovery cannot overwrite old backups");
        Scene corruptBackup = new Scene(); corruptBackup.paid(); corruptBackup.machine.persistent.putString("aia2_clibano_cancel_backups_v1", "keep");
        check(ClibanoAccess.cancelProgress(corruptBackup.player, corruptBackup.machine).contains("не завершено") && corruptBackup.machine.persistent.getString("aia2_clibano_cancel_backups_v1").equals("keep"), "wrong-type backup preserved and recovery refused");
        Scene outer = new Scene(); Scene inner = new Scene(); outer.machine.midTick = inner::tick; outer.tick();
        check(!ClibanoAccess.inTick(outer.machine) && !ClibanoAccess.inTick(inner.machine), "nested static ticker restores both contexts");
        check(outer.machine.burnTime > 0 && inner.machine.burnTime > 0 && outer.machine.logic.cookingProgress[0] == 0 && inner.machine.logic.cookingProgress[0] == 0, "nested cold ticks pay their own actual fuel without cross-owner cooking");
    }
    public static void main(String[] args) {
        normalProductionAndEnergy(); prepaymentDenials(); lanesAndCurrentIdentities(); alloyEnhancersAndLaneIndependence(); restartLegacyAndProofIntegrity(); residueConversions(); explicitRecoveryAndScopes();
        Scene overlapping = new Scene(); overlapping.machine.slots[4] = item("minecraft:diamond");
        var alternative = overlapping.recipe(RUNE, "minecraft:diamond", null, "forbidden_arcanus:rune");
        overlapping.level.recipes.replace(overlapping.first, alternative); overlapping.paid();
        check(ClibanoPaidState.lane(overlapping.machine, 0).orElseThrow().recipeId().equals(ClibanoPaidState.lane(overlapping.machine, 1).orElseThrow().recipeId()),
                "native queue cannot replace the second overlapping lane with a different recipe");
        overlapping.steps(2);
        check(overlapping.machine.nativeFinishes == 2 && overlapping.machine.slots[5].getCount() == 2
                && overlapping.machine.slots[5].item.id.equals("forbidden_arcanus:arcane_crystal_dust"), "both planned overlapping lanes finish the current chosen recipe");
        Scene lastSlot = new Scene(); lastSlot.machine.slots[4] = item("minecraft:iron_ingot"); lastSlot.paid();
        lastSlot.machine.slots[5] = item("minecraft:gold_ingot", 64); lastSlot.steps(2);
        check(lastSlot.machine.nativeFinishes == 1 && lastSlot.machine.logic.cookingProgress[1] == 2
                && ClibanoPaidState.lane(lastSlot.machine, 1).isPresent(), "first lane filling last slot preserves second lane paid work instead of native reset");
        lastSlot.machine.slots[5] = ItemStack.EMPTY; lastSlot.tick();
        check(lastSlot.machine.nativeFinishes == 2, "second paid lane resumes after destination is emptied");
        System.out.println("ClibanoGuardHarness: " + checks + " actual-helper/handler/real-policy plus pinned native logic modeled assertions PASS");
    }
}
