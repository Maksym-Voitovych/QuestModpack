package ua.aia2.guard.mixin;

import java.lang.reflect.*;
import java.util.Map;
import java.util.function.BiPredicate;
import net.minecraft.core.BlockPos;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.context.UseOnContext;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.neoforged.neoforge.common.util.FakePlayer;
import net.neoforged.neoforge.network.handling.IPayloadContext;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;
import moze_intel.projecte.gameObjs.container.TransmutationContainer;
import ua.aia2.guard.Aia2MachineGuard;
import ua.aia2.guard.ProjectEAccess;
import ua.aia2.guard.ProjectEPassiveAccess;

/** Actual production helper/handler methods; Minecraft packet/world hosts are modeled. */
public final class ProjectEWorldHarness {
    private static int checks;
    private static final ServerLevel WORLD=new ServerLevel();
    private static final String TABLET="projecte:transmutation_tablet",STONE="projecte:philosophers_stone";
    private static final ItemStack stone=new ItemStack(STONE),tablet=new ItemStack(TABLET);
    private static final ServerPlayer early=new ServerPlayer(WORLD,"early"),a=new ServerPlayer(WORLD,"a"),late=new ServerPlayer(WORLD,"late");
    private static void check(boolean value,String reason){checks++;if(!value)throw new AssertionError(reason);}
    private static void policy(){
        Aia2MachineGuard.policy.clear();
        Aia2MachineGuard.policy.setRules(Map.of(TABLET,47,STONE,45,"projecte:fixture_unstaged",0,
                "projecte:repair_talisman",45,"fixture:future_capability",47,"projecte:alchemical_chest",45,"minecraft:stick",0));
        Aia2MachineGuard.policy.setTeamProgress("early",0);Aia2MachineGuard.policy.setTeamProgress("a",44);Aia2MachineGuard.policy.setTeamProgress("late",46);
        Aia2MachineGuard.policy.setReady();
    }
    private static Method method(Class<?> type,String name,Class<?>... args)throws Exception{var m=type.getDeclaredMethod(name,args);m.setAccessible(true);return m;}
    private static void invoke(Method m,Object target,Object...args)throws Exception{
        try{m.invoke(target,args);}catch(InvocationTargetException failure){if(failure.getCause()instanceof RuntimeException original)throw original;throw failure;}
    }
    private static final class GemModeHost extends ProjectEGemModeMixin{}
    private static final GemModeHost mode=new GemModeHost();
    private static CallbackInfoReturnable<Boolean> key(Method key,Player player,ItemStack stack)throws Exception{
        var callback=new CallbackInfoReturnable<Boolean>();invoke(key,null,player,stack,InteractionHand.MAIN_HAND,new Object(),new Object(),callback);return callback;
    }
    public static void main(String[]args)throws Exception{
        policy();ProjectEAccess.clearMenuSources();BuiltInRegistries.ITEM.known.add("minecraft:stick");
        ProjectEAccess.configureWhitelistJson("{\"minecraft:stick\":1}");
        check(ProjectEPassiveAccess.isProjectE(stone),"namespace matched from actual item registry key");
        check(!ProjectEPassiveAccess.isProjectE(ItemStack.EMPTY)&&!ProjectEPassiveAccess.isProjectE(null),"empty/null not ProjectE");
        check(!ProjectEPassiveAccess.isProjectE(new ItemStack("fixture:projecte")),"path name cannot impersonate namespace");
        check(!ProjectEPassiveAccess.mayUse(early,stone),"actual personal team below45 denied");
        check(ProjectEPassiveAccess.mayUse(a,stone),"actual synchronized personal45 allowed");
        check(!ProjectEPassiveAccess.mayUse(a,tablet)&&ProjectEPassiveAccess.mayUse(late,tablet),"tablet tier47 checked independently of common45");
        check(!ProjectEPassiveAccess.mayUse(early,new ItemStack("projecte:fixture_unstaged")),"ProjectE base floor45 protects unclassified lower native item");
        check(ProjectEPassiveAccess.mayUse(early,new ItemStack("minecraft:stick")),"unrelated vanilla item retains itempolicy behavior");
        check(!ProjectEPassiveAccess.mayUse(a,new ItemStack("fixture:future_capability")),"addon future capability floor cannot borrow base45");
        check(!ProjectEPassiveAccess.mayUse(new FakePlayer(WORLD,"late"),stone),"FakePlayer denied personal activation");
        check(!ProjectEPassiveAccess.mayUse(new Player(WORLD),stone),"nonserver player denied on server");
        check(!ProjectEPassiveAccess.mayUse(null,stone)&&!ProjectEPassiveAccess.mayUse(a,null)&&!ProjectEPassiveAccess.mayUse(a,ItemStack.EMPTY),"null actor/stack and empty fail closed");
        a.live="late";check(!ProjectEPassiveAccess.mayUse(a,stone),"stale synchronized team cannot retain personal access");a.live="a";
        a.synced="";check(!ProjectEPassiveAccess.mayUse(a,stone),"unsynchronized personal player fails closed");a.synced="a";
        Aia2MachineGuard.policy.setTeamProgress("a",43);check(!ProjectEPassiveAccess.mayUse(a,stone),"current stage downgrade takes effect without stack mutation");Aia2MachineGuard.policy.setTeamProgress("a",44);
        var client=new Level();client.client=true;check(ProjectEPassiveAccess.mayUse(new Player(client),stone),"client prediction remains native; no server permission claim");
        check(!ProjectEPassiveAccess.mayUseEntity(new Entity(WORLD),stone),"nonplayer carrier cannot use personal effect");

        var tick=method(ProjectEItemStackUseMixin.class,"aia2$wearerTick",Level.class,Entity.class,int.class,boolean.class,CallbackInfo.class);
        var world=method(ProjectEItemStackUseMixin.class,"aia2$worldUse",UseOnContext.class,CallbackInfoReturnable.class);
        var deniedTick=new CallbackInfo();invoke(tick,stone,WORLD,early,0,false,deniedTick);
        check(deniedTick.canceled&&stone.count==1&&!stone.modified,"inventory denial cancels callback and preserves stack data");
        var allowedTick=new CallbackInfo();invoke(tick,stone,WORLD,a,0,false,allowedTick);check(!allowedTick.canceled,"authorized inventory callback remains native");
        var mobTick=new CallbackInfo();invoke(tick,stone,WORLD,new Entity(WORLD),0,false,mobTick);check(mobTick.canceled,"unattributed server inventory effect denied");
        var clientTick=new CallbackInfo();invoke(tick,stone,client,new Entity(client),0,false,clientTick);check(!clientTick.canceled,"client visual inventory callback remains native");
        var ordinary=new ItemStack("minecraft:stick");var vanillaTick=new CallbackInfo();invoke(tick,ordinary,WORLD,early,0,false,vanillaTick);check(!vanillaTick.canceled,"generic hook does not block non-ProjectE inventory");
        var denyWorld=new CallbackInfoReturnable<InteractionResult>();invoke(world,stone,new UseOnContext(WORLD,early),denyWorld);check(denyWorld.canceled&&denyWorld.getReturnValue()==InteractionResult.FAIL,"world use denied with FAIL before native mutation");
        var nullWorld=new CallbackInfoReturnable<InteractionResult>();invoke(world,stone,new UseOnContext(WORLD,null),nullWorld);check(nullWorld.canceled,"nullable-player PhilosopherStone automation denied");
        var fakeWorld=new CallbackInfoReturnable<InteractionResult>();invoke(world,stone,new UseOnContext(WORLD,new FakePlayer(WORLD,"late")),fakeWorld);check(fakeWorld.canceled,"fake world use denied");
        var allowWorld=new CallbackInfoReturnable<InteractionResult>();invoke(world,stone,new UseOnContext(WORLD,a),allowWorld);check(!allowWorld.canceled,"authorized world use native");
        var clientWorld=new CallbackInfoReturnable<InteractionResult>();invoke(world,stone,new UseOnContext(client,new Player(client)),clientWorld);check(!clientWorld.canceled,"client use native");
        var vanillaWorld=new CallbackInfoReturnable<InteractionResult>();invoke(world,ordinary,new UseOnContext(WORLD,early),vanillaWorld);check(!vanillaWorld.canceled,"unrelated vanilla world use untouched");

        var supply=method(ProjectEHotbarPredicateMixin.class,"aia2$usableSupply",BiPredicate.class,Object.class,Object.class);
        int[]calls={0};BiPredicate<Player,ItemStack> predicate=(p,s)->{calls[0]++;return true;};
        check(!(boolean)supply.invoke(null,predicate,early,stone)&&calls[0]==0,"locked hotbar/Curios candidate never satisfies native supply predicate");
        check((boolean)supply.invoke(null,predicate,a,stone)&&calls[0]==1,"allowed actual candidate reaches native predicate once");
        check(!(boolean)supply.invoke(null,predicate,new Object(),stone)&&calls[0]==1,"unknown actor does not reach native predicate");
        check(!(boolean)supply.invoke(null,(BiPredicate<Player,ItemStack>)(p,s)->false,a,stone),"native false predicate result preserved");
        var key=method(ProjectEKeyCapabilityMixin.class,"aia2$actualHeldItem",Player.class,ItemStack.class,InteractionHand.class,Object.class,Object.class,CallbackInfoReturnable.class);
        var deniedKey=key(key,early,stone);check(deniedKey.canceled&&!deniedKey.getReturnValue(),"direct key capability denied before processor");
        check(!key(key,a,stone).canceled,"authorized key callback proceeds natively");
        check(key(key,a,tablet).canceled&&!key(key,late,tablet).canceled,"actual packet stack tier used independently of current mainhand");
        var volley=method(ProjectEArchangelMixin.class,"aia2$directVolley",ItemStack.class,Player.class,CallbackInfo.class);
        var deniedVolley=new CallbackInfo();invoke(volley,null,stone,early,deniedVolley);check(deniedVolley.canceled,"direct Archangel volley packet cannot bypass capability gate");
        var allowedVolley=new CallbackInfo();invoke(volley,null,stone,a,allowedVolley);check(!allowedVolley.canceled,"authorized direct volley remains native");
        var hand=ProjectEGemModeMixin.class.getDeclaredField("hand");hand.setAccessible(true);hand.set(mode,InteractionHand.OFF_HAND);
        var gem=method(ProjectEGemModeMixin.class,"aia2$modeMutation",IPayloadContext.class,CallbackInfo.class);
        a.main=stone;a.off=tablet;var deniedGem=new CallbackInfo();invoke(gem,mode,(IPayloadContext)()->a,deniedGem);check(deniedGem.canceled&&!tablet.modified&&tablet.count==1,"gem mutation uses packet hand and preserves locked data");
        a.off=stone;var allowedGem=new CallbackInfo();invoke(gem,mode,(IPayloadContext)()->a,allowedGem);check(!allowedGem.canceled,"authorized packet hand mode remains native");

        var pos=new BlockPos(1,64,2);var tile=new BlockEntity(WORLD,pos,"projecte:alchemical_chest","a");WORLD.blocks.put(pos,tile);
        check(ProjectEPassiveAccess.mayUseStored(tile,stone),"canonical loaded same-thread actual storage owner allowed");
        check(!ProjectEPassiveAccess.mayUseStored(tile,tablet),"stored item future floor cannot borrow chest floor");
        tile.removed=true;check(!ProjectEPassiveAccess.mayUseStored(tile,stone),"removed receiver denied");tile.removed=false;
        WORLD.loaded=false;check(!ProjectEPassiveAccess.mayUseStored(tile,stone),"unloaded receiver denied without loading chunk");WORLD.loaded=true;
        WORLD.server.sameThread=false;check(!ProjectEPassiveAccess.mayUseStored(tile,stone),"off-thread receiver denied");WORLD.server.sameThread=true;
        WORLD.blocks.put(pos,new BlockEntity(WORLD,pos,"projecte:alchemical_chest","late"));check(!ProjectEPassiveAccess.mayUseStored(tile,stone),"replaced old receiver cannot borrow replacement privileges");WORLD.blocks.put(pos,tile);
        check(!ProjectEPassiveAccess.mayUseStored(null,stone)&&!ProjectEPassiveAccess.mayUseStored(tile,ItemStack.EMPTY),"null receiver/empty stored item denied");
        var clientTile=new BlockEntity(client,pos,"projecte:alchemical_chest","late");check(!ProjectEPassiveAccess.mayUseStored(clientTile,stone),"storage authorization is serverworld only");

        var physical=new TransmutationContainer();a.containerMenu=physical;
        check(ProjectEAccess.mayUseContainer(a,physical),"physical handnull table available at45");
        var curio=new TransmutationContainer();a.nextMenu=curio;int opens=a.opens;
        check(ProjectEPassiveAccess.openTablet(tablet.getItem(),a,null,null).isEmpty()&&a.opens==opens&&a.containerMenu==physical,"Curios tablet47 denied before opening at45");
        late.containerMenu=physical;late.nextMenu=curio;
        check(ProjectEPassiveAccess.openTablet(tablet.getItem(),late,null,null).isPresent()&&late.containerMenu==curio,"actual tablet47 source opens through guarded helper");
        check(ProjectEAccess.mayUseContainer(late,curio),"new handnull tablet menu retains permitted47 origin");
        Aia2MachineGuard.policy.setTeamProgress("late",44);
        check(!ProjectEAccess.mayUseContainer(late,curio),"already-open Curios tablet closes on47-to45 downgrade");
        check(ProjectEAccess.mayUseContainer(late,physical),"same downgrade leaves actual physical table45 usable");
        ProjectEAccess.pause();check(!ProjectEAccess.mayUseContainer(late,curio),"EMC rebuilding pauses existing menus");
        ProjectEAccess.configureWhitelistJson("{\"minecraft:stick\":1}");check(!ProjectEAccess.mayUseContainer(late,curio),"remap preserves tablet origin floor rather than reclassifying handnull as table");
        policy();late.live="a";check(!ProjectEAccess.mayUseContainer(late,curio),"open tablet follows synchronized live membership");late.live="late";
        check(ProjectEAccess.mayUseContainer(late,curio),"restored actual stage/team reauthorizes existing menu");
        ProjectEAccess.markMenuSource(curio,45);Aia2MachineGuard.policy.setTeamProgress("late",44);check(!ProjectEAccess.mayUseContainer(late,curio),"later lower origin cannot downgrade recorded tablet tier");policy();
        late.emptyOpen=true;late.nextMenu=new TransmutationContainer();Object before=late.containerMenu;
        check(ProjectEPassiveAccess.openTablet(tablet.getItem(),late,null,null).isEmpty()&&late.containerMenu==before,"failed native menu open preserves original state");late.emptyOpen=false;
        var failure=new IllegalStateException("original-open-failure");late.openFailure=failure;
        try{ProjectEPassiveAccess.openTablet(tablet.getItem(),late,null,null);throw new AssertionError("missing native failure");}catch(IllegalStateException actual){check(actual==failure,"native open failure not silently rewritten as access denial");}late.openFailure=null;
        Aia2MachineGuard.policy.clear();check(!ProjectEPassiveAccess.mayUse(a,stone)&&!ProjectEPassiveAccess.mayUseStored(tile,stone),"reload unready state fails closed on personal and receiver paths");
        var unready=new CallbackInfo();invoke(tick,stone,WORLD,a,0,false,unready);check(unready.canceled,"already carried item paused immediately during guard reload");
        policy();ProjectEAccess.clearMenuSources();check(ProjectEAccess.mayUseContainer(a,physical),"source cleanup leaves physical table policy functional");
        System.out.println("ProjectEWorldHarness: "+checks+" actual-helper/handler/real-policy assertions; modeled Minecraft/world/packet hosts, no optional ProjectE dispatch");
    }
}
