package ua.aia2.guard;

import java.lang.reflect.Method;
import java.util.ArrayList;
import java.util.IdentityHashMap;
import java.util.List;
import java.util.Map;
import java.util.TreeMap;
import java.util.WeakHashMap;
import java.nio.file.Files;
import com.mojang.logging.LogUtils;
import net.minecraft.core.BlockPos;
import net.minecraft.core.HolderLookup;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.registries.Registries;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.nbt.ListTag;
import net.minecraft.nbt.NbtUtils;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.crafting.Recipe;
import net.minecraft.world.item.crafting.RecipeHolder;
import net.minecraft.world.item.crafting.RecipeType;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.saveddata.SavedData;
import net.minecraft.world.level.dimension.DimensionType;
import net.minecraft.world.level.storage.LevelResource;

/** Explicitly owned fire-crafting bases, never an inferred nearby player or flame. */
public final class FireWorksiteAccess {
    static final String DATA_NAME = "aia2_fire_worksites_v1";
    private static final int LIMIT = 65536;
    private static final String CLASS = "com.enderio.enderio.content.fire_crafting.FireCraftingRecipe";
    private static final org.slf4j.Logger LOGGER = LogUtils.getLogger();
    private record Site(String team, BlockState base) {}
    private record Definition(Method base, Method dimension, List<ItemStack> outputs, Block after) {}
    private static final Map<ServerLevel, SiteData> DATA = new WeakHashMap<>();
    private static final Map<ServerLevel, RecipeCache> RECIPES = new WeakHashMap<>();
    private static final class RecipeCache {
        Object generation;
        List<RecipeHolder<?>> recipes = List.of();
        final IdentityHashMap<Recipe<?>, Definition> definitions = new IdentityHashMap<>();
    }
    private FireWorksiteAccess() {}
    public static void clearRuntime() { DATA.clear(); RECIPES.clear(); }

    /** Raw current list, not a team filter. Fixes EnderIO's manager-identity-only reload cache. */
    @SuppressWarnings({"unchecked", "rawtypes"})
    public static List<RecipeHolder<?>> recipes(ServerLevel level) {
        var cache = RECIPES.computeIfAbsent(level, ignored -> new RecipeCache());
        Object generation = level.getRecipeManager().getRecipes();
        if (cache.generation != generation) {
            var type = BuiltInRegistries.RECIPE_TYPE.get(ResourceLocation.parse("enderio:fire_crafting"));
            cache.recipes = type == null ? List.of() : List.copyOf(
                    level.getRecipeManager().getAllRecipesFor((RecipeType) type));
            cache.definitions.clear();
            cache.generation = generation;
        }
        return cache.recipes;
    }

    private static Definition definition(ServerLevel level, Recipe<?> recipe) {
        recipes(level);
        var cache = RECIPES.get(level);
        if (!cache.definitions.containsKey(recipe)) {
            Definition checked = null;
            if (recipe != null && CLASS.equals(recipe.getClass().getName())
                    && cache.recipes.stream().anyMatch(holder -> holder.value() == recipe)) {
                try {
                    var type = recipe.getClass();
                    var outputs = new ArrayList<ItemStack>();
                    for (Object result : (List<?>) type.getMethod("results").invoke(recipe)) {
                        var resultType = result.getClass();
                        ItemStack stack = ((ItemStack) resultType.getMethod("result").invoke(result)).copy();
                        int min = ((Number) resultType.getMethod("minCount").invoke(result)).intValue();
                        int max = ((Number) resultType.getMethod("maxCount").invoke(result)).intValue();
                        float chance = ((Number) resultType.getMethod("chance").invoke(result)).floatValue();
                        if (stack.isEmpty() || min < 0 || max < min || max > stack.getMaxStackSize()
                                || !Float.isFinite(chance) || chance < 0 || chance > 1) {
                            throw new IllegalArgumentException("Unsafe EnderIO fire result bounds/chance");
                        }
                        if (chance > 0 && max > 0) { stack.setCount(max); outputs.add(stack); }
                    }
                    var after = (java.util.Optional<?>) type.getMethod("blockAfterBurning").invoke(recipe);
                    checked = new Definition(type.getMethod("isBaseValid", Block.class),
                            type.getMethod("isDimensionValid", net.minecraft.resources.ResourceKey.class),
                            List.copyOf(outputs), after.isPresent() ? (Block) after.get() : null);
                } catch (ReflectiveOperationException | RuntimeException unsupported) { /* Fail closed. */ }
            }
            cache.definitions.put(recipe, checked);
        }
        return cache.definitions.get(recipe);
    }

