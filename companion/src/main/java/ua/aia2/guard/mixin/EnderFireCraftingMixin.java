package ua.aia2.guard.mixin;

import java.util.List;
import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.item.crafting.Recipe;
import net.minecraft.world.level.Level;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Pseudo;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Coerce;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;
import ua.aia2.guard.FireWorksiteAccess;

@Pseudo
@Mixin(targets = "com.enderio.enderio.content.fire_crafting.FireCraftingManager", remap = false)
abstract class EnderFireCraftingMixin {
    @Inject(method = "spawnInfinityDrops(Lnet/minecraft/world/level/Level;Lnet/minecraft/core/BlockPos;Lcom/enderio/enderio/content/fire_crafting/FireCraftingRecipe;)V",
            at = @At("HEAD"), cancellable = true, remap = false, require = 1)
    private static void aia2$ownedWorksite(Level level, BlockPos pos, @Coerce Object recipe, CallbackInfo callback) {
        if (!(recipe instanceof Recipe<?> current) || !FireWorksiteAccess.maySpawn(level, pos, current)) callback.cancel();
    }

    @Inject(method = "getRecipes(Lnet/minecraft/world/level/Level;)Ljava/util/List;", at = @At("HEAD"),
            cancellable = true, remap = false, require = 1)
    private void aia2$currentRecipes(Level level, CallbackInfoReturnable<List<?>> callback) {
        if (level instanceof ServerLevel server) callback.setReturnValue(FireWorksiteAccess.recipes(server));
    }
}
