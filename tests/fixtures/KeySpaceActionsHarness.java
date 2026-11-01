package ua.aia2.guard;

import com.google.gson.JsonArray;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.inventory.CraftingContainer;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.crafting.CraftingInput;
import net.minecraft.world.item.crafting.CraftingRecipe;
import net.minecraft.world.item.crafting.Recipe;
import net.minecraft.world.item.crafting.RecipeHolder;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.entity.CrafterBlockEntity;
import net.neoforged.neoforge.common.util.FakePlayer;

/** Actual key bridge and required-action helper; native recipe callbacks and MC receivers modeled. */
public final class KeySpaceActionsHarness {
    private static int assertions;
    private static JsonArray canonical;
    private static void check(boolean value, String message) {
        assertions++; if (!value) throw new AssertionError(message);
    }
    private static final class NativeRecipe implements CraftingRecipe {
        final String output;
        NativeRecipe(String output) { this.output = output; }
        public ItemStack assemble(CraftingInput input, Object registry) {
            return new ItemStack(BuiltInRegistries.ITEM.add(output));
        }
    }
    private static final class Fixture {
        final MinecraftServer server = new MinecraftServer();
        final ServerLevel level = new ServerLevel(server);
        final Map<String, Recipe<?>> recipes = new HashMap<>();
        final ServerPlayer player = new ServerPlayer(level);
        Fixture(boolean syntheticCrafting) {
            server.world = level;
            KeyProductionBridge.clearRuntime();
            ProductionMilestoneBridge.proofs.clear(); ProductionMilestoneBridge.failure = null;
            ProductionMilestoneBridge.reads = 0;
            Aia2MachineGuard.ready = true; Aia2MachineGuard.craftAllowed = true;
            Aia2MachineGuard.teams.clear(); Aia2MachineGuard.teams.put(player.getUUID(), "A");
            JsonArray rules = canonical.deepCopy();
            var holders = new ArrayList<RecipeHolder<?>>();
            for (var element : rules) {
                var row = element.getAsJsonObject();
                String id = row.get("recipeId").getAsString(), output = row.get("output").getAsString();
                BuiltInRegistries.ITEM.add(output);
                if (syntheticCrafting && (row.get("epoch").getAsInt() == 37 || row.get("epoch").getAsInt() == 38))
                    row.addProperty("serializer", "minecraft:crafting_shaped");
                Recipe<?> recipe = new NativeRecipe(output);
                recipes.put(id, recipe); holders.add(new RecipeHolder<>(ResourceLocation.parse(id), recipe));
            }
            level.recipes.replace(holders); KeyProductionBridge.configure(rules.toString());
            for (int epoch = 1; epoch <= 48; epoch++) for (String branch : List.of("tech", "arcane"))
                for (String team : List.of("A", "B")) KeyProductionBridge.setReady(team, epoch, branch, true);
        }
        Recipe<?> recipe(int epoch, String branch) { return recipes.get("aia2:dual/e" + String.format("%02d", epoch) + "/" + branch); }
        ItemStack output(int epoch, String branch) {
            return new ItemStack(BuiltInRegistries.ITEM.add("kubejs:aia2_" + branch + "_key_" + String.format("%02d", epoch)));
        }
        void actions(int epoch, String team) {
            for (int tier : epoch == 37 ? new int[]{1, 2} : new int[]{3, 4})
                ProductionMilestoneBridge.grant(server, team, "nasa_tier_" + tier + "_rocket");
        }
        boolean may(int epoch, String branch, String team) { return KeyProductionBridge.mayProcess(level, team, recipe(epoch, branch)); }
        boolean proof(int epoch, String branch, String team) { return KeyProductionBridge.hasProof(server, team, epoch, branch); }
        BlockEntity machine(String team) { var m = new BlockEntity(level); m.owner = team; return m; }
        void select(int epoch, String branch) {
            level.recipes.matched = level.recipes.getRecipes().stream().filter(h -> h.value() == recipe(epoch, branch)).findFirst().orElseThrow();
        }
    }

    private static void allRulesAndTeams() {
        var f = new Fixture(false);
        check(canonical.size() == 96, "all actual 96 pack rules are loaded without altered serializers");
        for (int epoch = 1; epoch <= 48; epoch++) for (String branch : List.of("tech", "arcane")) {
            boolean applies = branch.equals("tech") && (epoch == 37 || epoch == 38);
            check(f.may(epoch, branch, "A") == !applies, "actual key pre-process matrix " + epoch + ":" + branch);
            check(f.may(epoch, branch, "B") == !applies, "second independent team pre-process matrix " + epoch + ":" + branch);
            KeyProductionBridge.finishedMachine(f.machine("A"), f.recipe(epoch, branch));
            check(f.proof(epoch, branch, "A") == !applies, "post-consumption proof matrix " + epoch + ":" + branch);
            check(!f.proof(epoch, branch, "B"), "another team's key proof never appears " + epoch + ":" + branch);
        }
        for (int epoch : new int[]{37, 38}) {
            f.actions(epoch, "A");
            check(f.may(epoch, "tech", "A"), "both exact native actions admit own technology key");
            check(!f.may(epoch, "tech", "B"), "other team cannot borrow manufacturing history");
            KeyProductionBridge.finishedMachine(f.machine("A"), f.recipe(epoch, "tech"));
            check(f.proof(epoch, "tech", "A"), "post-consumption native callback records when action evidence exists");
            check(!f.proof(epoch, "tech", "B"), "completion remains team-bound");
        }
        check(ProductionMilestoneBridge.reads > 0, "real helper consulted distinct native action journal");
    }

