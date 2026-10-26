package ua.aia2.guard.mixin;

import net.minecraft.world.entity.player.Player;
import net.minecraft.world.inventory.AbstractContainerMenu;
import net.minecraft.world.item.ItemStack;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Pseudo;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;
import ua.aia2.guard.ProjectEAccess;

@Pseudo
@Mixin(targets = "moze_intel.projecte.gameObjs.container.TransmutationContainer", remap = false)
abstract class ProjectETransmutationMixin {
    @Inject(method = "quickMoveStack(Lnet/minecraft/world/entity/player/Player;I)Lnet/minecraft/world/item/ItemStack;", at = @At("HEAD"), cancellable = true, remap = false, require = 1)
    private void aia2$guardQuickMove(Player player, int slot, CallbackInfoReturnable<ItemStack> callback) {
        if (!ProjectEAccess.mayUseContainer(player, this)) { callback.setReturnValue(ItemStack.EMPTY); return; }
        var menu = (AbstractContainerMenu)(Object)this;
        if (slot >= 11 && slot <= 26 && (slot >= menu.slots.size()
                || !ProjectEAccess.mayExtract(player, menu.slots.get(slot).getItem()))) callback.setReturnValue(ItemStack.EMPTY);
    }
}
