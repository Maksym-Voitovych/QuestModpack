package ua.aia2.guard.mixin;

import java.lang.reflect.Method;
import java.util.*;
import moze_intel.projecte.api.proxy.IEMCProxy;
import moze_intel.projecte.gameObjs.container.TransmutationContainer;
import moze_intel.projecte.gameObjs.container.inventory.TransmutationInventory;
import moze_intel.projecte.gameObjs.container.slots.transmutation.SlotOutput;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.inventory.*;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;
import net.neoforged.neoforge.common.util.FakePlayer;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;
import ua.aia2.guard.Aia2MachineGuard;
import ua.aia2.guard.ProjectEAccess;

/** Actual helpers and handlers; optional menus/EMC API/MC host modeled. */
public final class ProjectEOutputHarness {
    static int checks;
    static final Level WORLD=new Level();
    static final ServerPlayer OWNER=new ServerPlayer(WORLD,"a");
    static final IEMCProxy.Mutable EMC=(IEMCProxy.Mutable)IEMCProxy.INSTANCE;
    static final String CONFIG="{\"minecraft:iron_ingot\":256,\"minecraft:gold_ingot\":2048}";
    static final ItemStack IRON=new ItemStack("minecraft:iron_ingot");
    static final class QuickHost extends ProjectETransmutationMixin implements AbstractContainerMenu{}
    static final class ChildMenu extends TransmutationContainer{ChildMenu(){}ChildMenu(TransmutationInventory inv){super(inv);}}
    static final class ChildSlot extends SlotOutput { ChildSlot(TransmutationInventory i,ItemStack s){super(i,s);} }
    static void check(boolean condition,String why){checks++;if(!condition)throw new AssertionError(why);}
    static void policy(){Aia2MachineGuard.policy.clear();Aia2MachineGuard.policy.setRules(Map.of("minecraft:iron_ingot",0,"minecraft:gold_ingot",0,"future:crystal",47,"kubejs:configured_key",1,"kubejs:aia2_tech_key_45",1,"projecte:transmutation_tablet",47));Aia2MachineGuard.policy.setTeamProgress("a",44);Aia2MachineGuard.policy.setTeamProgress("b",0);Aia2MachineGuard.policy.setReady();}
    static void config(){EMC.values.clear();EMC.values.put("minecraft:iron_ingot",256L);EMC.values.put("minecraft:gold_ingot",2048L);EMC.values.put("future:crystal",1234L);EMC.throwsError=false;ProjectEAccess.configureWhitelistJson(CONFIG);}
    static void invalid(String json,String why){boolean rejected=false;try{ProjectEAccess.configureWhitelistJson(json);}catch(RuntimeException expected){rejected=true;}check(rejected,why);check(!ProjectEAccess.mayExtract(OWNER,IRON),"invalid config pauses old ready outputs");config();}
    static Method method(Class<?> owner,String name,Class<?>...args)throws Exception{var m=owner.getDeclaredMethod(name,args);m.setAccessible(true);return m;}

    static void quickChecks()throws Exception {
        var inv=new TransmutationInventory(OWNER);var menu=new ChildMenu(inv);OWNER.containerMenu=menu;
        var slot=new SlotOutput(inv,IRON);Method move=method(ProjectETransmutationMixin.class,"aia2$guardQuickMove",Player.class,int.class,CallbackInfoReturnable.class);
        Aia2MachineGuard.policy.setTeamProgress("a",43);var blocked=new CallbackInfoReturnable<ItemStack>();move.invoke(menu,OWNER,11,blocked);check(blocked.canceled&&blocked.getReturnValue()==ItemStack.EMPTY,"quick-move HEAD rejects old privilege before native inventory/EMC mutation");
        Aia2MachineGuard.policy.setTeamProgress("a",44);AbstractContainerMenu.slots.clear();for(int i=0;i<27;i++)AbstractContainerMenu.slots.add(slot);
        var good=new CallbackInfoReturnable<ItemStack>();move.invoke(menu,OWNER,11,good);check(!good.canceled,"quick-move preserves valid current output");
        var variant=new ItemStack("minecraft:iron_ingot");variant.modified=true;slot.stack=variant;var bad=new CallbackInfoReturnable<ItemStack>();move.invoke(menu,OWNER,11,bad);check(bad.canceled,"quick-move rejects raw modified components");slot.stack=IRON;
        EMC.values.put("minecraft:iron_ingot",0L);var zero=new CallbackInfoReturnable<ItemStack>();move.invoke(menu,OWNER,11,zero);check(zero.canceled,"quick-move rejects stale zero-EMC output");config();
        AbstractContainerMenu.slots.clear();var missing=new CallbackInfoReturnable<ItemStack>();move.invoke(menu,OWNER,26,missing);check(missing.canceled,"quick-move rejects output beyond actual menu size");
        var input=new CallbackInfoReturnable<ItemStack>();move.invoke(menu,OWNER,1,input);check(!input.canceled,"authorized input transfer remains native");
        menu.tablet(new ItemStack("projecte:transmutation_tablet"));var tablet=new CallbackInfoReturnable<ItemStack>();move.invoke(menu,OWNER,1,tablet);check(tablet.canceled,"tablet47 cannot use table45 quickmove");
        System.out.println("ProjectEOutputHarness quick: "+checks+" actual-helper/handler/real-policy assertions; modeled Minecraft/EMC/menu, no optional ProjectE dispatch");
    }

