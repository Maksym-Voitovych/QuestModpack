package ua.aia2.guard.mixin;

import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Pseudo;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Coerce;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;
import ua.aia2.guard.ForbiddenRitualAccess;

@Pseudo
@Mixin(targets = "com.stal111.forbidden_arcanus.common.block.entity.forge.essence.EssencesStorage", remap = false)
public abstract class ForbiddenEssencePaymentMixin {
    @Inject(method = "reduce(Lcom/stal111/forbidden_arcanus/common/block/entity/forge/essence/EssencesDefinition;)V",
            at = @At("RETURN"), remap = false, require = 1)
    private void aia2$paid(@Coerce Object definition, CallbackInfo callback) {
        ForbiddenRitualAccess.paid(this, definition);
    }
}
