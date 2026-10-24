package ua.aia2.guard.mixin;

import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.item.crafting.RecipeHolder;
import net.minecraft.world.level.block.entity.BlockEntity;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Pseudo;
import org.spongepowered.asm.mixin.Shadow;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;
import ua.aia2.guard.Aia2MachineGuard;

/** DE 3.1.4: packet-started and NBT-restored fusion recipes bypass lookup hooks. */
@Pseudo
@Mixin(targets = "com.brandon3055.draconicevolution.blocks.tileentity.TileFusionCraftingCore", remap = false)
abstract class DraconicFusionCoreMixin {
    @Shadow(remap = false) public abstract boolean isCrafting();
    @Shadow(remap = false) public abstract RecipeHolder<?> getActiveRecipe();
    @Shadow(remap = false) public abstract void cancelCraft();

    @Inject(method = "tick()V", at = @At("HEAD"), cancellable = true, remap = false, require = 1)
    private void aia2$guardCachedFusion(CallbackInfo callback) {
        BlockEntity core = (BlockEntity) (Object) this;
        if (!(core.getLevel() instanceof ServerLevel) || !isCrafting()) return;
        RecipeHolder<?> holder = getActiveRecipe();
        if (holder != null && !Aia2MachineGuard.mayProcessRecipe(core, holder.value())) {
            // DE's native cancellation clears injector charging requirements;
            // it neither shrinks catalyst/ingredient stacks nor clears progress data.
            cancelCraft();
            callback.cancel();
        }
    }
}
