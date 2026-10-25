package ua.aia2.guard.mixin;

import java.util.List;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.crafting.Recipe;
import net.minecraft.world.level.block.entity.BlockEntity;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Pseudo;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Coerce;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;
import ua.aia2.guard.Aia2MachineGuard;

/** Oritech's cached holder uses a recipe TYPE as its ID: inspect value identity. */
@Pseudo
@Mixin(targets={"rearth.oritech.block.base.entity.MachineBlockEntity",
        "rearth.oritech.block.entity.processing.CentrifugeBlockEntity",
        "rearth.oritech.block.entity.processing.RefineryBlockEntity",
        "rearth.oritech.block.entity.processing.CoolerBlockEntity",
        "rearth.oritech.block.entity.processing.TaintedRefineryBlockEntity"},remap=false)
abstract class OritechMachineMixin {
    @Inject(method="craftItem(Lrearth/oritech/init/recipes/OritechRecipe;Ljava/util/List;Ljava/util/List;)V",
            at=@At("HEAD"),cancellable=true,remap=false,require=1)
    private void aia2$guardItemCommit(@Coerce Object recipe,List<ItemStack> outputs,List<ItemStack> inputs,CallbackInfo callback) {
        if (!(recipe instanceof Recipe<?> nativeRecipe) ||
                !Aia2MachineGuard.mayProcessRecipe((BlockEntity)(Object)this,nativeRecipe)) callback.cancel();
    }
}
