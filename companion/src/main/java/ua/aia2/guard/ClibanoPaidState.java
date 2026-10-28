package ua.aia2.guard;

import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import java.util.WeakHashMap;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.nbt.Tag;

/** Two-lane receipt storage only; the native adapter proves payment and current permissions. */
public final class ClibanoPaidState {
    public static final String TAG = "aia2_clibano_paid_v1";
    public enum Status { EMPTY, VERIFIED, CORRUPT }
    public record Lane(String recipeId, String definitionFingerprint, String inputFingerprint) {
        public Lane {
            if (recipeId == null || recipeId.length() > 256
                    || !recipeId.matches("[a-z0-9_.-]+:[a-z0-9_./-]+")
                    || !hash(definitionFingerprint) || !hash(inputFingerprint))
                throw new IllegalArgumentException("Invalid Clibano lane receipt");
        }
    }
    private static final class State {
        Status status = Status.EMPTY;
        Tag raw;
        Lane first, second;
    }
    // Values contain only immutable strings/NBT copies, never their weak controller key or a world.
    private static final Map<Object, State> STATES = new WeakHashMap<>();
    private static final Set<String> ROOT_KEYS = Set.of("schema", "first", "second");
    private static final Set<String> LANE_KEYS = Set.of("recipe", "definition", "input");
    private ClibanoPaidState() {}
    private static boolean hash(String value) { return value != null && value.matches("[0-9a-f]{64}"); }
    private static State state(Object controller) {
        return STATES.computeIfAbsent(Objects.requireNonNull(controller), ignored -> new State());
    }
    private static void index(int lane) {
        if (lane < 0 || lane > 1) throw new IllegalArgumentException("Clibano lane index must be 0 or 1");
    }
    private static Lane decode(Tag raw) {
        if (!(raw instanceof CompoundTag tag) || !tag.getAllKeys().equals(LANE_KEYS)
                || !tag.contains("recipe", Tag.TAG_STRING) || !tag.contains("definition", Tag.TAG_STRING)
                || !tag.contains("input", Tag.TAG_STRING))
            throw new IllegalArgumentException("Invalid Clibano lane NBT");
        return new Lane(tag.getString("recipe"), tag.getString("definition"), tag.getString("input"));
    }
    private static CompoundTag encode(Lane lane) {
        CompoundTag tag = new CompoundTag(); tag.putString("recipe", lane.recipeId());
        tag.putString("definition", lane.definitionFingerprint()); tag.putString("input", lane.inputFingerprint());
        return tag;
    }
    /** Call before native load. Unsupported/corrupt tags are retained verbatim and never authorized. */
    public static synchronized void load(Object controller, CompoundTag incoming) {
        Objects.requireNonNull(controller); Objects.requireNonNull(incoming);
        State checked = new State();
        Tag original = incoming.get(TAG); checked.raw = original == null ? null : original.copy();
        if (checked.raw != null) {
            checked.status = Status.CORRUPT;
            if (checked.raw instanceof CompoundTag tag && ROOT_KEYS.containsAll(tag.getAllKeys())
                    && tag.contains("schema", Tag.TAG_INT) && tag.getInt("schema") == 1) {
                try {
                    checked.first = tag.contains("first") ? decode(tag.get("first")) : null;
                    checked.second = tag.contains("second") ? decode(tag.get("second")) : null;
                    checked.status = Status.VERIFIED;
                } catch (IllegalArgumentException invalid) {
                    checked.first = null; checked.second = null;
                }
            }
        }
        STATES.put(controller, checked);
    }
    /** Save after native serialization; absence/codec failure cannot delete our retained raw ledger. */
    public static synchronized void save(Object controller, CompoundTag outgoing) {
        Objects.requireNonNull(controller); Objects.requireNonNull(outgoing);
        State checked = STATES.get(controller);
        if (checked == null) return;
        if (checked.raw == null) outgoing.remove(TAG);
        else outgoing.put(TAG, checked.raw.copy());
    }
    /** Trusted adapter only: never use current native progress alone to manufacture a receipt. */
    public static synchronized void setLanes(Object controller, Lane first, Lane second) {
        State previous = state(controller);
        if (previous.status == Status.CORRUPT)
            throw new IllegalStateException("Corrupt Clibano paid state requires explicit recovery");
        if (first == null && second == null) { clear(controller); return; }
        CompoundTag tag = new CompoundTag(); tag.putInt("schema", 1);
        if (first != null) tag.put("first", encode(first));
        if (second != null) tag.put("second", encode(second));
        State replacement = new State(); replacement.status = Status.VERIFIED;
        replacement.first = first; replacement.second = second; replacement.raw = tag;
        STATES.put(controller, replacement);
    }
    /** Replacing/clearing one completed lane must retain the other lane's independent receipt. */
    public static synchronized void setLane(Object controller, int lane, Lane receipt) {
        index(lane); State previous = state(controller);
        setLanes(controller, lane == 0 ? receipt : previous.first, lane == 1 ? receipt : previous.second);
    }
    public static synchronized Optional<Lane> lane(Object controller, int lane) {
        index(lane); State checked = state(controller);
        return checked.status == Status.VERIFIED ? Optional.ofNullable(lane == 0 ? checked.first : checked.second) : Optional.empty();
    }
    public static synchronized Status status(Object controller) { return state(controller).status; }
    public static synchronized boolean hasState(Object controller) { return state(controller).raw != null; }
    public static synchronized Tag rawState(Object controller) {
        Tag raw = state(controller).raw; return raw == null ? null : raw.copy();
    }
    /** Explicit trusted completion/cancellation only; a generic guard runtime reset must not call this. */
    public static synchronized void clear(Object controller) {
        STATES.put(Objects.requireNonNull(controller), new State());
    }
}
