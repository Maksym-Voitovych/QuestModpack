package ua.aia2.guard.mixin;

import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.level.block.CrafterBlock;
import net.minecraft.world.level.block.entity.CrafterBlockEntity;
import net.minecraft.world.level.block.state.BlockState;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;
import ua.aia2.guard.Aia2MachineGuard;
import ua.aia2.guard.GuardedCrafting;
import ua.aia2.guard.KeyProductionBridge;
import ua.aia2.guard.ProductionMilestoneBridge;

/** The vanilla crafter crafts in a scheduled block tick, outside BE tick dispatch. */
@Mixin(CrafterBlock.class)
abstract class CrafterDispenseMixin implements GuardedCrafting {
    @Inject(method = "dispenseFrom(Lnet/minecraft/world/level/block/state/BlockState;Lnet/minecraft/server/level/ServerLevel;Lnet/minecraft/core/BlockPos;)V",
            at = @At("HEAD"), cancellable = true, require = 1)
    private void aia2$guardCrafterDispense(BlockState state, ServerLevel level, BlockPos position, CallbackInfo callback) {
        if (level.getBlockEntity(position) instanceof CrafterBlockEntity crafter) {
            KeyProductionBridge.cancelCrafter(crafter);
            ProductionMilestoneBridge.cancelCrafter(crafter);
            if (!Aia2MachineGuard.mayTick(crafter)) {
                callback.cancel();
                return;
            }
            var input = crafter.asCraftInput();
            var recipe = CrafterBlock.getPotentialResults(level, input);
            if (recipe.isPresent()) {
                var output = recipe.get().value().assemble(input, level.registryAccess());
                if (!Aia2MachineGuard.mayProduce(crafter, output)) callback.cancel();
                else {
                    KeyProductionBridge.beginCrafter(crafter, recipe.get().value(), output);
                    ProductionMilestoneBridge.beginCrafter(crafter, recipe.get().value(), output);
                }
            }
        }
    }

    @Inject(method = "dispenseFrom(Lnet/minecraft/world/level/block/state/BlockState;Lnet/minecraft/server/level/ServerLevel;Lnet/minecraft/core/BlockPos;)V",
            at = @At("TAIL"), require = 1)
    private void aia2$recordCrafterProduction(BlockState state, ServerLevel level, BlockPos position, CallbackInfo callback) {
        if (level.getBlockEntity(position) instanceof CrafterBlockEntity crafter) {
            KeyProductionBridge.finishCrafter(crafter);
            ProductionMilestoneBridge.finishCrafter(crafter);
        }
    }
}
