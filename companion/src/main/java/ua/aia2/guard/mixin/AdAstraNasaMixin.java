package ua.aia2.guard.mixin;

import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.Level;
import net.minecraft.world.item.ItemStack;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Pseudo;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.Redirect;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;
import ua.aia2.guard.AdAstraNasaAccess;
import ua.aia2.guard.NasaProductionAccess;

@Pseudo
@Mixin(targets = "earth.terrarium.adastra.common.blockentities.machines.NasaWorkbenchBlockEntity", remap = false)
public abstract class AdAstraNasaMixin {
    @Inject(method = "canCraft()Z", at = @At("RETURN"), cancellable = true, remap = false, require = 1)
    private void aia2$select(CallbackInfoReturnable<Boolean> callback) {
        if (Boolean.TRUE.equals(callback.getReturnValue()) && !AdAstraNasaAccess.maySelect((BlockEntity)(Object)this))
            callback.setReturnValue(false);
    }

    @Inject(method = "craft()V", at = @At("HEAD"), cancellable = true, remap = false, require = 1)
    private void aia2$finish(CallbackInfo callback) {
        BlockEntity machine = (BlockEntity)(Object)this;
        if (!NasaProductionAccess.enterNative(machine)) {
            NasaProductionAccess.craft(machine); callback.cancel();
        }
    }

    @Redirect(method = "craft()V", at = @At(value = "INVOKE", target = "Lnet/minecraft/world/Containers;dropItemStack(Lnet/minecraft/world/level/Level;DDDLnet/minecraft/world/item/ItemStack;)V"), remap = false, require = 1, allow = 1)
    private void aia2$drop(Level level, double x, double y, double z, ItemStack stack) {
        NasaProductionAccess.drop((BlockEntity)(Object)this, level, x, y, z, stack);
    }

    @Redirect(method = "craft()V", at = @At(value = "INVOKE", target = "Lnet/minecraft/world/item/ItemStack;shrink(I)V"), remap = false, require = 1, allow = 1)
    private void aia2$debit(ItemStack stack, int amount) {
        NasaProductionAccess.shrink((BlockEntity)(Object)this, stack, amount);
    }
}
