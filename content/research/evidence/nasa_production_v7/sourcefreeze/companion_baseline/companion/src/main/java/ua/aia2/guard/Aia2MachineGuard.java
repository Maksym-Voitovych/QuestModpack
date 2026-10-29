package ua.aia2.guard;

import com.google.gson.Gson;
import com.google.gson.JsonObject;
import com.mojang.logging.LogUtils;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.crafting.Recipe;
import net.minecraft.world.item.crafting.RecipeManager;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.neoforged.fml.common.Mod;
import net.neoforged.neoforge.common.NeoForge;
import net.neoforged.neoforge.event.server.ServerAboutToStartEvent;
import net.neoforged.neoforge.event.server.ServerStoppedEvent;
import net.neoforged.neoforge.common.util.FakePlayer;
import org.slf4j.Logger;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.HashMap;
import java.util.IdentityHashMap;
import java.util.Map;
import java.util.UUID;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.atomic.AtomicLong;

/** Native bridge deliberately has no private FTB or KubeJS dependency. */
@Mod(Aia2MachineGuard.MOD_ID)
public final class Aia2MachineGuard {
    public static final String MOD_ID = "aia2_machine_guard";
    private static final String OWNER_TAG = "aia2_guard_owner_team";
    private static final Logger LOGGER = LogUtils.getLogger();
    private static final GuardPolicy POLICY = new GuardPolicy();
    private static final GuardPolicy ITEM_POLICY = new GuardPolicy();
    private static final GuardPolicy RECIPE_POLICY = new GuardPolicy();
    private static final RecipeIdentityIndex RECIPES = new RecipeIdentityIndex();
    private static final ThreadLocal<BlockEntity> TICK_CONTEXT = new ThreadLocal<>();
    private static final ClassValue<java.lang.reflect.Method> CACHED_RECIPE_ACCESSOR = new ClassValue<>() {
        @Override protected java.lang.reflect.Method computeValue(Class<?> type) {
            try { return type.getMethod("getRecipe"); }
            catch (ReflectiveOperationException error) { throw new IllegalStateException("Unsupported Mekanism CachedRecipe API", error); }
        }
    };
    private static final Map<UUID, String> PLAYER_TEAMS = new ConcurrentHashMap<>();
    private static final LiveTeamResolver LIVE_TEAMS = new LiveTeamResolver();
    private static final AtomicLong DENIED_TICKS = new AtomicLong();

    public Aia2MachineGuard() {
        NeoForge.EVENT_BUS.addListener(Aia2MachineGuard::serverAboutToStart);
        NeoForge.EVENT_BUS.addListener(Aia2MachineGuard::serverStopped);
        if (Boolean.getBoolean("aia2.guard.verifyMixin")) {
            verifyMixinBinding();
        }
    }

    /** Class availability is separate from an initialized progression bridge. */
    public static boolean isLoaded() {
        return true;
    }

    /** Monotonic bridge contract; loading a class alone never implies readiness. */
    public static int apiVersion() { return 4; }

    public static boolean isReady() {
        return POLICY.isReady() && ITEM_POLICY.isReady() && RECIPE_POLICY.isReady() && KeyProductionBridge.isConfigured();
    }

    public static void clearRuntime() {
        POLICY.clear();
        ITEM_POLICY.clear();
        RECIPE_POLICY.clear();
        RECIPES.reset();
        TICK_CONTEXT.remove();
        RobitRecipeAccess.clear();
        EnderTaskAccess.clearRuntime();
        FireWorksiteAccess.clearRuntime();
        KeyProductionBridge.clearRuntime();
        ProductionMilestoneBridge.clearRuntime();
        PLAYER_TEAMS.clear();
        LIVE_TEAMS.clear();
        DENIED_TICKS.set(0);
    }

    public static void setRules(Map<String, ? extends Number> rules) {
        POLICY.setRules(rules);
    }

    /** JSON avoids relying on Rhino's conversion of JavaScript objects to Map. */
    public static void setRulesJson(String json) {
        setRules(parseRulesJson(json));
    }

