package ua.aia2.guard.mixin;

import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Pseudo;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;
import ua.aia2.guard.ProjectEArmorAccess;
import ua.aia2.guard.ProjectEPassiveAccess;

@Pseudo
@Mixin(targets = "moze_intel.projecte.gameObjs.items.armor.GemHelmet", remap = false)
abstract class ProjectEGemHelmetMixin {
    @Inject(method = "toggleNightVision(Lnet/minecraft/world/item/ItemStack;Lnet/minecraft/world/entity/player/Player;)V", at = @At("HEAD"), cancellable = true, remap = false, require = 1)
    private static void aia2$guardVisionToggle(ItemStack stack, Player player, CallbackInfo callback) {
        if (!ProjectEPassiveAccess.mayUse(player, stack)) callback.cancel();
    }
    @Inject(method = "doZap(Lnet/minecraft/world/entity/player/Player;)V", at = @At("HEAD"), cancellable = true, remap = false, require = 1)
    private static void aia2$guardHelmetAbility(Player player, CallbackInfo callback) {
        if (!ProjectEArmorAccess.mayUseGemAbility(player, EquipmentSlot.HEAD)) callback.cancel();
    }
}
