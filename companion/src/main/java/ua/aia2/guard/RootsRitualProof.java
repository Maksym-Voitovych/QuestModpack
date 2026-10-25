package ua.aia2.guard;

import java.util.ArrayList;
import java.util.List;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.crafting.Ingredient;
import net.minecraft.world.item.crafting.Recipe;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.neoforged.neoforge.items.IItemHandler;

/** Checks the real altar inventory before effect and after native emptyAltar. */
public final class RootsRitualProof {
    public record Attempt(Recipe<?> recipe, String team, int inputUnits) {}
    private RootsRitualProof() {}

    public static Attempt begin(BlockEntity altar, Recipe<?> recipe, IItemHandler inventory) {
        if (!(altar.getLevel() instanceof ServerLevel) || inventory == null || recipe == null
                || !Aia2MachineGuard.mayProcessRecipe(altar, recipe)) return null;
        String team = Aia2MachineGuard.getOwner(altar);
        if (team == null || team.isBlank()) return null;
        List<Ingredient> ingredients = recipe.getIngredients();
        if (ingredients.isEmpty() || ingredients.size() > 3 || inventory.getSlots() != 3) return null;
        var inputs = new ArrayList<ItemStack>(3);
        int units = 0;
        for (int slot = 0; slot < inventory.getSlots(); slot++) {
            ItemStack stack = inventory.getStackInSlot(slot);
            if (!stack.isEmpty()) { inputs.add(stack); units += stack.getCount(); }
        }
        // Roots matches one nonempty slot per ingredient, including tag inputs.
        if (inputs.size() != ingredients.size() || units <= 0
                || !matches(ingredients, inputs, new boolean[inputs.size()], 0)) return null;
        return new Attempt(recipe, team, units);
    }

    private static boolean matches(List<Ingredient> ingredients, List<ItemStack> inputs, boolean[] used, int index) {
        if (index == ingredients.size()) return true;
        for (int slot = 0; slot < inputs.size(); slot++) {
            if (!used[slot] && ingredients.get(index).test(inputs.get(slot))) {
                used[slot] = true;
                if (matches(ingredients, inputs, used, index + 1)) return true;
                used[slot] = false;
            }
        }
        return false;
    }

    public static void finish(BlockEntity altar, IItemHandler inventory, Attempt attempt) {
        if (attempt == null || !(altar.getLevel() instanceof ServerLevel) || inventory == null
                || attempt.inputUnits() <= 0 || !attempt.team().equals(Aia2MachineGuard.getOwner(altar))) return;
        for (int slot = 0; slot < inventory.getSlots(); slot++) {
            if (!inventory.getStackInSlot(slot).isEmpty()) return;
        }
        // The shared bridge rechecks live policy, exact recipe identity,
        // serializer, output and configured team stage before writing SavedData.
        ProductionMilestoneBridge.finishedMachine(altar, attempt.recipe());
    }
}
