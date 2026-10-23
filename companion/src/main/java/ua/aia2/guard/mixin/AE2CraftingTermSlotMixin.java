package ua.aia2.guard.mixin;

import net.minecraft.world.entity.player.Player;
import net.minecraft.world.inventory.Slot;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Pseudo;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Coerce;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;
import ua.aia2.guard.Aia2MachineGuard;

/**
 * AE2 19.2.18 terminal uses its own click protocol and never vanilla ResultSlot.
 * All ordinary/stack/shift/all crafting actions pass this method before extraction.
 */
@Pseudo
@Mixin(targets = "appeng.menu.slot.CraftingTermSlot", remap = false)
abstract class AE2CraftingTermSlotMixin {
    @Inject(method = "doClick(Lappeng/helpers/InventoryAction;Lnet/minecraft/world/entity/player/Player;)V",
            at = @At("HEAD"), cancellable = true, remap = false, require = 1)
    private void aia2$guardTerminalCraft(@Coerce Object action, Player player, CallbackInfo callback) {
        if (!Aia2MachineGuard.mayCraft(player, ((Slot) (Object) this).getItem())) callback.cancel();
    }
}
