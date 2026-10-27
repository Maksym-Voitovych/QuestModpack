package ua.aia2.guard;

import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import java.util.UUID;
import java.util.WeakHashMap;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.nbt.Tag;

/** Receipt storage only. Native payment, current definitions and permissions are checked by the ritual adapter. */
public final class ForbiddenPaidState {
    public static final String ACTIVE_TAG = "active_ritual";
    public static final String RECEIPT_TAG = "aia2_paid_ritual_v1";
    public enum Status { EMPTY, LEGACY, PENDING, VERIFIED, CORRUPT }
    public record Receipt(String ritualId, String definitionFingerprint, String inputFingerprint,
                          String ownerTeam, UUID starter) {
        public Receipt {
            if (ritualId == null || ritualId.length() > 256 || !ritualId.matches("[a-z0-9_.-]+:[a-z0-9_./-]+")
                    || !hash(definitionFingerprint) || !hash(inputFingerprint)
                    || ownerTeam == null || ownerTeam.isBlank() || ownerTeam.length() > 256 || starter == null)
                throw new IllegalArgumentException("Invalid Forbidden ritual payment receipt");
        }
    }
    private static final class State {
        Status status = Status.EMPTY;
        Tag raw;
        Tag encodedReceipt;
        Receipt receipt;
        UUID attempt;
    }
    // Values contain only immutable data/NBT copies, never their weak manager key or the world.
    private static final Map<Object, State> STATES = new WeakHashMap<>();
    private static final Set<String> PAID_KEYS = Set.of("schema", "ritual", "definition", "input", "team", "starter");
    private static final Set<String> PENDING_KEYS = Set.of("schema", "pending", "attempt");
    private ForbiddenPaidState() {}
    private static boolean hash(String text) { return text != null && text.matches("[0-9a-f]{64}"); }
    private static State state(Object manager) { return STATES.computeIfAbsent(Objects.requireNonNull(manager), ignored -> new State()); }
    private static Tag copy(Tag tag) { return tag == null ? null : tag.copy(); }

    private static boolean nativeShape(Tag raw) {
        return raw instanceof CompoundTag tag && tag.contains("ritual", Tag.TAG_STRING)
                && tag.contains("counter", Tag.TAG_INT) && tag.getInt("counter") >= 0
                && tag.contains("lightning_counter", Tag.TAG_INT) && tag.getInt("lightning_counter") >= 0
                && tag.hasUUID("started_by");
    }
    private static boolean binds(Receipt receipt, Tag raw) {
        if (!nativeShape(raw)) return false;
        CompoundTag tag = (CompoundTag) raw;
        return receipt.ritualId().equals(tag.getString("ritual")) && receipt.starter().equals(tag.getUUID("started_by"));
    }
    private static CompoundTag encode(Receipt receipt) {
        CompoundTag tag = new CompoundTag();
        tag.putInt("schema", 1); tag.putString("ritual", receipt.ritualId());
        tag.putString("definition", receipt.definitionFingerprint()); tag.putString("input", receipt.inputFingerprint());
        tag.putString("team", receipt.ownerTeam()); tag.putUUID("starter", receipt.starter());
        return tag;
    }

    /** Call before native load: even a failed native registry decode retains its complete original data. */
    public static synchronized void load(Object manager, CompoundTag incoming) {
        Objects.requireNonNull(manager); Objects.requireNonNull(incoming);
        State s = new State(); s.raw = copy(incoming.get(ACTIVE_TAG)); s.encodedReceipt = copy(incoming.get(RECEIPT_TAG));
        if (s.encodedReceipt == null) {
            s.status = s.raw == null ? Status.EMPTY : nativeShape(s.raw) ? Status.LEGACY : Status.CORRUPT;
        } else {
            s.status = Status.CORRUPT;
            if (s.encodedReceipt instanceof CompoundTag tag && tag.contains("schema", Tag.TAG_INT) && tag.getInt("schema") == 1) {
                if (tag.getAllKeys().equals(PENDING_KEYS) && tag.contains("pending", Tag.TAG_BYTE)
                        && tag.getByte("pending") == 1 && tag.hasUUID("attempt")) {
                    s.attempt = tag.getUUID("attempt"); s.status = Status.PENDING;
                } else if (tag.getAllKeys().equals(PAID_KEYS) && tag.hasUUID("starter")
                        && tag.contains("ritual", Tag.TAG_STRING) && tag.contains("definition", Tag.TAG_STRING)
                        && tag.contains("input", Tag.TAG_STRING) && tag.contains("team", Tag.TAG_STRING)) {
                    try {
                        Receipt paid = new Receipt(tag.getString("ritual"), tag.getString("definition"),
                                tag.getString("input"), tag.getString("team"), tag.getUUID("starter"));
                        if (binds(paid, s.raw)) { s.receipt = paid; s.status = Status.VERIFIED; }
                    } catch (IllegalArgumentException invalid) { /* Preserve the original tag and remain blocked. */ }
                }
            }
        }
        STATES.put(manager, s);
    }

