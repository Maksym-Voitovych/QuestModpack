package ua.aia2.guard.mixin;

import net.minecraft.core.NonNullList;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Pseudo;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Redirect;
import ua.aia2.guard.ProjectEPassiveAccess;

/** Preserve native bag/ring selection, while excluding unavailable actual stacks. */
@Pseudo
@Mixin(targets = "moze_intel.projecte.gameObjs.items.AlchemicalBag", remap = false)
abstract class ProjectEBagSuctionMixin {
    @Redirect(method = "getFirstBagWithSuctionItem(Lnet/minecraft/world/entity/player/Player;Lnet/minecraft/core/NonNullList;)Lnet/minecraft/world/item/ItemStack;",
            at = @At(value = "INVOKE", target = "Lnet/minecraft/world/item/ItemStack;isEmpty()Z"), remap = false, require = 2, allow = 2)
    private static boolean aia2$unavailableSuctionStack(ItemStack stack, Player player, NonNullList<ItemStack> inventory) {
        return stack.isEmpty() || !ProjectEPassiveAccess.mayUse(player, stack);
    }
}
