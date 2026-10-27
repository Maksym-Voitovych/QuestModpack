package ua.aia2.guard.mixin;

import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Pseudo;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;
import ua.aia2.guard.ProjectEArmorAccess;
import ua.aia2.guard.ProjectEPassiveAccess;

@Pseudo
@Mixin(targets = "moze_intel.projecte.gameObjs.items.armor.GemChest", remap = false)
abstract class ProjectEGemChestMixin {
    @Inject(method = "doExplode(Lnet/minecraft/world/entity/player/Player;)V", at = @At("HEAD"), cancellable = true, remap = false, require = 1)
    private static void aia2$guardChestAbility(Player player, CallbackInfo callback) {
        if (!ProjectEArmorAccess.mayUseGemAbility(player, EquipmentSlot.CHEST)) callback.cancel();
    }
    @Inject(method = "canProtectAgainstFire(Lnet/minecraft/world/item/ItemStack;Lnet/minecraft/world/entity/player/Player;)Z", at = @At("HEAD"), cancellable = true, remap = false, require = 1)
    private void aia2$guardChestFire(ItemStack stack, Player player, CallbackInfoReturnable<Boolean> callback) {
        if (!ProjectEPassiveAccess.mayUse(player, stack)) callback.setReturnValue(false);
    }
}