    public static void setItemRulesJson(String json) {
        ITEM_POLICY.setRules(parseRulesJson(json));
    }

    public static void setRecipeRulesJson(String json) {
        RECIPE_POLICY.setRules(parseRulesJson(json));
        RECIPES.reset();
    }

    public static void configureKeyRulesJson(String json) { KeyProductionBridge.configure(json); }
    public static void setKeyRulesJson(String json) { configureKeyRulesJson(json); }
    public static void setTeamKeyReady(String team, int epoch, String branch, boolean ready) {
        KeyProductionBridge.setReady(team, epoch, branch, ready);
    }
    public static boolean hasProductionProof(MinecraftServer server, String team, int epoch, String branch) {
        return KeyProductionBridge.hasProof(server, team, epoch, branch);
    }

    private static Map<String, Number> parseRulesJson(String json) {
        JsonObject input = new Gson().fromJson(json, JsonObject.class);
        if (input == null) {
            throw new IllegalArgumentException("Block rules must be a JSON object");
        }
        var rules = new HashMap<String, Number>();
        input.entrySet().forEach(entry -> {
            if (!entry.getValue().isJsonPrimitive() || !entry.getValue().getAsJsonPrimitive().isNumber()) {
                throw new IllegalArgumentException("Stage must be a number for " + entry.getKey());
            }
            rules.put(entry.getKey(), entry.getValue().getAsDouble());
        });
        return rules;
    }

    public static void setTeamProgress(String team, int completed) {
        POLICY.setTeamProgress(team, completed);
        ITEM_POLICY.setTeamProgress(team, completed);
        RECIPE_POLICY.setTeamProgress(team, completed);
    }

    public static void setPlayerTeam(String playerId, String team) {
        if (team == null || team.isBlank()) {
            throw new IllegalArgumentException("A player requires a nonempty team");
        }
        PLAYER_TEAMS.put(UUID.fromString(playerId), team);
    }

    /** Keep Java UUID access behind the native boundary: KubeJS remaps getUUID. */
    public static void syncPlayer(ServerPlayer player, String team, int completed) {
        if (player == null || player instanceof FakePlayer) {
            throw new IllegalArgumentException("A real server player is required for guard synchronization");
        }
        setTeamProgress(team, completed);
        PLAYER_TEAMS.put(player.getUUID(), team);
    }

    /** Call only after the script has supplied every persisted team's progress. */
    public static void setReady() {
        if (!KeyProductionBridge.isConfigured()) throw new IllegalStateException("Dual key proof rules have not been configured");
        ITEM_POLICY.setReady();
        RECIPE_POLICY.setReady();
        POLICY.setReady();
    }

    public static int getRequiredStage(String blockId) {
        return POLICY.getRequiredStage(blockId);
    }

    public static int getRequiredItemStage(String itemId) { return ITEM_POLICY.getRequiredStage(itemId); }

    public static String getOwner(BlockEntity blockEntity) {
        return blockEntity.getPersistentData().getString(OWNER_TAG);
    }

    /** Trusted server bridge must check player access before assigning an owner. */
    public static void setOwner(BlockEntity blockEntity, String team) {
        if (!(blockEntity.getLevel() instanceof ServerLevel) || team == null || team.isBlank()) {
            throw new IllegalArgumentException("A machine owner requires a server block entity and team");
        }
        String oldOwner = getOwner(blockEntity);
        if (!oldOwner.isBlank() && !oldOwner.equals(team)) {
            throw new IllegalStateException("Machine already belongs to a different team");
        }
        blockEntity.getPersistentData().putString(OWNER_TAG, team);
        blockEntity.setChanged();
    }

    /** Unique typed bridge: a visible Clibano frame owns its actual internal controller. */
    public static boolean claimClibano(ServerPlayer player, BlockEntity frame) {
        return ClibanoOwnership.claim(player, frame);
    }

    public static long getDeniedTicks() {
        return DENIED_TICKS.get();
    }

