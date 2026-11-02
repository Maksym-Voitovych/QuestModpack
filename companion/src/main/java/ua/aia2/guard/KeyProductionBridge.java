package ua.aia2.guard;

import com.google.gson.JsonArray;
import com.google.gson.JsonElement;
import com.google.gson.JsonParser;
import com.mojang.logging.LogUtils;
import net.minecraft.core.HolderLookup;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.inventory.CraftingContainer;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.crafting.Recipe;
import net.minecraft.world.item.crafting.RecipeHolder;
import net.minecraft.world.item.crafting.RecipeType;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.entity.CrafterBlockEntity;
import net.minecraft.world.level.saveddata.SavedData;
import net.minecraft.world.level.storage.LevelResource;
import net.neoforged.neoforge.common.util.FakePlayer;

import java.nio.file.Files;
import java.util.HashMap;
import java.util.HashSet;
import java.util.IdentityHashMap;
import java.util.Map;
import java.util.Set;
import java.util.WeakHashMap;

/**
 * Receipts are authoritative world data, not possession checks or item NBT.
 * Only post-consumption native hooks may record one. Script reload clears rules
 * and temporary branch eligibility, but never touches the saved receipts.
 */
public final class KeyProductionBridge {
    static final String DATA_NAME = "aia2_key_production_v1";
    private static final int MAX_TEAMS = 16384;
    private static final int MAX_PROOFS = 96;
    private static final org.slf4j.Logger LOGGER = LogUtils.getLogger();
    private static final Map<ServerLevel, ReceiptData> DATA = new WeakHashMap<>();
    public record Rule(String recipeId, String output, int epoch, String branch, String serializer) {}
    public record PlayerAttempt(MinecraftServer server, String team, Rule rule, java.util.UUID playerId) {}
    private static final Set<String> SERIALIZERS = Set.of("minecraft:crafting_shaped", "create:mixing",
            "create:compacting", "mekanism:metallurgic_infusing");
    private static Map<String, Rule> byRecipe = Map.of();
    private static Map<String, Rule> byOutput = Map.of();
    private static final Map<String, Set<String>> eligible = new HashMap<>();
    private static final Map<Object, Rule> identityRules = new IdentityHashMap<>();
    private static Object generation;
    private static boolean configured;
    private record CrafterAttempt(Rule rule, String team, int inputUnits) {}
    private static final Map<CrafterBlockEntity, CrafterAttempt> crafterAttempts = new WeakHashMap<>();

    private KeyProductionBridge() {}

    /** Deployment capability; receipt schema remains version1. */
    public static int journalProtectionVersion() { return 1; }

    public static synchronized void clearRuntime() {
        configured = false;
        byRecipe = Map.of();
        byOutput = Map.of();
        eligible.clear();
        identityRules.clear();
        generation = null;
        crafterAttempts.clear();
        DATA.clear();
    }

    public static synchronized void configure(String json) {
        JsonElement parsed = JsonParser.parseString(json);
        if (!parsed.isJsonArray()) throw new IllegalArgumentException("dualKeys must be a JSON array");
        JsonArray entries = parsed.getAsJsonArray();
        var recipes = new HashMap<String, Rule>();
        var outputs = new HashMap<String, Rule>();
        for (JsonElement entry : entries) {
            var data = entry.getAsJsonObject();
            String id = data.get("recipeId").getAsString();
            String output = data.get("output").getAsString();
            int epoch = data.get("epoch").getAsInt();
            String branch = data.get("branch").getAsString();
            String serializer = data.get("serializer").getAsString();
            validateEpochBranch(epoch, branch);
            if (data.get("epoch").getAsDouble() != epoch || !id.contains(":") || !output.contains(":")
                    || ResourceLocation.tryParse(id) == null || ResourceLocation.tryParse(output) == null
                    || !SERIALIZERS.contains(serializer)) throw new IllegalArgumentException("Unsupported dual key rule " + id);
            if (!BuiltInRegistries.ITEM.containsKey(ResourceLocation.parse(output))) {
                throw new IllegalArgumentException("Unregistered dual key output " + output);
            }
            Rule rule = new Rule(id, output, epoch, branch, serializer);
            if (recipes.put(id, rule) != null || outputs.put(output, rule) != null) {
                throw new IllegalArgumentException("Duplicate dual key recipe/output " + id);
            }
        }
        byRecipe = Map.copyOf(recipes);
        byOutput = Map.copyOf(outputs);
        configured = true;
        generation = null;
        identityRules.clear();
    }

