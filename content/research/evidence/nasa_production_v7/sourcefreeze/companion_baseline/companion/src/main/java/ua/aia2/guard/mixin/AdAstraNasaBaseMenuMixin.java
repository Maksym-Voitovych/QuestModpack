package ua.aia2.guard.mixin;

import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Pseudo;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;
import ua.aia2.guard.AdAstraNasaAccess;

@Pseudo
@Mixin(targets = "earth.terrarium.adastra.common.menus.base.BaseContainerMenu", remap = false)
public abstract class AdAstraNasaBaseMenuMixin {
    @Inject(method = "stillValid(Lnet/minecraft/world/entity/player/Player;)Z", at = @At("HEAD"), cancellable = true, remap = false, require = 1)
    private void aia2$stillOwned(Player player, CallbackInfoReturnable<Boolean> callback) {
        if (AdAstraNasaAccess.isNasaMenu(this) && !AdAstraNasaAccess.mayUseMenu(this, player)) callback.setReturnValue(false);
    }

    @Inject(method = "quickMoveStack(Lnet/minecraft/world/entity/player/Player;I)Lnet/minecraft/world/item/ItemStack;",
            at = @At("HEAD"), cancellable = true, remap = false, require = 1)
    private void aia2$shiftMove(Player player, int slot, CallbackInfoReturnable<ItemStack> callback) {
        // Slot14 is a recipe preview, not manufactured stock. The native slot
        // forbids pickup, but a direct quickMoveStack caller skips that check.
        if (AdAstraNasaAccess.isNasaMenu(this) && (slot == 14 || !AdAstraNasaAccess.mayUseMenu(this, player)))
            callback.setReturnValue(ItemStack.EMPTY);
    }
}
