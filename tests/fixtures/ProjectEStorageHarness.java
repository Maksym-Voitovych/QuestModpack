package ua.aia2.guard.mixin;

import java.lang.reflect.*;
import java.util.Map;
import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.state.BlockState;
import net.neoforged.neoforge.common.util.FakePlayer;
import net.neoforged.neoforge.items.IItemHandler;
import ua.aia2.guard.Aia2MachineGuard;
import ua.aia2.guard.ProjectEStorageAccess;

/** Actual storage helper/handlers and real GuardPolicy; native host/capabilities are modeled. */
public final class ProjectEStorageHarness {
    private static int checks;
    private static final BlockPos POS = new BlockPos(2,64,3), OTHER = new BlockPos(4,64,5);
    private static final Level WORLD = new Level();
    private static final BlockState STATE = new BlockState("projecte:alchemical_chest");
    public static final class Inventory implements IItemHandler {}
    public static final class Capability implements moze_intel.projecte.api.capabilities.item.IAlchBagItem,
            moze_intel.projecte.api.capabilities.item.IAlchChestItem,moze_intel.projecte.api.capabilities.item.IPedestalItem {
        int calls; boolean changed=true; RuntimeException failure;
        BlockEntity expected; boolean expectNull;
        private boolean apply(ItemStack stack) {
            calls++;
            check(Aia2MachineGuard.currentTickOwner() == (expectNull ? null : expected), "native callback sees actual receiver context, not caller");
            if (failure != null) throw failure;
            stack.count--;
            return changed;
        }
        public boolean updateInAlchBag(IItemHandler inv,Player player,ItemStack stack) { return apply(stack); }
        public boolean updateInAlchChest(Level world,BlockPos pos,ItemStack stack) { return apply(stack); }
        public <T extends BlockEntity> boolean updateInPedestal(ItemStack stack,Level world,BlockPos pos,T tile) {
            check(tile == expected, "pedestal capability receives its original receiver"); return apply(stack);
        }
    }
    private static final class PrivateCapability implements moze_intel.projecte.api.capabilities.item.IAlchBagItem {
        public boolean updateInAlchBag(IItemHandler inventory,Player player,ItemStack stack) { return true; }
    }
    private static void check(boolean value,String reason) { checks++;if(!value)throw new AssertionError(reason); }
    private static void policies() {
        Aia2MachineGuard.policy.clear();Aia2MachineGuard.items.clear();
        Aia2MachineGuard.policy.setRules(Map.of("projecte:alchemical_chest",45,"projecte:dm_pedestal",45));
        Aia2MachineGuard.items.setRules(Map.of("projecte:repair_talisman",45,"fixture:future_capability",47,"minecraft:stick",0));
        for (var policy : java.util.List.of(Aia2MachineGuard.policy,Aia2MachineGuard.items)) {
            policy.setTeamProgress("early",0);policy.setTeamProgress("a",44);policy.setTeamProgress("late",46);policy.setReady();
        }
    }
    private static BlockEntity tile(Level world,BlockPos pos,String id,String owner) {
        var tile=new BlockEntity(world,pos,id,owner);world.blocks.put(pos,tile);return tile;
    }
    private static Method method(Class<?> type,String name,Class<?>... args) throws Exception {
        var method=type.getDeclaredMethod(name,args);method.setAccessible(true);return method;
    }
    private static boolean invoke(Method method,Object... args) throws Exception {
        try { return (boolean)method.invoke(null,args); }
        catch (InvocationTargetException failure) { if(failure.getCause() instanceof RuntimeException original)throw original;throw failure; }
    }
    public static void main(String[] args) throws Exception {
        policies();
        var bag=method(ProjectEBagPassiveMixin.class,"aia2$guardBagPassive",Object.class,IItemHandler.class,Player.class,ItemStack.class);
        var chest=method(ProjectEChestPassiveMixin.class,"aia2$guardChestPassive",Object.class,Level.class,BlockPos.class,ItemStack.class,Level.class,BlockPos.class,BlockState.class,Object.class);
        var pedestal=method(ProjectEPedestalPassiveMixin.class,"aia2$guardPedestalPassive",Object.class,ItemStack.class,Level.class,BlockPos.class,BlockEntity.class,Level.class,BlockPos.class,BlockState.class,Object.class);
        var inv=new Inventory();var early=new ServerPlayer(WORLD,"early");var a=new ServerPlayer(WORLD,"a");
        var parent=tile(WORLD,OTHER,"projecte:dm_pedestal","late");
        Aia2MachineGuard.enterTick(parent);
        var cap=new Capability();cap.expectNull=true;
        var ordinary=new ItemStack("minecraft:stick");
        check(!invoke(bag,cap,inv,early,ordinary)&&cap.calls==0&&ordinary.count==1,"bag feature itself45 denied even when inner addon capability stage0");
        var item=new ItemStack("projecte:repair_talisman");
        check(invoke(bag,cap,inv,a,item)&&cap.calls==1&&item.count==0,"authorized personal bag invokes capability once and preserves native mutation");
        check(Aia2MachineGuard.currentTickOwner()==parent,"bag clears borrowed context only during callback then restores it");
        check(invoke(bag,new PrivateCapability(),inv,a,new ItemStack("projecte:repair_talisman")),"public capability API supports private addon implementations");
        var future=new ItemStack("fixture:future_capability");
        check(!invoke(bag,cap,inv,a,future)&&future.count==1&&cap.calls==1,"bag rejects future inner capability without mutation");
        check(!invoke(bag,cap,inv,new FakePlayer(WORLD,"a"),new ItemStack("projecte:repair_talisman")),"FakePlayer cannot activate a personal bag");
        a.live="late";check(!invoke(bag,cap,inv,a,new ItemStack("projecte:repair_talisman")),"changed live team cannot retain bag privileges");a.live="a";
        a.synced=false;check(!invoke(bag,cap,inv,a,new ItemStack("projecte:repair_talisman")),"unsynchronized player fails closed");a.synced=true;
        cap.failure=new IllegalStateException("original-native-bag-failure");
        try { invoke(bag,cap,inv,a,new ItemStack("projecte:repair_talisman"));throw new AssertionError("missing native failure"); }
        catch (IllegalStateException thrown) {check(thrown==cap.failure,"native callback exception remains original");}
        check(Aia2MachineGuard.currentTickOwner()==parent,"bag finally restores caller after native exception");cap.failure=null;
        var client=new Level();client.client=true;
        check(invoke(bag,cap,inv,new Player(client),new ItemStack("projecte:repair_talisman")),"client bag callback remains native visual behavior");
        var receiver=tile(WORLD,POS,"projecte:alchemical_chest","a");cap.expectNull=false;cap.expected=receiver;
        var stable=new ItemStack("projecte:repair_talisman");
        check(invoke(chest,cap,WORLD,POS,stable,WORLD,POS,STATE,receiver)&&stable.count==0,"actual chest receiver authorizes and forwards passive callback");
        check(Aia2MachineGuard.currentTickOwner()==parent,"chest restores caller after success");
        var later=new ItemStack("fixture:future_capability");int before=cap.calls;
        check(!invoke(chest,cap,WORLD,POS,later,WORLD,POS,STATE,receiver)&&later.count==1&&cap.calls==before,"early chest cannot borrow late caller for future item");
        cap.changed=false;check(!invoke(chest,cap,WORLD,POS,new ItemStack("projecte:repair_talisman"),WORLD,POS,STATE,receiver)&&cap.calls==before+1,"native false result is preserved after an allowed callback");cap.changed=true;
        cap.failure=new IllegalArgumentException("original-native-chest-failure");
        try {invoke(chest,cap,WORLD,POS,new ItemStack("projecte:repair_talisman"),WORLD,POS,STATE,receiver);throw new AssertionError("missing native failure");}
        catch(IllegalArgumentException thrown){check(thrown==cap.failure,"chest native exception is not hidden as denial");}
        check(Aia2MachineGuard.currentTickOwner()==parent,"chest finally restores caller on failure");cap.failure=null;
        var replacement=tile(WORLD,POS,"projecte:alchemical_chest","late");
        check(!invoke(chest,cap,WORLD,POS,new ItemStack("projecte:repair_talisman"),WORLD,POS,STATE,receiver),"stale original chest cannot borrow replacement owner");
        WORLD.blocks.put(POS,receiver);
        check(!invoke(chest,cap,WORLD,POS,new ItemStack("projecte:repair_talisman"),WORLD,OTHER,STATE,receiver),"mismatched tick and callback position denied");
        check(!invoke(chest,cap,WORLD,POS,new ItemStack("projecte:repair_talisman"),client,POS,STATE,receiver),"mismatched tick and callback level denied");
        receiver.removed=true;check(!invoke(chest,cap,WORLD,POS,new ItemStack("projecte:repair_talisman"),WORLD,POS,STATE,receiver),"removed original receiver denied");receiver.removed=false;
        var unowned=tile(WORLD,POS,"projecte:alchemical_chest","");
        check(!invoke(chest,cap,WORLD,POS,new ItemStack("projecte:repair_talisman"),WORLD,POS,STATE,unowned),"unowned storage has no inferred nearby owner");
        var stand=tile(WORLD,POS,"projecte:dm_pedestal","a");cap.expected=stand;
        check(invoke(pedestal,cap,new ItemStack("projecte:repair_talisman"),WORLD,POS,stand,WORLD,POS,STATE,stand),"authorized pedestal callback runs with actual original owner");
        check(Aia2MachineGuard.currentTickOwner()==parent,"pedestal restores parent after success");
        var futureStand=new ItemStack("fixture:future_capability");before=cap.calls;
        check(!invoke(pedestal,cap,futureStand,WORLD,POS,stand,WORLD,POS,STATE,stand)&&futureStand.count==1&&cap.calls==before,"pedestal cannot activate imported future stack");
        check(!invoke(pedestal,cap,new ItemStack("projecte:repair_talisman"),WORLD,POS,stand,WORLD,POS,STATE,replacement),"pedestal call receiver must equal original static tile");
        var old=stand;stand=tile(WORLD,POS,"projecte:dm_pedestal","late");
        check(!invoke(pedestal,cap,new ItemStack("projecte:repair_talisman"),WORLD,POS,old,WORLD,POS,STATE,old),"stale pedestal cannot authorize through its replacement");
        cap.expected=stand;cap.failure=new IllegalStateException("original-native-pedestal-failure");
        try {invoke(pedestal,cap,new ItemStack("projecte:repair_talisman"),WORLD,POS,stand,WORLD,POS,STATE,stand);throw new AssertionError("missing failure");}
        catch(IllegalStateException thrown){check(thrown==cap.failure,"pedestal native failure remains original");}
        check(Aia2MachineGuard.currentTickOwner()==parent,"pedestal finally restores caller on failure");cap.failure=null;
        Aia2MachineGuard.policy.setTeamProgress("late",43);
        check(!invoke(pedestal,cap,new ItemStack("projecte:repair_talisman"),WORLD,POS,stand,WORLD,POS,STATE,stand),"progress downgrade pauses an already active pedestal without altering it");
        Aia2MachineGuard.policy.clear();
        check(!invoke(bag,cap,inv,a,new ItemStack("projecte:repair_talisman")),"unready bag access fails closed");
        check(!invoke(pedestal,cap,new ItemStack("projecte:repair_talisman"),WORLD,POS,stand,WORLD,POS,STATE,stand),"unready storage fails closed");
        check(!ProjectEStorageAccess.chest(cap,WORLD,POS,new ItemStack("projecte:repair_talisman"),null),"missing original tile denied");
        Aia2MachineGuard.exitTick(null);
        System.out.println("ProjectEStorageHarness: "+checks+" actual-helper/handler/real-policy assertions; modeled Minecraft/capabilities/parent-policy API, no optional ProjectE dispatch");
    }
}