    private static void staleEligibilityAndHistory() {
        var f = new Fixture(false);
        var historical = new KeyProductionBridge.ReceiptData();
        historical.proofs.put("A", new java.util.HashSet<>(Set.of("37:tech", "37:arcane")));
        f.level.data.values.put("aia2_key_production_v1", historical);
        check(f.proof(37, "tech", "A"), "synthetic historical key receipt remains readable");
        check(KeyProductionBridge.mayCraftOutput("kubejs:aia2_tech_key_37", "A"), "early output hint still models cached script eligibility");
        check(!f.may(37, "tech", "A"), "native recipe boundary rejects stale cached ready and old key receipt");
        ProductionMilestoneBridge.grant(f.server, "A", "nasa_tier_1_rocket");
        check(!f.may(37, "tech", "A"), "one of two actions is insufficient");
        ProductionMilestoneBridge.grant(f.server, "A", "nasa_tier_3_rocket");
        check(!f.may(37, "tech", "A"), "unrelated higher-tier receipt cannot replace second action");
        f.actions(37, "A"); check(f.may(37, "tech", "A"), "native action pair permits new processing");
        KeyProductionBridge.setReady("A", 37, "tech", false);
        check(!f.may(37, "tech", "A"), "native action receipts do not replace missing FTB branch completion");
        check(f.proof(37, "tech", "A"), "new rules never erase an existing key receipt");
        KeyProductionBridge.clearRuntime();
        check(f.proof(37, "tech", "A") && f.proof(37, "arcane", "A"), "runtime reset preserves historical team receipt data");
    }

    private static void unavailableAndCallbacks() {
        var f = new Fixture(false); f.actions(37, "A");
        ProductionMilestoneBridge.failure = new IllegalStateException("modeled unreadable native action journal");
        check(!f.may(37, "tech", "A"), "native guard converts journal lookup failure to denial");
        KeyProductionBridge.finishedMachine(f.machine("A"), f.recipe(37, "tech"));
        check(!f.proof(37, "tech", "A"), "late callback cannot record against unavailable action journal");
        check(f.may(36, "tech", "A") && f.may(37, "arcane", "A"), "other epochs and independent arcane branch retain old action requirements");
        ProductionMilestoneBridge.failure = null;
        Aia2MachineGuard.ready = false;
        KeyProductionBridge.finishedMachine(f.machine("A"), f.recipe(37, "tech"));
        check(!f.proof(37, "tech", "A"), "native guard readiness remains mandatory");
        Aia2MachineGuard.ready = true; f.server.sameThread = false;
        check(!f.may(37, "tech", "A"), "applicable off-thread production denied");
        f.server.sameThread = true;
        KeyProductionBridge.finishedMachine(f.machine("B"), f.recipe(37, "tech"));
        check(!f.proof(37, "tech", "B"), "machine owner with no action evidence cannot borrow online builder");
    }

