package ua.aia2.guard.mixin;

import net.minecraft.core.BlockPos;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.entity.BlockEntityTicker;
import net.minecraft.world.level.block.state.BlockState;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Pseudo;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Redirect;
import ua.aia2.guard.Aia2MachineGuard;

/** ProjectE inlines the native ticker and otherwise skips the standard guard. */
@Pseudo
@Mixin(targets = "moze_intel.projecte.gameObjs.items.rings.TimeWatch", remap = false)
abstract class ProjectETimeWatchMixin {
    @Redirect(method = "provideBonusTicks(Lnet/minecraft/world/level/Level;Lnet/minecraft/core/BlockPos;Lnet/minecraft/world/level/block/state/BlockState;Lnet/minecraft/world/level/block/entity/BlockEntity;Lnet/minecraft/world/level/chunk/LevelChunk$BoundTickingBlockEntity;I)V",
            at = @At(value = "INVOKE", target = "Lnet/minecraft/world/level/block/entity/BlockEntityTicker;tick(Lnet/minecraft/world/level/Level;Lnet/minecraft/core/BlockPos;Lnet/minecraft/world/level/block/state/BlockState;Lnet/minecraft/world/level/block/entity/BlockEntity;)V"),
            remap = false, require = 1)
    private void aia2$ownedBonusTick(BlockEntityTicker<BlockEntity> ticker, Level level, BlockPos pos,
                                     BlockState state, BlockEntity target) {
        // Rechecked for every bonus tick, including a stage change mid-batch.
        if (target == null || !Aia2MachineGuard.mayTick(target)) return;
        BlockEntity parent = Aia2MachineGuard.enterTick(target);
        try { ticker.tick(level, pos, state, target); }
        finally { Aia2MachineGuard.exitTick(parent); }
    }
}
