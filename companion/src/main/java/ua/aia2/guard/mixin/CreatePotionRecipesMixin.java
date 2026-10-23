package ua.aia2.guard.mixin;

import java.util.List;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Pseudo;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;
import ua.aia2.guard.CreatePotionRecipeAccess;

/** Record exact native dynamic recipe identities, including an already-generated cached list. */
@Pseudo
@Mixin(targets = "com.simibubi.create.content.fluids.potion.PotionMixingRecipes", remap = false)
abstract class CreatePotionRecipesMixin {
    @Inject(method = "createRecipes(Lnet/minecraft/world/level/Level;)Ljava/util/List;",
            at = @At("RETURN"), remap = false, require = 1)
    private static void aia2$registerNativeBrewing(CallbackInfoReturnable<List<?>> callback) {
        CreatePotionRecipeAccess.registerGenerated(callback.getReturnValue());
    }
}