    /** No old/unknown paid state may be silently replaced by another start attempt. */
    public static synchronized UUID begin(Object manager) {
        State s = state(manager);
        if (s.status != Status.EMPTY || s.raw != null || s.encodedReceipt != null)
            throw new IllegalStateException("Existing Forbidden ritual state must be resolved before a new start");
        s.attempt = UUID.randomUUID(); s.status = Status.PENDING;
        CompoundTag pending = new CompoundTag(); pending.putInt("schema", 1);
        pending.putBoolean("pending", true); pending.putUUID("attempt", s.attempt); s.encodedReceipt = pending;
        return s.attempt;
    }

    /** Called only from the exact native reduce RETURN inside the matching scoped start attempt. */
    public static synchronized void markPaid(Object manager, UUID attempt, Receipt receipt, Tag encodedActive) {
        State s = state(manager); Objects.requireNonNull(receipt);
        if (s.status != Status.PENDING || attempt == null || !attempt.equals(s.attempt))
            throw new IllegalStateException("No matching Forbidden ritual payment attempt");
        if (!binds(receipt, encodedActive)) throw new IllegalArgumentException("Receipt does not bind the actual native ritual");
        s.raw = copy(encodedActive); s.receipt = receipt; s.encodedReceipt = encode(receipt); s.attempt = null; s.status = Status.VERIFIED;
    }

    /** An interrupted prepayment attempt with active native state stays pending and cannot run. */
    public static synchronized void abortUnpaid(Object manager, UUID attempt, boolean nativeActive) {
        State s = state(manager);
        if (s.status == Status.PENDING && attempt != null && attempt.equals(s.attempt) && !nativeActive && s.raw == null) clear(manager);
    }

    /** Refresh counters from the actual native active object; corrupt/legacy snapshots remain untouched. */
    public static synchronized boolean captureActive(Object manager, Tag encodedActive) {
        State s = state(manager);
        if (s.status == Status.CORRUPT || s.status == Status.LEGACY && s.raw != null) return false;
        if (!nativeShape(encodedActive) || s.status == Status.VERIFIED && !binds(s.receipt, encodedActive)) return false;
        // A native codec re-encode may omit fields it does not understand. Updating the known
        // counters must not silently discard opaque extension data retained from an earlier save.
        if (s.raw instanceof CompoundTag retained && encodedActive instanceof CompoundTag current) {
            CompoundTag merged = retained.copy();
            for (String key : current.getAllKeys()) merged.put(key, current.get(key).copy());
            s.raw = merged;
        } else s.raw = copy(encodedActive);
        if (s.status == Status.EMPTY) s.status = Status.LEGACY;
        return true;
    }

    /** Call after native save. A failed/omitted native codec can never erase retained paid NBT. */
    public static synchronized void save(Object manager, CompoundTag outgoing, boolean preserveRaw) {
        Objects.requireNonNull(manager); Objects.requireNonNull(outgoing);
        State s = STATES.get(manager);
        if (s == null) return;
        Tag current = outgoing.get(ACTIVE_TAG);
        if (s.raw != null && (preserveRaw || current == null || s.status != Status.VERIFIED && s.status != Status.EMPTY)) {
            outgoing.put(ACTIVE_TAG, s.raw.copy());
        } else if (current != null) {
            // A changed native ID/starter is not evidence that the original paid operation
            // disappeared. Preserve its snapshot rather than persisting the mismatching tag.
            captureActive(manager, current);
            if (s.raw != null) outgoing.put(ACTIVE_TAG, s.raw.copy());
        }
        if (s.encodedReceipt == null) outgoing.remove(RECEIPT_TAG);
        else outgoing.put(RECEIPT_TAG, s.encodedReceipt.copy());
    }

    public static synchronized Status status(Object manager) { return state(manager).status; }
    public static synchronized Optional<Receipt> receipt(Object manager) {
        State s = state(manager); return s.status == Status.VERIFIED ? Optional.of(s.receipt) : Optional.empty();
    }
    public static synchronized boolean hasRetainedActive(Object manager) { return state(manager).raw != null; }
    public static synchronized Tag rawActive(Object manager) { return copy(state(manager).raw); }

    /** Explicit trusted native finish or user-requested cancellation only; never a generic runtime reset. */
    public static synchronized void clear(Object manager) { STATES.put(Objects.requireNonNull(manager), new State()); }
}
