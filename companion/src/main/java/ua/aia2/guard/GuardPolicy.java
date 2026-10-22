package ua.aia2.guard;

import java.util.HashMap;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

/** Minecraft-independent policy, shared by the native ticker bridge and tests. */
public final class GuardPolicy {
    private volatile Map<String, Integer> rules = Map.of();
    private final Map<String, Integer> teamProgress = new ConcurrentHashMap<>();
    private volatile boolean ready;

    public synchronized void clear() {
        ready = false;
        teamProgress.clear();
        rules = Map.of();
    }

    /** Replace the complete rules snapshot only after all entries are validated. */
    public synchronized void setRules(Map<String, ? extends Number> replacements) {
        var checked = new HashMap<String, Integer>();
        replacements.forEach((id, value) -> {
            if (id == null || !id.matches("[a-z0-9_.-]+:[a-z0-9_./-]+") || value == null) {
                throw new IllegalArgumentException("Invalid block rule: " + id);
            }
            double raw = value.doubleValue();
            int required = value.intValue();
            if (!Double.isFinite(raw) || raw != required || required < 0 || required > 100) {
                throw new IllegalArgumentException("Invalid block stage for " + id + ": " + value);
            }
            checked.put(id, required);
        });
        rules = Map.copyOf(checked);
    }

    public void setTeamProgress(String team, int completed) {
        if (team == null || team.isBlank() || completed < 0 || completed > 48) {
            throw new IllegalArgumentException("Invalid team progress");
        }
        teamProgress.put(team, completed);
    }

    public void setReady() {
        if (rules.isEmpty()) {
            throw new IllegalStateException("Cannot enable guard without a block rules snapshot");
        }
        ready = true;
    }

    public boolean isReady() {
        return ready;
    }

    public int getRequiredStage(String blockId) {
        Integer required = rules.get(blockId);
        // An unclassified modded controller must not silently bypass progression.
        return required != null ? required : blockId.startsWith("minecraft:") ? 0 : 100;
    }

    public boolean mayTick(String blockId, String ownerTeam) {
        int required = getRequiredStage(blockId);
        if (required <= 1) {
            return true;
        }
        if (!ready || ownerTeam == null || ownerTeam.isBlank()) {
            return false;
        }
        Integer completed = teamProgress.get(ownerTeam);
        if (completed == null) {
            return false;
        }
        if (required == 99) {
            return completed == 48;
        }
        return required <= 48 && required <= completed + 1;
    }
}
