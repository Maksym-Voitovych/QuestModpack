package ua.aia2.guard.mixin;

import java.lang.reflect.Method;
import java.util.*;
import com.enderio.enderio.content.fire_crafting.FireCraftingRecipe;
import com.enderio.enderio.content.fire_crafting.FireCraftingRecipe.Result;
import net.minecraft.core.BlockPos;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.resources.ResourceKey;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.crafting.BaseRecipe;
import net.minecraft.world.item.crafting.Recipe;
import net.minecraft.world.item.crafting.RecipeHolder;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.state.BlockState;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;
import ua.aia2.guard.Aia2MachineGuard;
import ua.aia2.guard.FireWorksiteAccess;

/** Actual helper/handlers, real policy; Minecraft storage/optional recipe host modeled. */
public final class FireWorksiteHarness {
    private static int checks;
    private static final ServerLevel WORLD = new ServerLevel();
    private static final BlockPos BASE = new BlockPos(4,64,5), FIRE = new BlockPos(4,65,5);
    private static final Block BEDROCK = new Block("minecraft:bedrock"), AFTER = new Block("minecraft:cobblestone");
    private static final BlockState STATE = new BlockState(BEDROCK);
    private static final ResourceLocation ID = ResourceLocation.parse("enderio:fire_crafting/infinity");
    private static final Method REGISTER;
    static {
        try { REGISTER=FireWorksiteAccess.class.getDeclaredMethod("register",ServerLevel.class,BlockPos.class,String.class);REGISTER.setAccessible(true); }
        catch (Exception error) { throw new ExceptionInInitializerError(error); }
    }
    private static void check(boolean value,String reason) { checks++;if(!value)throw new AssertionError(reason); }
    private static void setupPolicy() {
        Aia2MachineGuard.policy.clear();
        Aia2MachineGuard.policy.setRules(Map.of("minecraft:bedrock",1));
        Aia2MachineGuard.policy.setTeamProgress("a",18);
        Aia2MachineGuard.policy.setTeamProgress("b",17);
        Aia2MachineGuard.policy.setReady();
        Aia2MachineGuard.items.put("enderio:grains_of_infinity",19);
        Aia2MachineGuard.items.put("minecraft:diamond",32);
        Aia2MachineGuard.items.put("botania:mana_tablet",5);
        Aia2MachineGuard.items.put("kubejs:aia2_tech_key_19",1);
        Aia2MachineGuard.items.put("kubejs:custom_trusted_key",1);
        Aia2MachineGuard.blocks.put("minecraft:cobblestone",1);
    }
    private static FireCraftingRecipe recipe(List<Result> outputs,Block after) {
        return new FireCraftingRecipe(outputs,List.of(BEDROCK),List.of(new ResourceKey<Level>("minecraft:overworld")),Optional.ofNullable(after));
    }
    private static Result result(String id,int min,int max,float chance) { return new Result(new ItemStack(id),min,max,chance); }
    private static FireCraftingRecipe valid() {return recipe(List.of(result("enderio:grains_of_infinity",1,3,0.75f)),null);}
    private static void install(FireCraftingRecipe recipe) {
        WORLD.recipes.rows.clear();WORLD.recipes.rows.put(ID,new RecipeHolder<>(ID,recipe));
        WORLD.recipes.generation=new Object();Aia2MachineGuard.recipes.put(recipe,19);
    }
    private static boolean register(String team) throws Exception {return (boolean)REGISTER.invoke(null,WORLD,BASE,team);}
    private static boolean run(FireCraftingRecipe recipe) {return FireWorksiteAccess.maySpawn(WORLD,FIRE,recipe);}
    private static void denied(FireCraftingRecipe recipe,String why) { install(recipe);check(!run(recipe),why); }

