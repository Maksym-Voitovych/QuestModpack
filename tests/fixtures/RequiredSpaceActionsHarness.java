package ua.aia2.guard;

import java.util.List;
import net.minecraft.server.MinecraftServer;

/** Actual production helper; Minecraft server and journal receivers are explicit models. */
public final class RequiredSpaceActionsHarness {
    private static int checks;
    private static void check(boolean condition, String message) {
        checks++;
        if (!condition) throw new AssertionError(message);
    }
    private static void invalid(Runnable action, String message) {
        boolean rejected = false;
        try { action.run(); } catch (IllegalArgumentException expected) { rejected = true; }
        check(rejected, message);
    }
    private static boolean proof(MinecraftServer server, String team, int epoch, String branch) {
        return RequiredSpaceActions.hasRequiredActions(server, team, epoch, branch);
    }
    public static void main(String[] args) {
        MinecraftServer server = new MinecraftServer();
        MinecraftServer other = new MinecraftServer();
        check(RequiredSpaceActions.contractVersion() == 1, "pending contract has a stable positive version");

        for (int epoch = 1; epoch <= 48; epoch++) {
            for (String branch : List.of("tech", "arcane")) {
                boolean applies = branch.equals("tech") && (epoch == 37 || epoch == 38);
                check(RequiredSpaceActions.applies(epoch, branch) == applies, "only the two reviewed technology epochs apply");
                ProductionMilestoneBridge.reads.clear();
                check(proof(server, "team-a", epoch, branch) == !applies, "no receipt cannot satisfy an applicable key");
                check(ProductionMilestoneBridge.reads.size() == (applies ? 1 : 0), "unrelated keys never touch the extra journal");
                if (!applies) {
                    check(proof(null, null, epoch, branch), "extra action policy does not invent restrictions for other branches");
                }
            }
        }

        for (int epoch : new int[]{0, -1, 49, Integer.MIN_VALUE, Integer.MAX_VALUE}) {
            invalid(() -> RequiredSpaceActions.applies(epoch, "tech"), "invalid applies epoch rejected");
            invalid(() -> proof(server, "team-a", epoch, "tech"), "invalid read epoch rejected");
        }
        for (String branch : new String[]{null, "", "TECH", "magic", "tech ", "unknown"}) {
            invalid(() -> RequiredSpaceActions.applies(37, branch), "invalid applies branch rejected");
            invalid(() -> proof(server, "team-a", 37, branch), "invalid read branch rejected");
        }

        for (int epoch : new int[]{37, 38}) {
            check(!proof(null, "team-a", epoch, "tech"), "applicable key needs a real server");
            for (String team : new String[]{null, "", " ", "\t\n"})
                check(!proof(server, team, epoch, "tech"), "applicable key needs a nonblank team");
            server.sameThread = false;
            ProductionMilestoneBridge.reads.clear();
            check(!proof(server, "team-a", epoch, "tech"), "off-thread proof read is denied");
            check(ProductionMilestoneBridge.reads.isEmpty(), "off-thread call never reaches SavedData");
            server.sameThread = true;
        }

        ProductionMilestoneBridge.grant(server, "team-a", "nasa_tier_1_rocket");
        check(!proof(server, "team-a", 37, "tech"), "one of two independent rocket tiers is insufficient");
        check(!proof(server, "team-a", 38, "tech"), "first-epoch proof cannot stand in for advanced rockets");
        ProductionMilestoneBridge.grant(server, "team-a", "nasa_tier_2_rocket");
        check(proof(server, "team-a", 37, "tech"), "two actual team journal receipts satisfy epoch37");
        check(!proof(server, "team-b", 37, "tech"), "a different team cannot inherit the builder's receipts");
        check(!proof(other, "team-a", 37, "tech"), "another server/world with the same team name cannot inherit receipts");
        ProductionMilestoneBridge.grant(server, "team-a", "nasa_tier_4_rocket");
        check(!proof(server, "team-a", 38, "tech"), "advanced receipt order does not remove the other tier requirement");
        ProductionMilestoneBridge.grant(server, "team-a", "nasa_tier_3_rocket");
        check(proof(server, "team-a", 38, "tech"), "both advanced team receipts satisfy epoch38");

        ProductionMilestoneBridge.reads.clear();
        check(proof(server, "team-a", 37, "tech"), "epoch37 remains satisfied independently");
        check(ProductionMilestoneBridge.reads.equals(List.of("team-a:nasa_tier_1_rocket", "team-a:nasa_tier_2_rocket")),
                "exact epoch37 proof identifiers and order are used");
        ProductionMilestoneBridge.reads.clear();
        check(proof(server, "team-a", 38, "tech"), "epoch38 remains satisfied independently");
        check(ProductionMilestoneBridge.reads.equals(List.of("team-a:nasa_tier_3_rocket", "team-a:nasa_tier_4_rocket")),
                "exact epoch38 proof identifiers and order are used");

        ProductionMilestoneBridge.configured = false;
        check(proof(server, "team-a", 37, "tech"), "runtime rule reset does not invalidate existing durable evidence");
        check(proof(server, "team-a", 38, "tech"), "advanced durable evidence also survives runtime reset");
        ProductionMilestoneBridge.failure = new IllegalStateException("modeled unreadable journal");
        boolean propagated = false;
        try { proof(server, "team-a", 37, "tech"); }
        catch (IllegalStateException expected) { propagated = expected == ProductionMilestoneBridge.failure; }
        check(propagated, "journal failure propagates to the caller's fail-closed cache cleanup");
        check(proof(server, "team-a", 38, "arcane"), "unrelated branch does not depend on an unreadable extra journal");
        check(proof(server, "team-a", 36, "tech"), "earlier key does not depend on an unreadable extra journal");
        ProductionMilestoneBridge.failure = null;
        check(proof(server, "team-a", 37, "tech"), "same durable evidence is usable after storage recovers");
        check(ProductionMilestoneBridge.writes == 0, "readiness never writes/adopts/fabricates receipts");
        System.out.println(checks + " required-space-action actual-helper modeled assertions PASS; no FTB/Minecraft launch");
    }
}
