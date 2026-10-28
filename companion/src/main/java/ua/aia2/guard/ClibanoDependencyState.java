package ua.aia2.guard;

import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import java.util.TreeMap;
import java.util.WeakHashMap;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.nbt.Tag;

/** Historical dependency storage only; current native values never certify an earlier operation.
 * Separate from the existing strict ClibanoPaidState schema1 and its unchanged lane hashes.
 */
public final class ClibanoDependencyState {
    public static final String TAG = "aia2_clibano_dependencies_v1";
    public enum Status { EMPTY, VERIFIED, CORRUPT }
    public record Residue(String definition, int amount) {
        public Residue {
            if (!hash(definition) || amount < 1 || amount > 64)
                throw new IllegalArgumentException("Invalid historical Clibano residue");
        }
    }
    private record State(Status status, Tag raw, String first, String second, Map<String, Residue> residues) {}
    // Values contain only immutable strings/records/maps and owned NBT copies, never their weak key/world.
    private static final Map<Object, State> STATES = new WeakHashMap<>();
    private static final Set<String> ROOT_KEYS = Set.of("schema", "first", "second", "residues");
    private static final Set<String> RESIDUE_KEYS = Set.of("definition", "amount");
    private ClibanoDependencyState() {}
    private static boolean hash(String value) { return value != null && value.matches("[0-9a-f]{64}"); }
    private static boolean id(String value) {
        return value != null && value.length() <= 256 && value.matches("[a-z0-9_.-]+:[a-z0-9_./-]+");
    }
    private static State empty() { return new State(Status.EMPTY, null, null, null, Map.of()); }
    private static State state(Object controller) {
        return STATES.computeIfAbsent(Objects.requireNonNull(controller), ignored -> empty());
    }
    private static State editable(Object controller) {
        State previous = state(controller);
        if (previous.status == Status.CORRUPT)
            throw new IllegalStateException("Corrupt Clibano dependency history requires explicit recovery");
        return previous;
    }
    private static void index(int lane) {
        if (lane < 0 || lane > 1) throw new IllegalArgumentException("Clibano lane index must be 0 or 1");
    }
    private static String laneTag(CompoundTag tag, String name) {
        if (!tag.contains(name)) return null;
        if (!tag.contains(name, Tag.TAG_STRING) || !hash(tag.getString(name)))
            throw new IllegalArgumentException("Invalid Clibano dependency fingerprint");
        return tag.getString(name);
    }
    private static Map<String, Residue> checked(Map<String, Residue> incoming) {
        Objects.requireNonNull(incoming);
        if (incoming.size() > 64) throw new IllegalArgumentException("Too many Clibano residue histories");
        int total = 0;
        Map<String, Residue> copy = new TreeMap<>();
        for (var entry : incoming.entrySet()) {
            if (!id(entry.getKey()) || entry.getValue() == null)
                throw new IllegalArgumentException("Invalid Clibano residue history entry");
            Residue value = entry.getValue(); total += value.amount;
            if (total > 64) throw new IllegalArgumentException("Clibano residue history exceeds capacity");
            copy.put(entry.getKey(), value);
        }
        return Map.copyOf(copy);
    }
    private static Map<String, Residue> residueTags(CompoundTag root) {
        if (!root.contains("residues", Tag.TAG_COMPOUND))
            throw new IllegalArgumentException("Missing Clibano residue history map");
        CompoundTag encoded = root.getCompound("residues");
        if (encoded.getAllKeys().size() > 64)
            throw new IllegalArgumentException("Too many Clibano residue histories");
        Map<String, Residue> residues = new TreeMap<>();
        for (String id : encoded.getAllKeys()) {
            if (!(encoded.get(id) instanceof CompoundTag tag) || !tag.getAllKeys().equals(RESIDUE_KEYS)
                    || !tag.contains("definition", Tag.TAG_STRING) || !tag.contains("amount", Tag.TAG_INT))
                throw new IllegalArgumentException("Invalid Clibano residue history NBT");
            residues.put(id, new Residue(tag.getString("definition"), tag.getInt("amount")));
        }
        return checked(residues);
    }
    /** Call before native load. An absent extension is not evidence of previous dependencies. */
    public static synchronized void load(Object controller, CompoundTag incoming) {
        Objects.requireNonNull(controller); Objects.requireNonNull(incoming);
        Tag original = incoming.get(TAG);
        State loaded = empty();
        if (original != null) {
            Tag raw = original.copy(); loaded = new State(Status.CORRUPT, raw, null, null, Map.of());
            if (raw instanceof CompoundTag tag && ROOT_KEYS.containsAll(tag.getAllKeys())
                    && tag.contains("schema", Tag.TAG_INT) && tag.getInt("schema") == 1) {
                try {
                    loaded = new State(Status.VERIFIED, raw, laneTag(tag, "first"), laneTag(tag, "second"), residueTags(tag));
                } catch (IllegalArgumentException invalid) { /* Retain the entire original extension without authorizing it. */ }
            }
        }
        STATES.put(controller, loaded);
    }
    /** Save after native serialization; no codec omission can erase retained unknown history. */
    public static synchronized void save(Object controller, CompoundTag outgoing) {
        Objects.requireNonNull(controller); Objects.requireNonNull(outgoing);
        State stored = STATES.get(controller);
        if (stored == null) return;
        if (stored.raw == null) outgoing.remove(TAG);
        else outgoing.put(TAG, stored.raw.copy());
    }
    private static void replace(Object controller, String first, String second, Map<String, Residue> incoming) {
        if (first != null && !hash(first) || second != null && !hash(second))
            throw new IllegalArgumentException("Invalid Clibano dependency fingerprint");
        Map<String, Residue> residues = checked(incoming);
        if (first == null && second == null && residues.isEmpty()) { clear(controller); return; }
        CompoundTag encoded = new CompoundTag(); encoded.putInt("schema", 1);
        if (first != null) encoded.putString("first", first);
        if (second != null) encoded.putString("second", second);
        CompoundTag encodedResidues = new CompoundTag();
        // Sort here rather than relying on the iteration order of Map.copyOf.
        new TreeMap<>(residues).forEach((id, residue) -> {
            CompoundTag tag = new CompoundTag(); tag.putString("definition", residue.definition);
            tag.putInt("amount", residue.amount); encodedResidues.put(id, tag);
        });
        encoded.put("residues", encodedResidues);
        STATES.put(controller, new State(Status.VERIFIED, encoded, first, second, residues));
    }
    /** Trusted fresh/verified adapter update; clearing one lane retains independent work and residues. */
    public static synchronized void setLane(Object controller, int lane, String fingerprint) {
        index(lane); State previous = editable(controller);
        replace(controller, lane == 0 ? fingerprint : previous.first, lane == 1 ? fingerprint : previous.second, previous.residues);
    }
    /** Trusted observed residue addition/conversion only; never derive history from an imported balance. */
    public static synchronized void setResidues(Object controller, Map<String, Residue> residues) {
        State previous = editable(controller); replace(controller, previous.first, previous.second, residues);
    }
    /** Explicit cooking cancellation must not discard independently accumulated residue history. */
    public static synchronized void clearLanes(Object controller) {
        State previous = editable(controller); replace(controller, null, null, previous.residues);
    }
    public static synchronized Optional<String> lane(Object controller, int lane) {
        index(lane); State stored = state(controller);
        return stored.status == Status.VERIFIED ? Optional.ofNullable(lane == 0 ? stored.first : stored.second) : Optional.empty();
    }
    public static synchronized Map<String, Residue> residues(Object controller) {
        State stored = state(controller); return stored.status == Status.VERIFIED ? stored.residues : Map.of();
    }
    public static synchronized Status status(Object controller) { return state(controller).status; }
    public static synchronized Tag rawState(Object controller) {
        Tag raw = state(controller).raw; return raw == null ? null : raw.copy();
    }
    /** Explicit backed-up trusted recovery only; never called by a generic runtime reset. */
    public static synchronized void clear(Object controller) {
        STATES.put(Objects.requireNonNull(controller), empty());
    }
}