    private static boolean matches(ServerLevel level, BlockPos base, Recipe<?> recipe, Definition def) {
        if (def == null) return false;
        try {
            return Boolean.TRUE.equals(def.base().invoke(recipe, level.getBlockState(base).getBlock()))
                    && Boolean.TRUE.equals(def.dimension().invoke(recipe, level.dimension()));
        } catch (ReflectiveOperationException | RuntimeException unsupported) { return false; }
    }

    private static boolean permits(ServerLevel level, String team, Recipe<?> recipe, Definition def) {
        return def != null && permitsOutputs(level, team, recipe, def.outputs(), def.after());
    }

    private static boolean permitsOutputs(ServerLevel level, String team, Recipe<?> recipe, List<ItemStack> outputs, Block after) {
        if (outputs == null || outputs.isEmpty() || !Aia2MachineGuard.mayObserveStage(team, 19)
                || !Aia2MachineGuard.mayProcessOwnedRecipe(level, team, recipe)) return false;
        for (ItemStack stack : outputs) {
            if (stack == null || stack.isEmpty()) return false;
            String id = BuiltInRegistries.ITEM.getKey(stack.getItem()).toString();
            if (KeyProductionBridge.isKeyOutput(id) || id.matches("kubejs:aia2_(tech|arcane|epoch)_key_[0-9]{2}")
                    || !Aia2MachineGuard.mayUseItemByTeam(id, team)
                    || CreativeManaGuard.isCreativeTablet(stack) && !Aia2MachineGuard.mayObserveStage(team, 99)) return false;
        }
        return after == null || Aia2MachineGuard.mayObserveStage(team,
                Aia2MachineGuard.getRequiredStage(BuiltInRegistries.BLOCK.getKey(after).toString()));
    }

    public static boolean isWorksiteBase(ServerLevel level, BlockPos base) {
        for (var holder : recipes(level)) if (matches(level, base, holder.value(), definition(level, holder.value()))) return true;
        return false;
    }

    /** Explicit claim gesture; validating a real live/synchronized player never grants progress. */
    public static String claim(ServerPlayer player, BlockPos base) {
        if (!(player.level() instanceof ServerLevel level) || !level.getServer().isSameThread()) return "Робоча основа потребує серверного гравця.";
        String team = Aia2MachineGuard.synchronizedPlayerTeam(player);
        if (team.isBlank() || !Aia2MachineGuard.mayObserveStage(team, 19)) return "Вогняне ремесло відкривається в епосі 19; дочекайтеся синхронізації команди.";
        if (data(level).blocked) return "Дані вогняних майданчиків пошкоджено. Захист закритий; оригінал збережено. Адміністратору: перевірте журнал сервера.";
        for (var holder : recipes(level)) {
            var def = definition(level, holder.value());
            if (matches(level, base, holder.value(), def)) {
                if (!permits(level, team, holder.value(), def)) return "Рецепт або його результати ще недоступні вашій команді.";
                return register(level, base, team) ? "Робочу основу закріплено за вашою командою. Тепер запаліть вогонь звичайним кліком або подайте Fire Water."
                        : "Ця робоча основа вже належить іншій команді.";
            }
        }
        return "На цій основі немає чинного рецепта вогняного ремесла.";
    }

    /** Trusted server-internal operation, also used by opt-in native fixtures. */
    static boolean register(ServerLevel level, BlockPos base, String team) {
        if (!level.getServer().isSameThread() || team == null || team.isBlank()
                || !Aia2MachineGuard.mayObserveStage(team, 19) || level.getBlockState(base).isAir()) return false;
        var data = data(level);
        if (data.blocked) return false;
        Site old = data.sites.get(base.asLong());
        if (old != null && !old.team().equals(team)) return false;
        if (old == null && data.sites.size() >= LIMIT) throw new IllegalStateException("AIA2 fire worksite limit reached in dimension");
        Site site = new Site(team, level.getBlockState(base));
        if (!site.equals(old)) {
            data.sites.put(base.asLong(), site);
            level.getDataStorage().set(DATA_NAME, data);
            data.setDirty();
        }
        return true;
    }

    /** Called at the single common native spawn edge, before RNG, entities or base mutation. */
    public static boolean maySpawn(Level world, BlockPos fire, Recipe<?> recipe) {
        if (!(world instanceof ServerLevel level) || !level.getServer().isSameThread() || !Aia2MachineGuard.isReady()) return false;
        var def = definition(level, recipe);
        return matches(level, fire.below(), recipe, def)
                && mayRunAtWorksite(level, fire, recipe, def.outputs(), def.after());
    }

