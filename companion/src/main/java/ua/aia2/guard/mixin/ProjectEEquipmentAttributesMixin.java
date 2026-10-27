package ua.aia2.guard.mixin;

import java.util.Map;
import java.util.function.BiConsumer;
import net.minecraft.core.Holder;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.ai.attributes.Attribute;
import net.minecraft.world.entity.ai.attributes.AttributeModifier;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.Redirect;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;
import ua.aia2.guard.ProjectEArmorAttributes;

@Mixin(LivingEntity.class)
abstract class ProjectEEquipmentAttributesMixin {
    @Redirect(method = "collectEquipmentChanges()Ljava/util/Map;",
            at = @At(value = "INVOKE", target = "Lnet/minecraft/world/item/ItemStack;forEachModifier(Lnet/minecraft/world/entity/EquipmentSlot;Ljava/util/function/BiConsumer;)V", ordinal = 1), require = 1)
    private void aia2$availableEquipmentAttributes(ItemStack stack, EquipmentSlot slot,
                                                  BiConsumer<Holder<Attribute>, AttributeModifier> action) {
        ProjectEArmorAttributes.apply((LivingEntity)(Object)this, stack, slot, action);
    }

    @Inject(method = "collectEquipmentChanges()Ljava/util/Map;", at = @At("RETURN"), require = 1)
    private void aia2$currentEquipmentPolicy(CallbackInfoReturnable<Map<EquipmentSlot, ItemStack>> callback) {
        if ((Object)this instanceof Player player) ProjectEArmorAttributes.reconcile(player, callback.getReturnValue());
    }
}
