package ua.aia2.guard.mixin;

import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Pseudo;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;
import ua.aia2.guard.CreativeManaGuard;

import java.util.List;

/** Filters both ordinary inventory/event sources and the native accessories list. */
@Pseudo
@Mixin(targets = "velrondevs.botania.common.impl.mana.ManaItemHandlerImpl", remap = false)
abstract class BotaniaManaItemHandlerMixin {
    @Inject(method = {"getManaItems(Lnet/minecraft/world/entity/player/Player;)Ljava/util/List;",
            "getManaAccesories(Lnet/minecraft/world/entity/player/Player;)Ljava/util/List;"},
            at = @At("RETURN"), cancellable = true, remap = false, require = 1)
    private void aia2$filterCreativeSupplies(Player player, CallbackInfoReturnable<List<ItemStack>> callback) {
        callback.setReturnValue(CreativeManaGuard.filterPlayerSupplies(player, callback.getReturnValue()));
    }
}
