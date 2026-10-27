package ua.aia2.guard.mixin;

import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Pseudo;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Redirect;
import ua.aia2.guard.ProjectEArmorAccess;

@Pseudo
@Mixin(targets = "moze_intel.projecte.events.PlayerEvents", remap = false)
abstract class ProjectEArmorEventsMixin {
    @Redirect(method = "onLivingDamaged(Lnet/neoforged/neoforge/event/entity/living/LivingIncomingDamageEvent;)V",
            at = @At(value = "INVOKE", target = "Lnet/minecraft/world/entity/LivingEntity;getArmorSlots()Ljava/lang/Iterable;"), remap = false, require = 1)
    private static Iterable<ItemStack> aia2$availableDamageArmor(LivingEntity entity) {
        return ProjectEArmorAccess.armor(entity);
    }
}
