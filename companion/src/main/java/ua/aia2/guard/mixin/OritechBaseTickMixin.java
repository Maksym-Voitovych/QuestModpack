package ua.aia2.guard.mixin;

import java.util.Optional;
import net.minecraft.world.item.crafting.RecipeHolder;
import net.minecraft.world.level.block.entity.BlockEntity;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Pseudo;
import org.spongepowered.asm.mixin.Shadow;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Coerce;
import org.spongepowered.asm.mixin.injection.Redirect;
import ua.aia2.guard.Aia2MachineGuard;

/** Filter after AtomicForge adjusts capacity; filtering inside super would erase RF. */
@Pseudo
@Mixin(targets="rearth.oritech.block.base.entity.MachineBlockEntity",remap=false)
abstract class OritechBaseTickMixin {
    @Shadow(remap=false) protected abstract Optional<RecipeHolder<?>> getRecipe();

    @Redirect(method="serverTick(Lnet/minecraft/world/level/Level;Lnet/minecraft/core/BlockPos;Lnet/minecraft/world/level/block/state/BlockState;Lrearth/oritech/api/networking/NetworkedBlockEntity;)V",
            at=@At(value="INVOKE",target="Lrearth/oritech/block/base/entity/MachineBlockEntity;getRecipe()Ljava/util/Optional;"),
            remap=false,require=1)
    private Optional<RecipeHolder<?>> aia2$guardTickSelection(@Coerce Object receiver) {
        return getRecipe().filter(holder ->
                Aia2MachineGuard.mayProcessRecipe((BlockEntity)(Object)this,holder.value()));
    }
}
