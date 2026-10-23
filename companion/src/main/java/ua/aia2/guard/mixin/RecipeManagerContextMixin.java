package ua.aia2.guard.mixin;

import java.util.Optional;
import net.minecraft.world.item.crafting.RecipeHolder;
import net.minecraft.world.item.crafting.RecipeManager;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;
import ua.aia2.guard.Aia2MachineGuard;
import ua.aia2.guard.GuardedCrafting;

/** Filter only a running block entity's individual lookup, never global recipe lists or JEI. */
@Mixin(RecipeManager.class)
abstract class RecipeManagerContextMixin implements GuardedCrafting {
    @Inject(method = "getRecipeFor", at = @At("RETURN"), cancellable = true, require = 1)
    private void aia2$guardOwnedLookup(CallbackInfoReturnable<Optional<RecipeHolder<?>>> callback) {
        var holder = callback.getReturnValue();
        if (holder.isPresent() && !Aia2MachineGuard.mayLookupRecipeInCurrentTick(holder.get().value())) {
            callback.setReturnValue(Optional.empty());
        }
    }
}
