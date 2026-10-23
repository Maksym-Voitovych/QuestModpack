package ua.aia2.guard.mixin;

import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Pseudo;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Coerce;
import org.spongepowered.asm.mixin.injection.Redirect;
import ua.aia2.guard.RobitRecipeAccess;

/** Establish a team scope only around Robit's native smelting monitor. */
@Pseudo
@Mixin(targets = "mekanism.common.entity.EntityRobit", remap = false)
abstract class MekanismRobitRecipeMixin {
    @Redirect(method = "baseTick()V", at = @At(value = "INVOKE", target =
            "Lmekanism/common/recipe/lookup/monitor/RecipeCacheLookupMonitor;updateAndProcess()Z"),
            require = 1, remap = false)
    private boolean aia2$ownedSmelting(@Coerce Object monitor) {
        return RobitRecipeAccess.updateAndProcess(this, monitor);
    }
}
