package ua.aia2.guard.mixin;

import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Pseudo;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;
import ua.aia2.guard.Aia2MachineGuard;

/** Exact Mekanism 10.7.19.85 CachedRecipe.process(): before energy and input consumption. */
@Pseudo
@Mixin(targets = "mekanism.api.recipes.cache.CachedRecipe", remap = false)
abstract class MekanismCachedRecipeMixin {
    @Inject(method = "process()V", at = @At("HEAD"), cancellable = true, remap = false, require = 1)
    private void aia2$guardCachedProcess(CallbackInfo callback) {
        if (!Aia2MachineGuard.mayProcessCachedRecipe(this)) callback.cancel();
    }
}
