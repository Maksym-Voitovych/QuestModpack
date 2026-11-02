package ua.aia2.guard;

import com.google.gson.Gson;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Arrays;
import java.util.HashSet;
import java.util.List;
import java.util.Set;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.crafting.CraftingInput;
import net.minecraft.world.item.crafting.CraftingRecipe;
import net.minecraft.world.item.crafting.Recipe;
import net.minecraft.world.item.crafting.RecipeHolder;
import net.minecraft.world.level.block.entity.BlockEntity;

/** Actual key journal; binary NBT/Vanilla IO and native completion receivers are modeled. */
public final class KeyLedgerHarness {
    private static final String DATA = "aia2_key_production_v1";
    private static final Gson GSON = new Gson();
    private static Path directory;
    private static int checks, fixtures;
    private static void check(boolean value, String reason) {
        checks++; if (!value) throw new AssertionError(reason);
    }
    private static void fails(Runnable action, String reason) {
        boolean failed = false;
        try { action.run(); } catch (RuntimeException expected) { failed = true; }
        check(failed, reason);
    }
    private static final class Fixture {
        final MinecraftServer server = new MinecraftServer();
        final ServerLevel level = new ServerLevel(server);
        final BlockEntity machine = new BlockEntity(level);
        final Recipe<?> recipe;
        Fixture() throws Exception {
            server.world = level; server.root = directory.resolve("fixture-" + fixtures++);
            machine.owner = "team";
            recipe = new CraftingRecipe() {
                public ItemStack assemble(CraftingInput input, Object registry) {
                    return new ItemStack(BuiltInRegistries.ITEM.add("minecraft:iron_ingot"));
                }
            };
            level.recipes.replace(List.of(new RecipeHolder<>(ResourceLocation.parse("aia2:key_ledger_fixture"), recipe)));
            ProductionMilestoneBridge.proofs.clear(); ProductionMilestoneBridge.failure = null;
            activate();
        }
        void activate() {
            KeyProductionBridge.clearRuntime();
            BuiltInRegistries.ITEM.add("minecraft:iron_ingot");
            KeyProductionBridge.configure("[{\"recipeId\":\"aia2:key_ledger_fixture\",\"output\":\"minecraft:iron_ingot\",\"epoch\":8,\"branch\":\"tech\",\"serializer\":\"minecraft:crafting_shaped\"}]");
            KeyProductionBridge.setReady("team", 8, "tech", true);
        }
        boolean proof(String team, int epoch, String branch) { return KeyProductionBridge.hasProof(server, team, epoch, branch); }
        void record() { KeyProductionBridge.finishedMachine(machine, recipe); }
        KeyProductionBridge.ReceiptData stored() { return (KeyProductionBridge.ReceiptData)level.data.values.get(DATA); }
        void reload(CompoundTag tag) { level.data.raw.put(DATA, tag); level.data.values.clear(); activate(); }
    }
    private static CompoundTag valid() {
        var tag = new CompoundTag(); tag.putInt("schema", 1); tag.put("teams", new CompoundTag()); return tag;
    }
    private static CompoundTag all96(String team) {
        var tag = valid(); var saved = new CompoundTag();
        for (int epoch = 1; epoch <= 48; epoch++) for (String branch : List.of("tech", "arcane"))
            saved.putBoolean(epoch + ":" + branch, true);
        tag.getCompound("teams").put(team, saved); return tag;
    }
    private static void invalid(CompoundTag tag, String reason) {
        var original = GSON.toJsonTree(tag);
        var loaded = KeyProductionBridge.ReceiptData.load(tag, null);
        check(loaded.blocked && loaded.proofs.isEmpty(), "malformed journal closed without partial history: " + reason);
        check(!loaded.dirty, "blocked load is never dirty: " + reason);
        var output = new CompoundTag();
        fails(() -> loaded.save(output, null), "blocked save refuses: " + reason);
        check(output.size() == 0 && GSON.toJsonTree(tag).equals(original), "source/output NBT preserved: " + reason);
    }
    private static void lifecycle() throws Exception {
        var f = new Fixture();
        check(!f.proof("team", 8, "tech"), "configuring actual bridge never fabricates history");
        check(f.level.data.values.isEmpty() && f.level.data.writes == 0, "read does not install or write a fresh journal");
        check(!KeyProductionBridge.hasProof(null, "team", 8, "tech") && !f.proof("", 8, "tech"), "absent server or team cannot supply history");
        check(f.level.data.writes == 0, "unavailable identity lookup does not install journal");
        f.record();
        check(f.proof("team", 8, "tech") && !f.proof("other", 8, "tech"), "trusted native completion records only owning team");
        check(f.level.data.writes == 1 && f.stored().dirty, "new completion installs and dirties journal exactly once");
        f.stored().dirty = false; f.record();
        check(f.level.data.writes == 1 && !f.stored().dirty, "duplicate completion is idempotent without new storage writes");
        KeyProductionBridge.clearRuntime();
        check(f.proof("team", 8, "tech"), "runtime reset never deletes durable proof");
        CompoundTag saved = f.stored().save(new CompoundTag(), null);
        f.reload(saved);
        check(f.proof("team", 8, "tech"), "strict modeled storage reload preserves actual key history");
        check(GSON.toJsonTree(f.stored().save(new CompoundTag(), null)).equals(GSON.toJsonTree(saved)), "schema1 round-trip preserves exact historical payload");
        f.server.sameThread = false;
        fails(() -> f.proof("team", 8, "tech"), "off-thread journal read stays closed");
        fails(f::record, "off-thread native completion cannot mutate history");
        f.server.sameThread = true;
        check(f.proof("team", 8, "tech"), "off-thread rejection never reset history");
    }
    private static void history96AndAliases() throws Exception {
        var tag = all96("team"); var loaded = KeyProductionBridge.ReceiptData.load(tag, null);
        check(!loaded.blocked && loaded.proofs.get("team").size() == 96, "all48x2 canonical historical keys fit actual loader");
        check(GSON.toJsonTree(loaded.save(new CompoundTag(), null)).equals(GSON.toJsonTree(tag)), "all96 canonical proof payloads round-trip without changes");
        var f = new Fixture(); f.reload(tag);
        for (int epoch = 1; epoch <= 48; epoch++) for (String branch : List.of("tech", "arcane"))
            check(f.proof("team", epoch, branch), "actual lookup retains canonical history " + epoch + ":" + branch);
        check(!f.proof("other", 48, "arcane"), "complete history cannot migrate to other team");
        f.record(); check(f.level.data.writes == 0 && !f.stored().dirty, "existing key at96 cap remains idempotent");

        var aliases = valid(); var aliasProofs = new CompoundTag();
        aliasProofs.putBoolean("08:tech", true); aliasProofs.putBoolean("+8:arcane", true);
        aliases.getCompound("teams").put("team", aliasProofs); f.reload(aliases);
        check(!f.proof("team", 8, "tech") && !f.proof("team", 8, "arcane"), "parse-valid aliases never become canonical authority");
        check(GSON.toJsonTree(f.stored().save(new CompoundTag(), null)).equals(GSON.toJsonTree(aliases)), "accepted aliases preserved literally, not normalized or discarded");
        f.record();
        check(f.proof("team", 8, "tech") && f.stored().proofs.get("team").contains("08:tech"), "legitimate later native completion adds canonical receipt without deleting alias");

        var full = all96("team"); full.getCompound("teams").getCompound("team").remove("8:tech");
        full.getCompound("teams").getCompound("team").putBoolean("08:tech", true); f.reload(full);
        check(!f.proof("team", 8, "tech") && f.stored().proofs.get("team").size() == 96, "bounded alias history has no canonical receipt");
        var snapshot = GSON.toJsonTree(f.stored().save(new CompoundTag(), null)); int writes = f.level.data.writes;
        fails(f::record, "new97th proof is refused before mutation");
        check(f.level.data.writes == writes && !f.stored().dirty && GSON.toJsonTree(f.stored().save(new CompoundTag(), null)).equals(snapshot), "proof cap refusal preserves full old journal");
    }
    private static void corruptFiles() throws Exception {
        var f = new Fixture(); Path file = f.server.root.resolve("data").resolve(DATA + ".dat");
        Files.createDirectories(file.getParent()); byte[] bytes = "unreadable-original-key-journal".getBytes(); Files.write(file, bytes);
        f.level.data.readFailure = true;
        fails(() -> f.proof("team", 8, "tech"), "unreadable existing key file must stay closed");
        check(f.level.data.values.isEmpty() && f.level.data.writes == 0, "unreadable existing key file is not replaced with an empty SavedData");
        fails(f::record, "native record cannot overwrite unreadable original");
        check(Arrays.equals(Files.readAllBytes(file), bytes) && f.level.data.writes == 0, "corrupt original file bytes survive attempted completion");
        f.activate();
        fails(() -> f.proof("team", 8, "tech"), "runtime reset and reconfigure cannot erase unreadable file sentinel");
        check(Arrays.equals(Files.readAllBytes(file), bytes) && f.level.data.writes == 0, "corrupt bytes preserved across runtime reset");
        var malformed = new Fixture(); var bad = valid(); bad.putInt("schema", 2); var original = GSON.toJsonTree(bad); malformed.reload(bad);
        fails(() -> malformed.proof("team", 8, "tech"), "strict invalid loaded journal closes proof queries");
        fails(malformed::record, "strict invalid loaded journal closes writes");
        check(malformed.stored().blocked && !malformed.stored().dirty && malformed.level.data.writes == 0, "invalid deserialized sentinel remains undirtied");
        check(GSON.toJsonTree(bad).equals(original), "original malformed NBT retained unchanged");
    }
    private static void malformed() {
        var tag = valid(); tag.remove("schema"); invalid(tag, "missing schema");
        tag = valid(); tag.putString("schema", "1"); invalid(tag, "schema string");
        tag = valid(); tag.putLong("schema", 1L); invalid(tag, "schema long");
        tag = valid(); tag.putInt("schema", 2); invalid(tag, "future schema");
        tag = valid(); tag.remove("teams"); invalid(tag, "missing teams");
        tag = valid(); tag.putString("teams", "broken"); invalid(tag, "teams type");
        tag = valid(); tag.getCompound("teams").putString("team", "broken"); invalid(tag, "team type");
        for (String team : List.of(" ", "x".repeat(129))) { tag = valid(); tag.getCompound("teams").put(team, new CompoundTag()); invalid(tag, "team bounds"); }
        for (String proof : List.of("", "tech", "0:tech", "49:tech", "-1:tech", "1:wrong", "1:tech:extra", "99999999999999999999999:tech", "0".repeat(65) + "8:tech")) {
            tag = valid(); var values = new CompoundTag(); values.putBoolean(proof, true); tag.getCompound("teams").put("team", values); invalid(tag, "proof syntax " + proof);
        }
        for (int kind = 0; kind < 4; kind++) {
            tag = valid(); var values = new CompoundTag();
            if (kind == 0) values.putInt("8:tech", 1);
            if (kind == 1) values.putBoolean("8:tech", false);
            if (kind == 2) values.putByte("8:tech", (byte)2);
            if (kind == 3) values.putString("8:tech", "true");
            tag.getCompound("teams").put("team", values); invalid(tag, "proof tag/value " + kind);
        }
        tag = all96("team"); tag.getCompound("teams").getCompound("team").putBoolean("08:tech", true); invalid(tag, "97proofs");
        tag = valid(); for (int i = 0; i < 16385; i++) tag.getCompound("teams").put("t" + i, new CompoundTag()); invalid(tag, "16385teams");
    }
    private static void teamsCap() throws Exception {
        var tag = valid(); for (int i = 0; i < 16383; i++) tag.getCompound("teams").put("history_" + i, new CompoundTag());
        var own = new CompoundTag(); own.putBoolean("8:tech", true); tag.getCompound("teams").put("team", own);
        var f = new Fixture(); f.reload(tag);
        check(f.proof("team", 8, "tech") && f.stored().proofs.size() == 16384, "exact team cap retains valid existing canonical proof");
        f.record(); check(f.level.data.writes == 0, "existing proof at team cap remains idempotent");
        f.machine.owner = "new_team"; KeyProductionBridge.setReady("new_team", 8, "tech", true);
        int before = f.stored().proofs.size(); fails(f::record, "new16385th team denied before mutation");
        check(f.stored().proofs.size() == before && !f.stored().dirty && f.level.data.writes == 0, "team-cap refusal preserves old history and dirty state");
        tag.getCompound("teams").getCompound("team").remove("8:tech"); f.reload(tag); f.machine.owner = "team";
        f.record(); check(f.proof("team", 8, "tech") && f.stored().proofs.size() == 16384, "existing team may acquire legitimate receipt at team cap");
    }
    public static void main(String[] args) throws Exception {
        check(KeyProductionBridge.journalProtectionVersion() == 1, "journal deployment capability is version1 without a schema migration");
        directory = Path.of(args[0]); lifecycle(); history96AndAliases(); corruptFiles(); malformed(); teamsCap();
        System.out.println(checks + " key actual-bridge journal modeled assertions PASS; native completion, NBT codecs and storage IO modeled");
    }
}