    /** Shared site/output boundary; optional codec/base matching is checked by maySpawn first. */
    static boolean mayRunAtWorksite(ServerLevel level, BlockPos fire, Recipe<?> recipe, List<ItemStack> outputs, Block after) {
        if (!level.getServer().isSameThread() || !Aia2MachineGuard.isReady()) return false;
        var site = data(level).sites.get(fire.below().asLong());
        return site != null && site.base() == level.getBlockState(fire.below())
                && permitsOutputs(level, site.team(), recipe, outputs, after);
    }

    /** Exact mutation hook; removing/replacing even the same block type revokes a site's ownership. */
    public static void baseChanged(Level world, BlockPos pos, BlockState old, BlockState next) {
        if (!(world instanceof ServerLevel level) || old == null || old == next || !level.getServer().isSameThread()) return;
        var data = data(level);
        if (data.blocked) return;
        if (data.sites.remove(pos.asLong()) != null) data.setDirty();
    }

    static String owner(ServerLevel level, BlockPos base) {
        Site site = data(level).sites.get(base.asLong());
        return site != null && site.base() == level.getBlockState(base) ? site.team() : "";
    }

    private static SiteData data(ServerLevel level) {
        if (!level.getServer().isSameThread()) throw new IllegalStateException("Fire worksites require the server thread");
        return DATA.computeIfAbsent(level, world -> {
            SiteData stored = world.getDataStorage().get(SiteData.FACTORY, DATA_NAME);
            if (stored != null) return stored;
            // Vanilla swallows read/deserialize errors. An existing unreadable
            // file must never be replaced by computeIfAbsent's empty record.
            var file = DimensionType.getStorageFolder(world.dimension(),
                    world.getServer().getWorldPath(LevelResource.ROOT)).resolve("data").resolve(DATA_NAME + ".dat");
            if (Files.exists(file)) {
                LOGGER.error("Unreadable AIA2 fire worksite ledger {}; production/claims remain closed and the file is preserved", file);
                SiteData blocked = new SiteData(); blocked.blocked = true; return blocked;
            }
            // Empty dimensions only get an in-memory map. No SavedData file is
            // installed or dirtied until a real station is registered.
            return new SiteData();
        });
    }

    static final class SiteData extends SavedData {
        static final Factory<SiteData> FACTORY = new Factory<>(SiteData::new, SiteData::load);
        final Map<Long, Site> sites = new TreeMap<>();
        boolean blocked;
        static SiteData load(CompoundTag tag, HolderLookup.Provider registries) {
            try { return readStrict(tag, registries); }
            catch (RuntimeException malformed) {
                LOGGER.error("Invalid AIA2 fire worksite ledger; claims/production remain closed and original data is preserved", malformed);
                SiteData result = new SiteData(); result.blocked = true; return result;
            }
        }
        private static SiteData readStrict(CompoundTag tag, HolderLookup.Provider registries) {
            if (tag.getInt("schema") != 1) throw new IllegalStateException("Unsupported AIA2 fire worksite schema");
            if (!tag.contains("sites", 9)) throw new IllegalStateException("Missing/invalid AIA2 fire sites list");
            SiteData result = new SiteData();
            ListTag sites = (ListTag) tag.get("sites");
            if (!sites.isEmpty() && sites.getElementType() != 10) throw new IllegalStateException("Invalid AIA2 fire site entry type");
            if (sites.size() > LIMIT) throw new IllegalStateException("Too many AIA2 fire worksites");
            for (int i = 0; i < sites.size(); i++) {
                CompoundTag entry = sites.getCompound(i);
                String team = entry.getString("team");
                BlockState state = NbtUtils.readBlockState(registries.lookupOrThrow(Registries.BLOCK), entry.getCompound("base"));
                if (team.isBlank() || team.length() > 128 || state.isAir() || !entry.contains("pos", 4)
                        || result.sites.put(entry.getLong("pos"), new Site(team, state)) != null) {
                    throw new IllegalStateException("Invalid or duplicate AIA2 fire worksite");
                }
            }
            return result;
        }
        @Override public CompoundTag save(CompoundTag tag, HolderLookup.Provider registries) {
            if (blocked) throw new IllegalStateException("Refusing to overwrite a corrupt AIA2 fire worksite ledger");
            tag.putInt("schema", 1);
            ListTag entries = new ListTag();
            sites.forEach((pos, site) -> {
                CompoundTag entry = new CompoundTag();
                entry.putLong("pos", pos); entry.putString("team", site.team());
                entry.put("base", NbtUtils.writeBlockState(site.base())); entries.add(entry);
            });
            tag.put("sites", entries); return tag;
        }
    }
}
