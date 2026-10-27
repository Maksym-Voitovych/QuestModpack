package ua.aia2.guard;

import java.util.Map;
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
            EnhancerHelper.ITEMS.clear(); KeyProductionBridge.KEYS.clear();
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

        s=new Scene();Object enhancer=new Object();Holder<Object> boost=s.enhancers.put("test:boost",enhancer);s.manager.dataCache.boosts.add(boost);s.denied("cached enhancer absent from physical slots");
        s=new Scene();boost=s.enhancers.put("test:boost",new Object());EnhancerHelper.ITEMS.put("test:enhancer",boost);s.forge.slots[0]=new ItemStack("test:enhancer");s.manager.dataCache.boosts.add(boost);s.paid();
        s.enhancers.put("test:boost",new Object());s.paused("stale native enhancer holder after reload");

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
        System.out.println("ForbiddenRitualHarness: "+checks+" actual-helper/handler/real-policy modeled assertions PASS");
    }
}
