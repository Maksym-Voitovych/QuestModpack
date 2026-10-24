package ua.aia2.guard.mixin;

import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.block.entity.BlockEntity;
import org.spongepowered.asm.mixin.Final;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Pseudo;
import org.spongepowered.asm.mixin.Shadow;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;
import ua.aia2.guard.CreativeManaGuard;

/** Native pool exchange has an owning BlockEntity even when the tablet is a dropped entity. */
@Pseudo
@Mixin(targets = "velrondevs.botania.common.item.ManaTabletItem$ManaItemImpl", remap = false)
abstract class BotaniaManaTabletPoolMixin {
    @Shadow(remap = false) @Final private ItemStack stack;

    @Inject(method = {"canReceiveManaFromPool(Lnet/minecraft/world/level/block/entity/BlockEntity;)Z",
            "canExportManaToPool(Lnet/minecraft/world/level/block/entity/BlockEntity;)Z"},
            at = @At("HEAD"), cancellable = true, remap = false, require = 1)
    private void aia2$guardCreativePoolExchange(BlockEntity pool, CallbackInfoReturnable<Boolean> callback) {
        if (!CreativeManaGuard.mayExchangeWithPool(pool, stack)) callback.setReturnValue(false);
    }
}
