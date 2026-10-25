package dev.shadowsoffire.apothic_enchanting.mixin;

import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

import dev.shadowsoffire.apothic_enchanting.enchantments.CrescendoHooks;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResultHolder;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.entity.projectile.Projectile;
import net.minecraft.world.item.CrossbowItem;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;

@Mixin(value = CrossbowItem.class, remap = false)
public class CrossbowItemMixin {

    @Inject(method = "tryLoadProjectiles", at = @At(value = "RETURN"))
    private static void apoth_setupCrescendoShots(LivingEntity shooter, ItemStack crossbow, CallbackInfoReturnable<Boolean> cir) {
        if (cir.getReturnValueZ() && !shooter.level().isClientSide()) {
            CrescendoHooks.prepareCrescendoShots(shooter, crossbow);
        }
    }

    @Inject(method = "use", at = @At(value = "RETURN", ordinal = 0))
    public void apoth_addCharges(Level pLevel, Player pPlayer, InteractionHand pHand, CallbackInfoReturnable<InteractionResultHolder<ItemStack>> ci) {
        if (pPlayer.level() instanceof ServerLevel sl) {
            CrescendoHooks.reloadFromCrescendoCharge(sl, pPlayer.getItemInHand(pHand));
        }
    }

    @Inject(method = "createProjectile", at = @At(value = "RETURN"))
    private void apoth_markArrows(Level level, LivingEntity shooter, ItemStack weapon, ItemStack ammo, boolean isCrit, CallbackInfoReturnable<Projectile> cir) {
        CrescendoHooks.markGeneratedArrows(cir.getReturnValue(), weapon);
    }

}
