package ua.aia2.guard;

import java.util.Map;
import java.util.List;
import net.minecraft.core.HolderSet;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.registries.Registries;
import net.minecraft.tags.TagKey;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.crafting.Ingredient;
import com.stal111.forbidden_arcanus.common.block.entity.forge.ritual.RitualInput;
import com.stal111.forbidden_arcanus.common.item.enhancer.EnhancerDefinition;
import com.stal111.forbidden_arcanus.common.item.enhancer.effect.ConditionalEnhancerEffect;
import com.stal111.forbidden_arcanus.common.item.enhancer.effect.ModifyRequiredEssenceEffect;
import java.util.Optional;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Holder;
import net.minecraft.core.Registry;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.nbt.ListTag;
import net.minecraft.nbt.Tag;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;
import com.stal111.forbidden_arcanus.core.registry.FARegistries;
import com.stal111.forbidden_arcanus.common.block.entity.PedestalBlockEntity;
import com.stal111.forbidden_arcanus.common.block.entity.forge.HephaestusForgeBlockEntity;
import com.stal111.forbidden_arcanus.common.block.entity.forge.ForgeDataCache;
import com.stal111.forbidden_arcanus.common.block.entity.forge.ritual.ActiveRitualData;
import com.stal111.forbidden_arcanus.common.block.entity.forge.ritual.Ritual;
import com.stal111.forbidden_arcanus.common.block.entity.forge.ritual.RitualManager;
import com.stal111.forbidden_arcanus.common.block.entity.forge.ritual.result.CreateItemResult;
import com.stal111.forbidden_arcanus.common.block.entity.forge.ritual.result.TransmuteInputResult;
import com.stal111.forbidden_arcanus.common.block.entity.forge.ritual.result.UpgradeTierResult;
import com.stal111.forbidden_arcanus.common.item.enhancer.EnhancerHelper;
import ua.aia2.guard.mixin.ForbiddenForgeInputMixin;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

