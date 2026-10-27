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
@Mixin(targets = "moze_intel.projecte.gameObjs.block_entities.AlchBlockEntityChest", remap = false)
abstract class ProjectEChestPassiveMixin {
    @Redirect(method = "tickServer(Lnet/minecraft/world/level/Level;Lnet/minecraft/core/BlockPos;Lnet/minecraft/world/level/block/state/BlockState;Lmoze_intel/projecte/gameObjs/block_entities/AlchBlockEntityChest;)V",
            at = @At(value = "INVOKE", target = "Lmoze_intel/projecte/api/capabilities/item/IAlchChestItem;updateInAlchChest(Lnet/minecraft/world/level/Level;Lnet/minecraft/core/BlockPos;Lnet/minecraft/world/item/ItemStack;)Z"), remap = false, require = 1)
    private static boolean aia2$guardChestPassive(@Coerce Object capability, Level level, BlockPos pos, ItemStack stack,
                                                 Level tickLevel, BlockPos tickPos, BlockState state, @Coerce Object originalTile) {
        return tickLevel == level && tickPos.equals(pos) && originalTile instanceof BlockEntity receiver
                && ProjectEStorageAccess.chest(capability, level, pos, stack, receiver);
    }
}