    public static void main(String[]args)throws Exception {
        policy();BuiltInRegistries.ITEM.known.addAll(Set.of("minecraft:iron_ingot","minecraft:gold_ingot","future:crystal","kubejs:configured_key","kubejs:aia2_tech_key_45","projecte:transmutation_tablet"));
        if(args.length>0){config();quickChecks();return;}
        check(!ProjectEAccess.mayUseMenu(OWNER),"initial EMC API policy not configured");config();
        check(ProjectEAccess.mayUseMenu(OWNER),"completed44 grants epoch45 menu access");
        check(ProjectEAccess.mayExtract(OWNER,IRON),"current plain whitelisted positive-value output available");
        Aia2MachineGuard.policy.setTeamProgress("a",43);check(!ProjectEAccess.mayUseMenu(OWNER),"live stage downgrade revokes already open menu");check(!ProjectEAccess.mayExtract(OWNER,IRON),"normal extraction rechecks current stage");Aia2MachineGuard.policy.setTeamProgress("a",44);
        OWNER.live="b";check(!ProjectEAccess.mayUseMenu(OWNER),"changed live team cannot retain old synchronized privilege");OWNER.live="a";
        OWNER.synced="";check(!ProjectEAccess.mayUseMenu(OWNER),"unsynchronized player is denied");OWNER.synced="a";
        check(!ProjectEAccess.mayUseMenu(new FakePlayer(WORLD,"a")),"fake player cannot use old transmutation knowledge");
        check(!ProjectEAccess.mayUseMenu(new Player(WORLD)),"nonserver player on server world fails closed");check(!ProjectEAccess.mayUseMenu(null),"missing player fails closed");
        Level client=new Level();client.client=true;Player clientPlayer=new Player(client);check(ProjectEAccess.mayUseMenu(clientPlayer),"client prediction stays native");check(ProjectEAccess.mayExtract(clientPlayer,IRON),"server gate does not remove client preview");
        check(!ProjectEAccess.mayExtract(OWNER,ItemStack.EMPTY),"empty output denied");check(!ProjectEAccess.mayExtract(OWNER,null),"missing output denied");
        ItemStack variant=new ItemStack("minecraft:iron_ingot");variant.modified=true;check(!ProjectEAccess.mayExtract(OWNER,variant),"raw modified component variant cannot use item-only EMC");
        check(!ProjectEAccess.mayExtract(OWNER,new ItemStack("future:crystal")),"positive EMC alone cannot admit excluded future item");
        EMC.values.put("minecraft:iron_ingot",0L);check(!ProjectEAccess.mayExtract(OWNER,IRON),"cached zero-EMC output denied instead of native free output");
        EMC.values.put("minecraft:iron_ingot",257L);check(!ProjectEAccess.mayExtract(OWNER,IRON),"different current EMC cannot reuse old whitelist price");
        EMC.values.put("minecraft:iron_ingot",256L);EMC.throwsError=true;check(!ProjectEAccess.mayExtract(OWNER,IRON),"reflection invocation/API failures fail closed");EMC.throwsError=false;
        ProjectEAccess.pause();check(!ProjectEAccess.mayUseMenu(OWNER),"remap pause revokes stale menus before EMC changes");check(!ProjectEAccess.mayExtract(OWNER,IRON),"remap pause revokes stale slot results");config();
        invalid("[]","array-shaped whitelist rejected");invalid("{}","empty whitelist rejected");invalid("{\"minecraft:iron_ingot\":0}","zero EMC rejected");invalid("{\"minecraft:iron_ingot\":1.5}","fractional EMC rejected");invalid("{\"minecraft:iron_ingot\":\"256\"}","numeric string rejected");invalid("{\"minecraft:iron_ingot\":true}","boolean EMC rejected");invalid("{\"missing:item\":1}","unregistered item rejected");invalid("{\"minecraft:iron_ingot\":9007199254740992}","unsafe Rhino numeric integer rejected");invalid("{\"kubejs:configured_key\":1}","configured manufacture key cannot be whitelisted");invalid("{\"kubejs:aia2_tech_key_45\":1}","epoch key pattern cannot be whitelisted");
        var inv=new TransmutationInventory(OWNER);var attached=new ChildMenu(inv);OWNER.containerMenu=attached;var slot=new SlotOutput(inv,IRON);check(ProjectEAccess.mayExtractSlot(slot,IRON),"slot reads exact private native inventory/player");check(ProjectEAccess.mayExtractSlot(new ChildSlot(inv,IRON),IRON),"inherited output inventory field resolved correctly");check(!ProjectEAccess.mayExtractSlot(new Object(),IRON),"unknown slot API fails closed");
        OWNER.containerMenu=new ChildMenu(new TransmutationInventory(OWNER));check(!ProjectEAccess.mayExtractSlot(slot,IRON),"detached old slot cannot charge the active menu's owner");OWNER.containerMenu=attached;
        attached.tablet(new ItemStack("projecte:transmutation_tablet"));check(!ProjectEAccess.mayUseContainer(OWNER,attached),"tablet requires47 even when placed table45 is available");check(!ProjectEAccess.mayExtractSlot(slot,IRON),"tablet output cannot borrow placed-table floor");
        Aia2MachineGuard.policy.setTeamProgress("a",46);check(ProjectEAccess.mayExtractSlot(slot,IRON),"tablet47 output resumes only after its own stage");Aia2MachineGuard.policy.setTeamProgress("a",44);attached.tablet(ItemStack.EMPTY);
        check(ProjectEAccess.mayExtractSlot(slot,IRON),"same inventory association works after switching back to physical table");
        Method remove=method(ProjectEOutputSlotMixin.class,"aia2$currentEmc",int.class,CallbackInfoReturnable.class);
        var allowed=new CallbackInfoReturnable<ItemStack>();remove.invoke(slot,1,allowed);check(!allowed.canceled,"actual remove HEAD preserves native valid extraction");
        var zero=new CallbackInfoReturnable<ItemStack>();remove.invoke(slot,0,zero);check(zero.canceled&&zero.getReturnValue()==ItemStack.EMPTY,"zero-amount remove rejected before native EMC mutation");
        EMC.values.put("minecraft:iron_ingot",0L);var stale=new CallbackInfoReturnable<ItemStack>();remove.invoke(slot,1,stale);check(stale.canceled&&stale.getReturnValue()==ItemStack.EMPTY,"actual remove HEAD stops zero-EMC stale output");config();
        var menu=new ChildMenu();check(ProjectEAccess.isTransmutation(menu),"inherited transmutation menu identity detected");check(!ProjectEAccess.isTransmutation(new HandMixinHost()),"unrelated hand menus retain their own behavior");
        Method valid=method(ProjectEHandMenuMixin.class,"aia2$currentMenuOwner",Player.class,CallbackInfoReturnable.class);
        Method click=method(ProjectEHandMenuMixin.class,"aia2$guardClick",int.class,int.class,ClickType.class,Player.class,CallbackInfo.class);
        var validResult=new CallbackInfoReturnable<Boolean>();valid.invoke(menu,OWNER,validResult);check(!validResult.canceled,"actual inherited stillValid allows native conditions when authorized");
        Aia2MachineGuard.policy.setTeamProgress("a",43);var deniedValid=new CallbackInfoReturnable<Boolean>();valid.invoke(menu,OWNER,deniedValid);check(deniedValid.canceled&&Boolean.FALSE.equals(deniedValid.getReturnValue()),"inherited stillValid closes stale placed-table menu");
        var deniedClick=new CallbackInfo();click.invoke(menu,11,0,ClickType.PICKUP,OWNER,deniedClick);check(deniedClick.canceled,"actual click HEAD stops menu action before native effects");
        var unrelated=new CallbackInfoReturnable<Boolean>();valid.invoke(new HandMixinHost(),OWNER,unrelated);check(!unrelated.canceled,"unrelated PE hand menu is not accidentally closed");
        Aia2MachineGuard.policy.clear();check(!ProjectEAccess.mayUseMenu(OWNER),"native bridge readiness loss closes current menu");
        System.out.println("ProjectEOutputHarness: "+checks+" actual-helper/handler/real-policy assertions; modeled Minecraft/EMC/menus, no optional ProjectE dispatch or knowledge deletion claim");
    }
}
