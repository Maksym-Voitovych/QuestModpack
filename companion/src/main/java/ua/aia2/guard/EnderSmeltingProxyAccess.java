package ua.aia2.guard;

import java.lang.reflect.Method;
import java.util.List;
import java.util.function.ToIntFunction;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.crafting.RecipeHolder;
import net.minecraft.world.item.crafting.SmeltingRecipe;
import net.neoforged.neoforge.common.crafting.SizedIngredient;

/** Validates the exact registered furnace conversions made by EnderIO 8.2.12-beta. */
public final class EnderSmeltingProxyAccess {
    private static final String ALLOY = "com.enderio.enderio.content.machines.alloy.AlloySmeltingRecipe";
    private static final String PREFIX = "smelting/";
    private record Access(Method smelting, Method inputs, Method output, Method experience) {}
    private static final Access UNAVAILABLE = new Access(null, null, null, null);
    private static final ClassValue<Access> METHODS = new ClassValue<>() {
        @Override protected Access computeValue(Class<?> type) {
            if (!type.getName().equals(ALLOY)) return UNAVAILABLE;
            try {
                return new Access(type.getMethod("isSmelting"), type.getMethod("inputs"),
                        type.getMethod("output"), type.getMethod("experience"));
            } catch (ReflectiveOperationException | RuntimeException | LinkageError unavailable) {
                return UNAVAILABLE;
            }
        }
    };

    private EnderSmeltingProxyAccess() {}

    /**
     * A data recipe can set is_smelting itself. The shared source Ingredient identity,
     * current manager entries and full result establish the native conversion instead.
     * EnderIO's MachineRecipe#getResultItem is empty, so use its output() accessor.
     */
    public static int requiredStage(RecipeHolder<?> converted, ServerLevel level,
            ToIntFunction<String> recipeStage, ToIntFunction<String> itemStage) {
        if (converted == null || level == null || recipeStage == null || itemStage == null) return 100;
        try {
            Object recipe = converted.value();
            Access access = METHODS.get(recipe.getClass());
            if (access == UNAVAILABLE || !Boolean.TRUE.equals(access.smelting().invoke(recipe))) return 100;
            var manager = level.getRecipeManager();
            var canonical = manager.byKey(converted.id()).orElse(null);
            if (canonical == null || canonical.value() != recipe) return 100;

            String path = converted.id().getPath();
            if (!converted.id().getNamespace().equals("enderio") || !path.startsWith(PREFIX)) return 100;
            int separator = path.indexOf('/', PREFIX.length());
            if (separator <= PREFIX.length() || separator == path.length() - 1) return 100;
            var sourceId = ResourceLocation.fromNamespaceAndPath(
                    path.substring(PREFIX.length(), separator), path.substring(separator + 1));
            var sourceHolder = manager.byKey(sourceId).orElse(null);
            if (sourceHolder == null || !(sourceHolder.value() instanceof SmeltingRecipe source)) return 100;
            var sourceInputs = source.getIngredients();
            if (sourceInputs.isEmpty() || sourceInputs.getFirst().isEmpty()) return 100;

            Object inputs = access.inputs().invoke(recipe);
            if (!(inputs instanceof List<?> sizedInputs) || sizedInputs.size() != 1
                    || !(sizedInputs.getFirst() instanceof SizedIngredient sized)
                    || sized.count() != 1 || sized.ingredient() != sourceInputs.getFirst()) return 100;
            Object result = access.output().invoke(recipe);
            var originalOutput = source.getResultItem(level.registryAccess());
            if (!(result instanceof ItemStack output) || output.isEmpty() || originalOutput.isEmpty()
                    || output.getCount() != originalOutput.getCount()
                    || !ItemStack.isSameItemSameComponents(output, originalOutput)) return 100;
            Object experience = access.experience().invoke(recipe);
            if (!(experience instanceof Float xp) || Float.compare(xp, source.getExperience()) != 0) return 100;

            String outputId = BuiltInRegistries.ITEM.getKey(output.getItem()).toString();
            if (outputId.matches("kubejs:aia2_(tech|arcane|epoch)_key_[0-9]{2}")
                    || KeyProductionBridge.isKeyOutput(outputId)) return 100;
            int required = Math.max(recipeStage.applyAsInt(sourceId.toString()), itemStage.applyAsInt(outputId));
            if (CreativeManaGuard.isCreativeTablet(output)) required = Math.max(required, 99);
            return required;
        } catch (ReflectiveOperationException | RuntimeException | LinkageError incompatible) {
            return 100;
        }
    }
}
