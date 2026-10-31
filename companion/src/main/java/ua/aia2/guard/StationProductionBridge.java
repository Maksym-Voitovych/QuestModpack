package ua.aia2.guard;

import com.google.gson.JsonElement;
import com.google.gson.JsonParser;
import com.mojang.logging.LogUtils;
import java.nio.file.Files;
import java.util.HashMap;
import java.util.HashSet;
import java.util.Map;
import java.util.Set;
import java.util.WeakHashMap;
import net.minecraft.core.HolderLookup;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.item.crafting.Recipe;
import net.minecraft.world.level.saveddata.SavedData;
import net.minecraft.world.level.storage.LevelResource;

/** Historical team proofs of paid, newly registered stations and a completed native landing. */
public final class StationProductionBridge {
    static final String DATA_NAME = "aia2_stations_v1";
    private static final int MAX_TEAMS = 16384;
    private static final int MAX_PROOFS = 64;
    private static final org.slf4j.Logger LOGGER = LogUtils.getLogger();
    private static final Map<ServerLevel, ReceiptData> DATA = new WeakHashMap<>();
    private record Rule(String id, int epoch, String dimension, String recipeId) {}
    private static Map<String, Rule> rules = Map.of();
    private StationProductionBridge() {}

    /** Runtime reload never deletes or reinterprets historical SavedData. */
    public static void clearRuntime() { rules = Map.of(); DATA.clear(); }
    public static boolean isConfigured() { return rules.size() == 6; }

    /** One signature for Rhino; accept only the six reviewed native station recipes. */
    public static void configureJson(String json) {
        rules = Map.of();
        JsonElement parsed = JsonParser.parseString(json);
        if (!parsed.isJsonArray() || parsed.getAsJsonArray().size() != 6)
            throw new IllegalArgumentException("Expected six reviewed station rules");
        var checked = new HashMap<String, Rule>();
        for (var element : parsed.getAsJsonArray()) {
            var entry = element.getAsJsonObject();
            String id = entry.get("id").getAsString();
            String planet = id.startsWith("station_") && id.endsWith("_orbit")
                    ? id.substring(8, id.length() - 6) : "";
            if (!Set.of("earth", "moon", "mars", "mercury", "venus", "glacio").contains(planet))
                throw new IllegalArgumentException("Unsupported station rule " + id);
            int epoch = Set.of("earth", "moon", "mars").contains(planet) ? 37 : 38;
            String dimension = "ad_astra:" + planet + "_orbit";
            String recipe = "ad_astra:space_station/" + planet + "_orbit_space_station";
            if (entry.get("epoch").getAsDouble() != epoch || !dimension.equals(entry.get("dimension").getAsString())
                    || !recipe.equals(entry.get("recipeId").getAsString())
                    || !"ad_astra:space_station_recipe".equals(entry.get("serializer").getAsString())
                    || !("aia2:stations/" + planet + "_orbit").equals(entry.get("advancement").getAsString())
                    || checked.put(dimension, new Rule(id, epoch, dimension, recipe)) != null)
                throw new IllegalArgumentException("Invalid station rule " + id);
        }
        rules = Map.copyOf(checked);
    }

    private static Rule rule(ServerLevel level, String team, Recipe<?> recipe) {
        Rule rule = rules.get(level.dimension().location().toString());
        if (rule == null || !Aia2MachineGuard.mayObserveStage(team, rule.epoch())
                || !Aia2MachineGuard.mayProcessOwnedRecipe(level, team, recipe)
                || !"ad_astra:space_station_recipe".equals(
                    String.valueOf(BuiltInRegistries.RECIPE_SERIALIZER.getKey(recipe.getSerializer())))) return null;
        for (var holder : level.getRecipeManager().getRecipes())
            if (holder.value() == recipe && holder.id().toString().equals(rule.recipeId())) return rule;
        return null;
    }

    /** Called before any payment. A corrupt journal must remain closed and untouched. */
    static boolean readyFor(ServerLevel level, String team, Recipe<?> recipe) {
        if (team == null || team.isBlank() || team.length() > 128) return false;
        Rule rule = rule(level, team, recipe);
        if (rule == null) return false;
        ReceiptData data = data(level.getServer());
        Set<String> existing = data.proofs.get(team);
        return !data.blocked && (existing != null || data.proofs.size() < MAX_TEAMS)
                && (existing == null || existing.contains(rule.id()) || existing.size() < MAX_PROOFS);
    }

