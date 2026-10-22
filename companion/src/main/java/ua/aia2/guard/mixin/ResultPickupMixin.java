package ua.aia2.guard.mixin;

import net.minecraft.world.entity.player.Player;
import net.minecraft.world.inventory.ResultSlot;
import net.minecraft.world.inventory.Slot;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;
import ua.aia2.guard.Aia2MachineGuard;
import ua.aia2.guard.GuardedCrafting;

@Mixin(Slot.class)
abstract class ResultPickupMixin implements GuardedCrafting {
    @Inject(method = "mayPickup(Lnet/minecraft/world/entity/player/Player;)Z",
            at = @At("HEAD"), cancellable = true, require = 1)
    private void aia2$guardCraftingPickup(Player player, CallbackInfoReturnable<Boolean> callback) {
        if ((Object) this instanceof ResultSlot resultSlot
                && !Aia2MachineGuard.mayCraft(player, resultSlot.getItem())) {
            callback.setReturnValue(false);
        }
    }
}
