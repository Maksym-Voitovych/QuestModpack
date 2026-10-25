package ua.aia2.guard.mixin;

import net.minecraft.world.item.crafting.Recipe;
import net.minecraft.world.level.block.entity.BlockEntity;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Pseudo;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Coerce;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;
import ua.aia2.guard.Aia2MachineGuard;

/** The three fluid processors override lookup and commit fluid outputs after super.craftItem. */
@Pseudo
@Mixin(targets={"rearth.oritech.block.entity.processing.CentrifugeBlockEntity",
        "rearth.oritech.block.entity.processing.RefineryBlockEntity",
        "rearth.oritech.block.entity.processing.TaintedRefineryBlockEntity"},remap=false)
abstract class OritechFluidMachineMixin {
    @Inject(method="craftFluids(Lrearth/oritech/init/recipes/OritechRecipe;)V",
            at=@At("HEAD"),cancellable=true,remap=false,require=1)
    private void aia2$guardFluidCommit(@Coerce Object recipe,CallbackInfo callback) {
        if (!(recipe instanceof Recipe<?> nativeRecipe) ||
                !Aia2MachineGuard.mayProcessRecipe((BlockEntity)(Object)this,nativeRecipe)) callback.cancel();
    }
}
