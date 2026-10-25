package ua.aia2.guard.mixin;

import net.minecraft.world.level.Level;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Pseudo;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Redirect;

/** Restore the same strict noon window on each vanilla Minecraft day. */
@Pseudo
@Mixin(targets = "elucent.rootsclassic.mutation.mutations.MutagenRadiantDaisyRecipe", remap = false)
abstract class RootsMutationRadiantMixin {
    @Redirect(method = "matches(Ljava/util/List;Lnet/minecraft/world/level/Level;Lnet/minecraft/core/BlockPos;Lnet/minecraft/world/entity/player/Player;)Z",
            at = @At(value = "INVOKE", target = "Lnet/minecraft/world/level/Level;getDayTime()J"),
            remap = false, require = 2, expect = 2, allow = 2)
    private long aia2$mutationTimeOfDay(Level level) {
        return Math.floorMod(level.getDayTime(), 24000L);
    }
}
