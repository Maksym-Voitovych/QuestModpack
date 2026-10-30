package ua.aia2.guard;

import java.util.Arrays;

/**
 * Bounded capacity allocation for overlapping station ingredients.
 * Each inventory unit can pay at most one demand. No Minecraft or recipe API is used here.
 */
public final class StationPaymentPlan {
    public static final int MAX_PARTS = 64;
    public static final int MAX_ENTRY_UNITS = 4096;
    public static final int MAX_TOTAL_UNITS = 16384;

    private StationPaymentPlan() {}

    /**
     * Returns a new array of total debits per slot, or null for invalid/infeasible input.
     * {@code accepted[demandIndex][slotIndex]} describes ingredient membership.
     * Capacities may be zero; demands must be positive. Both aggregate capacities
     * and aggregate demands are bounded independently by MAX_TOTAL_UNITS.
     * Caller arrays are copied and never modified. A stable index order makes the
     * chosen valid allocation deterministic, without greedy false negatives.
     */
    public static int[] allocate(int[] capacities, int[] demands, boolean[][] accepted) {
        if (capacities == null || demands == null || accepted == null
                || capacities.length == 0 || capacities.length > MAX_PARTS
                || demands.length == 0 || demands.length > MAX_PARTS
                || accepted.length != demands.length) return null;
        int[] available = capacities.clone();
        int[] required = demands.clone();
        boolean[][] membership = new boolean[required.length][];
        for (int index = 0; index < required.length; index++) {
            boolean[] row = accepted[index];
            if (row == null || row.length != available.length) return null;
            membership[index] = row.clone();
        }
        int capacityTotal = 0, demandTotal = 0;
        for (int count : available) {
            if (count < 0 || count > MAX_ENTRY_UNITS) return null;
            capacityTotal += count;
            if (capacityTotal > MAX_TOTAL_UNITS) return null;
        }
        for (int count : required) {
            if (count <= 0 || count > MAX_ENTRY_UNITS) return null;
            demandTotal += count;
            if (demandTotal > MAX_TOTAL_UNITS) return null;
        }
        if (demandTotal > capacityTotal) return null;

        // source -> inventory slots -> ingredient demands -> sink. Reverse edges
        // permit a later constrained demand to reclaim a unit from an earlier one.
        int source = 0, firstSlot = 1, firstDemand = firstSlot + available.length;
        int sink = firstDemand + required.length;
        int[][] residual = new int[sink + 1][sink + 1];
        for (int slot = 0; slot < available.length; slot++) {
            residual[source][firstSlot + slot] = available[slot];
            for (int demand = 0; demand < required.length; demand++) {
                if (membership[demand][slot])
                    residual[firstSlot + slot][firstDemand + demand] = Math.min(available[slot], required[demand]);
            }
        }
        for (int demand = 0; demand < required.length; demand++)
            residual[firstDemand + demand][sink] = required[demand];

        int[] level = new int[sink + 1], next = new int[sink + 1];
        int paid = 0;
        while (paid < demandTotal && levels(residual, source, sink, level)) {
            Arrays.fill(next, 0);
            int sent;
            while (paid < demandTotal
                    && (sent = send(source, sink, demandTotal - paid, residual, level, next)) != 0)
                paid += sent;
        }
        if (paid != demandTotal) return null;
        int[] debits = new int[available.length];
        for (int slot = 0; slot < debits.length; slot++)
            debits[slot] = available[slot] - residual[source][firstSlot + slot];
        return debits;
    }

    private static boolean levels(int[][] residual, int source, int sink, int[] level) {
        Arrays.fill(level, -1);
        int[] queue = new int[level.length];
        int head = 0, tail = 0;
        queue[tail++] = source; level[source] = 0;
        while (head < tail) {
            int current = queue[head++];
            for (int target = 0; target < level.length; target++) {
                if (residual[current][target] > 0 && level[target] == -1) {
                    level[target] = level[current] + 1;
                    queue[tail++] = target;
                }
            }
        }
        return level[sink] != -1;
    }

    // At most 130 vertices; residual paths and recursion depth are structurally bounded.
    private static int send(int current, int sink, int limit, int[][] residual, int[] level, int[] next) {
        if (current == sink) return limit;
        for (; next[current] < level.length; next[current]++) {
            int target = next[current];
            if (residual[current][target] <= 0 || level[target] != level[current] + 1) continue;
            int sent = send(target, sink, Math.min(limit, residual[current][target]), residual, level, next);
            if (sent == 0) continue;
            residual[current][target] -= sent;
            residual[target][current] += sent;
            return sent;
        }
        return 0;
    }
}