/** Calls actual helpers/handlers. Minecraft, codecs and the optional native body are modeled. */
public final class ForbiddenRitualHarness {
    private static int checks;
    private static final String ID = "forbidden_arcanus:arcane_crystal_obelisk";
    private static void check(boolean value, String message) {
        checks++;
        if (!value) throw new AssertionError(message);
    }
    private static void throwsNative(Runnable call, String expected) {
        try { call.run(); throw new AssertionError("Expected native exception: " + expected); }
        catch (IllegalStateException error) { check(error.getMessage().equals(expected), "native exception propagated: " + expected); }
    }
    private static void rejectsDependency(Runnable action,String message) {
        boolean denied=false;try{action.run();}catch(IllegalArgumentException|IllegalStateException expected){denied=true;}
        check(denied,message);
    }
    private static void progress(int completed) {
        Aia2MachineGuard.BLOCKS.setTeamProgress("a", completed);
        Aia2MachineGuard.ITEMS.setTeamProgress("a", completed);
    }
    private static final class Scene {
        final ServerLevel level = new ServerLevel();
        final HephaestusForgeBlockEntity forge = new HephaestusForgeBlockEntity();
        final PedestalBlockEntity pedestal = new PedestalBlockEntity();
        final ServerPlayer player = new ServerPlayer(level);
        final Registry<Object> rituals = new Registry<>(), enhancers = new Registry<>();
        Ritual ritual = new Ritual(new CreateItemResult(new ItemStack("minecraft:emerald")));
        Holder<Object> holder;
        RitualManager manager;
        Scene() {
            Aia2MachineGuard.ready = true;
            Aia2MachineGuard.BLOCKS.setRules(Map.of(
                    "forbidden_arcanus:hephaestus_forge_tier_1",15,
                    "forbidden_arcanus:hephaestus_forge_tier_2",21,
                    "forbidden_arcanus:hephaestus_forge_tier_5",31));
            Aia2MachineGuard.ITEMS.setRules(Map.of(
                    "forbidden_arcanus:eternal_stella",34,
                    "test:enhancer",15,"test:registered_key",0));
            progress(14); Aia2MachineGuard.BLOCKS.setReady(); Aia2MachineGuard.ITEMS.setReady();
            level.access.registries.put(FARegistries.RITUAL, rituals);
            level.access.registries.put(FARegistries.ENHANCER_DEFINITION, enhancers);
            forge.level = level; forge.pos = new BlockPos(0,0,0); level.tiles.put(forge.pos,forge);
            pedestal.level = level; pedestal.pos = new BlockPos(1,0,0); level.tiles.put(pedestal.pos,pedestal);
            manager = new RitualManager(forge); forge.rituals = manager;
            manager.dataCache.entries.add(new ForgeDataCache.Entry(pedestal.pos,pedestal.stack.copy()));
            holder = rituals.put(ID,ritual); manager.validRitual = holder;
            EnhancerHelper.ITEMS.clear(); KeyProductionBridge.KEYS.clear(); BuiltInRegistries.ITEM.tags.clear();
        }
        Optional<?> start() { return manager.start(player,forge.essences.storage,holder); }
        void paid() { check(start().equals(Optional.of(true)),"valid native start succeeds"); }
        void denied(String message) {
            ItemStack main=forge.slots[4].copy(),pedestalBefore=pedestal.stack.copy();
            int essence=forge.essences.storage.balance;
            check(start().isEmpty(),message);
            check(manager.activeRitualData==null&&manager.startMutations==0&&forge.essences.storage.balance==essence,
                    "denial precedes active state, payment and pedestal callbacks: "+message);
            check(ItemStack.matches(main,forge.slots[4])&&ItemStack.matches(pedestalBefore,pedestal.stack),"denial leaves physical inputs: "+message);
        }
        void replace(Ritual replacement) { ritual=replacement; holder=rituals.put(ID,replacement); }
        void paused(String message) {
            int counter=manager.activeRitualData==null?-1:manager.activeRitualData.counter;
            int nativeTicks=manager.nativeTicks;
            check(manager.tick().isEmpty(),message);
            check(manager.nativeTicks==nativeTicks&&manager.nativeFinish==0&&manager.nativeFail==0,"paused call cannot enter native tick/reset: "+message);
            check(counter==(manager.activeRitualData==null?-1:manager.activeRitualData.counter),"paused call preserves counter: "+message);
            check(ForbiddenPaidState.hasRetainedActive(manager),"paused call retains native snapshot: "+message);
        }
    }
    public static final class UnknownResult {
        int calls;
        public ItemStack getResultItem(ItemStack ignored) { calls++; return new ItemStack("minecraft:emerald"); }
    }
    private static ForbiddenDependencies.Snapshot snapshot(Scene s) {
        return ForbiddenDependencies.capture(s.ritual,s.enhancers,s.manager.dataCache.boosts,
                s.level.registryAccess(),List.of(s.pedestal.stack),s.forge.slots[4]);
    }
    private static final TagKey<Item> MAIN_TAG=TagKey.create(Registries.ITEM,ResourceLocation.parse("test:main"));
    private static HolderSet.Named<Item> bindMain(String... ids) {
        List<Holder<Item>> holders=java.util.Arrays.stream(ids)
                .map(id->BuiltInRegistries.ITEM.wrapAsHolder(BuiltInRegistries.item(id))).toList();
        return BuiltInRegistries.ITEM.bind(MAIN_TAG,holders);
    }
    private static void tagMain(Scene s,String... ids) {bindMain(ids);s.ritual.main=Ingredient.of(MAIN_TAG);}
    private static CompoundTag oldPaidWithoutDependencies(Scene s) {
        CompoundTag root=s.manager.saveRaw(true);root.getCompound(ForbiddenPaidState.ACTIVE_TAG).remove(ForbiddenDependencies.ACTIVE_TAG);
        return root;
    }
    private static void loadSameManager(Scene s,CompoundTag root) {s.manager.loadRaw(root);}
    private static Holder<Object> install(Scene s,EnhancerDefinition definition) {
        Holder<Object> holder=s.enhancers.put("test:boost",definition);
        s.manager.dataCache.boosts.clear();s.manager.dataCache.boosts.add(holder);
        EnhancerHelper.ITEMS.put("test:enhancer",holder);s.forge.slots[0]=new ItemStack("test:enhancer");return holder;
    }
    private static void transitiveDependencies() {
        Scene s=new Scene();var plain=snapshot(s);
        check(!plain.hasDependencies(),"plain item-only ritual has no transitive gameplay dependency");
        check(plain.equals(snapshot(s)),"dependency capture deterministic");
        s.paid();CompoundTag exact=s.manager.saveRaw(true);
        check(exact.getCompound(ForbiddenPaidState.RECEIPT_TAG).getAllKeys().size()==6,"existing receipt schema1 six keys unchanged");
        check(exact.getCompound(ForbiddenPaidState.ACTIVE_TAG).contains(ForbiddenDependencies.ACTIVE_TAG),"new payment records dependency extension in native active tag");
        check(ForbiddenDependencies.matches(exact.getCompound(ForbiddenPaidState.ACTIVE_TAG),plain),"new paid extension verifies current dependencies");
        CompoundTag old=oldPaidWithoutDependencies(s);loadSameManager(s,old);
        check(s.manager.tick().isEmpty()&&s.manager.activeRitualData.counter==1,"old plain item-only payment may resume without inventing proof");
        check(!s.manager.saveRaw(true).getCompound(ForbiddenPaidState.ACTIVE_TAG).contains(ForbiddenDependencies.ACTIVE_TAG),"legacy plain resume/save never adopts current snapshot as old payment evidence");

        s=new Scene();tagMain(s,"minecraft:diamond","minecraft:emerald");var tagged=snapshot(s);
        check(tagged.hasDependencies(),"tagged main is a gameplay dependency");
        s.ritual.main.getItems();var named=BuiltInRegistries.ITEM.getTag(MAIN_TAG).orElseThrow();
        bindMain("minecraft:emerald","minecraft:diamond");
        check(BuiltInRegistries.ITEM.getTag(MAIN_TAG).orElseThrow()==named,"modeled current tag binding retains Named identity on bind");
        check(tagged.equals(snapshot(s)),"tag member iteration reorder preserves canonical dependency hash");
        bindMain("minecraft:diamond","minecraft:emerald","minecraft:gold_ingot");
        check(!tagged.fingerprint().equals(snapshot(s).fingerprint()),"same Ingredient with memoized getItems sees current registry membership change");
        var unrelated=TagKey.create(Registries.ITEM,ResourceLocation.parse("test:unrelated"));
        var beforeUnrelated=snapshot(s);BuiltInRegistries.ITEM.bind(unrelated,List.of(BuiltInRegistries.ITEM.wrapAsHolder(BuiltInRegistries.item("minecraft:coal"))));
        check(beforeUnrelated.equals(snapshot(s)),"unrelated tag binding does not invalidate paid gameplay dependencies");
        s.paid();var saved=s.manager.saveRaw(true);int paidCounter=s.manager.activeRitualData.counter;
        bindMain("minecraft:diamond","minecraft:emerald","minecraft:gold_ingot","minecraft:redstone");s.paused("new unrelated accepted tag member changes paid dependency snapshot");
        check(s.manager.activeRitualData.counter==paidCounter,"tag expansion cannot advance paid counter");
        bindMain("minecraft:gold_ingot","minecraft:emerald","minecraft:diamond");
        check(s.manager.tick().isEmpty()&&s.manager.activeRitualData.counter==1,"restored exact tag membership resumes paid progress");
        check(s.manager.saveRaw(true).getCompound(ForbiddenPaidState.ACTIVE_TAG).getCompound(ForbiddenDependencies.ACTIVE_TAG)
                .equals(saved.getCompound(ForbiddenPaidState.ACTIVE_TAG).getCompound(ForbiddenDependencies.ACTIVE_TAG)),"native counter refresh preserves exact dependency snapshot extension");
        loadSameManager(s,s.manager.saveRaw(true));check(s.manager.tick().isEmpty()&&s.manager.activeRitualData.counter==2,"dependency snapshot survives modeled restart/native codec omission");

        s=new Scene();s.ritual.main=new Ingredient(new Ingredient.ItemValue(new ItemStack("minecraft:diamond")),new Ingredient.TagValue(MAIN_TAG));var absentAlternative=snapshot(s);
        check(absentAlternative.hasDependencies(),"empty or absent tag alternative still records a transitive dependency");
        BuiltInRegistries.ITEM.bind(MAIN_TAG,List.of());check(!absentAlternative.fingerprint().equals(snapshot(s).fingerprint()),"absent versus bound-empty item tag remains distinguishable");
        var emptyEnhancerTag=TagKey.create(FARegistries.ENHANCER_DEFINITION,ResourceLocation.parse("test:empty_required"));s.ritual.requirements().enhancers=s.enhancers.bind(emptyEnhancerTag,List.of());
        check(snapshot(s).hasDependencies(),"bound-empty required enhancer tag remains a historical gameplay dependency");

        s=new Scene();tagMain(s,"minecraft:diamond");s.paid();var oldTagged=oldPaidWithoutDependencies(s);loadSameManager(s,oldTagged);
        s.paused("old schema1 payment with tag dependency but no historical snapshot");
        check(s.manager.saveRaw(true).equals(oldTagged),"paused old tagged payment remains byte-structurally unchanged without snapshot adoption");

        for(int mode=0;mode<4;mode++) {
            s=new Scene();s.paid();var broken=s.manager.saveRaw(true);var active=broken.getCompound(ForbiddenPaidState.ACTIVE_TAG);
            if(mode==0)active.putString(ForbiddenDependencies.ACTIVE_TAG,"opaque-corrupt");
            else if(mode==1)active.getCompound(ForbiddenDependencies.ACTIVE_TAG).putInt("schema",99);
            else if(mode==2)active.getCompound(ForbiddenDependencies.ACTIVE_TAG).putString("extra_semantics","retain");
            else active.getCompound(ForbiddenDependencies.ACTIVE_TAG).remove("schema");
            loadSameManager(s,broken);s.paused("malformed dependency snapshot variant "+mode);
            check(s.manager.saveRaw(true).equals(broken),"malformed dependency extension preserved variant "+mode);
        }

        s=new Scene();s.ritual.main=new Ingredient(true,new Ingredient.ItemValue(new ItemStack("minecraft:diamond")));s.denied("custom ingredient without reviewed transitive adapter");
        s=new Scene();s.ritual.inputs=List.of(new RitualInput(new Ingredient(true,new Ingredient.ItemValue(new ItemStack("minecraft:iron_ingot"))),1));s.denied("custom pedestal ingredient without reviewed transitive adapter");
        s=new Scene();tagMain(s,"minecraft:diamond");s.ritual.main.getItems();BuiltInRegistries.ITEM.tags.remove(MAIN_TAG);s.denied("removed current tag despite stale Ingredient items");
        s=new Scene();tagMain(s,"minecraft:diamond");s.ritual.main.getItems();bindMain("minecraft:emerald");s.denied("stale Ingredient match cannot authorize item absent from current tag");
        s=new Scene();s.ritual.inputs=List.of(new RitualInput(Ingredient.of("minecraft:iron_ingot"),2));s.denied("native per-pedestal amount cannot count one stack as two inputs");

        s=new Scene();var enhancer=new EnhancerDefinition();install(s,enhancer);check(snapshot(s).hasDependencies(),"installed enhancer definition is a gameplay dependency");
        s.paid();var changed=new EnhancerDefinition();changed.definition="changed";install(s,changed);s.paused("same-ID refreshed enhancer definition changed despite physical and cached holders matching");
        install(s,enhancer);check(s.manager.tick().isEmpty()&&s.manager.activeRitualData.counter==1,"restored exact current enhancer definition resumes");
        s=new Scene();install(s,new EnhancerDefinition());s.paid();var oldEnhanced=oldPaidWithoutDependencies(s);loadSameManager(s,oldEnhanced);
        s.paused("old paid installed enhancer without historical dependency snapshot");check(s.manager.saveRaw(true).equals(oldEnhanced),"legacy enhancer payment cannot adopt current registry as history");

        s=new Scene();var first=install(s,new EnhancerDefinition());var enhancerTag=TagKey.create(FARegistries.ENHANCER_DEFINITION,ResourceLocation.parse("test:required"));
        s.ritual.requirements().enhancers=s.enhancers.bind(enhancerTag,List.of(first));var required=snapshot(s);
        var second=s.enhancers.put("test:other",new EnhancerDefinition());s.enhancers.bind(enhancerTag,List.of(first,second));
        check(!required.fingerprint().equals(snapshot(s).fingerprint()),"required enhancer tag membership is resolved from current binding");
        s.enhancers.bind(enhancerTag,List.of(first));check(required.equals(snapshot(s)),"restored enhancer tag returns same fingerprint");
        s.ritual.requirements().enhancers=HolderSet.direct(first);var direct=snapshot(s);
        check(direct.hasDependencies(),"direct required enhancer definitions remain dependencies");
        s.enhancers.entries.remove(ResourceLocation.parse("test:boost"));s.denied("removed required/current enhancer cannot be used");

        s=new Scene();var unknownEffect=new EnhancerDefinition();unknownEffect.effects=List.of(new ConditionalEnhancerEffect<>(new Object(),Optional.empty()));install(s,unknownEffect);s.denied("unreviewed enhancer effect implementation");
        s=new Scene();var unknownCondition=new EnhancerDefinition();unknownCondition.effects=List.of(new ConditionalEnhancerEffect<>(new ModifyRequiredEssenceEffect(2),Optional.of(List.of(new Object()))));install(s,unknownCondition);s.denied("unreviewed conditional enhancer dependency");

        s=new Scene();var supported=new EnhancerDefinition();supported.effects=List.of(new ConditionalEnhancerEffect<>(new ModifyRequiredEssenceEffect(2),Optional.of(List.of(new com.stal111.forbidden_arcanus.common.item.enhancer.condition.TimeCondition(0,100)))));
        install(s,supported);var supportedFingerprint=snapshot(s);s.paid();
        var differentEffect=new EnhancerDefinition();differentEffect.effects=List.of(new ConditionalEnhancerEffect<>(new ModifyRequiredEssenceEffect(3),Optional.of(List.of(new com.stal111.forbidden_arcanus.common.item.enhancer.condition.TimeCondition(0,100)))));
        install(s,differentEffect);s.paused("supported enhancer effect value changed under same registered ID");
        install(s,supported);check(s.manager.tick().isEmpty()&&s.manager.activeRitualData.counter==1,"restored exact supported enhancer effect resumes");
        var differentCondition=new EnhancerDefinition();differentCondition.effects=List.of(new ConditionalEnhancerEffect<>(new ModifyRequiredEssenceEffect(2),Optional.of(List.of(new com.stal111.forbidden_arcanus.common.item.enhancer.condition.TimeCondition(1,100)))));
        install(s,differentCondition);check(!supportedFingerprint.fingerprint().equals(snapshot(s).fingerprint()),"supported condition range participates in full enhancer definition fingerprint");s.paused("supported time condition definition changed");

        Scene late=new Scene();tagMain(late,"minecraft:diamond");late.paid();late.manager.tick();late.manager.tick();
        late.manager.midTick=()->bindMain("minecraft:diamond","minecraft:emerald");
        check(late.manager.tick().isEmpty()&&late.manager.nativeFinish==0,"late commit rechecks transitive membership before result");
        check(late.manager.activeRitualData.counter==2&&ForbiddenPaidState.status(late.manager)==ForbiddenPaidState.Status.VERIFIED,"late dependency denial retains paid receipt and precommit counter");
        bindMain("minecraft:diamond");late.manager.midTick=()->{};check(late.manager.tick().isPresent()&&late.manager.nativeFinish==1,"restored late dependency commits exactly once");

        Scene greedy=new Scene();
        greedy.ritual.inputs=List.of(new RitualInput(new Ingredient(new Ingredient.ItemValue(new ItemStack("minecraft:iron_ingot")),new Ingredient.ItemValue(new ItemStack("minecraft:gold_ingot"))),1),new RitualInput(Ingredient.of("minecraft:gold_ingot"),1));
        rejectsDependency(()->ForbiddenDependencies.capture(greedy.ritual,greedy.enhancers,List.of(),greedy.level.access,
                List.of(new ItemStack("minecraft:gold_ingot"),new ItemStack("minecraft:iron_ingot")),greedy.forge.slots[4]),"current ingredients replay native greedy order instead of inventing a reordered recipe match");
        check(ForbiddenDependencies.capture(greedy.ritual,greedy.enhancers,List.of(),greedy.level.access,
                List.of(new ItemStack("minecraft:iron_ingot"),new ItemStack("minecraft:gold_ingot")),greedy.forge.slots[4])!=null,"native greedy-compatible ordered pedestals pass");
        Scene tooManyInputs=new Scene();tooManyInputs.ritual.inputs=java.util.Collections.nCopies(9,new RitualInput(Ingredient.of("minecraft:iron_ingot"),1));tooManyInputs.denied("bounded ritual input count");
        Scene unknownValue=new Scene();unknownValue.ritual.main=new Ingredient(()->List.of(new ItemStack("minecraft:diamond")));unknownValue.denied("unknown vanilla ingredient Value implementation");
        Scene excessiveAmount=new Scene();excessiveAmount.ritual.inputs=List.of(new RitualInput(Ingredient.of("minecraft:iron_ingot"),129));excessiveAmount.denied("bounded native pedestal amount");
        Scene manyValues=new Scene();manyValues.ritual.main=new Ingredient(java.util.Collections.nCopies(65,new Ingredient.ItemValue(new ItemStack("minecraft:diamond"))).toArray(Ingredient.Value[]::new));manyValues.denied("bounded ingredient value count");
        Scene manyMembers=new Scene();tagMain(manyMembers,"minecraft:diamond");var hugeTag=new java.util.ArrayList<Holder<Item>>();
        for(int i=0;i<16385;i++)hugeTag.add(new Holder<Item>("test:mass/"+i,new Item("test:mass/"+i)));
        BuiltInRegistries.ITEM.bind(MAIN_TAG,hugeTag);manyMembers.denied("bounded current tag expansion before hashing unbounded data");
        Scene manyEffects=new Scene();var largeEffectDefinition=new EnhancerDefinition();largeEffectDefinition.effects=java.util.Collections.nCopies(65,new ConditionalEnhancerEffect<>(new ModifyRequiredEssenceEffect(2),Optional.empty()));install(manyEffects,largeEffectDefinition);manyEffects.denied("bounded installed enhancer effect list");
        Scene manyConditions=new Scene();var largeConditionalDefinition=new EnhancerDefinition();largeConditionalDefinition.effects=List.of(new ConditionalEnhancerEffect<>(new ModifyRequiredEssenceEffect(2),Optional.of(java.util.Collections.nCopies(33,new com.stal111.forbidden_arcanus.common.item.enhancer.condition.TimeCondition(0,100)))));install(manyConditions,largeConditionalDefinition);manyConditions.denied("bounded enhancer condition list");
        Scene manyEnhancers=new Scene();var requiredEnhancers=new java.util.ArrayList<Holder<Object>>();for(int i=0;i<65;i++)requiredEnhancers.add(manyEnhancers.enhancers.put("test:required/"+i,new EnhancerDefinition()));manyEnhancers.ritual.requirements().enhancers=HolderSet.direct(requiredEnhancers);manyEnhancers.denied("bounded required enhancer set");
        Scene manyTags=new Scene();var tagValues=new java.util.ArrayList<Ingredient.Value>();for(int i=0;i<64;i++){var key=TagKey.create(Registries.ITEM,ResourceLocation.parse("test:many/"+i));BuiltInRegistries.ITEM.bind(key,List.of(BuiltInRegistries.ITEM.wrapAsHolder(BuiltInRegistries.item("minecraft:diamond"))));tagValues.add(new Ingredient.TagValue(key));}manyTags.ritual.main=new Ingredient(tagValues.toArray(Ingredient.Value[]::new));
        var lastKey=TagKey.create(Registries.ITEM,ResourceLocation.parse("test:many/last"));BuiltInRegistries.ITEM.bind(lastKey,List.of(BuiltInRegistries.ITEM.wrapAsHolder(BuiltInRegistries.item("minecraft:iron_ingot"))));manyTags.ritual.inputs=List.of(new RitualInput(Ingredient.of(lastKey),1));manyTags.denied("bounded distinct ingredient tag count");
        rejectsDependency(()->new ForbiddenDependencies.Snapshot("short",false),"invalid dependency snapshot fingerprint rejected");
        CompoundTag duplicate=new CompoundTag();ForbiddenDependencies.attach(duplicate,plain);
        rejectsDependency(()->ForbiddenDependencies.attach(duplicate,plain),"dependency payment extension cannot be attached twice");
        check(!ForbiddenDependencies.matches(null,plain),"missing retained native state cannot validate even item-only dependencies");
        CompoundTag malformedHash=new CompoundTag();ForbiddenDependencies.attach(malformedHash,plain);malformedHash.getCompound(ForbiddenDependencies.ACTIVE_TAG).putString("fingerprint","short");
        check(!ForbiddenDependencies.matches(malformedHash,plain),"short dependency fingerprint never matches");
        malformedHash.getCompound(ForbiddenDependencies.ACTIVE_TAG).putInt("fingerprint",1);check(!ForbiddenDependencies.matches(malformedHash,plain),"wrong-typed dependency fingerprint never matches");

        Scene hugeDescription=new Scene();var hugeDefinition=new EnhancerDefinition();hugeDefinition.definition="x".repeat(4097);install(hugeDescription,hugeDefinition);hugeDescription.denied("bounded encoded enhancer text before canonical hash");
        Scene deepDescription=new Scene();var deepDefinition=new EnhancerDefinition();com.google.gson.JsonArray nested=new com.google.gson.JsonArray(),current=nested;for(int i=0;i<33;i++){var next=new com.google.gson.JsonArray();current.add(next);current=next;}deepDefinition.description=nested;install(deepDescription,deepDefinition);deepDescription.denied("bounded encoded enhancer nesting before recursive canonical hash");
        Scene once=new Scene();var onceDefinition=new EnhancerDefinition();var onceHolder=install(once,onceDefinition);once.ritual.requirements().enhancers=HolderSet.direct(java.util.List.of(onceHolder));snapshot(once);check(onceDefinition.encodings==1,"required and installed same enhancer serialized once within a dependency capture");

        Scene paymentRace=new Scene();tagMain(paymentRace,"minecraft:diamond");paymentRace.manager.beforePayment=()->bindMain("minecraft:diamond","minecraft:emerald");
        check(paymentRace.start().isPresent()&&paymentRace.forge.essences.storage.payments==1,"dependency mutation after native payment preserves operation without throwing into server event");
        check(ForbiddenPaidState.status(paymentRace.manager)==ForbiddenPaidState.Status.PENDING&&ForbiddenPaidState.hasRetainedActive(paymentRace.manager),"paid but mismatched payment remains pending/preserved without fabricated refund");
        paymentRace.paused("mixed prepayment dependency snapshots cannot run");
    }
    public static void main(String[] ignored) {
        Scene s=new Scene(); s.paid();
        check(s.forge.essences.storage.balance==90&&s.forge.essences.storage.payments==1,"payment executed exactly once");
        check(ForbiddenPaidState.status(s.manager)==ForbiddenPaidState.Status.VERIFIED,"receipt certified after actual reduce RETURN");
        check(!ForbiddenRitualAccess.inTick(s.manager),"no tick scope after start");
        check(s.manager.tick().isEmpty()&&s.manager.activeRitualData.counter==1,"first actual native tick runs");
        check(s.manager.tick().isEmpty()&&s.manager.activeRitualData.counter==2,"duration boundary waits native progress semantics");
        check(s.manager.tick().isPresent()&&s.manager.nativeFinish==1&&s.manager.activeRitualData==null,"duration+1 commit counter is allowed exactly once");
        check(ForbiddenPaidState.status(s.manager)==ForbiddenPaidState.Status.EMPTY&&!ForbiddenPaidState.hasRetainedActive(s.manager),"successful finish clears payment before native reset");
        check(s.manager.tick().isEmpty()&&s.manager.nativeFinish==1,"completed ritual cannot replay");

        s=new Scene();Aia2MachineGuard.ready=false;s.denied("unready policy");
        s=new Scene();progress(13);s.denied("future forge");
        s=new Scene();s.player.team="b";s.denied("other player team");
        s=new Scene();s.player.fake=true;s.denied("fake player");
        s=new Scene();s.forge.team="";s.denied("unowned forge");
        s=new Scene();s.level.server.sameThread=false;s.denied("off-server thread");
        s=new Scene();s.level.loaded=false;s.denied("unloaded receiver");
        s=new Scene();s.forge.removed=true;s.denied("removed receiver");
        s=new Scene();s.level.tiles.remove(s.forge.pos);s.denied("noncanonical receiver");
        s=new Scene();s.manager.affordable=false;s.denied("unaffordable native essence cost");
        s=new Scene();s.ritual.requirements=false;s.denied("ritual native requirements");
        s=new Scene();s.manager.dataCache.main.count=3;s.denied("stale main stack count");
        s=new Scene();s.manager.dataCache.entries.add(s.manager.dataCache.entries.getFirst());s.denied("duplicate pedestal coordinates");
        s=new Scene();s.level.tiles.remove(s.pedestal.pos);s.denied("missing physical pedestal");
        s=new Scene();s.pedestal.stack.components.put("foreign","changed");s.denied("stale physical pedestal components");
        s=new Scene();s.ritual.duration=0;s.denied("zero native duration");
        s=new Scene();s.ritual.duration=1200001;s.denied("unbounded native duration");

        s=new Scene();s.ritual.result=new CreateItemResult(new ItemStack("forbidden_arcanus:eternal_stella"));s.denied("future output");
        s=new Scene();s.ritual.result=new CreateItemResult(new ItemStack("kubejs:aia2_tech_key_15"));s.denied("key output pattern");
        s=new Scene();KeyProductionBridge.KEYS.add("test:registered_key");s.ritual.result=new CreateItemResult(new ItemStack("test:registered_key"));s.denied("registered key output");
        s=new Scene();UnknownResult unknown=new UnknownResult();s.ritual.result=unknown;s.denied("unknown result implementation");check(unknown.calls==0,"unknown result is never preview-called");
        s=new Scene();s.ritual.result=new UpgradeTierResult(2);s.denied("future tier despite empty item result");progress(20);s.paid();
        s=new Scene();s.ritual.result=new UpgradeTierResult(6);s.denied("invalid native target tier");
        s=new Scene();s.ritual.result=new TransmuteInputResult("minecraft:emerald");s.paid();check(s.forge.slots[4].count==1,"transmutation preview does not mutate main stack");
        s=new Scene();s.forge.slots[4].components.put("creative",true);s.manager.dataCache.main=s.forge.slots[4].copy();s.denied("copied future component input");

        Scene before=new Scene();before.manager.throwBeforePay=true;
        throwsNative(before::start,"before payment");
        check(before.forge.essences.storage.payments==0&&ForbiddenPaidState.status(before.manager)==ForbiddenPaidState.Status.PENDING,"prepayment exception does not certify free active ritual");
        before.paused("unpaid active after native exception");
        ForbiddenRitualAccess.paid(before.forge.essences.storage,before.ritual.requirements().essences());
        check(ForbiddenPaidState.status(before.manager)==ForbiddenPaidState.Status.PENDING,"finally removes failed START scope");
        Scene after=new Scene();after.manager.throwAfterPay=true;
        throwsNative(after::start,"after payment");
        check(after.forge.essences.storage.payments==1&&ForbiddenPaidState.status(after.manager)==ForbiddenPaidState.Status.VERIFIED,"post-payment exception preserves valid proof");
        after.manager.throwAfterPay=false;check(after.manager.tick().isEmpty()&&after.manager.activeRitualData.counter==1,"paid operation resumes after callback exception");
        Scene tickThrow=new Scene();tickThrow.paid();tickThrow.manager.throwTick=true;
        throwsNative(tickThrow.manager::tick,"native tick exception");
        check(!ForbiddenRitualAccess.inTick(tickThrow.manager),"native exception restores TICK scope");
        check(ForbiddenPaidState.status(tickThrow.manager)==ForbiddenPaidState.Status.VERIFIED,"native exception keeps receipt and actual progress");
        check(!ForbiddenRitualAccess.mayCommit(tickThrow.manager),"commit outside scope denied after exception");

        Scene preActive=new Scene();
        throwsNative(()->ForbiddenRitualAccess.start(preActive.manager,preActive.player,preActive.forge.essences.storage,
                Optional.of(preActive.holder),holder->{throw new IllegalStateException("before active creation");}),"before active creation");
        check(ForbiddenPaidState.status(preActive.manager)==ForbiddenPaidState.Status.EMPTY&&!ForbiddenPaidState.hasRetainedActive(preActive.manager),"exception before active creation safely aborts only unpaid pending token");
        preActive.paid();
        Scene nestedOuter=new Scene(),nestedInner=new Scene();
        nestedOuter.manager.beforePayment=()->nestedInner.start();nestedOuter.paid();
        check(ForbiddenPaidState.status(nestedOuter.manager)==ForbiddenPaidState.Status.VERIFIED&&ForbiddenPaidState.status(nestedInner.manager)==ForbiddenPaidState.Status.VERIFIED,"nested START restores outer storage scope and certifies both exact payments");
        check(nestedOuter.forge.essences.storage.payments==1&&nestedInner.forge.essences.storage.payments==1,"nested start never substitutes or doubles storage payment");
        nestedOuter.manager.tick();nestedOuter.manager.tick();nestedOuter.manager.midTick=()->nestedInner.manager.tick();
        check(nestedOuter.manager.tick().isPresent()&&nestedOuter.manager.nativeFinish==1&&nestedInner.manager.activeRitualData.counter==1,"nested TICK finally restores outer commit scope");
        check(!ForbiddenRitualAccess.inTick(nestedOuter.manager)&&!ForbiddenRitualAccess.inTick(nestedInner.manager),"nested native callbacks leave no parent or child tick context");

        s=new Scene();s.paid();s.manager.fail();
        check(s.manager.nativeFail==0&&s.manager.activeRitualData!=null&&s.manager.dataCache.entries.size()==1,"destructive onDataChanged/load failure blocked outside native tick");
        s=new Scene();s.paid();s.manager.tick();Ritual old=s.ritual;Ritual changed=new Ritual(old.result);changed.definition="changed";s.replace(changed);s.paused("changed same-ID direct definition");
        CompoundTag retained=s.manager.saveRaw(true);
        check(retained.getCompound(ForbiddenPaidState.ACTIVE_TAG).getInt("counter")==1,"omitted native codec cannot erase paid counter");
        s.replace(old);check(s.manager.tick().isEmpty()&&s.manager.activeRitualData.counter==2,"restored exact definition resumes original progress");
        s=new Scene();s.paid();s.manager.tick();Ritual equivalent=new Ritual(s.ritual.result);s.replace(equivalent);
        check(s.manager.tick().isEmpty()&&s.manager.activeRitualData.getRitual()==equivalent,"identical direct codec reload rebinds current holder");
        check(s.manager.activeRitualData.counter==2,"rebind retains progress");
        s=new Scene();s.paid();s.manager.tick();s.rituals.entries.clear();s.paused("removed ritual registry entry");
        CompoundTag saved=s.manager.saveRaw(true);RitualManager restarted=new RitualManager(s.forge);s.forge.rituals=restarted;restarted.dataCache=s.manager.dataCache;restarted.loadRaw(saved);restarted.fail();
        check(restarted.activeRitualData==null&&restarted.nativeFail==0&&ForbiddenPaidState.hasRetainedActive(restarted),"failed native load cannot reset retained paid state");
        check(restarted.tick().isEmpty()&&restarted.nativeTicks==0,"missing definition after restart stays paused");
        s.rituals.put(ID,s.ritual);check(restarted.tick().isEmpty()&&restarted.activeRitualData.counter==2,"restored registry after restart reconstructs current native object and counter");

        s=new Scene();s.paid();s.pedestal.stack.count=2;s.paused("changed paid physical pedestal count");s.pedestal.stack.count=1;check(s.manager.tick().isEmpty()&&s.manager.activeRitualData.counter==1,"restored paid inputs resume");
        s=new Scene();s.paid();s.forge.slots[4].components.put("foreign","new");s.manager.dataCache.main=s.forge.slots[4].copy();s.paused("changed paid main components even with refreshed native cache");
        s=new Scene();s.paid();s.player.team="b";s.paused("online starter moved team");s.level.server.players.map.remove(s.player.uuid);check(s.manager.tick().isEmpty()&&s.manager.activeRitualData.counter==1,"offline starter permits production without inventing advancement grant");
        s=new Scene();s.paid();s.forge.team="b";s.paused("changed forge ownership");

        Scene mid=new Scene();mid.paid();mid.manager.tick();mid.manager.tick();mid.manager.midTick=()->mid.player.team="b";
        check(mid.manager.tick().isEmpty(),"commit denial returns Optional.empty instead of clearing main slot with EMPTY");
        check(mid.manager.activeRitualData.counter==2&&mid.manager.nativeFinish==0&&ForbiddenPaidState.status(mid.manager)==ForbiddenPaidState.Status.VERIFIED,"late denial restores native counter and preserves paid state");
        mid.player.team="a";mid.manager.midTick=()->{};check(mid.manager.tick().isPresent()&&mid.manager.nativeFinish==1,"late-denied operation resumes and commits once");

        s=new Scene();CompoundTag legacy=new CompoundTag();s.manager.activeRitualData=new ActiveRitualData(s.holder,1,0,s.player.uuid);legacy.put(ForbiddenPaidState.ACTIVE_TAG,ForbiddenRitualAccess.activeTag(s.manager));s.manager.loadRaw(legacy);s.manager.fail();s.paused("legacy operation without proof");check(s.manager.saveRaw(true).equals(legacy),"legacy native tag remains byte-structurally unchanged");
        check(ForbiddenRitualAccess.status(s.player,0,0,0).contains("LEGACY"),"status reports unverified legacy state");

        s=new Scene();Object enhancer=new EnhancerDefinition();Holder<Object> boost=s.enhancers.put("test:boost",enhancer);s.manager.dataCache.boosts.add(boost);s.denied("cached enhancer absent from physical slots");
        s=new Scene();boost=s.enhancers.put("test:boost",new EnhancerDefinition());EnhancerHelper.ITEMS.put("test:enhancer",boost);s.forge.slots[0]=new ItemStack("test:enhancer");s.manager.dataCache.boosts.add(boost);s.paid();
        s.enhancers.put("test:boost",new EnhancerDefinition());s.paused("stale native enhancer holder after reload");

        s=new Scene();check(ForbiddenRitualAccess.mayConsumeEssence(s.forge,new ItemStack("minecraft:iron_ingot")),"current ordinary essence input permitted");
        check(!ForbiddenRitualAccess.mayConsumeEssence(s.forge,new ItemStack("kubejs:aia2_arcane_key_15")),"keys cannot be laundered into essence");
        check(!ForbiddenRitualAccess.mayConsumeEssence(s.forge,new ItemStack("forbidden_arcanus:eternal_stella")),"future items cannot be consumed before ritual tick");
        CallbackInfoReturnable<Optional<?>> inputResult=new CallbackInfoReturnable<>(Optional.of("native input"));
        RitualManager.invoke(s.forge,ForbiddenForgeInputMixin.class,"aia2$input",new Class<?>[]{Level.class,ItemStack.class,Object.class,CallbackInfoReturnable.class},s.level,new ItemStack("kubejs:aia2_tech_key_15"),new Object(),inputResult);
        check(inputResult.cancelled&&inputResult.getReturnValue().isEmpty(),"actual Forge input handler cancels denied native lookup");
        s.forge.team="";check(!ForbiddenRitualAccess.mayConsumeEssence(s.forge,new ItemStack("minecraft:iron_ingot")),"unowned automated essence receiver denied");

        Scene cancel=new Scene();cancel.paid();int balance=cancel.forge.essences.storage.balance;
        ItemStack savedMain=cancel.forge.slots[4].copy(),savedPedestal=cancel.pedestal.stack.copy();
        String cancelled=ForbiddenRitualAccess.cancel(cancel.player,0,0,0);
        check(cancelled.contains("Ритуал скасовано"),"operator explicit recovery succeeds: "+cancelled);
        check(cancel.manager.activeRitualData==null&&ForbiddenPaidState.status(cancel.manager)==ForbiddenPaidState.Status.EMPTY,"explicit recovery clears native active and receipt");
        check(ItemStack.matches(savedMain,cancel.forge.slots[4])&&ItemStack.matches(savedPedestal,cancel.pedestal.stack),"explicit recovery preserves all physical inputs");
        check(cancel.forge.essences.storage.balance==balance&&cancel.manager.nativeFinish==0&&cancel.manager.nativeFail==0,"explicit recovery neither refunds essence nor runs native result/failure");
        ListTag backups=cancel.forge.persistent.getList("aia2_fa_cancel_backups_v1",Tag.TAG_COMPOUND);
        check(backups.size()==1&&((CompoundTag)backups.get(0)).contains(ForbiddenPaidState.RECEIPT_TAG),"cancel retains full paid receipt in bounded forge backup");
        check(((CompoundTag)backups.get(0)).getCompound(ForbiddenPaidState.ACTIVE_TAG).getString("ritual").equals(ID),"cancel backup binds original native ritual");
        check(cancel.pedestal.height==120&&cancel.manager.magicCircleController.removed==1,"recovery restores passive pedestal height and removes circle without native reset");
        for(int i=1;i<8;i++){cancel.paid();check(ForbiddenRitualAccess.cancel(cancel.player,0,0,0).contains("Ритуал скасовано"),"permitted bounded backup "+(i+1));}
        cancel.paid();CompoundTag fullBackup=cancel.forge.persistent.copy();
        check(ForbiddenRitualAccess.cancel(cancel.player,0,0,0).contains("Скасування не завершено"),"ninth backup refuses overwrite");
        check(cancel.forge.persistent.equals(fullBackup)&&cancel.manager.activeRitualData!=null&&ForbiddenPaidState.status(cancel.manager)==ForbiddenPaidState.Status.VERIFIED,"full backup refusal preserves both original backups and live paid state");

        Scene permission=new Scene();permission.paid();permission.player.permissions=0;
        check(ForbiddenRitualAccess.cancel(permission.player,0,0,0).contains("права оператора"),"nonoperator recovery denied");
        check(permission.manager.activeRitualData!=null&&permission.forge.persistent.isEmpty(),"nonoperator denial makes no state or backup writes");
        permission.player.permissions=2;permission.player.team="b";
        check(ForbiddenRitualAccess.cancel(permission.player,0,0,0).contains("іншій команді"),"operator cannot cancel another team's forge");
        permission.player.team="a";permission.player.pos=new BlockPos(9,0,0);
        check(ForbiddenRitualAccess.cancel(permission.player,0,0,0).contains("ближче"),"operator must be near exact forge");
        check(permission.manager.activeRitualData!=null&&permission.forge.persistent.isEmpty(),"nonowner/far denials make no state or backup writes");
        Scene malformed=new Scene();malformed.paid();malformed.forge.persistent.putString("aia2_fa_cancel_backups_v1","preserve opaque");
        CompoundTag opaqueBackup=malformed.forge.persistent.copy();
        check(ForbiddenRitualAccess.cancel(malformed.player,0,0,0).contains("Скасування не завершено"),"wrong-typed backup blocks recovery");
        check(malformed.forge.persistent.equals(opaqueBackup)&&malformed.manager.activeRitualData!=null,"wrong-typed backup and active state retained verbatim");
        Scene wrongElements=new Scene();wrongElements.paid();CompoundTag str=new CompoundTag();str.putString("value","retain wrong list element");ListTag wrongList=new ListTag();wrongList.add(str.get("value"));wrongElements.forge.persistent.put("aia2_fa_cancel_backups_v1",wrongList);
        CompoundTag wrongListBefore=wrongElements.forge.persistent.copy();
        check(ForbiddenRitualAccess.cancel(wrongElements.player,0,0,0).contains("Скасування не завершено"),"list of wrong element type cannot masquerade as empty backup list");
        check(wrongElements.forge.persistent.equals(wrongListBefore)&&wrongElements.manager.activeRitualData!=null,"wrong list contents and paid state remain untouched");
        Scene legacyCancel=new Scene();CompoundTag oldNative=new CompoundTag();legacyCancel.manager.activeRitualData=new ActiveRitualData(legacyCancel.holder,1,0,legacyCancel.player.uuid);oldNative.put(ForbiddenPaidState.ACTIVE_TAG,ForbiddenRitualAccess.activeTag(legacyCancel.manager));legacyCancel.manager.loadRaw(oldNative);
        check(ForbiddenRitualAccess.cancel(legacyCancel.player,0,0,0).contains("Ритуал скасовано"),"unparsed legacy native state has explicit recovery path");
        check(((CompoundTag)legacyCancel.forge.persistent.getList("aia2_fa_cancel_backups_v1",Tag.TAG_COMPOUND).get(0)).getCompound(ForbiddenPaidState.ACTIVE_TAG).getInt("counter")==1,"legacy recovery retains original native progress in backup without certifying payment");
        transitiveDependencies();
        System.out.println("ForbiddenRitualHarness: "+checks+" actual-helper/handler/real-policy modeled assertions PASS");
    }
}