    public static synchronized boolean isConfigured() { return configured; }

    public static synchronized void setReady(String team, int epoch, String branch, boolean ready) {
        validateEpochBranch(epoch, branch);
        if (team == null || team.isBlank()) throw new IllegalArgumentException("A key branch requires an owning team");
        String proof = key(epoch, branch);
        if (ready) eligible.computeIfAbsent(team, ignored -> new HashSet<>()).add(proof);
        else {
            Set<String> values = eligible.get(team);
            if (values != null) {
                values.remove(proof);
                if (values.isEmpty()) eligible.remove(team);
            }
        }
    }

    private static synchronized boolean eligible(String team, Rule rule) {
        return configured && team != null && byRecipe.get(rule.recipeId()) == rule
                && eligible.getOrDefault(team, Set.of()).contains(key(rule.epoch(), rule.branch()));
    }

    /** Native recipe boundaries cannot trust a stale script eligibility projection or old key receipt. */
    private static boolean actionsAllowed(MinecraftServer server, String team, Rule rule) {
        try { return RequiredSpaceActions.hasRequiredActions(server, team, rule.epoch(), rule.branch()); }
        catch (RuntimeException unavailableJournal) { return false; }
    }

    public static synchronized boolean mayCraftOutput(String itemId, String team) {
        Rule rule = byOutput.get(itemId);
        return rule == null || eligible(team, rule);
    }

    public static synchronized boolean isKeyOutput(String itemId) { return byOutput.containsKey(itemId); }

    private static synchronized Rule rule(ServerLevel level, Recipe<?> recipe) {
        Object snapshot = level.getRecipeManager().getRecipes();
        if (generation != snapshot) {
            identityRules.clear();
            for (RecipeHolder<?> holder : level.getRecipeManager().getRecipes()) {
                Rule found = byRecipe.get(holder.id().toString());
                if (found != null) identityRules.put(holder.value(), found);
            }
            generation = snapshot;
        }
        return identityRules.get(recipe);
    }

    public static boolean mayProcess(ServerLevel level, String team, Recipe<?> recipe) {
        Rule rule = rule(level, recipe);
        return rule == null || eligible(team, rule) && actionsAllowed(level.getServer(), team, rule);
    }

    public static PlayerAttempt beginPlayerCraft(Player player, CraftingContainer slots, ItemStack output) {
        if (!(player instanceof ServerPlayer real) || player instanceof FakePlayer || player.isCreative()
                || !(player.level() instanceof ServerLevel level)) return null;
        var matched = level.getRecipeManager().getRecipeFor(RecipeType.CRAFTING, slots.asCraftInput(), level);
        if (matched.isEmpty()) return null;
        // Shift-click drains the result stack before ResultSlot.onTake; rebuild
        // the still-unconsumed matching recipe's output for that native path.
        if (output.isEmpty()) output = matched.get().value().assemble(slots.asCraftInput(), level.registryAccess());
        Rule rule = rule(level, matched.get().value());
        String team = Aia2MachineGuard.resolveCurrentTeam(real.getUUID());
        if (rule == null || !rule.serializer().equals("minecraft:crafting_shaped") || !eligible(team, rule)
                || !actionsAllowed(real.getServer(), team, rule)
                || !rule.output().equals(BuiltInRegistries.ITEM.getKey(output.getItem()).toString())
                || !Aia2MachineGuard.mayCraft(real, output)) return null;
        return new PlayerAttempt(real.getServer(), team, rule, real.getUUID());
    }

