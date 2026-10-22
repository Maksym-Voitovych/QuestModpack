package ua.aia2.guard;

import com.google.gson.Gson;
import com.google.gson.JsonObject;
import com.mojang.logging.LogUtils;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
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

    public static boolean isReady() {
        return POLICY.isReady() && ITEM_POLICY.isReady();
    }

    public static void clearRuntime() {
        POLICY.clear();
        ITEM_POLICY.clear();
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
    }

    public static void setPlayerTeam(String playerId, String team) {
        if (team == null || team.isBlank()) {
            throw new IllegalArgumentException("A player requires a nonempty team");
        }
        PLAYER_TEAMS.put(UUID.fromString(playerId), team);
    }

    /** Call only after the script has supplied every persisted team's progress. */
    public static void setReady() {
        ITEM_POLICY.setReady();
        POLICY.setReady();
    }

    public static int getRequiredStage(String blockId) {
        return POLICY.getRequiredStage(blockId);
    }

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
        String id = BuiltInRegistries.ITEM.getKey(output.getItem()).toString();
        if (ITEM_POLICY.getRequiredStage(id) <= 1) {
            return true;
        }
        if (!isReady() || player instanceof FakePlayer) {
            return false;
        }
        String synchronizedTeam = PLAYER_TEAMS.get(player.getUUID());
        String currentTeam = LIVE_TEAMS.resolve(player.getUUID());
        return synchronizedTeam != null && synchronizedTeam.equals(currentTeam)
                && ITEM_POLICY.mayTick(id, currentTeam);
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
        return ITEM_POLICY.getRequiredStage(id) <= 1 || isReady() && ITEM_POLICY.mayTick(id, getOwner(blockEntity));
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
                    "net.minecraft.world.level.block.CrafterBlock"}) {
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
            LOGGER.info("AIA2 block rules loaded; staged machines await the server progression bridge");
        } catch (IOException | RuntimeException failure) {
            LOGGER.error("AIA2 machine rules could not load from {}. Modded machines remain locked until the progression bridge initializes.",
                    configuration, failure);
        }
    }

    private static void serverStopped(ServerStoppedEvent event) {
        clearRuntime();
    }
}