    /** Called before the native BlockEntityTicker, including its cached recipe. */
    public static boolean mayTick(BlockEntity blockEntity) {
        if (!(blockEntity.getLevel() instanceof ServerLevel)) {
            return true;
        }
        String id = BuiltInRegistries.BLOCK.getKey(blockEntity.getBlockState().getBlock()).toString();
        boolean allowed = POLICY.getRequiredStage(id) <= 1 || isReady() && POLICY.mayTick(id, getOwner(blockEntity));
        if (!allowed) {
            DENIED_TICKS.incrementAndGet();
        }
        return allowed;
    }

    /** Checks a result before vanilla takes ingredients or runs result callbacks. */
    public static boolean mayCraft(Player player, ItemStack output) {
        if (!(player instanceof ServerPlayer) || output.isEmpty()) {
            return true;
        }
        if (CreativeManaGuard.isCreativeTablet(output) && !mayUsePostgameMana(player)) return false;
        String id = BuiltInRegistries.ITEM.getKey(output.getItem()).toString();
        if (ITEM_POLICY.getRequiredStage(id) <= 1 && !KeyProductionBridge.isKeyOutput(id)) {
            return true;
        }
        if (!isReady() || player instanceof FakePlayer) {
            return false;
        }
        String synchronizedTeam = PLAYER_TEAMS.get(player.getUUID());
        String currentTeam = LIVE_TEAMS.resolve(player.getUUID());
        return synchronizedTeam != null && synchronizedTeam.equals(currentTeam)
                && ITEM_POLICY.mayTick(id, currentTeam) && KeyProductionBridge.mayCraftOutput(id, currentTeam);
    }

    /** Native automation has an owning team, rather than a crafting player. */
    public static boolean mayProduce(BlockEntity blockEntity, ItemStack output) {
        if (!(blockEntity.getLevel() instanceof ServerLevel)) {
            return true;
        }
        if (!mayTick(blockEntity)) {
            return false;
        }
        if (output.isEmpty()) {
            return true;
        }
        String id = BuiltInRegistries.ITEM.getKey(output.getItem()).toString();
        String team = getOwner(blockEntity);
        if (!CreativeManaGuard.mayExchangeWithPool(blockEntity, output)) return false;
        return (ITEM_POLICY.getRequiredStage(id) <= 1 || isReady() && ITEM_POLICY.mayTick(id, team))
                && KeyProductionBridge.mayCraftOutput(id, team);
    }

    /** Same live-team validation as crafting; completed48 is distinct from being in epoch48. */
    public static boolean mayUsePostgameMana(Player player) {
        if (player == null) return false;
        if (player.level().isClientSide()) return true;
        if (!(player instanceof ServerPlayer) || player instanceof FakePlayer || !isReady()) return false;
        String synchronizedTeam = PLAYER_TEAMS.get(player.getUUID());
        String currentTeam = LIVE_TEAMS.resolve(player.getUUID());
        return synchronizedTeam != null && synchronizedTeam.equals(currentTeam)
                && RECIPE_POLICY.mayUseStage(99, currentTeam);
    }

    /** Called around the actual ticker in a try/finally; nested ticks restore the parent. */
    public static BlockEntity enterTick(BlockEntity blockEntity) {
        BlockEntity parent = TICK_CONTEXT.get();
        TICK_CONTEXT.set(blockEntity);
        return parent;
    }

    public static void exitTick(BlockEntity parent) {
        if (parent == null) TICK_CONTEXT.remove(); else TICK_CONTEXT.set(parent);
    }

    /** Typed access for optional machine components; never guesses a world or owner. */
    public static ServerLevel currentTickServerLevel() {
        BlockEntity owner = TICK_CONTEXT.get();
        return owner != null && owner.getLevel() instanceof ServerLevel level ? level : null;
    }

    public static BlockEntity currentTickOwner() { return TICK_CONTEXT.get(); }

    public static boolean mayProduceInCurrentTick(ItemStack output) {
        BlockEntity owner = TICK_CONTEXT.get();
        return owner != null && mayProduce(owner, output);
    }

