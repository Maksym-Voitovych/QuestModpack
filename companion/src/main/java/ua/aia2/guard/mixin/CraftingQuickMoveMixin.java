package ua.aia2.guard.mixin;

import net.minecraft.world.entity.player.Player;
import net.minecraft.world.inventory.AbstractContainerMenu;
import net.minecraft.world.inventory.CraftingMenu;
import net.minecraft.world.inventory.InventoryMenu;
import net.minecraft.world.item.ItemStack;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;
import ua.aia2.guard.Aia2MachineGuard;
import ua.aia2.guard.GuardedCrafting;

@Mixin({CraftingMenu.class, InventoryMenu.class})
abstract class CraftingQuickMoveMixin implements GuardedCrafting {
    @Inject(method = "quickMoveStack(Lnet/minecraft/world/entity/player/Player;I)Lnet/minecraft/world/item/ItemStack;",
            at = @At("HEAD"), cancellable = true, require = 1)
    private void aia2$guardCraftingQuickMove(Player player, int slot, CallbackInfoReturnable<ItemStack> callback) {
        if (slot == 0 && !Aia2MachineGuard.mayCraft(player, ((AbstractContainerMenu) (Object) this).getSlot(0).getItem())) {
            callback.setReturnValue(ItemStack.EMPTY);
        }
    }
}
