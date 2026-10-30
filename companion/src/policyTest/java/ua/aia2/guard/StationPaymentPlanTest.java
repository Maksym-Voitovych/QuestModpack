package ua.aia2.guard;

import java.util.Arrays;

/** Pure Java capacity/oracle regressions; does not execute Ad Astra or mutate an inventory. */
public final class StationPaymentPlanTest {
    private static int assertions, oracleCases;

    private static void check(boolean condition, String message) {
        assertions++;
        if (!condition) throw new AssertionError(message);
    }

    private static void exact(int[] capacities, int[] demands, boolean[][] accepted, int[] expected) {
        int[] beforeCapacity = capacities.clone(), beforeDemand = demands.clone();
        boolean[][] beforeAccepted = Arrays.stream(accepted).map(boolean[]::clone).toArray(boolean[][]::new);
        int[] actual = StationPaymentPlan.allocate(capacities, demands, accepted);
        check(Arrays.equals(actual, expected), "Unexpected slot debit plan");
        check(Arrays.equals(capacities, beforeCapacity), "Capacities mutated");
        check(Arrays.equals(demands, beforeDemand), "Demands mutated");
        check(Arrays.deepEquals(accepted, beforeAccepted), "Ingredient membership mutated");
    }

    private static boolean oracle(int[] capacities, int[] demands, boolean[][] accepted, int demand) {
        while (demand < demands.length && demands[demand] == 0) demand++;
        if (demand == demands.length) return true;
        for (int slot = 0; slot < capacities.length; slot++) {
            if (capacities[slot] == 0 || !accepted[demand][slot]) continue;
            capacities[slot]--; demands[demand]--;
            boolean possible = oracle(capacities, demands, accepted, demand);
            capacities[slot]++; demands[demand]++;
            if (possible) return true;
        }
        return false;
    }

    private static void compareOracle(int[] capacities, int[] demands, boolean[][] accepted) {
        oracleCases++;
        int[] actual = StationPaymentPlan.allocate(capacities, demands, accepted);
        boolean possible = oracle(capacities.clone(), demands.clone(), accepted, 0);
        check((actual != null) == possible, "Flow feasibility disagrees with exhaustive unit assignment");
        if (actual == null) return;
        int sum = 0;
        check(actual.length == capacities.length, "Wrong slot count");
        for (int slot = 0; slot < actual.length; slot++) {
            check(actual[slot] >= 0 && actual[slot] <= capacities[slot], "Slot overdrawn");
            sum += actual[slot];
        }
        check(sum == Arrays.stream(demands).sum(), "Demand units duplicated or left unpaid");
        check(oracle(actual.clone(), demands.clone(), accepted, 0), "Returned debits cannot satisfy the ingredients");
    }

    private static void exhaustiveOracle() {
        // All 3x3 membership graphs, all slot capacities0..2 and all demands1..2.
        // This includes disconnected graphs, overlapping tags, bottlenecks and reverse-edge rerouting.
        for (int mask = 0; mask < 512; mask++) {
            boolean[][] accepted = new boolean[3][3];
            for (int demand = 0; demand < 3; demand++)
                for (int slot = 0; slot < 3; slot++)
                    accepted[demand][slot] = (mask & (1 << (demand * 3 + slot))) != 0;
            for (int capacityPattern = 0; capacityPattern < 27; capacityPattern++) {
                int[] capacities = new int[3]; int value = capacityPattern;
                for (int slot = 0; slot < 3; slot++) { capacities[slot] = value % 3; value /= 3; }
                for (int demandPattern = 0; demandPattern < 8; demandPattern++) {
                    int[] demands = new int[3];
                    for (int demand = 0; demand < 3; demand++) demands[demand] = 1 + ((demandPattern >> demand) & 1);
                    compareOracle(capacities, demands, accepted);
                }
            }
        }
    }