    public static void main(String[] args) throws Exception {
        setupPolicy();WORLD.blocks.put(BASE.asLong(),STATE);
        BuiltInRegistries.RECIPE_TYPE.rows.put(ResourceLocation.parse("enderio:fire_crafting"),FireCraftingRecipe.TYPE);
        var first=valid();install(first);
        check(FireWorksiteAccess.isWorksiteBase(WORLD,BASE),"native base/dimension should be recognized before claim");
        check(!run(first),"natural or imported fire must not mint a worksite");
        check(!register("b"),"team before19 cannot register production site");
        FireWorksiteAccess.claim(new ServerPlayer(WORLD,"a"),BASE);
        check(run(first),"explicit real-player claim at19 preserves mandatory grain route");
        check(!register("b"),"site cannot be stolen by another team");
        Aia2MachineGuard.policy.setTeamProgress("a",17);
        check(!run(first),"live team rollback rechecks epoch floor");
        Aia2MachineGuard.policy.setTeamProgress("a",18);
        check(run(first),"progress restored without deleting claimed worksite");
        WORLD.dimension=new ResourceKey<>("minecraft:the_nether");
        check(!run(first),"explicit worksite must still match recipe dimension");
        WORLD.dimension=new ResourceKey<>("minecraft:overworld");
        WORLD.blocks.put(BASE.asLong(),new BlockState(new Block("minecraft:stone")));
        check(!run(first),"changed base state cannot use old site receipt");
        WORLD.blocks.put(BASE.asLong(),STATE);
        check(run(first),"fixture restored exact original state");

        denied(recipe(List.of(result("enderio:grains_of_infinity",1,1,1),result("minecraft:diamond",1,1,0.001f)),null),"even rare future secondary output denied");
        var ignored=recipe(List.of(result("enderio:grains_of_infinity",1,1,1),result("minecraft:diamond",1,1,0)),null);
        install(ignored);check(run(ignored),"zero-probability secondary result cannot produce a future item");
        denied(recipe(List.of(result("enderio:grains_of_infinity",0,0,1)),null),"no realizable result must not authorize native mutation");
        denied(recipe(List.of(result("enderio:grains_of_infinity",-1,1,1)),null),"negative count bounds denied before RNG");
        denied(recipe(List.of(result("enderio:grains_of_infinity",3,2,1)),null),"inverted count bounds denied before RNG");
        denied(recipe(List.of(result("enderio:grains_of_infinity",1,65,1)),null),"oversized result stack denied");
        denied(recipe(List.of(result("enderio:grains_of_infinity",1,1,Float.NaN)),null),"NaN chance fails closed");
        denied(recipe(List.of(result("enderio:grains_of_infinity",1,1,Float.POSITIVE_INFINITY)),null),"infinite chance fails closed");
        denied(recipe(List.of(result("enderio:grains_of_infinity",1,1,-0.01f)),null),"negative chance fails closed");
        denied(recipe(List.of(result("enderio:grains_of_infinity",1,1,1.01f)),null),"chance above1 fails closed");
        denied(recipe(List.of(new Result(ItemStack.EMPTY,0,0,0)),null),"malformed empty result fails closed");
        denied(recipe(List.of(result("kubejs:aia2_tech_key_19",1,1,1)),null),"epoch key pattern cannot bypass manufacturing receipt");
        denied(recipe(List.of(result("kubejs:custom_trusted_key",1,1,1)),null),"configured key also cannot be fire-produced");
        denied(recipe(List.of(result("unknown:unclassified_item",1,1,1)),null),"unclassified item fails closed");
        var tablet=new ItemStack("botania:mana_tablet");tablet.creative=true;
        var creative=recipe(List.of(new Result(tablet,1,1,1)),null);
        denied(creative,"creative component checked even when ordinary item is early");
        Aia2MachineGuard.policy.setTeamProgress("a",48);check(run(creative),"creative component allowed only after completed48");
        Aia2MachineGuard.policy.setTeamProgress("a",18);
        var post=recipe(List.of(result("enderio:grains_of_infinity",1,1,1)),AFTER);
        install(post);check(run(post),"accessible base-after-burning remains native route");
        Aia2MachineGuard.blocks.put(AFTER.id,32);check(!run(post),"base mutation cannot manufacture future block");
        Aia2MachineGuard.blocks.put(AFTER.id,1);

        var old=valid();install(old);check(run(old),"current canonical recipe accepted");
        var listBefore=FireWorksiteAccess.recipes(WORLD);
        var changed=recipe(List.of(result("minecraft:diamond",1,1,1)),null);install(changed);
        check(!run(old),"same-ID old object rejected after manager snapshot reload");
        check(!run(changed),"replacement cannot retain old allowed output definition");
        check(FireWorksiteAccess.recipes(WORLD).get(0).value()==changed,"same manager reload refreshes list");
        check(listBefore.get(0).value()==old,"cached returned snapshot stays immutable");
        WORLD.recipes.rows.clear();WORLD.recipes.generation=new Object();
        check(FireWorksiteAccess.recipes(WORLD).isEmpty(),"removed native recipe disappears from custom list");
        check(!run(changed),"removed recipe not authorized via lingering reference");
        var unclassified=valid();install(unclassified);Aia2MachineGuard.recipes.remove(unclassified);
        check(!run(unclassified),"canonical recipe still needs explicit recipe policy");
        install(first);WORLD.server.sameThread=false;
        check(!run(first),"off-thread invocation denied");WORLD.server.sameThread=true;
        Aia2MachineGuard.policy.clear();check(!run(first),"not-ready guard never authorizes native output");setupPolicy();
        check(!FireWorksiteAccess.maySpawn(new Level(),FIRE,first),"client/non-server world denied");
        var counterfeit=new BaseRecipe(new com.google.gson.JsonObject());counterfeit.type=FireCraftingRecipe.TYPE;
        WORLD.recipes.rows.put(ID,new RecipeHolder<>(ID,counterfeit));WORLD.recipes.generation=new Object();
        Aia2MachineGuard.recipes.put(counterfeit,19);
        check(!FireWorksiteAccess.maySpawn(WORLD,FIRE,counterfeit),"wrong runtime recipe class cannot claim reflection contract");

        install(first);
        Method spawn=EnderFireCraftingMixin.class.getDeclaredMethod("aia2$ownedWorksite",Level.class,BlockPos.class,Object.class,CallbackInfo.class);spawn.setAccessible(true);
        var accepted=new CallbackInfo();spawn.invoke(null,WORLD,FIRE,first,accepted);check(!accepted.canceled,"common spawn edge accepts legit site");
        var wrong=new CallbackInfo();spawn.invoke(null,WORLD,FIRE,new Object(),wrong);check(wrong.canceled,"common spawn edge rejects nonrecipe object");
        WORLD.blocks.put(BASE.asLong(),new BlockState(BEDROCK));
        var denied=new CallbackInfo();spawn.invoke(null,WORLD,FIRE,first,denied);check(denied.canceled,"common spawn edge cannot use stale base receipt");WORLD.blocks.put(BASE.asLong(),STATE);
        Method list=EnderFireCraftingMixin.class.getDeclaredMethod("aia2$currentRecipes",Level.class,CallbackInfoReturnable.class);list.setAccessible(true);
        var receiver=new EnderFireCraftingMixin(){};
        var response=new CallbackInfoReturnable<List<?>>();list.invoke(receiver,WORLD,response);
        check(response.canceled&&response.getReturnValue().size()==1,"server list handler replaces broken native generation cache");
        check(((RecipeHolder<?>)response.getReturnValue().get(0)).value()==first,"server list is raw current recipes, not owner-filtered");
        var clientResponse=new CallbackInfoReturnable<List<?>>();list.invoke(receiver,new Level(),clientResponse);
        check(!clientResponse.canceled,"client recipe lookup remains native");
        System.out.println("FireWorksiteHarness: "+checks+" actual-helper/handler/real-policy assertions; modeled Minecraft/storage and optional recipe host, no optional EnderIO dispatch");
    }
}
