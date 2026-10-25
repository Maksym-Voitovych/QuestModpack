package ua.aia2.guard.mixin;

import java.util.Optional;
import net.minecraft.world.item.crafting.RecipeHolder;
import net.minecraft.world.level.block.entity.BlockEntity;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Pseudo;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;
import ua.aia2.guard.Aia2MachineGuard;

/** Only direct-list overrides: base lookup is filtered after polymorphic dispatch. */
@Pseudo
@Mixin(targets={"rearth.oritech.block.entity.processing.CentrifugeBlockEntity",
        "rearth.oritech.block.entity.processing.RefineryBlockEntity",
        "rearth.oritech.block.entity.processing.CoolerBlockEntity",
        "rearth.oritech.block.entity.processing.TaintedRefineryBlockEntity"},remap=false)
abstract class OritechRecipeLookupMixin {
    @Inject(method="getRecipe()Ljava/util/Optional;",at=@At("RETURN"),cancellable=true,remap=false,require=1)
    private void aia2$guardCachedLookup(CallbackInfoReturnable<Optional<RecipeHolder<?>>> callback) {
        callback.setReturnValue(callback.getReturnValue().filter(holder ->
                Aia2MachineGuard.mayProcessRecipe((BlockEntity)(Object)this,holder.value())));
    }
}