    private static void invalidShapesAndBounds() {
        check(StationPaymentPlan.allocate(null, new int[]{1}, new boolean[][]{{true}}) == null, "Null capacities");
        check(StationPaymentPlan.allocate(new int[]{1}, null, new boolean[][]{{true}}) == null, "Null demands");
        check(StationPaymentPlan.allocate(new int[]{1}, new int[]{1}, null) == null, "Null membership");
        check(StationPaymentPlan.allocate(new int[0], new int[]{1}, new boolean[][]{{}}) == null, "No slots");
        check(StationPaymentPlan.allocate(new int[]{1}, new int[0], new boolean[0][]) == null, "No demands");
        check(StationPaymentPlan.allocate(new int[]{1}, new int[]{1}, new boolean[0][]) == null, "Wrong rows");
        check(StationPaymentPlan.allocate(new int[]{1}, new int[]{1}, new boolean[][]{null}) == null, "Null row");
        check(StationPaymentPlan.allocate(new int[]{1}, new int[]{1}, new boolean[][]{{true, true}}) == null, "Wrong columns");
        for (int invalid : new int[]{-1, 4097, Integer.MIN_VALUE, Integer.MAX_VALUE}) {
            check(StationPaymentPlan.allocate(new int[]{invalid}, new int[]{1}, new boolean[][]{{true}}) == null, "Invalid capacity");
            check(StationPaymentPlan.allocate(new int[]{1}, new int[]{invalid}, new boolean[][]{{true}}) == null, "Invalid demand");
        }
        check(StationPaymentPlan.allocate(new int[]{1}, new int[]{0}, new boolean[][]{{true}}) == null, "Zero demand");
        check(StationPaymentPlan.allocate(new int[]{0}, new int[]{1}, new boolean[][]{{true}}) == null, "Zero capacity cannot pay");
        check(StationPaymentPlan.allocate(new int[65], new int[]{1}, new boolean[1][65]) == null, "65 slots");
        check(StationPaymentPlan.allocate(new int[]{1}, new int[65], new boolean[65][1]) == null, "65 demands");
        int[] excess = new int[17]; Arrays.fill(excess, 1024);
        check(StationPaymentPlan.allocate(excess, new int[]{1}, new boolean[1][17]) == null, "Aggregate capacity budget");
        check(StationPaymentPlan.allocate(new int[]{4096}, excess, new boolean[17][1]) == null, "Aggregate demand budget");
        int[] maxCapacity = new int[64], maxDemand = new int[64];
        Arrays.fill(maxCapacity, 256); Arrays.fill(maxDemand, 256);
        boolean[][] maxMembership = new boolean[64][64]; for (boolean[] row : maxMembership) Arrays.fill(row, true);
        exact(maxCapacity, maxDemand, maxMembership, maxCapacity);
        exact(new int[]{4096, 4096, 4096, 4096}, new int[]{4096, 4096, 4096, 4096},
                new boolean[][]{{true, true, true, true}, {true, true, true, true}, {true, true, true, true}, {true, true, true, true}},
                new int[]{4096, 4096, 4096, 4096});
    }

    private static void orderAndCopies() {
        int[] capacities = {2, 1, 3}; int[] demands = {2, 2};
        boolean[][] membership = {{true, true, false}, {true, false, true}};
        int[] first = StationPaymentPlan.allocate(capacities, demands, membership);
        check(first != null, "Feasible order fixture");
        for (int attempt = 0; attempt < 20; attempt++)
            check(Arrays.equals(first, StationPaymentPlan.allocate(capacities, demands, membership)), "Non-deterministic allocation");
        int[] saved = first.clone(); first[0] = 999;
        check(Arrays.equals(saved, StationPaymentPlan.allocate(capacities, demands, membership)), "Returned plan aliases persistent storage");
        for (int[] slotOrder : new int[][]{{0, 1, 2}, {0, 2, 1}, {1, 0, 2}, {1, 2, 0}, {2, 0, 1}, {2, 1, 0}}) {
            for (int[] demandOrder : new int[][]{{0, 1}, {1, 0}}) {
                int[] c = new int[3], d = new int[2]; boolean[][] a = new boolean[2][3];
                for (int slot = 0; slot < 3; slot++) c[slot] = capacities[slotOrder[slot]];
                for (int demand = 0; demand < 2; demand++) {
                    d[demand] = demands[demandOrder[demand]];
                    for (int slot = 0; slot < 3; slot++) a[demand][slot] = membership[demandOrder[demand]][slotOrder[slot]];
                }
                compareOracle(c, d, a);
            }
        }
    }

    public static void main(String[] arguments) {
        exact(new int[]{1, 63}, new int[]{64}, new boolean[][]{{true, true}}, new int[]{1, 63});
        exact(new int[]{1, 62}, new int[]{64}, new boolean[][]{{true, true}}, null);
        exact(new int[]{1}, new int[]{1, 1}, new boolean[][]{{true}, {true}}, null);
        exact(new int[]{64}, new int[]{64, 64}, new boolean[][]{{true}, {true}}, null);
        exact(new int[]{1, 1}, new int[]{1, 1}, new boolean[][]{{true, true}, {true, false}}, new int[]{1, 1});
        exact(new int[]{1, 0, 2}, new int[]{2}, new boolean[][]{{false, true, true}}, new int[]{0, 0, 2});
        invalidShapesAndBounds();
        orderAndCopies();
        exhaustiveOracle();
        System.out.println("StationPaymentPlanTest: " + assertions + " assertions passed; " + oracleCases
                + " exhaustive small capacity/ingredient cases (pure Java; no Ad Astra inventory or world executed)");
    }
}
