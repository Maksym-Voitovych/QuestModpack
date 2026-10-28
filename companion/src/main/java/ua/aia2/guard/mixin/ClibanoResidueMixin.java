package ua.aia2.guard.mixin;

import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.core.Holder;
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
    @Inject(method = "tick(Lcom/stal111/forbidden_arcanus/common/block/entity/clibano/ClibanoMainBlockEntity;)V",
            at = @At("RETURN"), remap = false, require = 1)
    private void aia2$combined(@Coerce Object machine, CallbackInfo callback) {
        ClibanoAccess.convertedResidues(this, (BlockEntity)machine);
    }
    @Inject(method = "increaseType(Lnet/minecraft/core/Holder;I)V",
            at = @At("HEAD"), cancellable = true, remap = false, require = 1)
    private void aia2$credit(Holder<?> type, int amount, CallbackInfo callback) {
        if (!ClibanoAccess.mayIncreaseResidue(this, type, amount)) callback.cancel();
    }
    @Inject(method = "increaseType(Lnet/minecraft/core/Holder;I)V",
            at = @At("RETURN"), remap = false, require = 1)
    private void aia2$credited(Holder<?> type, int amount, CallbackInfo callback) {
        ClibanoAccess.increasedResidue(this, type, amount);
    }
}
