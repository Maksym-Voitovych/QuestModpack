package ua.aia2.guard.mixin;

import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Pseudo;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Redirect;
import ua.aia2.guard.ProjectEArmorAccess;

/** Native tick still runs, including removal of old flight/swimming modifiers. */
@Pseudo
@Mixin(targets = "moze_intel.projecte.handlers.InternalAbilities", remap = false)
abstract class ProjectEArmorAbilitiesMixin {
    @Redirect(method = {"canWalkOnWater(Lnet/minecraft/world/entity/player/Player;)Lmoze_intel/projecte/handlers/InternalAbilities$WalkOnType;",
                        "canWalkOnLava(Lnet/minecraft/world/entity/player/Player;)Lmoze_intel/projecte/handlers/InternalAbilities$WalkOnType;"},
            at = @At(value = "INVOKE", target = "Lnet/minecraft/world/entity/player/Player;getItemBySlot(Lnet/minecraft/world/entity/EquipmentSlot;)Lnet/minecraft/world/item/ItemStack;"), remap = false, require = 1)
    private static ItemStack aia2$availableWalkingArmor(Player player, EquipmentSlot slot) { return ProjectEArmorAccess.equipment(player, slot); }
}
