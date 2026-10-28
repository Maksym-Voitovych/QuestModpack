package ua.aia2.guard;

import com.google.gson.JsonObject;
import com.mojang.serialization.Codec;
import com.mojang.serialization.JsonOps;
import java.lang.reflect.InvocationTargetException;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;
import net.minecraft.core.Holder;
import net.minecraft.core.Registry;
import net.minecraft.resources.RegistryOps;
import net.minecraft.resources.ResourceKey;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.crafting.Ingredient;
import net.minecraft.world.item.crafting.Recipe;
import net.minecraft.world.level.block.entity.BlockEntity;

/** Current dependencies only. The separate historical ledger decides whether paid work may resume. */
public final class ClibanoDependencies {
    private static final String BASE = "com.stal111.forbidden_arcanus.common.";
    public record Snapshot(String fingerprint, boolean hasDependencies) {}
    private ClibanoDependencies() {}
    private static void require(boolean condition, String reason) {
        if (!condition) throw new IllegalArgumentException(reason);
    }
    private static Object call(Object object, String name) {
        try { return object.getClass().getMethod(name).invoke(object); }
        catch (InvocationTargetException failure) { throw new IllegalArgumentException("не вдалося прочитати залежності Clibano", failure.getCause()); }
        catch (ReflectiveOperationException failure) { throw new IllegalArgumentException("невідоме визначення Clibano", failure); }
    }
    @SuppressWarnings("unchecked")
    private static Registry<Object> registry(BlockEntity machine, String name) {
        try {
            Class<?> registries = Class.forName("com.stal111.forbidden_arcanus.core.registry.FARegistries", false, machine.getClass().getClassLoader());
            return ((ServerLevel)machine.getLevel()).registryAccess().registryOrThrow(
                    (ResourceKey<Registry<Object>>)registries.getField(name).get(null));
        } catch (ReflectiveOperationException failure) { throw new IllegalArgumentException("реєстр Clibano недоступний", failure); }
    }
    private static String id(Holder<?> holder) { return holder.unwrapKey().orElseThrow().location().toString(); }
    private static ForbiddenDependencies.IngredientView ingredients(Recipe<?> recipe) {
        require(recipe.getClass().getName().equals(BASE + "item.crafting.ClibanoRecipe"), "невідомий рецепт Clibano");
        List<Ingredient> inputs = recipe.getIngredients();
        require(inputs.size() >= 1 && inputs.size() <= 2, "непідтримуваний розмір рецепта Clibano");
        return ForbiddenDependencies.currentIngredients(inputs);
    }
    private static boolean matches(BlockEntity machine, ForbiddenDependencies.IngredientView view, int[] lanes) {
        List<ItemStack> inputs = new ArrayList<>();
        for (int lane : lanes) {
            require(lane >= 0 && lane < 2, "невідомий слот Clibano");
            try {
                ItemStack stack = (ItemStack)machine.getClass().getMethod("getStack", int.class).invoke(machine, lane + 3);
                if (!stack.isEmpty()) inputs.add(stack);
            } catch (ReflectiveOperationException failure) { throw new IllegalArgumentException("входи Clibano недоступні", failure); }
        }
        var rules = view.rules();
        if (inputs.size() != rules.size()) return false;
        if (rules.size() == 1) return rules.getFirst().test(inputs.getFirst());
        // Native RecipeMatcher is shapeless, not Forge's greedy pedestal matching.
        return rules.get(0).test(inputs.get(0)) && rules.get(1).test(inputs.get(1))
                || rules.get(0).test(inputs.get(1)) && rules.get(1).test(inputs.get(0));
    }
    public static boolean inputsMatch(BlockEntity machine, Recipe<?> recipe, int[] lanes) {
        return matches(machine, ingredients(recipe), lanes);
    }
    @SuppressWarnings("unchecked")
    public static String residueDefinition(BlockEntity machine, Holder<?> holder) {
        Object value = holder.value();
        require(value.getClass().getName().equals(BASE + "block.entity.clibano.residue.ResidueType"), "невідомий тип залишків");
        require(registry(machine, "RESIDUE_TYPE").get(ResourceLocation.parse(id(holder))) == value, "застаріле визначення залишків");
        Object combine = call(value, "combineInfo");
        int count = ((Number)call(combine, "requiredAmount")).intValue();
        ItemStack result = (ItemStack)call(combine, "result");
        require(count > 0 && count <= 64 && !result.isEmpty() && result.getCount() <= result.getMaxStackSize(), "непідтримуваний результат залишків");
        try {
            Codec<Object> codec = (Codec<Object>)value.getClass().getField("DIRECT_CODEC").get(null);
            return ForbiddenDependencies.hash(codec.encodeStart(RegistryOps.create(JsonOps.INSTANCE,
                    ((ServerLevel)machine.getLevel()).registryAccess()), value).getOrThrow());
        } catch (ReflectiveOperationException failure) { throw new IllegalArgumentException("кодек залишків недоступний", failure); }
    }
    public static Snapshot capture(BlockEntity machine, Recipe<?> recipe, Holder<?> enhancer, int[] lanes) {
        var ingredients = ingredients(recipe);
        require(matches(machine, ingredients, lanes), "входи Clibano не відповідають поточним тегам");
        return definitionSnapshot(machine, recipe, enhancer, ingredients);
    }
    /** Post-consumption observer: inspect definitions, never pretend the consumed inputs remain. */
    public static Snapshot definitionSnapshot(BlockEntity machine, Recipe<?> recipe, Holder<?> enhancer) {
        return definitionSnapshot(machine, recipe, enhancer, ingredients(recipe));
    }
    private static Snapshot definitionSnapshot(BlockEntity machine, Recipe<?> recipe, Holder<?> enhancer,
                                               ForbiddenDependencies.IngredientView ingredients) {
        JsonObject data = new JsonObject(); data.add("item_tags", ingredients.tags());
        JsonObject enhancers = new JsonObject();
        var registry = registry(machine, "ENHANCER_DEFINITION");
        var provider = ((ServerLevel)machine.getLevel()).registryAccess();
        Optional<?> required = (Optional<?>)call(recipe, "requiredEnhancer");
        if (required.isPresent()) {
            Holder<?> holder = (Holder<?>)required.get();
            enhancers.add(id(holder), ForbiddenDependencies.enhancer(holder, registry, provider));
        }
        if (enhancer != null) {
            require(registry.get(ResourceLocation.parse(id(enhancer))) == enhancer.value(), "застарілий фізичний підсилювач");
            if (!enhancers.has(id(enhancer))) enhancers.add(id(enhancer), ForbiddenDependencies.enhancer(enhancer, registry, provider));
        }
        data.add("enhancers", enhancers);
        Optional<?> residue = (Optional<?>)call(recipe, "residueChance");
        if (residue.isPresent()) {
            require(residue.get().getClass().getName().equals(BASE + "block.entity.clibano.residue.ResidueChance"), "невідомий шанс залишків");
            Holder<?> holder = (Holder<?>)call(residue.get(), "type");
            JsonObject definition = new JsonObject(); definition.addProperty("id", id(holder));
            definition.addProperty("definition", residueDefinition(machine, holder)); data.add("residue", definition);
        }
        return new Snapshot(ForbiddenDependencies.hash(data), ingredients.tags().size() > 0 || enhancers.size() > 0 || residue.isPresent());
    }
}
