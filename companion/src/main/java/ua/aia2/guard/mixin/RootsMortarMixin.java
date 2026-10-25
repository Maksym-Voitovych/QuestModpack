package ua.aia2.guard.mixin;

import java.util.Optional;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.item.crafting.Recipe;
import net.minecraft.world.item.crafting.RecipeHolder;
import net.minecraft.world.item.crafting.RecipeInput;
import net.minecraft.world.item.crafting.RecipeManager;
import net.minecraft.world.item.crafting.RecipeType;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.entity.BlockEntity;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Pseudo;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Redirect;
import ua.aia2.guard.Aia2MachineGuard;

/** Roots Classic 1.5.10: pestle interaction runs outside BlockEntityTicker. */
@Pseudo
@Mixin(targets = "elucent.rootsclassic.block.mortar.MortarBlockEntity", remap = false)
abstract class RootsMortarMixin {
    @Redirect(method = "tryActivateRecipe(Lnet/minecraft/world/entity/player/Player;Lnet/minecraft/world/level/block/state/BlockState;)Lnet/minecraft/world/ItemInteractionResult;",
            at = @At(value = "INVOKE", target = "Lnet/minecraft/world/item/crafting/RecipeManager;getRecipeFor(Lnet/minecraft/world/item/crafting/RecipeType;Lnet/minecraft/world/item/crafting/RecipeInput;Lnet/minecraft/world/level/Level;)Ljava/util/Optional;"),
            remap = false, require = 1)
    private <I extends RecipeInput, T extends Recipe<I>> Optional<RecipeHolder<T>> aia2$guardPestleLookup(
            RecipeManager manager, RecipeType<T> type, I input, Level level) {
        Optional<RecipeHolder<T>> result = manager.getRecipeFor(type, input, level);
        if (!(level instanceof ServerLevel)) return result;
        // Filter before Roots assembles/spawns the spell powder and clears inputs.
        // An empty result uses its ordinary invalid-recipe path; insert/retrieve
        // interactions and client rendering retain their native behavior.
        return result.filter(holder -> Aia2MachineGuard.mayProcessRecipe(
                (BlockEntity) (Object) this, holder.value()));
    }
}