    /** No public generic recorder and no adoption from the native station registry. */
    static void finishedStation(ServerPlayer player, ServerLevel level, Recipe<?> recipe, String team) {
        if (!StationConstructionAccess.isCommittingStation(player, level, recipe, team)
                || !readyFor(level, team, recipe)) return;
        Rule rule = rule(level, team, recipe);
        ReceiptData data = data(level.getServer());
        if (data.proofs.computeIfAbsent(team, ignored -> new HashSet<>()).add(rule.id())) {
            level.getServer().overworld().getDataStorage().set(DATA_NAME, data);
            data.setDirty();
        }
    }

    public static boolean hasProof(MinecraftServer server, String team, String id) {
        validateId(id);
        if (server == null || team == null || team.isBlank()) return false;
        ReceiptData data = data(server);
        if (data.blocked) throw new IllegalStateException("Station proof journal is unreadable; original file preserved");
        return data.proofs.getOrDefault(team, Set.of()).contains(id);
    }

    private static ReceiptData data(MinecraftServer server) {
        if (!server.isSameThread() || server.overworld() == null)
            throw new IllegalStateException("Station proofs require the live server thread");
        return DATA.computeIfAbsent(server.overworld(), world -> {
            ReceiptData stored = world.getDataStorage().get(ReceiptData.FACTORY, DATA_NAME);
            if (stored != null) return stored;
            // Vanilla catches disk/loader failures. Do not replace an existing unreadable file.
            if (Files.exists(server.getWorldPath(LevelResource.ROOT).resolve("data").resolve(DATA_NAME + ".dat"))) {
                LOGGER.error("Unreadable AIA2 station journal; station proofs/construction remain closed; file preserved");
                ReceiptData blocked = new ReceiptData(); blocked.blocked = true; return blocked;
            }
            return new ReceiptData(); // Not installed/dirtied until an actual successful operation.
        });
    }
    private static void validateId(String id) {
        if (id == null || !id.matches("[a-z0-9_]{1,64}")) throw new IllegalArgumentException("Invalid station proof ID");
    }

    static final class ReceiptData extends SavedData {
        static final Factory<ReceiptData> FACTORY = new Factory<>(ReceiptData::new, ReceiptData::load);
        final Map<String, Set<String>> proofs = new HashMap<>();
        boolean blocked;
        static ReceiptData load(CompoundTag tag, HolderLookup.Provider registries) {
            try {
                if (!tag.contains("schema", 3) || tag.getInt("schema") != 1 || !tag.contains("teams", 10))
                    throw new IllegalArgumentException("Invalid station proof schema/teams");
                ReceiptData result = new ReceiptData();
                CompoundTag teams = tag.getCompound("teams");
                if (teams.size() > MAX_TEAMS) throw new IllegalArgumentException("Too many station teams");
                for (String team : teams.getAllKeys()) {
                    if (team.isBlank() || team.length() > 128 || !teams.contains(team, 10))
                        throw new IllegalArgumentException("Invalid station team");
                    CompoundTag saved = teams.getCompound(team);
                    if (saved.size() > MAX_PROOFS) throw new IllegalArgumentException("Too many station proofs");
                    Set<String> proofs = new HashSet<>();
                    for (String id : saved.getAllKeys()) {
                        validateId(id);
                        if (!saved.contains(id, 1) || saved.getByte(id) != 1)
                            throw new IllegalArgumentException("Invalid station proof value");
                        proofs.add(id);
                    }
                    result.proofs.put(team, proofs);
                }
                return result;
            } catch (RuntimeException malformed) {
                LOGGER.error("Invalid AIA2 station journal; original data preserved", malformed);
                ReceiptData result = new ReceiptData(); result.blocked = true; return result;
            }
        }
        @Override public CompoundTag save(CompoundTag tag, HolderLookup.Provider registries) {
            if (blocked) throw new IllegalStateException("Refusing to overwrite a corrupt station journal");
            tag.putInt("schema", 1);
            CompoundTag teams = new CompoundTag();
            proofs.forEach((team, proofs) -> {
                CompoundTag saved = new CompoundTag();
                proofs.forEach(id -> saved.putBoolean(id, true)); teams.put(team, saved);
            });
            tag.put("teams", teams); return tag;
        }
    }
}
