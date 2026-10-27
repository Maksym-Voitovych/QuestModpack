package ua.aia2.guard;

import java.util.UUID;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.nbt.Tag;

/** Actual receipt primitive; NBT host is modeled here and checked separately in the native server. */
public final class ForbiddenPaidStateHarness {
    private static int checks;
    private static final UUID STARTER = UUID.fromString("4e140b0e-2bb0-4169-b9d2-5483ab0e6d56");
    private static final String ID = "forbidden_arcanus:eternal_stella";
    private static final ForbiddenPaidState.Receipt PAID = new ForbiddenPaidState.Receipt(ID, "a".repeat(64), "b".repeat(64), "team-a", STARTER);
    private static void check(boolean value, String why) { checks++; if (!value) throw new AssertionError(why); }
    private static void rejects(Runnable call, String why) {
        boolean failed = false;
        try { call.run(); } catch (IllegalArgumentException | IllegalStateException expected) { failed = true; }
        check(failed, why);
    }
    private static CompoundTag active(int counter) {
        CompoundTag tag = new CompoundTag(); tag.putString("ritual", ID); tag.putInt("counter", counter);
        tag.putInt("lightning_counter", 0); tag.putUUID("started_by", STARTER);
        CompoundTag extra = new CompoundTag(); extra.putString("foreign", "keep"); tag.put("unknown_native_extension", extra);
        return tag;
    }
    private static CompoundTag paidRoot() {
        Object manager = new Object(); UUID token = ForbiddenPaidState.begin(manager);
        ForbiddenPaidState.markPaid(manager, token, PAID, active(7));
        CompoundTag saved = new CompoundTag(); ForbiddenPaidState.save(manager, saved, false); return saved;
    }
    public static void main(String[] args) {
        Object manager = new Object();
        check(ForbiddenPaidState.status(manager) == ForbiddenPaidState.Status.EMPTY, "new manager empty");
        UUID attempt = ForbiddenPaidState.begin(manager);
        check(ForbiddenPaidState.status(manager) == ForbiddenPaidState.Status.PENDING, "start pending before payment");
        check(ForbiddenPaidState.receipt(manager).isEmpty(), "pending never grants paid receipt");
        check(!ForbiddenPaidState.hasRetainedActive(manager), "pre-active start has no invented native state");
        rejects(() -> ForbiddenPaidState.begin(manager), "second start cannot overwrite pending attempt");
        rejects(() -> ForbiddenPaidState.markPaid(manager, UUID.randomUUID(), PAID, active(0)), "wrong attempt cannot record payment");
        rejects(() -> ForbiddenPaidState.markPaid(manager, attempt, PAID, null), "missing native state cannot record payment");
        CompoundTag wrong = active(0); wrong.putUUID("started_by", UUID.randomUUID());
        rejects(() -> ForbiddenPaidState.markPaid(manager, attempt, PAID, wrong), "starter mismatch cannot bind receipt");
        CompoundTag wrongRitual = active(0); wrongRitual.putString("ritual", "forbidden_arcanus:other");
        rejects(() -> ForbiddenPaidState.markPaid(manager, attempt, PAID, wrongRitual), "ritual ID mismatch cannot bind receipt");
        CompoundTag paymentSnapshot = active(0);
        ForbiddenPaidState.markPaid(manager, attempt, PAID, paymentSnapshot);
        paymentSnapshot.putInt("counter", 91);
        check(((CompoundTag) ForbiddenPaidState.rawActive(manager)).getInt("counter") == 0, "markPaid takes defensive native snapshot");
        check(ForbiddenPaidState.status(manager) == ForbiddenPaidState.Status.VERIFIED, "exact payment and native state bound");
        check(ForbiddenPaidState.receipt(manager).orElseThrow().equals(PAID), "immutable receipt retained");
        rejects(() -> ForbiddenPaidState.markPaid(manager, attempt, PAID, active(0)), "same attempt cannot replay markPaid");
        rejects(() -> ForbiddenPaidState.begin(manager), "paid operation cannot be silently replaced");

        CompoundTag save = new CompoundTag(); save.put(ForbiddenPaidState.ACTIVE_TAG, active(20)); save.putString("foreign", "untouched");
        ForbiddenPaidState.save(manager, save, false);
        check(save.getCompound(ForbiddenPaidState.ACTIVE_TAG).getInt("counter") == 20, "normal native save retains current counter");
        check(((CompoundTag) ForbiddenPaidState.rawActive(manager)).getInt("counter") == 20, "snapshot tracks actual native counter");
        ((CompoundTag) ForbiddenPaidState.rawActive(manager)).putInt("counter", 99);
        check(((CompoundTag) ForbiddenPaidState.rawActive(manager)).getInt("counter") == 20, "read returns defensive copy");
        save.getCompound(ForbiddenPaidState.ACTIVE_TAG).putInt("counter", 90);
        check(((CompoundTag) ForbiddenPaidState.rawActive(manager)).getInt("counter") == 20, "outgoing root cannot mutate state");
        CompoundTag changed = new CompoundTag(); changed.put(ForbiddenPaidState.ACTIVE_TAG, active(800));
        ForbiddenPaidState.save(manager, changed, true);
        check(changed.getCompound(ForbiddenPaidState.ACTIVE_TAG).getInt("counter") == 20, "blocked save overlays original current progress");
        CompoundTag omitted = new CompoundTag(); ForbiddenPaidState.save(manager, omitted, false);
        check(omitted.getCompound(ForbiddenPaidState.ACTIVE_TAG).getInt("counter") == 20, "native codec omission cannot erase paid snapshot");
        check(save.getString("foreign").equals("untouched"), "foreign root data preserved");

        CompoundTag nativeWithoutExtensions = active(21); nativeWithoutExtensions.remove("unknown_native_extension");
        CompoundTag refresh = new CompoundTag(); refresh.put(ForbiddenPaidState.ACTIVE_TAG, nativeWithoutExtensions);
        ForbiddenPaidState.save(manager, refresh, false);
        check(refresh.getCompound(ForbiddenPaidState.ACTIVE_TAG).getInt("counter") == 21, "codec refresh advances actual native counter");
        check(refresh.getCompound(ForbiddenPaidState.ACTIVE_TAG).getCompound("unknown_native_extension").getString("foreign").equals("keep"), "codec refresh preserves opaque native extension data");
        for (int mode = 0; mode < 3; mode++) {
            CompoundTag mismatching = active(999);
            switch (mode) {
                case 0 -> mismatching.putUUID("started_by", UUID.randomUUID());
                case 1 -> mismatching.putString("ritual", "forbidden_arcanus:other");
                case 2 -> mismatching.putInt("counter", -1);
            }
            CompoundTag rejectedSave = new CompoundTag(); rejectedSave.put(ForbiddenPaidState.ACTIVE_TAG, mismatching);
            ForbiddenPaidState.save(manager, rejectedSave, false);
            check(rejectedSave.getCompound(ForbiddenPaidState.ACTIVE_TAG).getInt("counter") == 21, "invalid native refresh retains original paid snapshot variant " + mode);
            Object preservedPaid = new Object(); ForbiddenPaidState.load(preservedPaid, rejectedSave);
            check(ForbiddenPaidState.status(preservedPaid) == ForbiddenPaidState.Status.VERIFIED && ForbiddenPaidState.receipt(preservedPaid).orElseThrow().equals(PAID), "rejected refresh remains valid paid operation after restart variant " + mode);
        }

        Object reloaded = new Object(); ForbiddenPaidState.load(reloaded, omitted);
        check(ForbiddenPaidState.status(reloaded) == ForbiddenPaidState.Status.VERIFIED, "new manager restores valid receipt");
        check(ForbiddenPaidState.receipt(reloaded).orElseThrow().equals(PAID), "receipt fields survive save/load");
        omitted.getCompound(ForbiddenPaidState.ACTIVE_TAG).putInt("counter", 70);
        omitted.getCompound(ForbiddenPaidState.RECEIPT_TAG).putString("team", "edited");
        check(ForbiddenPaidState.receipt(reloaded).orElseThrow().ownerTeam().equals("team-a"), "incoming root deep copied");
        check(((CompoundTag) ForbiddenPaidState.rawActive(reloaded)).getInt("counter") == 20, "incoming counter deep copied");

        Object legacy = new Object(); CompoundTag legacyRoot = new CompoundTag(); legacyRoot.put(ForbiddenPaidState.ACTIVE_TAG, active(13));
        ForbiddenPaidState.load(legacy, legacyRoot);
        check(ForbiddenPaidState.status(legacy) == ForbiddenPaidState.Status.LEGACY, "preexisting active without proof stays legacy");
        check(ForbiddenPaidState.receipt(legacy).isEmpty(), "legacy is never automatically paid");
        rejects(() -> ForbiddenPaidState.begin(legacy), "legacy cannot be overwritten by new start");
        check(!ForbiddenPaidState.captureActive(legacy, active(99)), "legacy raw snapshot cannot be silently upgraded");
        CompoundTag legacyOut = new CompoundTag(); legacyOut.put(ForbiddenPaidState.ACTIVE_TAG, active(60)); ForbiddenPaidState.save(legacy, legacyOut, false);
        check(legacyOut.getCompound(ForbiddenPaidState.ACTIVE_TAG).getInt("counter") == 13, "legacy progress retained even after native re-encode");
        check(!legacyOut.contains(ForbiddenPaidState.RECEIPT_TAG), "legacy save invents no receipt");

        CompoundTag badRoot = paidRoot(); badRoot.getCompound(ForbiddenPaidState.RECEIPT_TAG).putInt("schema", 2);
        Object unknown = new Object(); ForbiddenPaidState.load(unknown, badRoot);
        check(ForbiddenPaidState.status(unknown) == ForbiddenPaidState.Status.CORRUPT, "unknown schema blocked");
        check(ForbiddenPaidState.receipt(unknown).isEmpty(), "unknown schema grants no receipt");
        rejects(() -> ForbiddenPaidState.begin(unknown), "unknown schema cannot be replaced");
        check(!ForbiddenPaidState.captureActive(unknown, active(80)), "unknown schema cannot be recertified");
        CompoundTag badOut = new CompoundTag(); ForbiddenPaidState.save(unknown, badOut, false);
        check(badOut.equals(badRoot), "unknown root receipt and raw native data preserved verbatim");

        for (int mode = 0; mode < 12; mode++) {
            CompoundTag bad = paidRoot(); CompoundTag receipt = bad.getCompound(ForbiddenPaidState.RECEIPT_TAG);
            switch (mode) {
                case 0 -> receipt.putString("schema", "1");
                case 1 -> receipt.putString("definition", "short");
                case 2 -> receipt.putString("team", " ");
                case 3 -> receipt.putString("future_semantic_field", "do-not-ignore");
                case 4 -> bad.remove(ForbiddenPaidState.ACTIVE_TAG);
                case 5 -> bad.getCompound(ForbiddenPaidState.ACTIVE_TAG).putString("ritual", "forbidden_arcanus:other");
                case 6 -> bad.getCompound(ForbiddenPaidState.ACTIVE_TAG).putInt("counter", -1);
                case 7 -> bad.getCompound(ForbiddenPaidState.ACTIVE_TAG).putString("counter", "7");
                case 8 -> bad.getCompound(ForbiddenPaidState.ACTIVE_TAG).putUUID("started_by", UUID.randomUUID());
                case 9 -> bad.getCompound(ForbiddenPaidState.ACTIVE_TAG).putInt("lightning_counter", -1);
                case 10 -> receipt.putString("starter", STARTER.toString());
                case 11 -> receipt.putString("input", "A".repeat(64));
            }
            Object corrupt = new Object(); ForbiddenPaidState.load(corrupt, bad);
            check(ForbiddenPaidState.status(corrupt) == ForbiddenPaidState.Status.CORRUPT && ForbiddenPaidState.receipt(corrupt).isEmpty(), "malformed paid state blocked variant " + mode);
            CompoundTag after = new CompoundTag(); ForbiddenPaidState.save(corrupt, after, false);
            check(after.equals(bad), "malformed paid state preserved variant " + mode);
        }
        CompoundTag opaque = new CompoundTag(); opaque.putString(ForbiddenPaidState.ACTIVE_TAG, "unparsed-native"); opaque.putString(ForbiddenPaidState.RECEIPT_TAG, "unparsed-receipt");
        Object opaqueManager = new Object(); ForbiddenPaidState.load(opaqueManager, opaque);
        CompoundTag opaqueSaved = new CompoundTag(); ForbiddenPaidState.save(opaqueManager, opaqueSaved, true);
        check(opaqueSaved.equals(opaque), "noncompound native/receipt tags preserved verbatim");
        check(ForbiddenPaidState.status(opaqueManager) == ForbiddenPaidState.Status.CORRUPT, "opaque tags remain blocked");

        Object unpaid = new Object(); UUID unpaidToken = ForbiddenPaidState.begin(unpaid);
        ForbiddenPaidState.abortUnpaid(unpaid, UUID.randomUUID(), false);
        check(ForbiddenPaidState.status(unpaid) == ForbiddenPaidState.Status.PENDING, "wrong token cannot abort attempt");
        ForbiddenPaidState.abortUnpaid(unpaid, unpaidToken, true);
        check(ForbiddenPaidState.status(unpaid) == ForbiddenPaidState.Status.PENDING, "active prepayment exception remains blocked");
        check(ForbiddenPaidState.captureActive(unpaid, active(0)), "interrupted active can be retained without certification");
        ForbiddenPaidState.abortUnpaid(unpaid, unpaidToken, false);
        check(ForbiddenPaidState.status(unpaid) == ForbiddenPaidState.Status.PENDING, "retained raw state cannot be dropped on absent parsed native active");
        CompoundTag pendingSaved = new CompoundTag(); ForbiddenPaidState.save(unpaid, pendingSaved, true);
        Object pendingReload = new Object(); ForbiddenPaidState.load(pendingReload, pendingSaved);
        check(ForbiddenPaidState.status(pendingReload) == ForbiddenPaidState.Status.PENDING && ForbiddenPaidState.receipt(pendingReload).isEmpty(), "interrupted attempt survives restart without paid grant");
        Object noActive = new Object(); UUID noActiveToken = ForbiddenPaidState.begin(noActive); ForbiddenPaidState.abortUnpaid(noActive, noActiveToken, false);
        check(ForbiddenPaidState.status(noActive) == ForbiddenPaidState.Status.EMPTY, "known pre-active unpaid failure may abort safely");
        UUID replacementAttempt = ForbiddenPaidState.begin(noActive);
        rejects(() -> ForbiddenPaidState.markPaid(noActive, noActiveToken, PAID, active(0)), "aborted old token cannot pay replacement attempt");
        ForbiddenPaidState.abortUnpaid(noActive, noActiveToken, false);
        check(ForbiddenPaidState.status(noActive) == ForbiddenPaidState.Status.PENDING, "aborted old token cannot cancel replacement attempt");
        ForbiddenPaidState.markPaid(noActive, replacementAttempt, PAID, active(0));
        ForbiddenPaidState.abortUnpaid(noActive, replacementAttempt, false);
        check(ForbiddenPaidState.status(noActive) == ForbiddenPaidState.Status.VERIFIED, "abortUnpaid cannot erase a successfully paid attempt");
        CompoundTag tombstone = paidRoot(); tombstone.remove(ForbiddenPaidState.ACTIVE_TAG); tombstone.putString("foreign", "keep");
        ForbiddenPaidState.clear(reloaded); ForbiddenPaidState.save(reloaded, tombstone, false);
        check(!tombstone.contains(ForbiddenPaidState.RECEIPT_TAG) && !tombstone.contains(ForbiddenPaidState.ACTIVE_TAG), "trusted finish clears only owned receipt and restores no old active");
        check(tombstone.getString("foreign").equals("keep"), "trusted finish preserves foreign data");
        Object unseen = new Object(); CompoundTag untouched = opaque.copy(); ForbiddenPaidState.save(unseen, untouched, true);
        check(untouched.equals(opaque), "save before load never destroys opaque incoming data");
        rejects(() -> new ForbiddenPaidState.Receipt("bad", "a".repeat(64), "b".repeat(64), "team", STARTER), "invalid ritual identifier rejected");
        rejects(() -> new ForbiddenPaidState.Receipt(ID, "a".repeat(64), "b".repeat(64), "team", null), "missing starter rejected");
        rejects(() -> new ForbiddenPaidState.Receipt(ID, "a".repeat(64), "b".repeat(64), "x".repeat(257), STARTER), "unbounded owner team rejected");
        System.out.println("ForbiddenPaidStateHarness: " + checks + " actual-state/NBT-host modeled assertions PASS");
    }
}
