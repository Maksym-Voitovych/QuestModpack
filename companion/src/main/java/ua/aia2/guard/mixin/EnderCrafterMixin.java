package ua.aia2.guard.mixin;

import java.util.Queue;
import net.minecraft.core.HolderLookup;
import net.minecraft.core.NonNullList;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.crafting.CraftingRecipe;
import net.minecraft.world.item.crafting.RecipeHolder;
import net.minecraft.world.item.crafting.RecipeInput;
import net.minecraft.world.item.crafting.Recipe;
import net.minecraft.world.item.crafting.RecipeType;
import net.minecraft.world.item.crafting.RecipeManager;
import net.minecraft.world.level.Level;
import org.spongepowered.asm.mixin.Final;
import net.minecraft.world.level.block.entity.BlockEntity;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Pseudo;
import org.spongepowered.asm.mixin.Shadow;
import org.spongepowered.asm.mixin.Unique;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.Redirect;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;
import ua.aia2.guard.Aia2MachineGuard;
import ua.aia2.guard.EnderTaskAccess;

@Pseudo
@Mixin(targets="com.enderio.enderio.content.machines.crafter.CrafterBlockEntity",remap=false)
abstract class EnderCrafterMixin {
    @Shadow(remap=false) private RecipeHolder<?> recipe;
    @Shadow(remap=false) @Final private Queue<ItemStack> outputBuffer;
    @Unique private EnderTaskAccess.CraftPlan aia2$plan;

    @Redirect(method="updateRecipe()V",at=@At(value="INVOKE",target="Lnet/minecraft/world/item/crafting/RecipeManager;getRecipeFor(Lnet/minecraft/world/item/crafting/RecipeType;Lnet/minecraft/world/item/crafting/RecipeInput;Lnet/minecraft/world/level/Level;)Ljava/util/Optional;"),remap=false,require=1)
    private <I extends RecipeInput,T extends Recipe<I>> java.util.Optional<RecipeHolder<T>> aia2$ownLookup(
            RecipeManager manager,RecipeType<T> type,I input,Level world) {
        return EnderTaskAccess.lookup((BlockEntity)(Object)this,manager,type,input,world);
    }

    @Inject(method="craftItem()V",at=@At("HEAD"),cancellable=true,remap=false,require=1)
    private void aia2$guardCraft(CallbackInfo callback) {
        aia2$plan=null;
        var owner=(BlockEntity)(Object)this;
        if (owner.getLevel() instanceof net.minecraft.server.level.ServerLevel level) {
            var current=EnderTaskAccess.resolve(recipe,level);
            if (current!=null) { recipe=current;aia2$plan=EnderTaskAccess.prepareCrafter(owner,current); }
        }
        if (aia2$plan==null) callback.cancel();
    }

    @Redirect(method="craftItem()V",at=@At(value="INVOKE",target="Lnet/minecraft/world/item/crafting/CraftingRecipe;assemble(Lnet/minecraft/world/item/crafting/RecipeInput;Lnet/minecraft/core/HolderLookup$Provider;)Lnet/minecraft/world/item/ItemStack;"),remap=false,require=1)
    private ItemStack aia2$useValidatedResult(CraftingRecipe ignored,RecipeInput input,HolderLookup.Provider registry) {
        return aia2$plan.output().copy();
    }

    @Redirect(method="craftItem()V",at=@At(value="INVOKE",target="Lnet/minecraft/world/item/crafting/CraftingRecipe;getRemainingItems(Lnet/minecraft/world/item/crafting/RecipeInput;)Lnet/minecraft/core/NonNullList;"),remap=false,require=1)
    private NonNullList<ItemStack> aia2$useValidatedRemainders(CraftingRecipe ignored,RecipeInput input) {
        var result=NonNullList.withSize(aia2$plan.remaining().size(),ItemStack.EMPTY);
        for (int i=0;i<result.size();i++) result.set(i,aia2$plan.remaining().get(i).copy());
        return result;
    }

    @Inject(method="craftItem()V",at=@At("RETURN"),remap=false,require=1)
    private void aia2$releasePlan(CallbackInfo callback) { aia2$plan=null; }

    @Inject(method="processOutputBuffer()V",at=@At("HEAD"),cancellable=true,remap=false,require=1)
    private void aia2$guardQueue(CallbackInfo callback) {
        var next=outputBuffer.peek();
        if (next!=null && !Aia2MachineGuard.mayProduce((BlockEntity)(Object)this,next)) callback.cancel();
    }
}