    /** Invoked only at ResultSlot.onTake RETURN, after vanilla has consumed inputs. */
    public static void finishPlayerCraft(PlayerAttempt attempt, Player player, ItemStack output) {
        if (attempt == null || !(player instanceof ServerPlayer) || player instanceof FakePlayer || player.isCreative()) return;
        if (!attempt.playerId().equals(player.getUUID()) || !attempt.team().equals(Aia2MachineGuard.resolveCurrentTeam(player.getUUID()))) return;
        if (!output.isEmpty() && !attempt.rule().output().equals(BuiltInRegistries.ITEM.getKey(output.getItem()).toString())) return;
        record(attempt.server(), attempt.team(), attempt.rule());
    }

    /** Called after actual successful Basin input extraction/output acceptance. */
    public static void finishedMachine(BlockEntity machine, Recipe<?> recipe) {
        if (!(machine.getLevel() instanceof ServerLevel level) || !Aia2MachineGuard.isReady()) return;
        Rule rule = rule(level, recipe);
        String team = Aia2MachineGuard.getOwner(machine);
        if (rule == null || !eligible(team, rule)) return;
        record(level.getServer(), team, rule);
    }

    public static synchronized void beginCrafter(CrafterBlockEntity machine, Recipe<?> recipe, ItemStack output) {
        crafterAttempts.remove(machine);
        if (!(machine.getLevel() instanceof ServerLevel level)) return;
        Rule rule = rule(level, recipe);
        String team = Aia2MachineGuard.getOwner(machine);
        if (rule != null && rule.serializer().equals("minecraft:crafting_shaped") && eligible(team, rule)
                && actionsAllowed(level.getServer(), team, rule)
                && rule.output().equals(BuiltInRegistries.ITEM.getKey(output.getItem()).toString())) {
            crafterAttempts.put(machine, new CrafterAttempt(rule, team, inputUnits(machine)));
        }
    }

    public static synchronized void cancelCrafter(CrafterBlockEntity machine) { crafterAttempts.remove(machine); }

    public static synchronized void finishCrafter(CrafterBlockEntity machine) {
        CrafterAttempt attempt = crafterAttempts.remove(machine);
        if (attempt != null && machine.getLevel() instanceof ServerLevel level
                && attempt.team().equals(Aia2MachineGuard.getOwner(machine))
                && inputUnits(machine) < attempt.inputUnits() && eligible(attempt.team(), attempt.rule())) {
            record(level.getServer(), attempt.team(), attempt.rule());
        }
    }

    private static int inputUnits(CrafterBlockEntity machine) {
        int count = 0;
        for (int i = 0; i < machine.getContainerSize(); i++) count += machine.getItem(i).getCount();
        return count;
    }

    private static void record(MinecraftServer server, String team, Rule rule) {
        if (!server.isSameThread()) throw new IllegalStateException("Production receipts require the server thread");
        if (!eligible(team, rule) || !actionsAllowed(server, team, rule)) return;
        if (team == null || team.isBlank() || team.length() > 128)
            throw new IllegalArgumentException("Invalid key production proof team");
        ReceiptData data = data(server);
        if (data.blocked) throw new IllegalStateException("Key production journal is unreadable; original file preserved");
        String proof = key(rule.epoch(), rule.branch());
        Set<String> existing = data.proofs.get(team);
        if (existing != null && existing.contains(proof)) return;
        if (existing == null ? data.proofs.size() >= MAX_TEAMS : existing.size() >= MAX_PROOFS)
            throw new IllegalStateException("Key production journal capacity reached; original history preserved");
        data.proofs.computeIfAbsent(team, ignored -> new HashSet<>()).add(proof);
        server.overworld().getDataStorage().set(DATA_NAME, data);
        data.setDirty();
    }

    public static boolean hasProof(MinecraftServer server, String team, int epoch, String branch) {
        validateEpochBranch(epoch, branch);
        if (server == null || team == null || team.isBlank()) return false;
        ReceiptData data = data(server);
        if (data.blocked) throw new IllegalStateException("Key production journal is unreadable; original file preserved");
        return data.proofs.getOrDefault(team, Set.of()).contains(key(epoch, branch));
    }

