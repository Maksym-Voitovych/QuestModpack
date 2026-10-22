package ua.aia2.guard;

import java.util.HashMap;
import java.util.Map;

/** Runs with plain Java 21 too; no simulated Minecraft success is asserted. */
public final class GuardPolicyTest {
    private static int assertions;

    private static void expect(boolean condition, String message) {
        assertions++;
        if (!condition) throw new AssertionError(message);
    }

    private static void rejects(Runnable action, String message) {
        try {
            action.run();
            throw new AssertionError(message);
        } catch (IllegalArgumentException | IllegalStateException expected) {
            assertions++;
        }
    }

    public static void main(String[] args) throws Exception {
        GuardPolicy policy = new GuardPolicy();
        expect(policy.mayTick("minecraft:furnace", ""), "Vanilla remains available without bridge");
        expect(!policy.mayTick("mekanism:energized_smelter", "team-a"), "Unknown modded controller is locked");
        rejects(policy::setReady, "An empty rules snapshot must not enable the bridge");

        Map<String, Integer> rules = new HashMap<>();
        rules.put("minecraft:furnace", 0);
        rules.put("rootsclassic:mortar", 1);
        rules.put("create:mechanical_press", 4);
        rules.put("mekanism:energized_smelter", 16);
        rules.put("avaritia:creative_generator", 99);
        rules.put("funmod:unknown_generator", 100);
        policy.setRules(rules);
        rules.put("mekanism:energized_smelter", 0);
        expect(policy.getRequiredStage("mekanism:energized_smelter") == 16, "Rules are an immutable snapshot");
        expect(policy.mayTick("rootsclassic:mortar", ""), "Epoch one needs no ownership");
        policy.setTeamProgress("team-a", 15);
        expect(!policy.mayTick("mekanism:energized_smelter", "team-a"), "Bulk progress cannot bypass readiness barrier");
        policy.setReady();
        expect(policy.isReady(), "Ready state is visible to script bridge");
        expect(policy.mayTick("mekanism:energized_smelter", "team-a"), "Completing fifteen opens epoch sixteen");
        expect(!policy.mayTick("mekanism:energized_smelter", ""), "Unowned staged machine is locked");
        expect(!policy.mayTick("mekanism:energized_smelter", "absent-team"), "Unknown owner team is locked");
        policy.setTeamProgress("team-b", 2);
        expect(!policy.mayTick("create:mechanical_press", "team-b"), "Another team's progress does not leak");
        policy.setTeamProgress("team-b", 3);
        expect(policy.mayTick("create:mechanical_press", "team-b"), "The team's own next epoch is available");
        policy.setTeamProgress("team-b", 0);
        expect(!policy.mayTick("create:mechanical_press", "team-b"), "Progress removal locks an already known machine");

        policy.setTeamProgress("team-a", 47);
        expect(!policy.mayTick("avaritia:creative_generator", "team-a"), "Creative requires final completion");
        policy.setTeamProgress("team-a", 48);
        expect(policy.mayTick("avaritia:creative_generator", "team-a"), "Creative opens after epoch forty eight");
        expect(!policy.mayTick("funmod:unknown_generator", "team-a"), "Quarantine never unlocks");
        rejects(() -> policy.setTeamProgress("", 48), "Blank team is invalid");
        rejects(() -> policy.setTeamProgress("team-c", -1), "Negative progress is invalid");
        rejects(() -> policy.setTeamProgress("team-c", 49), "There is no epoch forty nine");
        rejects(() -> policy.setRules(Map.of("wrong id", 1)), "Invalid registry ID is rejected");
        rejects(() -> policy.setRules(Map.of("create:mechanical_press", 4.5)), "Fractional stage is rejected");
        rejects(() -> policy.setRules(Map.of("create:mechanical_press", Double.NaN)), "NaN stage is rejected");
        expect(policy.getRequiredStage("create:mechanical_press") == 4, "Bad rule update does not replace valid snapshot");

        for (int epoch = 2; epoch <= 48; epoch++) {
            policy.setRules(Map.of("testmod:machine", epoch));
            policy.setTeamProgress("boundary", epoch - 2);
            expect(!policy.mayTick("testmod:machine", "boundary"), "Epoch boundary must stay locked: " + epoch);
            policy.setTeamProgress("boundary", epoch - 1);
            expect(policy.mayTick("testmod:machine", "boundary"), "Epoch boundary must open sequentially: " + epoch);
        }
        policy.clear();
        expect(!policy.isReady(), "Server shutdown clears readiness");
        policy.setRules(Map.of("create:mechanical_press", 4));
        policy.setReady();
        expect(!policy.mayTick("create:mechanical_press", "team-a"), "A new server session cannot inherit old team progress");
        System.out.println("GuardPolicyTest: " + assertions + " assertions passed (pure Java policy; Minecraft not launched)");
        LiveTeamResolverTest.main(args);
    }
}
