package ua.aia2.guard;

import java.lang.reflect.Method;
import java.lang.ref.ReferenceQueue;
import java.lang.ref.WeakReference;
import java.util.HashSet;
import java.util.List;
import java.util.Set;
import java.util.function.ToIntFunction;
import net.minecraft.core.component.DataComponents;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.alchemy.PotionContents;
import net.minecraft.world.item.crafting.Recipe;
import net.minecraft.world.item.crafting.RecipeHolder;
import net.neoforged.neoforge.fluids.FluidStack;
import net.neoforged.neoforge.fluids.crafting.SizedFluidIngredient;

/** Only native Create-generated brewing recipes get a conservative dynamic policy. */
public final class CreatePotionRecipeAccess {
    private static final ReferenceQueue<Recipe<?>> RETIRED = new ReferenceQueue<>();
    private static final Set<NativeIdentity> GENERATED = new HashSet<>();
    private static final class NativeIdentity extends WeakReference<Recipe<?>> {
        private final int hash;
        NativeIdentity(Recipe<?> recipe, ReferenceQueue<Recipe<?>> queue) {
            super(recipe, queue);
            hash = System.identityHashCode(recipe);
        }
        @Override public int hashCode() { return hash; }
        @Override public boolean equals(Object other) {
            if (this == other) return true;
            Recipe<?> recipe = get();
            return recipe != null && other instanceof NativeIdentity identity && recipe == identity.get();
        }
    }
    private static final String MIXING_CLASS = "com.simibubi.create.content.kinetics.mixer.MixingRecipe";
    private record Access(Method fluidInputs, Method fluidOutputs, Method itemOutputs) {}
    private static final ClassValue<Access> METHODS = new ClassValue<>() {
        @Override protected Access computeValue(Class<?> type) {
            try {
                return new Access(type.getMethod("getFluidIngredients"), type.getMethod("getFluidResults"),
                        type.getMethod("getRollableResultsAsItemStacks"));
            } catch (ReflectiveOperationException unavailable) {
                throw new IllegalStateException("Unsupported Create 6.0.10 ProcessingRecipe API", unavailable);
            }
        }
    };

    private CreatePotionRecipeAccess() {}

    /** Invoked at PotionMixingRecipes.createRecipes RETURN, not inferred from a class name. */
    public static synchronized void registerGenerated(List<?> holders) {
        discardRetired();
        for (Object value : holders) {
            if (!(value instanceof RecipeHolder<?> holder)) continue;
            String id = holder.id().toString();
            if ((id.startsWith("create:potion_mixing_vanilla_") || id.startsWith("create:potion_mixing_modded_"))
                    && holder.value().getClass().getName().equals(MIXING_CLASS)) {
                GENERATED.add(new NativeIdentity(holder.value(), RETIRED));
            }
        }
    }

    /** Unknown recipes/potions/components stay quarantined; native vanilla effects open at Nether. */
    public static int requiredStage(Recipe<?> recipe, ToIntFunction<String> itemStage) {
        synchronized (CreatePotionRecipeAccess.class) {
            discardRetired();
            if (!GENERATED.contains(new NativeIdentity(recipe, null))) return 100;
        }
        try {
            int required = 15;
            for (var ingredient : recipe.getIngredients()) {
                ItemStack[] alternatives = ingredient.getItems();
                if (alternatives.length == 0) return 100;
                for (ItemStack stack : alternatives) {
                    if (stack.isEmpty()) return 100;
                    required = Math.max(required, itemStage.applyAsInt(BuiltInRegistries.ITEM.getKey(stack.getItem()).toString()));
                    // Generated brewing ingredients carry no data-bearing item variants.
                    if (!stack.getComponentsPatch().isEmpty()) return 100;
                }
            }
            Access access = METHODS.get(recipe.getClass());
            Object items = access.itemOutputs().invoke(recipe);
            if (!(items instanceof List<?> itemResults)) return 100;
            for (Object value : itemResults) {
                if (!(value instanceof ItemStack stack) || stack.isEmpty()) return 100;
                required = Math.max(required, itemStage.applyAsInt(BuiltInRegistries.ITEM.getKey(stack.getItem()).toString()));
                if (!stack.getComponentsPatch().isEmpty()) return 100;
            }
            Object inputs = access.fluidInputs().invoke(recipe);
            if (!(inputs instanceof List<?> fluidInputs) || fluidInputs.isEmpty()) return 100;
            for (Object value : fluidInputs) {
                if (!(value instanceof SizedFluidIngredient ingredient)) return 100;
                FluidStack[] alternatives = ingredient.getFluids();
                if (alternatives.length == 0) return 100;
                for (FluidStack stack : alternatives) required = Math.max(required, fluidStage(stack));
            }
            Object outputs = access.fluidOutputs().invoke(recipe);
            if (!(outputs instanceof List<?> fluidOutputs) || fluidOutputs.isEmpty()) return 100;
            for (Object value : fluidOutputs) {
                if (!(value instanceof FluidStack stack)) return 100;
                required = Math.max(required, fluidStage(stack));
            }
            return required;
        } catch (ReflectiveOperationException | RuntimeException incompatible) {
            return 100;
        }
    }

    private static void discardRetired() {
        for (var identity = RETIRED.poll(); identity != null; identity = RETIRED.poll()) GENERATED.remove(identity);
    }

    private static int fluidStage(FluidStack stack) {
        if (stack.isEmpty()) return 100;
        String fluid = BuiltInRegistries.FLUID.getKey(stack.getFluid()).toString();
        if (!fluid.equals("create:potion") && !fluid.equals("minecraft:water")) return 100;
        int required = 15;
        PotionContents contents = stack.getOrDefault(DataComponents.POTION_CONTENTS, PotionContents.EMPTY);
        if (!contents.customEffects().isEmpty()) return 100;
        if (contents.potion().isPresent()) {
            var key = contents.potion().get().unwrapKey();
            if (key.isEmpty() || !key.get().location().getNamespace().equals("minecraft")) return 100;
        } else if (!fluid.equals("minecraft:water")) return 100;
        for (var component : stack.getComponents()) {
            String id = BuiltInRegistries.DATA_COMPONENT_TYPE.getKey(component.type()).toString();
            if (id.equals("minecraft:potion_contents")) continue;
            if (id.equals("create:potion_fluid_bottle_type") && component.value() instanceof Enum<?> type) {
                if (type.name().equals("LINGERING")) required = 30;
                else if (!type.name().equals("REGULAR") && !type.name().equals("SPLASH")) return 100;
            } else return 100;
        }
        return required;
    }
}
