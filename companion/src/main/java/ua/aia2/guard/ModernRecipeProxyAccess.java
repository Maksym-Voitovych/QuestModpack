package ua.aia2.guard;

import com.google.gson.JsonElement;
import com.mojang.serialization.JsonOps;
import com.mojang.serialization.MapCodec;
import java.lang.ref.ReferenceQueue;
import java.lang.ref.WeakReference;
import java.util.HashMap;
import java.util.Map;
import java.util.function.ToIntFunction;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.resources.RegistryOps;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.item.crafting.Recipe;
import net.minecraft.world.item.crafting.RecipeHolder;
import net.minecraft.world.item.crafting.SmeltingRecipe;
import net.minecraft.world.item.crafting.StonecutterRecipe;
import net.minecraft.world.level.ItemLike;

/** Provenance for MI 2.5.10's three native conversions, not a class-name bypass. */
public final class ModernRecipeProxyAccess {
    private record Origin(Recipe<?> original, String compostItem) {}
    private record RebindCheck(WeakReference<Recipe<?>> replacement, boolean unchanged) {}
    private static final ReferenceQueue<Recipe<?>> RETIRED = new ReferenceQueue<>();
    private static final Map<Identity, Origin> ORIGINS = new HashMap<>();
    private static final Map<Identity, RebindCheck> REBINDS = new HashMap<>();
    private static final String MACHINE = "aztech.modern_industrialization.machines.recipe.MachineRecipe";
    private static final class Identity extends WeakReference<Recipe<?>> {
        private final int hash;
        Identity(Recipe<?> value, ReferenceQueue<Recipe<?>> queue) { super(value, queue); hash=System.identityHashCode(value); }
        @Override public int hashCode() { return hash; }
        @Override public boolean equals(Object other) {
            if (this == other) return true;
            return get()!=null && other instanceof Identity key && get()==key.get();
        }
    }
    private ModernRecipeProxyAccess() {}

    /**
     * Rebind paid work after reload only when the complete registered MI codec agrees.
     * A matching ID alone is insufficient: inputs, fluids, energy, probabilities,
     * components and process conditions can all change under the same ID.
     * Generated MI conversions are deliberately excluded: their IDs are not native
     * RecipeManager holders, so a changed source must not revive stale provenance.
     */
    public static RecipeHolder<?> rebindUnchanged(RecipeHolder<?> cached, ServerLevel level) {
        if (cached==null || level==null || !cached.value().getClass().getName().equals(MACHINE)) return null;
        var current=level.getRecipeManager().byKey(cached.id()).orElse(null);
        if (current==null || !current.value().getClass().getName().equals(MACHINE)) return null;
        Recipe<?> previous=cached.value(), replacement=current.value();
        if (previous==replacement) return current;
        if (previous.getType()!=replacement.getType() || previous.getSerializer()!=replacement.getSerializer()) return null;
        synchronized (ModernRecipeProxyAccess.class) {
            discardRetired();
            var checked=REBINDS.get(new Identity(previous,null));
            if (checked!=null && checked.replacement().get()==replacement) return checked.unchanged()?current:null;
        }
        boolean unchanged=sameSerializedRecipe(previous,replacement,level);
        synchronized (ModernRecipeProxyAccess.class) {
            discardRetired();
            // Both sides are weak: paused machines must not retain retired recipe graphs.
            REBINDS.put(new Identity(previous,RETIRED),new RebindCheck(new WeakReference<>(replacement),unchanged));
        }
        return unchanged?current:null;
    }

    @SuppressWarnings("unchecked")
    private static boolean sameSerializedRecipe(Recipe<?> previous, Recipe<?> replacement, ServerLevel level) {
        try {
            var ops=RegistryOps.create(JsonOps.INSTANCE,level.registryAccess());
            var codec=((MapCodec<Recipe<?>>)(MapCodec<?>)previous.getSerializer().codec()).codec();
            JsonElement before=codec.encodeStart(ops,previous).result().orElse(null);
            JsonElement after=codec.encodeStart(ops,replacement).result().orElse(null);
            return before!=null && before.equals(after);
        } catch (RuntimeException invalidCodec) {
            // Preserve paid inputs rather than restarting or guessing at an invalid recipe.
            return false;
        }
    }

    public static synchronized void registerConversion(RecipeHolder<?> original, RecipeHolder<?> generated, String kind) {
        discardRetired();
        if (original==null || generated==null || !generated.value().getClass().getName().equals(MACHINE)) return;
        String suffix;
        if (kind.equals("smelting") && original.value() instanceof SmeltingRecipe) suffix="_exported_mi_furnace";
        else if (kind.equals("stonecutting") && original.value() instanceof StonecutterRecipe) suffix="_exported_mi_cutting_machine";
        else return;
        if (!generated.id().getNamespace().equals(original.id().getNamespace()) ||
                !generated.id().getPath().equals("/"+original.id().getPath()+suffix)) return;
        ORIGINS.put(new Identity(generated.value(),RETIRED),new Origin(original.value(),null));
    }

    public static synchronized void registerCompost(ItemLike input, RecipeHolder<?> generated) {
        discardRetired();
        if (input==null || input.asItem()==null || generated==null || !generated.value().getClass().getName().equals(MACHINE)) return;
        var id=BuiltInRegistries.ITEM.getKey(input.asItem());
        if (!generated.id().getNamespace().equals("modern_industrialization") ||
                !generated.id().getPath().equals("/"+id.getPath()+"_to_plant_oil")) return;
        ORIGINS.put(new Identity(generated.value(),RETIRED),new Origin(null,id.toString()));
    }

    public static int requiredStage(Recipe<?> recipe, ServerLevel level,
                                    ToIntFunction<Object> nativeStage, ToIntFunction<String> itemStage) {
        Origin origin;
        synchronized (ModernRecipeProxyAccess.class) { discardRetired(); origin=ORIGINS.get(new Identity(recipe,null)); }
        if (origin==null) return 100;
        if (origin.compostItem()!=null) return Math.max(itemStage.applyAsInt(origin.compostItem()),
                itemStage.applyAsInt("modern_industrialization:plant_oil_bucket"));
        int stage=nativeStage.applyAsInt(origin.original());
        if (stage==100) return 100; // Original removed/replaced on reload: no stale fallback.
        var output=origin.original().getResultItem(level.registryAccess());
        if (output.isEmpty()) return 100;
        String id=BuiltInRegistries.ITEM.getKey(output.getItem()).toString();
        if (id.matches("kubejs:aia2_(tech|arcane|epoch)_key_[0-9]{2}")) return 100;
        stage=Math.max(stage,itemStage.applyAsInt(id));
        if (CreativeManaGuard.isCreativeTablet(output)) stage=Math.max(stage,99);
        return stage;
    }

    private static void discardRetired() {
        for (var key=RETIRED.poll();key!=null;key=RETIRED.poll()) {
            ORIGINS.remove(key);
            REBINDS.remove(key);
        }
    }
}
