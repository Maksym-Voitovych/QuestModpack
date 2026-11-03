package ua.aia2.guard;

import com.google.gson.JsonElement;
import com.google.gson.JsonParser;
import com.mojang.serialization.JsonOps;
import com.mojang.serialization.MapCodec;
import java.lang.reflect.Field;
import java.lang.reflect.Method;
import net.minecraft.resources.RegistryOps;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.item.crafting.Recipe;

/** Reviewed CDG1.3.15 Lines recipe; no optional classes are linked at load time. */
public final class CdgPanelAccess {
    private static final String RECIPE_CLASS = "com.jesz.createdieselgenerators.content.molds.CompressionMoldingRecipe";
    private static final String MOLD_CLASS = "com.jesz.createdieselgenerators.content.molds.MoldType";
    private static final String LINES = "createdieselgenerators:lines";
    private static final JsonElement EXPECTED = JsonParser.parseString("""
            {"ingredients":[{"tag":"c:plates/iron"}],"mold":"createdieselgenerators:lines",
             "results":[{"id":"createdieselgenerators:sheet_metal_panel","count":4}]}
            """);
    private record MoldAccess(Field field, Method id) {}
    private static final ClassValue<MoldAccess> MOLDS = new ClassValue<>() {
        @Override protected MoldAccess computeValue(Class<?> type) {
            try {
                Field field = type.getField("moldType");
                if (!field.getType().getName().equals(MOLD_CLASS))
                    throw new NoSuchFieldException("Unexpected CDG moldType class");
                return new MoldAccess(field, field.getType().getMethod("getId"));
            } catch (ReflectiveOperationException unsupported) {
                throw new IllegalStateException("Unsupported CDG compression Mold API", unsupported);
            }
        }
    };

    private CdgPanelAccess() {}

    /** The public CDG field can change independently of its serialized params. */
    public static boolean isCurrentMold(Recipe<?> recipe) {
        if (recipe == null || !recipe.getClass().getName().equals(RECIPE_CLASS)) return false;
        try {
            MoldAccess access = MOLDS.get(recipe.getClass());
            Object mold = access.field().get(recipe);
            if (mold == null || !mold.getClass().getName().equals(MOLD_CLASS)) return false;
            Object id = access.id().invoke(mold);
            return id instanceof ResourceLocation && LINES.equals(id.toString());
        } catch (ReflectiveOperationException | RuntimeException unsupported) {
            return false;
        }
    }

    /**
     * Run once per RecipeManager generation by the bridge's existing identity index.
     * Decode and re-encode the expected recipe with the same actual serializer:
     * defaults/field ordering may normalize, changed inputs/mold/output/chance may not.
     * result(), rather than resultOrPartial(), rejects partial codec failures.
     */
    @SuppressWarnings("unchecked")
    public static boolean matchesRecipe(Recipe<?> recipe, ServerLevel level) {
        if (level == null || !isCurrentMold(recipe)) return false;
        try {
            var ops = RegistryOps.create(JsonOps.INSTANCE, level.registryAccess());
            var codec = ((MapCodec<Recipe<?>>) (MapCodec<?>) recipe.getSerializer().codec()).codec();
            Recipe<?> expected = codec.parse(ops, EXPECTED.deepCopy()).result().orElse(null);
            if (expected == null || !isCurrentMold(expected)) return false;
            JsonElement before = codec.encodeStart(ops, expected).result().orElse(null);
            JsonElement actual = codec.encodeStart(ops, recipe).result().orElse(null);
            return before != null && before.equals(actual);
        } catch (RuntimeException unsupported) {
            return false;
        }
    }
}