    public static boolean mayProcessCachedRecipe(Object cachedRecipe) {
        BlockEntity context = TICK_CONTEXT.get();
        try {
            Object recipe = CACHED_RECIPE_ACCESSOR.get(cachedRecipe.getClass()).invoke(cachedRecipe);
            if (!(recipe instanceof Recipe<?> nativeRecipe)) return false;
            if (context != null) return mayProcessRecipe(context, nativeRecipe);
            return RobitRecipeAccess.hasContext() && RobitRecipeAccess.mayProcess(nativeRecipe);
        } catch (ReflectiveOperationException | RuntimeException failure) {
            return false;
        }
    }

    /** Runs only immediately after Mekanism finishProcessing consumed resources. */
    public static void finishedCachedRecipe(Object cachedRecipe) {
        BlockEntity context = TICK_CONTEXT.get();
        if (context == null) return;
        try {
            Object recipe = CACHED_RECIPE_ACCESSOR.get(cachedRecipe.getClass()).invoke(cachedRecipe);
            if (recipe instanceof Recipe<?> nativeRecipe) {
                KeyProductionBridge.finishedMachine(context, nativeRecipe);
                ProductionMilestoneBridge.finishedMachine(context, nativeRecipe);
            }
        } catch (ReflectiveOperationException failure) {
            LOGGER.error("Could not record a completed key process", failure);
        }
    }

    public static boolean mayLookupRecipeInCurrentTick(Recipe<?> recipe) {
        BlockEntity context = TICK_CONTEXT.get();
        return context == null || mayProcessRecipe(context, recipe);
    }

    /** Native machine components require a real owning ticker context. */
    public static boolean mayProcessRecipeInCurrentTick(Recipe<?> recipe) {
        BlockEntity owner = TICK_CONTEXT.get();
        return owner != null && mayProcessRecipe(owner, recipe);
    }

    /** MI replication copies components directly, without a Recipe or manufacture receipt. */
    public static boolean mayReplicateOutputInCurrentTick(ItemStack output) {
        BlockEntity owner = TICK_CONTEXT.get();
        if (owner == null || output == null || output.isEmpty()) return false;
        String id = BuiltInRegistries.ITEM.getKey(output.getItem()).toString();
        if (id.matches("kubejs:aia2_(tech|arcane|epoch)_key_[0-9]{2}") || KeyProductionBridge.isKeyOutput(id)) return false;
        return mayProduce(owner, output);
    }

    public static boolean mayProcessRecipe(BlockEntity owner, Recipe<?> recipe) {
        if (!(owner.getLevel() instanceof ServerLevel level)) return true;
        if (!mayTick(owner) || !isReady()) return false;
        return mayProcessOwnedRecipe(level, getOwner(owner), recipe);
    }

    public static String resolveCurrentTeam(UUID playerId) {
        return LIVE_TEAMS.resolve(playerId);
    }

    /** Uniquely named typed boundary; no Rhino UUID overload or fake-player identity. */
    public static String synchronizedPlayerTeam(ServerPlayer player) {
        if (player == null || player instanceof FakePlayer || !isReady()) return "";
        String synced = PLAYER_TEAMS.get(player.getUUID());
        String live = LIVE_TEAMS.resolve(player.getUUID());
        return synced != null && synced.equals(live) ? synced : "";
    }

    public static boolean mayUseItemByTeam(String itemId, String team) {
        return isReady() && ITEM_POLICY.mayTick(itemId, team);
    }

    public static boolean mayObserveStage(String team, int epoch) {
        return isReady() && team != null && !team.isBlank() && RECIPE_POLICY.mayUseStage(epoch, team);
    }

