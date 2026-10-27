package ua.aia2.guard.mixin;

import net.minecraft.core.BlockPos;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.state.BlockState;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Pseudo;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Coerce;
import org.spongepowered.asm.mixin.injection.Redirect;
import ua.aia2.guard.ProjectEStorageAccess;

@Pseudo
@Mixin(targets = "moze_intel.projecte.gameObjs.block_entities.DMPedestalBlockEntity", remap = false)
abstract class ProjectEPedestalPassiveMixin {
    @Redirect(method = "tickServer(Lnet/minecraft/world/level/Level;Lnet/minecraft/core/BlockPos;Lnet/minecraft/world/level/block/state/BlockState;Lmoze_intel/projecte/gameObjs/block_entities/DMPedestalBlockEntity;)V",
            at = @At(value = "INVOKE", target = "Lmoze_intel/projecte/api/capabilities/item/IPedestalItem;updateInPedestal(Lnet/minecraft/world/item/ItemStack;Lnet/minecraft/world/level/Level;Lnet/minecraft/core/BlockPos;Lnet/minecraft/world/level/block/entity/BlockEntity;)Z"), remap = false, require = 1)
    private static boolean aia2$guardPedestalPassive(@Coerce Object capability, ItemStack stack, Level level, BlockPos pos, BlockEntity receiver,
                                                    Level tickLevel, BlockPos tickPos, BlockState state, @Coerce Object originalTile) {
        return originalTile == receiver && tickLevel == level && tickPos.equals(pos)
                && ProjectEStorageAccess.pedestal(capability, stack, level, pos, receiver);
    }
}
