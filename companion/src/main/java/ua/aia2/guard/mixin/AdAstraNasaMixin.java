package ua.aia2.guard.mixin;

import net.minecraft.world.level.block.entity.BlockEntity;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Pseudo;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;
import ua.aia2.guard.AdAstraNasaAccess;

@Pseudo
@Mixin(targets = "earth.terrarium.adastra.common.blockentities.machines.NasaWorkbenchBlockEntity", remap = false)
public abstract class AdAstraNasaMixin {
    @Inject(method = "canCraft()Z", at = @At("RETURN"), cancellable = true, remap = false, require = 1)
    private void aia2$select(CallbackInfoReturnable<Boolean> callback) {
        if (Boolean.TRUE.equals(callback.getReturnValue()) && !AdAstraNasaAccess.maySelect((BlockEntity)(Object)this))
            callback.setReturnValue(false);
    }

    @Inject(method = "craft()V", at = @At("HEAD"), cancellable = true, remap = false, require = 1)
    private void aia2$finish(CallbackInfo callback) {
        if (!AdAstraNasaAccess.mayFinish((BlockEntity)(Object)this)) callback.cancel();
    }
}
