package ua.aia2.guard;

import com.google.gson.Gson;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Arrays;
import java.util.HashSet;
import java.util.List;
import java.util.Set;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.crafting.Recipe;
import net.minecraft.world.item.crafting.RecipeHolder;
import net.minecraft.world.item.crafting.RecipeInput;
import net.minecraft.world.item.crafting.RecipeSerializer;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.entity.BlockEntity;

/** Actual journal and public post-consumption entry; MC codecs/native dispatch are modeled. */
public final class MechanicsLedgerHarness {
    private static final String DATA = "aia2_mechanics_v1";
    private static final String PROOF = "fixture_process";
    private static int checks, fixtures;
    private static Path directory;
    private static void check(boolean value, String why) { checks++; if (!value) throw new AssertionError(why); }
    private static void fails(Runnable action, String why) {
        boolean denied = false;
        try { action.run(); } catch (RuntimeException expected) { denied = true; }
        check(denied, why);
    }
    private static String config(String id) {
        return "[{\"id\":\"" + id + "\",\"epoch\":37,\"output\":\"minecraft:iron_ingot\"," +
            "\"serializer\":\"minecraft:crafting_shaped\",\"recipeIds\":[\"aia2:ledger_fixture\"]}]";
    }
    private static final class Fixture {
        final MinecraftServer server = new MinecraftServer();
        final ServerLevel main = new ServerLevel();
        final BlockEntity machine;
        final Recipe<?> recipe;
        Fixture() throws Exception {
            ProductionMilestoneBridge.clearRuntime();
            server.root = directory.resolve("fixture-" + fixtures++);
            server.main = main; main.server = server;
            machine = new BlockEntity(main, "team");
            ItemStack output = new ItemStack("minecraft:iron_ingot", 1);
            recipe = new Recipe<RecipeInput>() {
                public boolean matches(RecipeInput input, Level level) { return true; }
                public ItemStack getResultItem(Object registries) { return output.copy(); }
                public RecipeSerializer<?> getSerializer() { return new RecipeSerializer<>("minecraft:crafting_shaped"); }
            };
            main.recipes.replace(List.of(new RecipeHolder<>(ResourceLocation.parse("aia2:ledger_fixture"), recipe)));
            ProductionMilestoneBridge.configureJson(config(PROOF));
        }
        void record() { ProductionMilestoneBridge.finishedMachine(machine, recipe); }
        boolean proof(String team, String id) { return ProductionMilestoneBridge.hasProof(server, team, id); }
        ProductionMilestoneBridge.ReceiptData stored() {
            return (ProductionMilestoneBridge.ReceiptData)main.storage.data.get(DATA);
        }
        void reload(CompoundTag raw) {
            main.storage.raw.put(DATA, raw); main.storage.data.clear();
            ProductionMilestoneBridge.clearRuntime(); ProductionMilestoneBridge.configureJson(config(PROOF));
        }
    }
    private static CompoundTag valid() {
        CompoundTag tag = new CompoundTag(); tag.putInt("schema", 1); tag.put("teams", new CompoundTag()); return tag;
    }
    private static CompoundTag teamTag(int count, boolean includeCurrent) {
        CompoundTag tag = valid(); CompoundTag proofs = new CompoundTag();
        for (int i = 0; i < count - (includeCurrent ? 1 : 0); i++) proofs.putBoolean("history_" + i, true);
        if (includeCurrent) proofs.putBoolean(PROOF, true);
        tag.getCompound("teams").put("team", proofs); return tag;
    }
    private static void invalid(CompoundTag tag, String why) {
        String before = new Gson().toJson(tag);
        var loaded = ProductionMilestoneBridge.ReceiptData.load(tag, null);
        check(loaded.blocked, "strict load closes " + why);
        check(!loaded.dirty, "strict load never dirties " + why);
        check(loaded.proofs.isEmpty(), "blocked journal exposes no partial history " + why);
        fails(() -> loaded.save(new CompoundTag(), null), "blocked save refuses " + why);
        check(before.equals(new Gson().toJson(tag)), "strict load preserves source NBT " + why);
    }
    private static void lifecycle() throws Exception {
        Fixture f = new Fixture();
        check(f.main.storage.writes == 0 && f.main.storage.data.isEmpty(), "config never creates or dirties a journal");
        check(!f.proof("team", PROOF), "empty history is not adopted from items/FTB completion");
        check(f.main.storage.writes == 0 && f.main.storage.data.isEmpty(), "empty lookup stays lazy");
        f.record();
        check(f.proof("team", PROOF), "trusted native completion records its team proof");
        check(!f.proof("other", PROOF), "receipt cannot transfer to a different team");
        check(f.main.storage.writes == 1 && f.stored().dirty, "first real record installs and dirties once");
        f.record(); check(f.main.storage.writes == 1, "repeat record is idempotent");
        CompoundTag saved = f.stored().save(new CompoundTag(), null);
        check(saved.contains("schema", 3) && saved.getInt("schema") == 1, "schema1 remains unchanged");
        check(saved.getCompound("teams").getCompound("team").contains(PROOF, 1), "receipt still uses boolean-byte NBT");
        ProductionMilestoneBridge.clearRuntime();
        check(!ProductionMilestoneBridge.isConfigured(), "runtime reset closes collection rules");
        check(f.proof("team", PROOF), "runtime reset preserves stored proof");
        f.reload(saved);
        check(f.proof("team", PROOF), "actual loader restores modeled saved proof");
        ProductionMilestoneBridge.configureJson(config("new_process"));
        check(f.proof("team", PROOF), "changing current configuration never erases valid historical ID");
        check(!f.proof("team", "new_process"), "configuration is never proof");
        f.record(); check(f.proof("team", PROOF) && f.proof("team", "new_process"), "new rule appends beside old receipt");
        check(!ProductionMilestoneBridge.hasProof(null, "team", PROOF), "null server cannot supply proof");
        check(!f.proof("", PROOF), "blank team cannot supply proof");
        fails(() -> f.proof("team", "bad:id"), "invalid ID is rejected");
        fails(() -> f.proof("team", null), "null ID is rejected");
        f.server.sameThread = false;
        fails(() -> f.proof("team", PROOF), "off-thread read stays closed");
        f.server.sameThread = true; f.server.main = null;
        fails(() -> f.proof("team", PROOF), "absent overworld stays closed");
    }
    private static void strictLoader() throws Exception {
        var empty = ProductionMilestoneBridge.ReceiptData.load(valid(), null);
        check(!empty.blocked && empty.proofs.isEmpty(), "valid empty schema loads");
        invalid(new CompoundTag(), "missing schema/teams");
        var schema = valid(); schema.putInt("schema", 2); invalid(schema, "unknown schema");
        var schemaType = valid(); schemaType.putByte("schema", (byte)1); invalid(schemaType, "byte schema is not int");
        var noTeams = valid(); noTeams.remove("teams"); invalid(noTeams, "missing teams");
        var teamsType = valid(); teamsType.putInt("teams", 0); invalid(teamsType, "integer teams");
        for (String team : List.of("", " ", "x".repeat(129))) {
            var tag = valid(); tag.getCompound("teams").put(team, new CompoundTag()); invalid(tag, "invalid team name");
        }
        var wrongTeam = valid(); wrongTeam.getCompound("teams").putString("team", "invalid"); invalid(wrongTeam, "non-compound team");
        for (String id : List.of("", "BAD", "bad:id", "x".repeat(65))) {
            var tag = valid(); var saved = new CompoundTag(); saved.putBoolean(id, true); tag.getCompound("teams").put("team", saved); invalid(tag, "invalid proof ID");
        }
        for (int value : new int[]{0, 2, -1}) {
            var tag = valid(); var saved = new CompoundTag(); saved.putByte(PROOF, (byte)value); tag.getCompound("teams").put("team", saved); invalid(tag, "non-true byte");
        }
        var wrongProof = valid(); var ints = new CompoundTag(); ints.putInt(PROOF, 1); wrongProof.getCompound("teams").put("team", ints); invalid(wrongProof, "integer proof is not boolean byte");
        invalid(teamTag(65, false), "65 proofs");
        var manyTeams = valid(); for (int i = 0; i < 16385; i++) manyTeams.getCompound("teams").put("t" + i, new CompoundTag()); invalid(manyTeams, "16385 teams");
        var historical = valid(); var saved = new CompoundTag(); saved.putBoolean("old_rule_no_longer_configured", true); historical.getCompound("teams").put("team", saved);
        var loaded = ProductionMilestoneBridge.ReceiptData.load(historical, null);
        check(!loaded.blocked && loaded.proofs.get("team").contains("old_rule_no_longer_configured"), "valid historical rule IDs remain");
        var restored = ProductionMilestoneBridge.ReceiptData.load(loaded.save(new CompoundTag(), null), null);
        check(restored.proofs.equals(loaded.proofs), "modeled serialization roundtrip is lossless");
    }
    private static void corruptAndBoundaries() throws Exception {
        Fixture f = new Fixture();
        Path file = f.server.root.resolve("data").resolve(DATA + ".dat"); Files.createDirectories(file.getParent());
        byte[] bytes = {4, 8, 15, 16, 23, 42}; Files.write(file, bytes);
        fails(() -> f.proof("team", PROOF), "existing unreadable file rejects read");
        fails(f::record, "existing unreadable file rejects real receipt append");
        check(Arrays.equals(Files.readAllBytes(file), bytes), "unreadable original bytes remain unchanged");
        check(f.main.storage.writes == 0 && f.main.storage.data.isEmpty(), "unreadable sentinel is never installed or dirtied");
        ProductionMilestoneBridge.clearRuntime(); ProductionMilestoneBridge.configureJson(config(PROOF));
        fails(() -> f.proof("team", PROOF), "reload cannot replace corrupt file with a blank journal");
        check(Arrays.equals(Files.readAllBytes(file), bytes), "reload still preserves original bytes");

        Fixture malformed = new Fixture(); malformed.reload(new CompoundTag());
        fails(() -> malformed.proof("team", PROOF), "loader-detected malformed NBT rejects read");
        fails(malformed::record, "loader-detected malformed NBT rejects append");
        check(malformed.stored().blocked && !malformed.stored().dirty && malformed.main.storage.writes == 0, "blocked loader sentinel is not dirtied/saved");
        fails(() -> malformed.stored().save(new CompoundTag(), null), "blocked journal cannot overwrite the raw data");

        Fixture full = new Fixture(); full.reload(teamTag(64, false));
        check(!full.proof("team", PROOF), "64 historical unrelated entries load without adoption");
        Set<String> original = new HashSet<>(full.stored().proofs.get("team"));
        fails(full::record, "65th proof is rejected before any journal mutation");
        check(full.stored().proofs.get("team").equals(original), "65th proof rejection preserves all64 previous entries");
        check(full.main.storage.writes == 0 && !full.stored().dirty, "capacity rejection has zero storage mutations");
        var reloadedFull = ProductionMilestoneBridge.ReceiptData.load(full.stored().save(new CompoundTag(), null), null);
        check(!reloadedFull.blocked && reloadedFull.proofs.get("team").size() == 64, "capacity rejection leaves data readable on next boot");
        full.reload(teamTag(64, true)); full.record();
        check(full.proof("team", PROOF) && full.main.storage.writes == 0 && !full.stored().dirty, "existing proof remains idempotent at64");

        Fixture maxTeams = new Fixture(); var tag = valid();
        for (int i = 0; i < 16384; i++) tag.getCompound("teams").put("t" + i, new CompoundTag());
        maxTeams.reload(tag);
        check(!maxTeams.proof("team", PROOF), "16384 existing teams load");
        fails(maxTeams::record, "16385th team is rejected");
        check(maxTeams.stored().proofs.size() == 16384 && maxTeams.main.storage.writes == 0, "new-team rejection preserves old teams");
        maxTeams.machine.owner = "t0"; maxTeams.record();
        check(maxTeams.proof("t0", PROOF) && maxTeams.stored().proofs.size() == 16384, "existing team can append a proof at team cap");
        check(!ProductionMilestoneBridge.ReceiptData.load(maxTeams.stored().save(new CompoundTag(), null), null).blocked, "existing-team append remains loader-compatible");

        Fixture badOwner = new Fixture();
        for (String owner : List.of("x".repeat(129))) {
            badOwner.machine.owner = owner; fails(badOwner::record, "invalid team is rejected before save");
        }
        check(badOwner.main.storage.writes == 0, "invalid ownership never installs data");
    }
    public static void main(String[] args) throws Exception {
        directory = Path.of(args[0]); lifecycle(); strictLoader(); corruptAndBoundaries();
        System.out.println(checks + " mechanics actual-bridge journal modeled assertions PASS; NBT codecs, storage IO and trusted native completion context modeled");
    }
}
