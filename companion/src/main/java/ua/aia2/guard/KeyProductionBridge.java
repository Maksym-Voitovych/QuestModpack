package ua.aia2.guard;

import com.google.gson.JsonArray;
import com.google.gson.JsonElement;
import com.google.gson.JsonParser;
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
import net.neoforged.neoforge.common.util.FakePlayer;

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

    public static synchronized void clearRuntime() {
        configured = false;
        byRecipe = Map.of();
        byOutput = Map.of();
        eligible.clear();
        identityRules.clear();
        generation = null;
        crafterAttempts.clear();
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
        return configured && team != null && eligible.getOrDefault(team, Set.of()).contains(key(rule.epoch(), rule.branch()));
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
        return rule == null || eligible(team, rule);
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
                && rule.output().equals(BuiltInRegistries.ITEM.getKey(output.getItem()).toString())) {
            crafterAttempts.put(machine, new CrafterAttempt(rule, team, inputUnits(machine)));
        }
    }

    public static synchronized void cancelCrafter(CrafterBlockEntity machine) { crafterAttempts.remove(machine); }

    public static synchronized void finishCrafter(CrafterBlockEntity machine) {
        CrafterAttempt attempt = crafterAttempts.remove(machine);
        if (attempt != null && machine.getLevel() instanceof ServerLevel level
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
        ReceiptData data = data(server);
        if (data.proofs.computeIfAbsent(team, ignored -> new HashSet<>()).add(key(rule.epoch(), rule.branch()))) data.setDirty();
    }

    public static boolean hasProof(MinecraftServer server, String team, int epoch, String branch) {
        validateEpochBranch(epoch, branch);
        if (server == null || team == null || team.isBlank()) return false;
        return data(server).proofs.getOrDefault(team, Set.of()).contains(key(epoch, branch));
    }

    private static ReceiptData data(MinecraftServer server) {
        if (server.overworld() == null) throw new IllegalStateException("The server overworld is not ready for production receipts");
        return server.overworld().getDataStorage().computeIfAbsent(ReceiptData.FACTORY, "aia2_key_production_v1");
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
        static ReceiptData load(CompoundTag tag, HolderLookup.Provider registries) {
            if (tag.getInt("schema") != 1) throw new IllegalStateException("Unsupported key production receipt schema");
            ReceiptData data = new ReceiptData();
            CompoundTag teams = tag.getCompound("teams");
            for (String team : teams.getAllKeys()) {
                Set<String> proofs = new HashSet<>();
                CompoundTag saved = teams.getCompound(team);
                for (String proof : saved.getAllKeys()) {
                    String[] parts = proof.split(":", 2);
                    if (parts.length != 2) throw new IllegalStateException("Invalid key production receipt");
                    validateEpochBranch(Integer.parseInt(parts[0]), parts[1]);
                    if (saved.getBoolean(proof)) proofs.add(proof);
                }
                data.proofs.put(team, proofs);
            }
            return data;
        }
        @Override public CompoundTag save(CompoundTag tag, HolderLookup.Provider registries) {
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
