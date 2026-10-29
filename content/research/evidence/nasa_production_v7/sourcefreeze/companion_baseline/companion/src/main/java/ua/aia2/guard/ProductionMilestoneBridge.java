package ua.aia2.guard;

import com.google.gson.JsonElement;
import com.google.gson.JsonParser;
import net.minecraft.core.HolderLookup;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.crafting.Recipe;
import net.minecraft.world.item.crafting.RecipeHolder;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.entity.CrafterBlockEntity;
import net.minecraft.world.level.saveddata.SavedData;

import java.util.HashMap;
import java.util.HashSet;
import java.util.IdentityHashMap;
import java.util.Map;
import java.util.Set;
import java.util.WeakHashMap;

/** Curated process proofs; only native post-consumption hooks may record. */
public final class ProductionMilestoneBridge {
    private record Rule(String id, int epoch, String output, String serializer) {}
    private record CrafterAttempt(Rule rule, Recipe<?> recipe, String team, int inputUnits) {}
    private static final Set<String> SERIALIZERS = Set.of("create:mixing", "create:compacting",
            "mekanism:metallurgic_infusing", "minecraft:crafting_shaped", "rootsclassic:ritual",
            "enderio:alloy_smelting", "powah:energizing", "forbidden_arcanus:clibano_combustion");
    private static Map<String, Rule> byRecipe = Map.of();
    private static final Map<Recipe<?>, Rule> identity = new IdentityHashMap<>();
    private static final Map<CrafterBlockEntity, CrafterAttempt> crafterAttempts = new WeakHashMap<>();
    private static Object generation;
    private static boolean configured;

    private ProductionMilestoneBridge() {}

    public static synchronized void clearRuntime() {
        configured = false;
        byRecipe = Map.of();
        identity.clear();
        generation = null;
        crafterAttempts.clear();
    }

    /** Unique Java signature avoids Rhino overload resolution. Configuration never writes receipts. */
    public static synchronized void configureJson(String json) {
        JsonElement parsed = JsonParser.parseString(json);
        if (!parsed.isJsonArray() || parsed.getAsJsonArray().isEmpty() || parsed.getAsJsonArray().size() > 64) {
            throw new IllegalArgumentException("Mechanic observations require 1..64 curated rules");
        }
        var checked = new HashMap<String, Rule>();
        var ids = new HashSet<String>();
        for (JsonElement element : parsed.getAsJsonArray()) {
            var data = element.getAsJsonObject();
            String id = data.get("id").getAsString();
            validateId(id);
            int epoch = data.get("epoch").getAsInt();
            String output = data.get("output").getAsString();
            String serializer = data.get("serializer").getAsString();
            if (data.get("epoch").getAsDouble() != epoch || epoch < 1 || epoch > 48 || !ids.add(id)
                    || !SERIALIZERS.contains(serializer) || ResourceLocation.tryParse(output) == null
                    || !BuiltInRegistries.ITEM.containsKey(ResourceLocation.parse(output))) {
                throw new IllegalArgumentException("Invalid mechanic observation " + id);
            }
            Rule rule = new Rule(id, epoch, output, serializer);
            var recipes = data.getAsJsonArray("recipeIds");
            if (recipes == null || recipes.isEmpty()) throw new IllegalArgumentException("Missing native recipes for " + id);
            for (JsonElement recipe : recipes) {
                String recipeId = recipe.getAsString();
                if (ResourceLocation.tryParse(recipeId) == null || checked.put(recipeId, rule) != null) {
                    throw new IllegalArgumentException("Invalid or duplicate mechanic recipe " + recipeId);
                }
            }
        }
        byRecipe = Map.copyOf(checked);
        identity.clear();
        generation = null;
        configured = true;
    }

    public static synchronized boolean isConfigured() { return configured; }

    private static synchronized Rule rule(ServerLevel level, Recipe<?> recipe) {
        if (!configured) return null;
        Object snapshot = level.getRecipeManager().getRecipes();
        if (generation != snapshot) {
            identity.clear();
            for (RecipeHolder<?> holder : level.getRecipeManager().getRecipes()) {
                Rule candidate = byRecipe.get(holder.id().toString());
                if (candidate != null) {
                    String serializer = BuiltInRegistries.RECIPE_SERIALIZER.getKey(holder.value().getSerializer()).toString();
                    ItemStack output = EnderTaskAccess.template(holder.value(),level);
                    if (candidate.serializer().equals(serializer) && !output.isEmpty()
                            && candidate.output().equals(BuiltInRegistries.ITEM.getKey(output.getItem()).toString())) {
                        identity.put(holder.value(), candidate);
                    }
                }
            }
            generation = snapshot;
        }
        return identity.get(recipe);
    }

    /** Called only after native input consumption (Basin, Mekanism, Roots). */
    public static void finishedMachine(BlockEntity machine, Recipe<?> recipe) {
        if (!(machine.getLevel() instanceof ServerLevel level)) return;
        Rule rule = rule(level, recipe);
        String team = Aia2MachineGuard.getOwner(machine);
        if (rule == null || team.isBlank() || !Aia2MachineGuard.mayObserveStage(team, rule.epoch())
                || !Aia2MachineGuard.mayProcessRecipe(machine, recipe)) return;
        record(level.getServer(), team, rule);
    }