    /** Synthetic shaped37 rule exercises the shared player boundary; real pack37 uses Mekanism. */
    private static void playerBoundary() {
        var f = new Fixture(true); f.select(37, "tech");
        var slots = new CraftingContainer(); var output = f.output(37, "tech");
        check(KeyProductionBridge.beginPlayerCraft(f.player, slots, output) == null, "player admission rejects missing actions before output consumption");
        f.actions(37, "A");
        var attempt = KeyProductionBridge.beginPlayerCraft(f.player, slots, output);
        check(attempt != null, "synthetic supported shaped rule admits with both actions");
        ProductionMilestoneBridge.proofs.clear();
        KeyProductionBridge.finishPlayerCraft(attempt, f.player, output);
        check(!f.proof(37, "tech", "A"), "post-consumption check detects removed evidence");
        f.actions(37, "A"); attempt = KeyProductionBridge.beginPlayerCraft(f.player, slots, output);
        Aia2MachineGuard.teams.put(f.player.getUUID(), "B"); f.actions(37, "B");
        KeyProductionBridge.finishPlayerCraft(attempt, f.player, output);
        check(!f.proof(37, "tech", "A") && !f.proof(37, "tech", "B"), "team change cannot attribute a player's in-flight craft");
        Aia2MachineGuard.teams.put(f.player.getUUID(), "A");
        attempt = KeyProductionBridge.beginPlayerCraft(f.player, slots, output);
        KeyProductionBridge.finishPlayerCraft(attempt, f.player, ItemStack.EMPTY);
        check(f.proof(37, "tech", "A"), "shift-click empty result retains valid admitted production");
        check(KeyProductionBridge.beginPlayerCraft(new FakePlayer(f.level), slots, output) == null, "fake player cannot begin a key receipt");
        f.player.creative = true;
        check(KeyProductionBridge.beginPlayerCraft(f.player, slots, output) == null, "creative cannot begin a key receipt");
        f.player.creative = false;
        var g = new Fixture(true); g.select(37, "tech"); g.actions(37, "A");
        var stale = KeyProductionBridge.beginPlayerCraft(g.player, slots, g.output(37, "tech"));
        check(stale != null, "captured rule exists before configuration reload");
        // A current rule reconfiguration invalidates the old Rule identity, even when IDs match.
        JsonArray reconfigured = canonical.deepCopy();
        for (var row : reconfigured) if (row.getAsJsonObject().get("epoch").getAsInt() == 37)
            row.getAsJsonObject().addProperty("serializer", "minecraft:crafting_shaped");
        KeyProductionBridge.configure(reconfigured.toString()); KeyProductionBridge.setReady("A", 37, "tech", true);
        KeyProductionBridge.finishPlayerCraft(stale, g.player, g.output(37, "tech"));
        check(!g.proof(37, "tech", "A"), "old captured rule cannot record after a same-ID configuration replacement");
    }

    /** Actual bridge callbacks; native redstone/debits are intentionally not simulated as proof. */
    private static void crafterBoundary() {
        var f = new Fixture(true); var machine = new CrafterBlockEntity(f.level);
        machine.slots = new ItemStack[]{new ItemStack(BuiltInRegistries.ITEM.add("minecraft:iron_ingot"), 9)};
        KeyProductionBridge.beginCrafter(machine, f.recipe(37, "tech"), f.output(37, "tech"));
        machine.slots[0].shrink(1); KeyProductionBridge.finishCrafter(machine);
        check(!f.proof(37, "tech", "A"), "crafter has no admitted attempt without action proofs");
        f.actions(37, "A");
        KeyProductionBridge.beginCrafter(machine, f.recipe(37, "tech"), f.output(37, "tech"));
        ProductionMilestoneBridge.failure = new IllegalStateException("late modeled journal failure");
        machine.slots[0].shrink(1); KeyProductionBridge.finishCrafter(machine);
        check(!f.proof(37, "tech", "A"), "late journal failure denies crafter receipt after modeled debit");
        ProductionMilestoneBridge.failure = null;
        KeyProductionBridge.beginCrafter(machine, f.recipe(37, "tech"), f.output(37, "tech"));
        KeyProductionBridge.setReady("A", 37, "tech", false);
        machine.slots[0].shrink(1); KeyProductionBridge.finishCrafter(machine);
        check(!f.proof(37, "tech", "A"), "branch eligibility revocation cancels in-flight crafter proof");
        KeyProductionBridge.setReady("A", 37, "tech", true);
        KeyProductionBridge.beginCrafter(machine, f.recipe(37, "tech"), f.output(37, "tech"));
        machine.slots[0].shrink(1); KeyProductionBridge.finishCrafter(machine);
        check(f.proof(37, "tech", "A"), "admitted crafter callback records only after input count falls");
        var saved = f.level.data.values.get("aia2_key_production_v1").save(new CompoundTag(), null);
        var restored = KeyProductionBridge.ReceiptData.load(saved, null);
        check(restored.proofs.getOrDefault("A", Set.of()).contains("37:tech"), "unchanged key journal schema preserves produced receipt");
        var changed = new Fixture(true); changed.actions(37, "A"); changed.actions(37, "B");
        var transferred = new CrafterBlockEntity(changed.level);
        transferred.slots = new ItemStack[]{new ItemStack(BuiltInRegistries.ITEM.add("minecraft:iron_ingot"), 9)};
        KeyProductionBridge.beginCrafter(transferred, changed.recipe(37, "tech"), changed.output(37, "tech"));
        transferred.owner = "B"; transferred.slots[0].shrink(1);
        KeyProductionBridge.finishCrafter(transferred);
        check(!changed.proof(37, "tech", "A") && !changed.proof(37, "tech", "B"),
                "crafter owner changed during native operation cannot grant either team's key receipt");
    }
    public static void main(String[] args) throws Exception {
        canonical = JsonParser.parseString(Files.readString(Path.of(args[0]))).getAsJsonObject().getAsJsonArray("dualKeys");
        allRulesAndTeams(); staleEligibilityAndHistory(); unavailableAndCallbacks(); playerBoundary(); crafterBoundary();
        System.out.println(assertions + " actual-key/required-space-action modeled assertions PASS; Minecraft callbacks, journals and policies modeled");
    }
}