    public static boolean mayProcessOwnedRecipe(ServerLevel level, String team, Recipe<?> recipe) {
        if (!isReady()) return false;
        RecipeManager manager = level.getRecipeManager();
        // RecipeManager is reused on reload; its immutable byName.values snapshot changes.
        var snapshot = manager.getRecipes();
        if (!RECIPES.isGeneration(snapshot)) {
            var index = new IdentityHashMap<Object, Integer>();
            for (var holder : snapshot) {
                int required = RECIPE_POLICY.getRequiredStage(holder.id().toString());
                if (required == 100) required = EnderSmeltingProxyAccess.requiredStage(
                        holder, level, RECIPE_POLICY::getRequiredStage, ITEM_POLICY::getRequiredStage);
                index.put(holder.value(), required);
            }
            RECIPES.replace(snapshot, index);
        }
        int stage = RECIPES.stage(recipe);
        if (stage == 100) stage = CreatePotionRecipeAccess.requiredStage(recipe, ITEM_POLICY::getRequiredStage);
        if (stage == 100) stage = ModernRecipeProxyAccess.requiredStage(recipe, level, RECIPES::stage, ITEM_POLICY::getRequiredStage);
        boolean allowed = RECIPE_POLICY.mayUseStage(stage, team) && KeyProductionBridge.mayProcess(level, team, recipe);
        if (!allowed) DENIED_TICKS.incrementAndGet();
        return allowed;
    }

    private static void verifyMixinBinding() {
        try {
            // Loading this one class does not create a world or accept an EULA.
            Class<?> target = Class.forName("net.minecraft.world.level.chunk.LevelChunk$BoundTickingBlockEntity",
                    false, Aia2MachineGuard.class.getClassLoader());
            if (!GuardedTicker.class.isAssignableFrom(target)) {
                throw new IllegalStateException("AIA2 native ticker Mixin marker is absent");
            }
            for (String name : new String[] {"net.minecraft.world.inventory.Slot",
                    "net.minecraft.world.inventory.CraftingMenu", "net.minecraft.world.inventory.InventoryMenu",
                    "net.minecraft.world.level.block.CrafterBlock", "net.minecraft.world.item.crafting.RecipeManager"}) {
                Class<?> craftingTarget = Class.forName(name, false, Aia2MachineGuard.class.getClassLoader());
                if (!GuardedCrafting.class.isAssignableFrom(craftingTarget)) {
                    throw new IllegalStateException("AIA2 crafting Mixin marker is absent: " + name);
                }
            }
            LOGGER.info("AIA2 native ticker and vanilla crafting Mixin bindings verified; no world or machine recipe was executed");
        } catch (ClassNotFoundException failure) {
            throw new IllegalStateException("AIA2 native ticker target is absent", failure);
        }
    }

    private static void serverAboutToStart(ServerAboutToStartEvent event) {
        clearRuntime();
        Path configuration = Path.of("kubejs", "config", "aia2_runtime.json");
        try (var reader = Files.newBufferedReader(configuration, StandardCharsets.UTF_8)) {
            JsonObject root = new Gson().fromJson(reader, JsonObject.class);
            if (root == null || !root.has("blockGates") || !root.get("blockGates").isJsonObject()) {
                throw new IOException("Missing blockGates object");
            }
            setRulesJson(root.getAsJsonObject("blockGates").toString());
            if (!root.has("itemGates") || !root.get("itemGates").isJsonObject()) {
                throw new IOException("Missing itemGates object");
            }
            setItemRulesJson(root.getAsJsonObject("itemGates").toString());
            if (!root.has("recipeGates") || !root.get("recipeGates").isJsonObject()) {
                throw new IOException("Missing recipeGates object");
            }
            setRecipeRulesJson(root.getAsJsonObject("recipeGates").toString());
            if (!root.has("dualKeys") || !root.get("dualKeys").isJsonArray()) throw new IOException("Missing dualKeys array");
            configureKeyRulesJson(root.getAsJsonArray("dualKeys").toString());
            LOGGER.info("AIA2 block rules loaded; staged machines await the server progression bridge");
        } catch (IOException | RuntimeException failure) {
            LOGGER.error("AIA2 machine rules could not load from {}. Modded machines remain locked until the progression bridge initializes.",
                    configuration, failure);
        }
    }

    private static void serverStopped(ServerStoppedEvent event) {
        clearRuntime();
        ProjectEAccess.pause();
        ProjectEAccess.clearMenuSources();
    }
}
