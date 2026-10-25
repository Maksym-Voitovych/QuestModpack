package dev.shadowsoffire.apothic_enchanting.mixin;

import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Pseudo;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

import dev.shadowsoffire.apothic_enchanting.enchantments.CrescendoHooks;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.projectile.Projectile;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;

@Pseudo
@Mixin(targets = "com.hollingsworth.arsnouveau.common.items.SpellCrossbow", remap = false)
public class SpellCrossbowMixin {

    /**
     * The spell crossbow has a different implementation of this method, so it needs a separate injection. Underlying logic should be the same.
     */
    @Inject(method = "Lcom/hollingsworth/arsnouveau/common/items/SpellCrossbow;tryLoadProjectiles(Lnet/minecraft/world/entity/LivingEntity;Lnet/minecraft/world/item/ItemStack;)Z", at = @At(value = "RETURN"))
    private static void apoth_setupCrescendoShots(LivingEntity shooter, ItemStack crossbow, CallbackInfoReturnable<Boolean> cir) {
        if (!shooter.level().isClientSide()) {
            CrescendoHooks.prepareCrescendoShots(shooter, crossbow);
        }
    }

    /**
     * Bailey writes very good code, so instead of overriding createProjectile, there's a separate private method that needs to be hooked into.
     */
    @Inject(method = "getArrow", at = @At(value = "RETURN"), require = 0)
    private void apoth_markArrows(Level pLevel, LivingEntity pLivingEntity, ItemStack pCrossbowStack, ItemStack pAmmoStack, CallbackInfoReturnable<Projectile> cir) {
        CrescendoHooks.markGeneratedArrows(cir.getReturnValue(), pCrossbowStack);
    }

}
