package ua.aia2.guard;

import java.util.List;
import java.util.Map;
import net.minecraft.server.MinecraftServer;

/**
 * Additional manufacturing evidence for new space-age technology keys.
 *
 * FTB task IDs retain their historical numeric/completed state during a pack
 * upgrade. That state cannot establish that a native NASA recipe ran. This
 * read-only check uses the existing team-owned production journal instead;
 * neither item possession, FTB completion nor old station ownership is read.
 * The caller still owns epoch access, branch eligibility and legacy pending
 * transition/recovery policy. This class grants no stages and writes no data.
 */
public final class RequiredSpaceActions {
    private static final Map<Integer, List<String>> TECHNOLOGY = Map.of(
            37, List.of("nasa_tier_1_rocket", "nasa_tier_2_rocket"),
            38, List.of("nasa_tier_3_rocket", "nasa_tier_4_rocket"));

    private RequiredSpaceActions() {}

    /** Persisted pending transactions can identify which additional contract they paid under. */
    public static int contractVersion() { return 1; }

    public static boolean applies(int epoch, String branch) {
        validate(epoch, branch);
        return branch.equals("tech") && TECHNOLOGY.containsKey(epoch);
    }

    /**
     * Unique signature for Rhino. Existing receipts remain authoritative after
     * runtime configuration reloads; no conversion from saved FTB counts occurs.
     * A journal lookup exception is intentionally propagated so script callers
     * can revoke every cached branch eligibility before reporting the failure.
     * Native recipe callers must treat such an exception as denied production.
     */
    public static boolean hasRequiredActions(MinecraftServer server, String team, int epoch, String branch) {
        if (!applies(epoch, branch)) return true;
        if (server == null || !server.isSameThread() || team == null || team.isBlank()) return false;
        for (String proof : TECHNOLOGY.get(epoch)) {
            if (!ProductionMilestoneBridge.hasProof(server, team, proof)) return false;
        }
        return true;
    }

    private static void validate(int epoch, String branch) {
        if (epoch < 1 || epoch > 48 || !("tech".equals(branch) || "arcane".equals(branch)))
            throw new IllegalArgumentException("Invalid required-space-action epoch/branch");
    }
}
