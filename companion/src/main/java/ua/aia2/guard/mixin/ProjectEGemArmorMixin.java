package ua.aia2.guard.mixin;

import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Pseudo;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Redirect;
import ua.aia2.guard.ProjectEArmorAccess;

@Pseudo
@Mixin(targets = "moze_intel.projecte.gameObjs.items.armor.GemArmorBase", remap = false)
abstract class ProjectEGemArmorMixin {
    @Redirect(method = {"hasAnyPiece(Lnet/minecraft/world/entity/player/Player;)Z", "hasFullSet(Lnet/minecraft/world/entity/player/Player;)Z"},
            at = @At(value = "INVOKE", target = "Lnet/minecraft/world/entity/player/Player;getItemBySlot(Lnet/minecraft/world/entity/EquipmentSlot;)Lnet/minecraft/world/item/ItemStack;"), remap = false, require = 1)
    private static ItemStack aia2$availableGemPiece(Player player, EquipmentSlot slot) { return ProjectEArmorAccess.equipment(player, slot); }
}
