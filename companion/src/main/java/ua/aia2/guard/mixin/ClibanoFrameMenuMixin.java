package ua.aia2.guard.mixin;

import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.BlockHitResult;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Pseudo;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;
import ua.aia2.guard.ClibanoOwnership;

@Pseudo
@Mixin(targets = "com.stal111.forbidden_arcanus.common.block.clibano.AbstractClibanoFrameBlock", remap = false)
public abstract class ClibanoFrameMenuMixin {
    @Inject(method = "useWithoutItem(Lnet/minecraft/world/level/block/state/BlockState;Lnet/minecraft/world/level/Level;Lnet/minecraft/core/BlockPos;Lnet/minecraft/world/entity/player/Player;Lnet/minecraft/world/phys/BlockHitResult;)Lnet/minecraft/world/InteractionResult;",
            at = @At("HEAD"), cancellable = true, remap = false, require = 1)
    private void aia2$boundMenu(BlockState state, Level level, BlockPos pos, Player player, BlockHitResult hit,
                                CallbackInfoReturnable<InteractionResult> callback) {
        if (!level.isClientSide() && player instanceof ServerPlayer serverPlayer)
            ClibanoOwnership.open(serverPlayer, level.getBlockEntity(pos));
        callback.setReturnValue(InteractionResult.sidedSuccess(level.isClientSide()));
    }
}
