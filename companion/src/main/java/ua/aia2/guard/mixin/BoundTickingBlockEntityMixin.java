package ua.aia2.guard.mixin;

import net.minecraft.world.level.block.entity.BlockEntity;
import org.spongepowered.asm.mixin.Final;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Shadow;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;
import ua.aia2.guard.Aia2MachineGuard;
import ua.aia2.guard.GuardedTicker;

/**
 * Standard Minecraft ticker dispatch covers all mods that use BlockEntityTicker.
 * It does not intercept entity ticks, scheduled block ticks or capability IO.
 */
@Mixin(targets = "net.minecraft.world.level.chunk.LevelChunk$BoundTickingBlockEntity")
abstract class BoundTickingBlockEntityMixin implements GuardedTicker {
    @Shadow @Final private BlockEntity blockEntity;

    @Inject(method = "tick", at = @At("HEAD"), cancellable = true, require = 1)
    private void aia2$guardMachineTick(CallbackInfo callback) {
        if (!Aia2MachineGuard.mayTick(blockEntity)) {
            callback.cancel();
        }
    }
}
