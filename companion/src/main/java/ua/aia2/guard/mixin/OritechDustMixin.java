package ua.aia2.guard.mixin;

import java.util.List;
import net.minecraft.world.item.crafting.Recipe;
import net.minecraft.world.item.crafting.RecipeHolder;
import net.minecraft.world.item.crafting.RecipeInput;
import net.minecraft.world.item.crafting.RecipeManager;
import net.minecraft.world.item.crafting.RecipeType;
import net.minecraft.world.level.Level;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Pseudo;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Redirect;
import ua.aia2.guard.Aia2MachineGuard;

/** Nine-small-dust compaction also queries the unfiltered recipe list. */
@Pseudo
@Mixin(targets="rearth.oritech.block.entity.processing.PulverizerBlockEntity",remap=false)
abstract class OritechDustMixin {
    @Redirect(method="combineSmallDusts(Ljava/util/List;Lnet/minecraft/world/level/Level;)V",
            at=@At(value="INVOKE",target="Lnet/minecraft/world/item/crafting/RecipeManager;getRecipesFor(Lnet/minecraft/world/item/crafting/RecipeType;Lnet/minecraft/world/item/crafting/RecipeInput;Lnet/minecraft/world/level/Level;)Ljava/util/List;"),
            remap=false,require=1)
    private static <I extends RecipeInput,T extends Recipe<I>> List<RecipeHolder<T>> aia2$guardCompaction(
            RecipeManager manager,RecipeType<T> type,I input,Level world) {
        return manager.getRecipesFor(type,input,world).stream()
                .filter(holder -> Aia2MachineGuard.mayProcessRecipeInCurrentTick(holder.value())).toList();
    }
}
