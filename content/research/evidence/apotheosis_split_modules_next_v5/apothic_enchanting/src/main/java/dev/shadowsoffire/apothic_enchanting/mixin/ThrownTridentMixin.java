package dev.shadowsoffire.apothic_enchanting.mixin;

import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Shadow;
import org.spongepowered.asm.mixin.Unique;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

import it.unimi.dsi.fastutil.ints.IntOpenHashSet;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.projectile.AbstractArrow;
import net.minecraft.world.entity.projectile.ThrownTrident;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.enchantment.EnchantmentHelper;
import net.minecraft.world.level.Level;
import net.minecraft.world.phys.EntityHitResult;
import net.minecraft.world.phys.Vec3;

/**
 * Mixin to tridents to enable Piercing to work.
 */
@Mixin(value = ThrownTrident.class, remap = false)
public abstract class ThrownTridentMixin extends AbstractArrow {

    @Unique
    private int pierces = 0;

    @Unique
    private Vec3 oldVel = null;

    @Shadow
    private boolean dealtDamage;

    protected ThrownTridentMixin(EntityType<? extends AbstractArrow> entityType, double x, double y, double z, Level level, ItemStack pickupItemStack, ItemStack firedFromWeapon) {
        super(entityType, x, y, z, level, pickupItemStack, firedFromWeapon);
    }

    @Inject(method = "<init>(Lnet/minecraft/world/level/Level;Lnet/minecraft/world/entity/LivingEntity;Lnet/minecraft/world/item/ItemStack;)V", at = @At("TAIL"), require = 1, remap = false)
    private void init(CallbackInfo ci) {
        if (!this.level().isClientSide()) {
            int pierce = EnchantmentHelper.getPiercingCount((ServerLevel) this.level(), this.getPickupItem(), this.getPickupItem());
            this.setPierceLevel((byte) pierce);
        }
    }

    @Inject(method = "onHitEntity(Lnet/minecraft/world/phys/EntityHitResult;)V", at = @At("HEAD"), cancellable = true, require = 1)
    public void startHitEntity(EntityHitResult res, CallbackInfo ci) {
        if (this.getPierceLevel() > 0) {
            if (this.piercingIgnoreEntityIds == null) {
                this.piercingIgnoreEntityIds = new IntOpenHashSet(this.getPierceLevel());
            }
            if (this.piercingIgnoreEntityIds.contains(res.getEntity().getId())) ci.cancel();
        }

        this.oldVel = this.getDeltaMovement();
    }

    @Inject(method = "onHitEntity(Lnet/minecraft/world/phys/EntityHitResult;)V", at = @At("TAIL"), cancellable = true, require = 1)
    public void endHitEntity(EntityHitResult res, CallbackInfo ci) {
        if (this.getPierceLevel() > 0) {
            this.piercingIgnoreEntityIds.add(res.getEntity().getId());

            if (this.piercingIgnoreEntityIds.size() <= this.getPierceLevel()) {
                this.dealtDamage = false;
                this.setDeltaMovement(this.oldVel);
            }
        }
    }

}
