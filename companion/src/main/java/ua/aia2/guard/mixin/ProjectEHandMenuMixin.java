package ua.aia2.guard.mixin;

import net.minecraft.world.entity.player.Player;
import net.minecraft.world.inventory.ClickType;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Pseudo;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;
import ua.aia2.guard.ProjectEAccess;

@Pseudo
@Mixin(targets = "moze_intel.projecte.gameObjs.container.PEHandContainer", remap = false)
abstract class ProjectEHandMenuMixin {
    @Inject(method = "stillValid(Lnet/minecraft/world/entity/player/Player;)Z", at = @At("HEAD"), cancellable = true, remap = false, require = 1)
    private void aia2$currentMenuOwner(Player player, CallbackInfoReturnable<Boolean> callback) {
        if (ProjectEAccess.isTransmutation(this) && !ProjectEAccess.mayUseContainer(player, this)) callback.setReturnValue(false);
    }
    @Inject(method = "clicked(IILnet/minecraft/world/inventory/ClickType;Lnet/minecraft/world/entity/player/Player;)V", at = @At("HEAD"), cancellable = true, remap = false, require = 1)
    private void aia2$guardClick(int slot, int button, ClickType type, Player player, CallbackInfo callback) {
        if (ProjectEAccess.isTransmutation(this) && !ProjectEAccess.mayUseContainer(player, this)) callback.cancel();
    }
}
