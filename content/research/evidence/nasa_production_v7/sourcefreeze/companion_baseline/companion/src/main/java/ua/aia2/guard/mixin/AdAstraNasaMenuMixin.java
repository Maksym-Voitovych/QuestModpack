package ua.aia2.guard.mixin;

import net.minecraft.world.entity.player.Player;
import net.minecraft.world.inventory.ClickType;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Pseudo;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;
import ua.aia2.guard.AdAstraNasaAccess;

@Pseudo
@Mixin(targets = "earth.terrarium.adastra.common.menus.machines.NasaWorkbenchMenu", remap = false)
public abstract class AdAstraNasaMenuMixin {
    @Inject(method = "clicked(IILnet/minecraft/world/inventory/ClickType;Lnet/minecraft/world/entity/player/Player;)V",
            at = @At("HEAD"), cancellable = true, remap = false, require = 1)
    private void aia2$ownerClick(int slot, int button, ClickType action, Player player, CallbackInfo callback) {
        if (!AdAstraNasaAccess.mayUseMenu(this, player)) callback.cancel();
    }
}
