package ua.aia2.guard;

import java.util.ArrayList;
import java.util.List;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.nbt.Tag;

/** Executes the actual ledger helper against a modeled NBT host, not the optional Clibano runtime. */
public final class ClibanoPaidStateHarness {
    private static int checks;
    private static final ClibanoPaidState.Lane FIRST = new ClibanoPaidState.Lane(
            "forbidden_arcanus:clibano_combustion/arcane_crystal_dust_from_clibano_combustion", "a".repeat(64), "b".repeat(64));
    private static final ClibanoPaidState.Lane SECOND = new ClibanoPaidState.Lane(
            "forbidden_arcanus:clibano_combustion/rune_from_clibano_combustion", "c".repeat(64), "d".repeat(64));
    private static void check(boolean value, String why) { checks++; if (!value) throw new AssertionError(why); }
    private static void rejects(Runnable call, String why) {
        boolean denied = false;
        try { call.run(); } catch (IllegalArgumentException | IllegalStateException | NullPointerException expected) { denied = true; }
        check(denied, why);
    }
    private static CompoundTag saved(Object manager) {
        CompoundTag tag = new CompoundTag(); ClibanoPaidState.save(manager, tag); return tag;
    }
    private static CompoundTag original() {
        Object manager = new Object(); ClibanoPaidState.setLanes(manager, FIRST, SECOND); return saved(manager);
    }
    public static void main(String[] args) {
        Object manager = new Object();
        check(ClibanoPaidState.status(manager) == ClibanoPaidState.Status.EMPTY, "new controller empty");
        check(!ClibanoPaidState.hasState(manager), "empty has no fabricated ledger");
        check(ClibanoPaidState.lane(manager, 0).isEmpty() && ClibanoPaidState.lane(manager, 1).isEmpty(), "no fabricated lane receipt");
        check(ClibanoPaidState.rawState(manager) == null, "empty has no raw state");
        ClibanoPaidState.setLane(manager, 0, FIRST);
        check(ClibanoPaidState.status(manager) == ClibanoPaidState.Status.VERIFIED && ClibanoPaidState.hasState(manager), "first receipt creates ledger");
        check(ClibanoPaidState.lane(manager, 0).orElseThrow().equals(FIRST), "first receipt roundtrips");
        check(ClibanoPaidState.lane(manager, 1).isEmpty(), "first operation cannot certify second lane");
        ClibanoPaidState.setLane(manager, 1, SECOND);
        check(ClibanoPaidState.lane(manager, 0).orElseThrow().equals(FIRST) && ClibanoPaidState.lane(manager, 1).orElseThrow().equals(SECOND), "independent simultaneous lanes");

        CompoundTag snapshot = saved(manager);
        check(snapshot.getCompound(ClibanoPaidState.TAG).getInt("schema") == 1, "explicit versioned schema");
        Object restored = new Object(); ClibanoPaidState.load(restored, snapshot);
        check(ClibanoPaidState.status(restored) == ClibanoPaidState.Status.VERIFIED, "fresh controller reload verifies known ledger");
        check(ClibanoPaidState.lane(restored, 0).orElseThrow().equals(FIRST) && ClibanoPaidState.lane(restored, 1).orElseThrow().equals(SECOND), "both lanes survive reload");
        check(saved(restored).equals(snapshot), "save/load stable native tag bytes representation");
        snapshot.getCompound(ClibanoPaidState.TAG).getCompound("first").putString("input", "f".repeat(64));
        check(ClibanoPaidState.lane(restored, 0).orElseThrow().equals(FIRST), "incoming root cannot mutate loaded ledger");
        check(saved(restored).getCompound(ClibanoPaidState.TAG).getCompound("first").getString("input").equals("b".repeat(64)), "loaded raw nested tag copied defensively");
        CompoundTag readRaw = (CompoundTag) ClibanoPaidState.rawState(restored);
        readRaw.putInt("schema", 99); readRaw.getCompound("second").putString("recipe", "foreign:changed");
        check(((CompoundTag)ClibanoPaidState.rawState(restored)).getInt("schema") == 1, "rawState read defensive copy");
        check(saved(restored).getCompound(ClibanoPaidState.TAG).getCompound("second").getString("recipe").equals(SECOND.recipeId()), "nested rawState copy defensive");

        CompoundTag outgoing = saved(restored); outgoing.getCompound(ClibanoPaidState.TAG).getCompound("second").putString("input", "0".repeat(64));
        check(saved(restored).getCompound(ClibanoPaidState.TAG).getCompound("second").getString("input").equals(SECOND.inputFingerprint()), "outgoing nested tags cannot mutate retained state");
        CompoundTag foreign = new CompoundTag(); foreign.putString("foreign", "keep"); ClibanoPaidState.save(restored, foreign);
        check(foreign.getString("foreign").equals("keep"), "save never changes foreign root data");

        ClibanoPaidState.setLane(restored, 0, null);
        check(ClibanoPaidState.lane(restored, 0).isEmpty() && ClibanoPaidState.lane(restored, 1).orElseThrow().equals(SECOND), "completion clears only its own lane");
        check(!saved(restored).getCompound(ClibanoPaidState.TAG).contains("first") && saved(restored).getCompound(ClibanoPaidState.TAG).contains("second"), "serialized lane independence");
        ClibanoPaidState.setLane(restored, 0, FIRST);
        ClibanoPaidState.setLane(restored, 1, null);
        check(ClibanoPaidState.lane(restored, 0).orElseThrow().equals(FIRST) && ClibanoPaidState.lane(restored, 1).isEmpty(), "second completion leaves first lane proof");
        ClibanoPaidState.setLane(restored, 0, null);
        check(ClibanoPaidState.status(restored) == ClibanoPaidState.Status.EMPTY && !ClibanoPaidState.hasState(restored), "last completion leaves empty ledger");
        CompoundTag oldOutgoing = original(); oldOutgoing.putString("foreign", "still here"); ClibanoPaidState.save(restored, oldOutgoing);
        check(!oldOutgoing.contains(ClibanoPaidState.TAG) && oldOutgoing.getString("foreign").equals("still here"), "tombstone removes old owned tag only");
        ClibanoPaidState.setLanes(restored, FIRST, SECOND); ClibanoPaidState.clear(restored);
        check(ClibanoPaidState.status(restored) == ClibanoPaidState.Status.EMPTY && saved(restored).get(ClibanoPaidState.TAG) == null, "explicit cancellation tombstone");
        Object untouched = new Object(); CompoundTag unknownOutgoing = original(); ClibanoPaidState.save(untouched, unknownOutgoing);
        check(unknownOutgoing.equals(original()), "save without a known state does not erase existing NBT");

        Object emptied = new Object(); ClibanoPaidState.setLanes(emptied, FIRST, SECOND); ClibanoPaidState.load(emptied, new CompoundTag());
        check(ClibanoPaidState.status(emptied) == ClibanoPaidState.Status.EMPTY && ClibanoPaidState.lane(emptied, 0).isEmpty(), "native reload absence clears previous in-memory snapshot");
        CompoundTag emptyKnown = new CompoundTag(), emptyOwned = new CompoundTag(); emptyOwned.putInt("schema", 1); emptyKnown.put(ClibanoPaidState.TAG, emptyOwned);
        ClibanoPaidState.load(emptied, emptyKnown);
        check(ClibanoPaidState.status(emptied) == ClibanoPaidState.Status.VERIFIED && ClibanoPaidState.lane(emptied, 0).isEmpty(), "known empty schema is not invented paid work");
        check(saved(emptied).equals(emptyKnown), "known empty input preserved until explicit mutation");
        ClibanoPaidState.setLanes(emptied, null, null);
        check(!ClibanoPaidState.hasState(emptied), "explicit empty update normalizes known empty ledger");

        List<CompoundTag> invalidRoots = new ArrayList<>();
        CompoundTag scalar = new CompoundTag(); scalar.putString(ClibanoPaidState.TAG, "opaque future format"); invalidRoots.add(scalar);
        CompoundTag number = new CompoundTag(); number.putInt(ClibanoPaidState.TAG, 42); invalidRoots.add(number);
        for (int mode = 0; mode < 13; mode++) {
            CompoundTag bad = original(); CompoundTag owned = bad.getCompound(ClibanoPaidState.TAG);
            switch (mode) {
                case 0 -> owned.putInt("schema", 2);
                case 1 -> owned.remove("schema");
                case 2 -> owned.putString("schema", "1");
                case 3 -> owned.putString("unknown_future_field", "must retain");
                case 4 -> owned.putString("first", "not a compound");
                case 5 -> owned.put("second", new CompoundTag());
                case 6 -> owned.getCompound("first").putString("recipe", "Invalid:Recipe");
                case 7 -> owned.getCompound("first").remove("input");
                case 8 -> owned.getCompound("second").putInt("definition", 4);
                case 9 -> owned.getCompound("second").putString("input", "f".repeat(63));
                case 10 -> owned.getCompound("first").putString("opaque_lane_extension", "must retain");
                case 11 -> owned.putBoolean("schema", true);
                case 12 -> owned.putInt("schema", -1);
            }
            invalidRoots.add(bad);
        }
        for (CompoundTag invalid : invalidRoots) {
            invalid.putString("foreign", "intact"); CompoundTag before = invalid.copy(); Object badManager = new Object();
            ClibanoPaidState.setLanes(badManager, FIRST, SECOND); ClibanoPaidState.load(badManager, invalid);
            check(ClibanoPaidState.status(badManager) == ClibanoPaidState.Status.CORRUPT, "unknown or corrupt format blocked");
            check(ClibanoPaidState.hasState(badManager) && ClibanoPaidState.lane(badManager, 0).isEmpty() && ClibanoPaidState.lane(badManager, 1).isEmpty(), "corrupt raw retained without exposing previous paid lanes");
            rejects(() -> ClibanoPaidState.setLane(badManager, 0, FIRST), "single-lane setter cannot overwrite corrupt ledger");
            rejects(() -> ClibanoPaidState.setLanes(badManager, FIRST, SECOND), "two-lane setter cannot overwrite corrupt ledger");
            rejects(() -> ClibanoPaidState.setLanes(badManager, null, null), "empty setter cannot silently erase corrupt ledger");
            CompoundTag current = before.copy(); ClibanoPaidState.save(badManager, current);
            check(current.equals(before), "corrupt original and foreign fields survive save verbatim");
            invalid.putString(ClibanoPaidState.TAG, "mutate original incoming root");
            check(saved(badManager).get(ClibanoPaidState.TAG).equals(before.get(ClibanoPaidState.TAG)), "corrupt incoming tag defensively retained");
            ClibanoPaidState.clear(badManager);
            check(ClibanoPaidState.status(badManager) == ClibanoPaidState.Status.EMPTY && !ClibanoPaidState.hasState(badManager), "only explicit trusted clear resolves corrupt state");
        }

        for (String recipe : new String[] {"", "missing_namespace", "Upper:case", ":empty", "empty:", "a:b:c", "white space:value", "x:" + "p".repeat(255)}) {
            rejects(() -> new ClibanoPaidState.Lane(recipe, "a".repeat(64), "b".repeat(64)), "invalid recipe ID rejected");
        }
        for (String hash : new String[] {"", "a".repeat(63), "a".repeat(65), "A".repeat(64), "g".repeat(64)}) {
            rejects(() -> new ClibanoPaidState.Lane("a:b", hash, "b".repeat(64)), "invalid definition hash rejected");
            rejects(() -> new ClibanoPaidState.Lane("a:b", "a".repeat(64), hash), "invalid input hash rejected");
        }
        rejects(() -> new ClibanoPaidState.Lane(null, "a".repeat(64), "b".repeat(64)), "null recipe rejected");
        rejects(() -> new ClibanoPaidState.Lane("a:b", null, "b".repeat(64)), "null definition rejected");
        rejects(() -> new ClibanoPaidState.Lane("a:b", "a".repeat(64), null), "null input rejected");
        rejects(() -> ClibanoPaidState.lane(manager, -1), "negative lane rejected");
        rejects(() -> ClibanoPaidState.setLane(manager, 2, FIRST), "third lane rejected");
        check(ClibanoPaidState.lane(manager, 0).orElseThrow().equals(FIRST) && ClibanoPaidState.lane(manager, 1).orElseThrow().equals(SECOND), "invalid-index operation leaves both lanes unchanged");
        rejects(() -> ClibanoPaidState.load(null, new CompoundTag()), "null controller rejected");
        rejects(() -> ClibanoPaidState.load(new Object(), null), "null root rejected");
        System.out.println("ClibanoPaidStateHarness: " + checks + " actual-state/NBT-host modeled assertions PASS");
    }
}
