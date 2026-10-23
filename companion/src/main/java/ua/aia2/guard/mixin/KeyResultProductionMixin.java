package ua.aia2.guard.mixin;

import net.minecraft.world.entity.player.Player;
import net.minecraft.world.inventory.CraftingContainer;
import net.minecraft.world.inventory.ResultSlot;
import net.minecraft.world.item.ItemStack;
import org.spongepowered.asm.mixin.Final;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Shadow;
import org.spongepowered.asm.mixin.Unique;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;
import ua.aia2.guard.KeyProductionBridge;

/** Pickup/creative insertion never reaches this post-consumption ResultSlot hook. */
@Mixin(ResultSlot.class)
abstract class KeyResultProductionMixin {
    @Shadow @Final private CraftingContainer craftSlots;
    @Unique private KeyProductionBridge.PlayerAttempt aia2$keyAttempt;

    @Inject(method = "onTake(Lnet/minecraft/world/entity/player/Player;Lnet/minecraft/world/item/ItemStack;)V",
            at = @At("HEAD"), require = 1)
    private void aia2$captureRecipe(Player player, ItemStack output, CallbackInfo callback) {
        aia2$keyAttempt = KeyProductionBridge.beginPlayerCraft(player, craftSlots, output);
    }

    @Inject(method = "onTake(Lnet/minecraft/world/entity/player/Player;Lnet/minecraft/world/item/ItemStack;)V",
            at = @At("RETURN"), require = 1)
    private void aia2$committedRecipe(Player player, ItemStack output, CallbackInfo callback) {
        KeyProductionBridge.PlayerAttempt attempt = aia2$keyAttempt;
        aia2$keyAttempt = null;
        KeyProductionBridge.finishPlayerCraft(attempt, player, output);
    }
}
