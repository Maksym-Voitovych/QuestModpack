package ua.aia2.guard.mixin;

import java.lang.reflect.Method;
import java.util.Optional;
import net.minecraft.core.BlockPos;
import net.minecraft.core.RegistryAccess;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.SpawnEggItem;
import net.minecraft.world.item.crafting.Recipe;
import net.minecraft.world.level.block.entity.BlockEntity;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;
import ua.aia2.guard.Aia2MachineGuard;
import ua.aia2.guard.EvilCraftAccess;
import ua.aia2.guard.KeyProductionBridge;

/** Actual helpers and handlers; world/recipe hosts are modeled, optional weaving is not run. */
public class EvilCraftGuardHarness {
    static int checks;
    static void check(boolean value, String why) { checks++; if (!value) throw new AssertionError(why); }
    public static class Reanimator extends BlockEntity {
        public EntityType<?> type = new EntityType<>("minecraft:pig");
        public EntityType<?> getEntityType() { return type; }
    }
    record Formula(ItemStack output) implements Recipe<Object> {
        public ItemStack getResultItem(RegistryAccess access) { return output; }
    }
    public static void main(String[] args) throws Exception {
        String selected = args[0];
        ServerLevel world = new ServerLevel();
        Reanimator tile = new Reanimator();tile.level=world;world.tiles.put(tile.pos,tile);
        Aia2MachineGuard.BLOCKS.setRules(java.util.Map.of("evilcraft:blood_infuser",13));
        Aia2MachineGuard.ITEMS.setRules(java.util.Map.of("evilcraft:dark_power_gem",13,"minecraft:nether_star",30,"minecraft:pig_spawn_egg",13,"kubejs:aia2_tech_key_13",13,"minecraft:paper",0));
        Aia2MachineGuard.RECIPES.setRules(java.util.Map.of("evilcraft:infuse",13));
        for(var policy:java.util.List.of(Aia2MachineGuard.BLOCKS,Aia2MachineGuard.ITEMS,Aia2MachineGuard.RECIPES)) {
            policy.setReady();policy.setTeamProgress("a",12);policy.setTeamProgress("b",0);
        }
        Formula recipe = new Formula(new ItemStack("evilcraft:dark_power_gem"));
        Aia2MachineGuard.REGISTERED.put(recipe,"evilcraft:infuse");
        check(EvilCraftAccess.mayInfuse(tile,recipe),"current canonical owner may infuse");
        check(!EvilCraftAccess.mayOutput(tile,new ItemStack("minecraft:nether_star")),"actual future loot denied after machine unlocked");
        check(!EvilCraftAccess.mayOutput(tile,new ItemStack("kubejs:aia2_tech_key_13")),"key copying always denied");
        KeyProductionBridge.KEYS.add("minecraft:paper");
        check(!EvilCraftAccess.mayOutput(tile,new ItemStack("minecraft:paper")),"configured manufacture outputs cannot copy");
        KeyProductionBridge.KEYS.clear();
        Aia2MachineGuard.ready=false;
        check(!EvilCraftAccess.mayInfuse(tile,recipe),"reload readiness closes infusion");
        check(!EvilCraftAccess.mayOutput(tile,recipe.output()),"reload closes direct loot too");
        Aia2MachineGuard.ready=true;
        check(EvilCraftAccess.mayInfuse(tile,recipe),"same native cached value resumes after readiness");
        tile.team="b";
        check(!EvilCraftAccess.mayInfuse(tile,recipe),"receiving team's stage applies, not parent caller");
        tile.team="a";
        Aia2MachineGuard.REGISTERED.remove(recipe);
        check(!EvilCraftAccess.mayInfuse(tile,recipe),"stale native cache rejected after identity reload");
        Formula replacement=new Formula(new ItemStack("evilcraft:dark_power_gem"));
        Aia2MachineGuard.REGISTERED.put(replacement,"evilcraft:infuse");
        check(!EvilCraftAccess.mayInfuse(tile,recipe),"equal replacement never authorizes old identity");
        check(EvilCraftAccess.mayInfuse(tile,replacement),"new canonical value can resume unpaid selection");
        world.tiles.remove(tile.pos);
        check(!EvilCraftAccess.mayInfuse(tile,replacement),"detached tile rejected");
        world.tiles.put(tile.pos,tile);tile.removed=true;
        check(!EvilCraftAccess.mayInfuse(tile,replacement),"removed tile rejected");
        tile.removed=false;world.loaded=false;
        check(!EvilCraftAccess.mayInfuse(tile,replacement),"unloaded receiver rejected");
        world.loaded=true;world.server.sameThread=false;
        check(!EvilCraftAccess.mayInfuse(tile,replacement),"off-thread world callback rejected");
        world.server.sameThread=true;
        check(!EvilCraftAccess.mayInfuse(tile,null),"null cached recipe rejected");
        check(!EvilCraftAccess.mayOutput(tile,ItemStack.EMPTY),"empty native output rejected");
        ItemStack componentOutput=new ItemStack("evilcraft:dark_power_gem");componentOutput.components.put("creative",true);
        check(!EvilCraftAccess.mayOutput(tile,componentOutput),"actual component output is passed to component policy");
        SpawnEggItem.EGGS.put(tile.type,new SpawnEggItem("minecraft:pig_spawn_egg"));
        check(EvilCraftAccess.mayReanimate(tile),"native entity type resolves allowed egg");
        tile.type=new EntityType<>("no-egg");
        check(!EvilCraftAccess.mayReanimate(tile),"no egg prevents blood loss/box clear before native tick");
        tile.type=new EntityType<>("minecraft:pig");
        if(selected.equals("infuser")) {
            Method hook=EvilCraftInfuserMixin.class.getDeclaredMethod("aia2$guardInfusion",ItemStack.class,CallbackInfoReturnable.class);hook.setAccessible(true);
            Optional<?> raw=Optional.of(replacement);var result=new CallbackInfoReturnable<Optional<?>>(raw);
            tile.team="b";hook.invoke(tile,new ItemStack("minecraft:paper"),result);
            check(result.getReturnValue().isEmpty() && raw.get()==replacement,"denied view does not mutate raw SingleCache");
            tile.team="a";result=new CallbackInfoReturnable<>(raw);hook.invoke(tile,new ItemStack("minecraft:paper"),result);
            check(result.getReturnValue().get()==replacement,"unlock sees unchanged raw cached value");
            result=new CallbackInfoReturnable<>(Optional.empty());hook.invoke(tile,new ItemStack("minecraft:paper"),result);
            check(result.getReturnValue().isEmpty(),"empty native result remains empty");
        } else {
            Method hook=EvilCraftSpiritOutputMixin.class.getDeclaredMethod("aia2$guardSpiritLoot",ItemStack.class,CallbackInfo.class);hook.setAccessible(true);
            var result=new CallbackInfo();hook.invoke(tile,new ItemStack("minecraft:nether_star"),result);
            check(result.cancelled,"future actual loot insertion canceled");
            result=new CallbackInfo();hook.invoke(tile,replacement.output(),result);
            check(!result.cancelled,"allowed loot insertion remains native");
        }
        Method reanimate=EvilCraftReanimatorMixin.class.getDeclaredMethod("aia2$guardReanimation",Object.class,ItemStack.class,int.class,int.class,CallbackInfo.class);reanimate.setAccessible(true);
        Object action=new EvilCraftReanimatorMixin(){};
        var result=new CallbackInfo();reanimate.invoke(action,tile,new ItemStack("minecraft:paper"),0,10,result);
        check(!result.cancelled,"allowed native reanimation callback runs");
        tile.team="b";result=new CallbackInfo();reanimate.invoke(action,tile,new ItemStack("minecraft:paper"),0,10,result);
        check(result.cancelled,"locked reanimation canceled before blood/egg/box mutation");
        System.out.println("EvilCraftGuardHarness "+selected+": "+checks+" actual-helper/handler/real-policy modeled assertions PASS");
    }
}
