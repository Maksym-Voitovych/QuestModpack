package ua.aia2.guard.mixin;

import net.minecraft.world.InteractionHand;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Pseudo;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Coerce;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;
import ua.aia2.guard.ProjectEPassiveAccess;

@Pseudo
@Mixin(targets = "moze_intel.projecte.network.packets.to_server.KeyPressPKT", remap = false)
abstract class ProjectEKeyCapabilityMixin {
    @Inject(method = "tryPerformCapability(Lnet/minecraft/world/entity/player/Player;Lnet/minecraft/world/item/ItemStack;Lnet/minecraft/world/InteractionHand;Lnet/neoforged/neoforge/capabilities/ItemCapability;Lmoze_intel/projecte/network/packets/to_server/KeyPressPKT$CapabilityProcessor;)Z",
            at = @At("HEAD"), cancellable = true, remap = false, require = 1)
    private static void aia2$actualHeldItem(Player player, ItemStack stack, InteractionHand hand,
            @Coerce Object capability, @Coerce Object processor, CallbackInfoReturnable<Boolean> callback) {
        if (!ProjectEPassiveAccess.mayUse(player, stack)) callback.setReturnValue(false);
    }
}
