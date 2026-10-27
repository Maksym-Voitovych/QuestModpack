package ua.aia2.guard.mixin;

import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.neoforged.neoforge.items.IItemHandler;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Pseudo;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Coerce;
import org.spongepowered.asm.mixin.injection.Redirect;
import ua.aia2.guard.ProjectEStorageAccess;

@Pseudo
@Mixin(targets = "moze_intel.projecte.events.TickEvents", remap = false)
abstract class ProjectEBagPassiveMixin {
    @Redirect(method = "playerTick(Lnet/neoforged/neoforge/event/tick/PlayerTickEvent$Post;)V",
            at = @At(value = "INVOKE", target = "Lmoze_intel/projecte/api/capabilities/item/IAlchBagItem;updateInAlchBag(Lnet/neoforged/neoforge/items/IItemHandler;Lnet/minecraft/world/entity/player/Player;Lnet/minecraft/world/item/ItemStack;)Z"), remap = false, require = 1)
    private static boolean aia2$guardBagPassive(@Coerce Object capability, IItemHandler inventory, Player player, ItemStack stack) {
        return ProjectEStorageAccess.bag(capability, inventory, player, stack);
    }
}
