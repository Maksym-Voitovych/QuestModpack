package ua.aia2.guard.mixin;

import net.minecraft.world.item.crafting.Recipe;
import net.minecraft.world.item.crafting.RecipeHolder;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Pseudo;
import org.spongepowered.asm.mixin.Shadow;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Coerce;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;
import ua.aia2.guard.Aia2MachineGuard;
import ua.aia2.guard.ModernRecipeProxyAccess;

/** MI lists recipes directly and restores paid in-flight recipes by ID. */
@Pseudo
@Mixin(targets="aztech.modern_industrialization.machines.components.CrafterComponent",remap=false)
abstract class ModernCrafterMixin {
    @Shadow(remap=false) private RecipeHolder<?> activeRecipe;
    @Shadow(remap=false) private long usedEnergy;
    @Shadow(remap=false) private int efficiencyTicks;

    @Inject(method="canStartRecipe(Laztech/modern_industrialization/machines/recipe/MachineRecipe;)Z",
            at=@At("HEAD"),cancellable=true,remap=false,require=1)
    private void aia2$guardStart(@Coerce Object recipe,CallbackInfoReturnable<Boolean> callback) {
        if (!(recipe instanceof Recipe<?> nativeRecipe) || !Aia2MachineGuard.mayProcessRecipeInCurrentTick(nativeRecipe))
            callback.setReturnValue(false);
    }

    @Inject(method="tickRecipe()Z",at=@At(value="INVOKE",target="Laztech/modern_industrialization/machines/components/CrafterComponent;loadDelayedActiveRecipe()V",shift=At.Shift.AFTER),
            cancellable=true,remap=false,require=1)
    private void aia2$guardPaidRecipe(CallbackInfoReturnable<Boolean> callback) {
        if (activeRecipe==null || Aia2MachineGuard.mayProcessRecipeInCurrentTick(activeRecipe.value())) return;
        if (usedEnergy==0) {
            // An idle efficiency cache is not paid work. Let native lookup find a
            // fresh permitted recipe instead of freezing forever on a retired object.
            efficiencyTicks=0;
            activeRecipe=null; // Same native clear condition: efficiencyTicks == 0 && usedEnergy == 0.
            return;
        }
        var rebound=ModernRecipeProxyAccess.rebindUnchanged(activeRecipe,Aia2MachineGuard.currentTickServerLevel());
        if (rebound!=null && Aia2MachineGuard.mayProcessRecipeInCurrentTick(rebound.value())) {
            activeRecipe=rebound;
            return;
        }
        callback.setReturnValue(false); // Pause changed/removed/locked paid work without losing inputs or EU.
    }
}
