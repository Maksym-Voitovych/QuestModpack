package ua.aia2.guard.mixin;

import java.util.Optional;
import net.minecraft.world.item.crafting.Recipe;
import net.minecraft.world.item.crafting.RecipeHolder;
import net.minecraft.world.item.crafting.RecipeInput;
import net.minecraft.world.item.crafting.RecipeManager;
import net.minecraft.world.item.crafting.RecipeType;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.entity.BlockEntity;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Pseudo;
import org.spongepowered.asm.mixin.Shadow;
import org.spongepowered.asm.mixin.Unique;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.Redirect;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;
import ua.aia2.guard.EnderTaskAccess;
import ua.aia2.guard.PowahOrbAccess;

@Pseudo
@Mixin(targets="owmii.powah.block.energizing.EnergizingOrbTile",remap=false)
abstract class PowahEnergizingOrbMixin {
    @Shadow(remap=false) private RecipeHolder<?> recipe;
    @Unique private PowahOrbAccess.Attempt aia2$attempt;

    @Inject(method="fillEnergy(J)J",at=@At("HEAD"),cancellable=true,remap=false,require=1)
    private void aia2$guardReceiver(long amount,CallbackInfoReturnable<Long> callback) {
        aia2$attempt=amount<0?null:PowahOrbAccess.begin((BlockEntity)(Object)this,recipe);
        if (aia2$attempt==null) callback.setReturnValue(0L);
        else recipe=aia2$attempt.holder();
    }

    @Inject(method="fillEnergy(J)J",at=@At(value="INVOKE",target="Lowmii/powah/lib/logistics/inventory/Inventory;setStackInSlot(ILnet/minecraft/world/item/ItemStack;)V",shift=At.Shift.AFTER),remap=false,require=1)
    private void aia2$observeBatch(long amount,CallbackInfoReturnable<Long> callback) {
        PowahOrbAccess.finish((BlockEntity)(Object)this,aia2$attempt);
        aia2$attempt=null;
    }

    @Inject(method="fillEnergy(J)J",at=@At("RETURN"),remap=false,require=1)
    private void aia2$releaseAttempt(long amount,CallbackInfoReturnable<Long> callback) { aia2$attempt=null; }

    @Redirect(method="checkRecipe()V",at=@At(value="INVOKE",target="Lnet/minecraft/world/item/crafting/RecipeManager;getRecipeFor(Lnet/minecraft/world/item/crafting/RecipeType;Lnet/minecraft/world/item/crafting/RecipeInput;Lnet/minecraft/world/level/Level;)Ljava/util/Optional;"),remap=false,require=1)
    private <I extends RecipeInput,T extends Recipe<I>> Optional<RecipeHolder<T>> aia2$ownLookup(
            RecipeManager manager,RecipeType<T> type,I input,Level level) {
        return EnderTaskAccess.lookup((BlockEntity)(Object)this,manager,type,input,level);
    }
}
