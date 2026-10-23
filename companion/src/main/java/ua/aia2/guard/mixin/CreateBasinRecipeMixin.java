package ua.aia2.guard.mixin;

import net.minecraft.world.item.crafting.Recipe;
import net.minecraft.world.level.block.entity.BlockEntity;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Pseudo;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Coerce;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;
import ua.aia2.guard.Aia2MachineGuard;
import ua.aia2.guard.KeyProductionBridge;

/** Create 6.0.10 mixing/compacting: reject before simulated or actual input extraction. */
@Pseudo
@Mixin(targets = "com.simibubi.create.content.processing.basin.BasinRecipe", remap = false)
abstract class CreateBasinRecipeMixin {
    @Inject(method = "apply(Lcom/simibubi/create/content/processing/basin/BasinBlockEntity;Lnet/minecraft/world/item/crafting/Recipe;Z)Z",
            at = @At("HEAD"), cancellable = true, remap = false, require = 1)
    private static void aia2$guardBasin(@Coerce Object basin, Recipe<?> recipe, boolean test,
                                       CallbackInfoReturnable<Boolean> callback) {
        if (!Aia2MachineGuard.mayProcessRecipe((BlockEntity) basin, recipe)) callback.setReturnValue(false);
    }

    @Inject(method = "apply(Lcom/simibubi/create/content/processing/basin/BasinBlockEntity;Lnet/minecraft/world/item/crafting/Recipe;Z)Z",
            at = @At("RETURN"), remap = false, require = 1)
    private static void aia2$recordCompletedBasin(@Coerce Object basin, Recipe<?> recipe, boolean test,
                                                CallbackInfoReturnable<Boolean> callback) {
        if (!test && Boolean.TRUE.equals(callback.getReturnValue())) {
            KeyProductionBridge.finishedMachine((BlockEntity) basin, recipe);
        }
    }
}