    private static ReceiptData data(MinecraftServer server) {
        if (!server.isSameThread() || server.overworld() == null)
            throw new IllegalStateException("Key production proofs require the live server thread");
        return DATA.computeIfAbsent(server.overworld(), world -> {
            ReceiptData stored = world.getDataStorage().get(ReceiptData.FACTORY, DATA_NAME);
            if (stored != null) return stored;
            // Vanilla catches IO/loader failures and can return null. A file
            // that already exists must never be replaced by an empty journal.
            if (Files.exists(server.getWorldPath(LevelResource.ROOT).resolve("data").resolve(DATA_NAME + ".dat"))) {
                LOGGER.error("Unreadable AIA2 key production journal; proofs remain closed and the file is preserved");
                ReceiptData blocked = new ReceiptData(); blocked.blocked = true; return blocked;
            }
            return new ReceiptData(); // Installed/dirtied only by a real native completion.
        });
    }

    private static String key(int epoch, String branch) { return epoch + ":" + branch; }
    private static void validateEpochBranch(int epoch, String branch) {
        if (epoch < 1 || epoch > 48 || !("tech".equals(branch) || "arcane".equals(branch))) {
            throw new IllegalArgumentException("Invalid epoch/key branch");
        }
    }

    static final class ReceiptData extends SavedData {
        static final Factory<ReceiptData> FACTORY = new Factory<>(ReceiptData::new, ReceiptData::load);
        final Map<String, Set<String>> proofs = new HashMap<>();
        boolean blocked;
        static ReceiptData load(CompoundTag tag, HolderLookup.Provider registries) {
            try {
                if (!tag.contains("schema", 3) || tag.getInt("schema") != 1 || !tag.contains("teams", 10))
                    throw new IllegalArgumentException("Invalid key production schema/teams");
                ReceiptData data = new ReceiptData();
                CompoundTag teams = tag.getCompound("teams");
                if (teams.size() > MAX_TEAMS) throw new IllegalArgumentException("Too many key production teams");
                for (String team : teams.getAllKeys()) {
                    if (team.isBlank() || team.length() > 128 || !teams.contains(team, 10))
                        throw new IllegalArgumentException("Invalid key production team");
                    CompoundTag saved = teams.getCompound(team);
                    if (saved.size() > MAX_PROOFS) throw new IllegalArgumentException("Too many key production proofs");
                    Set<String> proofs = new HashSet<>();
                    for (String proof : saved.getAllKeys()) {
                        if (proof.length() > 64 || !saved.contains(proof, 1) || saved.getByte(proof) != 1)
                            throw new IllegalArgumentException("Invalid key production proof type/value");
                        String[] parts = proof.split(":", 2);
                        if (parts.length != 2) throw new IllegalArgumentException("Invalid key production receipt");
                        validateEpochBranch(Integer.parseInt(parts[0]), parts[1]);
                        // Preserve parse-valid historical spellings literally.
                        // An alias such as 08:tech never becomes 8:tech proof.
                        proofs.add(proof);
                    }
                    data.proofs.put(team, proofs);
                }
                return data;
            } catch (RuntimeException malformed) {
                LOGGER.error("Invalid AIA2 key production journal; original data preserved", malformed);
                ReceiptData blocked = new ReceiptData(); blocked.blocked = true; return blocked;
            }
        }
        @Override public CompoundTag save(CompoundTag tag, HolderLookup.Provider registries) {
            if (blocked) throw new IllegalStateException("Refusing to overwrite a corrupt key production journal");
            tag.putInt("schema", 1);
            CompoundTag teams = new CompoundTag();
            proofs.forEach((team, keys) -> {
                CompoundTag values = new CompoundTag();
                keys.forEach(key -> values.putBoolean(key, true));
                teams.put(team, values);
            });
            tag.put("teams", teams);
            return tag;
        }
    }
}
