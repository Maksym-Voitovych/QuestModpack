package ua.aia2.guard.mixin;

import net.minecraft.world.level.block.entity.BlockEntity;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Pseudo;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Coerce;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;
import ua.aia2.guard.ClibanoAccess;

@Pseudo
@Mixin(targets = "com.stal111.forbidden_arcanus.common.block.entity.clibano.ResiduesStorage", remap = false)
public abstract class ClibanoResidueMixin {
    @Inject(method = "tick(Lcom/stal111/forbidden_arcanus/common/block/entity/clibano/ClibanoMainBlockEntity;)V",
            at = @At("HEAD"), cancellable = true, remap = false, require = 1)
    private void aia2$combine(@Coerce Object machine, CallbackInfo callback) {
        if (!ClibanoAccess.mayConvertResidues(this, (BlockEntity)machine)) callback.cancel();
    }
}
