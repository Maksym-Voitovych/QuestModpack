package ua.aia2.guard.mixin;

import java.util.List;
import net.minecraft.core.BlockPos;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;
import org.spongepowered.asm.mixin.Final;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Pseudo;
import org.spongepowered.asm.mixin.Shadow;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

/** Roots 1.5.10 forgot to reject missing entries before its multiset matcher. */
@Pseudo
@Mixin(targets = "elucent.rootsclassic.mutation.MutagenRecipe", remap = false)
abstract class RootsMutationIngredientsMixin {
    @Shadow(remap = false) @Final List<ItemStack> inputs;

    @Inject(method = "matches(Ljava/util/List;Lnet/minecraft/world/level/Level;Lnet/minecraft/core/BlockPos;Lnet/minecraft/world/entity/player/Player;)Z",
            at = @At("HEAD"), cancellable = true, remap = false, require = 1)
    private void aia2$requireAllMutationInputs(List<ItemStack> items, Level level, BlockPos pos,
                                              Player player, CallbackInfoReturnable<Boolean> callback) {
        // Keep native isSameItem matching, duplicate entries, count/component
        // semantics and all block/dimension/effect checks. Equal cardinality
        // makes its remove-on-match algorithm require every ingredient entry.
        if (items == null || items.size() != inputs.size()) callback.setReturnValue(false);
    }
}
