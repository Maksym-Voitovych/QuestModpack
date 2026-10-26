package ua.aia2.guard.mixin;

import net.minecraft.core.BlockPos;
import net.minecraft.world.level.chunk.LevelChunk;
import net.minecraft.world.level.block.state.BlockState;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;
import ua.aia2.guard.FireWorksiteAccess;

@Mixin(LevelChunk.class)
abstract class FireWorksiteBaseMixin {
    @Inject(method = "setBlockState(Lnet/minecraft/core/BlockPos;Lnet/minecraft/world/level/block/state/BlockState;Z)Lnet/minecraft/world/level/block/state/BlockState;",
            at = @At("RETURN"), require = 1)
    private void aia2$invalidateBase(BlockPos pos, BlockState next, boolean moved, CallbackInfoReturnable<BlockState> callback) {
        FireWorksiteAccess.baseChanged(((LevelChunk)(Object)this).getLevel(), pos, callback.getReturnValue(), next);
    }
}
