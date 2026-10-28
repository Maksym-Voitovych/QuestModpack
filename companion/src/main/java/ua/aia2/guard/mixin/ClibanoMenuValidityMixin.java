package ua.aia2.guard.mixin;

import net.minecraft.world.entity.player.Player;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Pseudo;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;
import ua.aia2.guard.ClibanoOwnership;

@Pseudo
@Mixin(targets = "com.stal111.forbidden_arcanus.common.inventory.clibano.ClibanoMenu", remap = false)
public abstract class ClibanoMenuValidityMixin {
    @Inject(method = "<init>(ILnet/neoforged/neoforge/items/ItemStackHandler;Lnet/minecraft/world/inventory/ContainerData;Ljava/util/Map;Lnet/valhelsia/valhelsia_core/api/common/block/entity/MenuCreationContext;)V",
            at = @At("RETURN"), remap = false, require = 1)
    private void aia2$bind(CallbackInfo callback) { ClibanoOwnership.bindMenu(this); }
    @Inject(method = "stillValid(Lnet/minecraft/world/entity/player/Player;)Z", at = @At("HEAD"), cancellable = true, remap = false, require = 1)
    private void aia2$liveOwner(Player player, CallbackInfoReturnable<Boolean> callback) {
        if (!ClibanoOwnership.mayKeepMenu(this, player)) callback.setReturnValue(false);
    }
}
