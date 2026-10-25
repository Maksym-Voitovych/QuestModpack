package ua.aia2.guard;

import net.minecraft.world.item.crafting.RecipeHolder;
import net.neoforged.neoforge.items.IItemHandler;

/** Implemented on the exact Roots 1.5.10 altar by its optional mixin. */
public interface RootsAltarAccess {
    RecipeHolder<?> getCurrentRitual();
    void setCurrentRitual(RecipeHolder<?> holder);
    int getProgress();
    void setProgress(int progress);
    IItemHandler aia2$getInventory();
    RootsRitualProof.Attempt aia2$getAttempt();
    void aia2$setAttempt(RootsRitualProof.Attempt attempt);
}
