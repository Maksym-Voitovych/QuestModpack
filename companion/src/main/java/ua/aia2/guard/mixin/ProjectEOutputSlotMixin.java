package ua.aia2.guard.mixin;

import net.minecraft.world.inventory.Slot;
import net.minecraft.world.item.ItemStack;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Pseudo;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;
import ua.aia2.guard.ProjectEAccess;

@Pseudo
@Mixin(targets = "moze_intel.projecte.gameObjs.container.slots.transmutation.SlotOutput", remap = false)
abstract class ProjectEOutputSlotMixin {
    @Inject(method = "remove(I)Lnet/minecraft/world/item/ItemStack;", at = @At("HEAD"), cancellable = true, remap = false, require = 1)
    private void aia2$currentEmc(int amount, CallbackInfoReturnable<ItemStack> callback) {
        if (amount <= 0 || !ProjectEAccess.mayExtractSlot(this, ((Slot)(Object)this).getItem())) callback.setReturnValue(ItemStack.EMPTY);
    }
}