    /** Post-input/output edge with actual cached outputs, not just a reloaded template. */
    public static void finishedObservedMachine(BlockEntity machine,Recipe<?> recipe,java.util.List<ItemStack> outputs) {
        if (!(machine.getLevel() instanceof ServerLevel level) || outputs==null) return;
        Rule rule=rule(level,recipe);
        if (rule==null || !EnderTaskAccess.mayOutput(machine,outputs)) return;
        ItemStack template=EnderTaskAccess.template(recipe,level);
        boolean observed=outputs.stream().anyMatch(stack -> !stack.isEmpty()
                && stack.getCount()==template.getCount() && ItemStack.isSameItemSameComponents(stack,template));
        if (!observed) return;
        String team=Aia2MachineGuard.getOwner(machine);
        if (team.isBlank() || !Aia2MachineGuard.mayObserveStage(team,rule.epoch())
                || !Aia2MachineGuard.mayProcessRecipe(machine,recipe)) return;
        record(level.getServer(),team,rule);
    }

    public static synchronized void cancelCrafter(CrafterBlockEntity machine) { crafterAttempts.remove(machine); }

    /** Supports the real vanilla test fixture and an explicitly configured native crafter recipe only. */
    public static synchronized void beginCrafter(CrafterBlockEntity machine, Recipe<?> recipe, ItemStack output) {
        crafterAttempts.remove(machine);
        if (!(machine.getLevel() instanceof ServerLevel level)) return;
        Rule rule = rule(level, recipe);
        String team = Aia2MachineGuard.getOwner(machine);
        if (rule != null && rule.serializer().equals("minecraft:crafting_shaped") && !team.isBlank()
                && rule.output().equals(BuiltInRegistries.ITEM.getKey(output.getItem()).toString())
                && Aia2MachineGuard.mayObserveStage(team, rule.epoch())) {
            crafterAttempts.put(machine, new CrafterAttempt(rule, recipe, team, inputUnits(machine)));
        }
    }

    public static synchronized void finishCrafter(CrafterBlockEntity machine) {
        CrafterAttempt attempt = crafterAttempts.remove(machine);
        if (attempt != null && machine.getLevel() instanceof ServerLevel level
                && inputUnits(machine) < attempt.inputUnits()
                && attempt.team().equals(Aia2MachineGuard.getOwner(machine))
                && Aia2MachineGuard.mayObserveStage(attempt.team(), attempt.rule().epoch())
                && Aia2MachineGuard.mayProcessRecipe(machine, attempt.recipe())) {
            record(level.getServer(), attempt.team(), attempt.rule());
        }
    }

    private static int inputUnits(CrafterBlockEntity machine) {
        int result = 0;
        for (int slot = 0; slot < machine.getContainerSize(); slot++) result += machine.getItem(slot).getCount();
        return result;
    }

    private static void record(MinecraftServer server, String team, Rule rule) {
        if (!server.isSameThread()) throw new IllegalStateException("Mechanic proofs require the server thread");
        ReceiptData data = data(server);
        if (data.proofs.computeIfAbsent(team, ignored -> new HashSet<>()).add(rule.id())) data.setDirty();
    }

    public static boolean hasProof(MinecraftServer server, String team, String id) {
        validateId(id);
        if (server == null || team == null || team.isBlank()) return false;
        return data(server).proofs.getOrDefault(team, Set.of()).contains(id);
    }

    private static ReceiptData data(MinecraftServer server) {
        if (server.overworld() == null) throw new IllegalStateException("Mechanic proof world is not ready");
        return server.overworld().getDataStorage().computeIfAbsent(ReceiptData.FACTORY, "aia2_mechanics_v1");
    }

    private static void validateId(String id) {
        if (id == null || !id.matches("[a-z0-9_]{1,64}")) throw new IllegalArgumentException("Invalid mechanic proof ID");
    }

    static final class ReceiptData extends SavedData {
        static final Factory<ReceiptData> FACTORY = new Factory<>(ReceiptData::new, ReceiptData::load);
        final Map<String, Set<String>> proofs = new HashMap<>();
        static ReceiptData load(CompoundTag tag, HolderLookup.Provider registries) {
            if (tag.getInt("schema") != 1) throw new IllegalStateException("Unsupported mechanic proof schema");
            ReceiptData result = new ReceiptData();
            CompoundTag teams = tag.getCompound("teams");
            for (String team : teams.getAllKeys()) {
                if (team.isBlank()) throw new IllegalStateException("Blank mechanic proof team");
                CompoundTag saved = teams.getCompound(team);
                var proofs = new HashSet<String>();
                for (String id : saved.getAllKeys()) { validateId(id); if (saved.getBoolean(id)) proofs.add(id); }
                result.proofs.put(team, proofs);
            }
            return result;
        }
        @Override public CompoundTag save(CompoundTag tag, HolderLookup.Provider registries) {
            tag.putInt("schema", 1);
            CompoundTag teams = new CompoundTag();
            proofs.forEach((team, proofs) -> {
                CompoundTag saved = new CompoundTag();
                proofs.forEach(id -> saved.putBoolean(id, true));
                teams.put(team, saved);
            });
            tag.put("teams", teams);
            return tag;
        }
    }
}
