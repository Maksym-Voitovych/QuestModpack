package ua.aia2.guard;

import java.util.IdentityHashMap;
import java.util.Map;

/** Recipe objects keep their stage through native recipe caches. No equality or per-tick scans. */
public final class RecipeIdentityIndex {
    private Object generation;
    private final Map<Object, Integer> stages = new IdentityHashMap<>();
    public synchronized void reset() { generation = null; stages.clear(); }
    public synchronized boolean isGeneration(Object value) { return generation == value; }
    public synchronized void replace(Object value, Map<Object, Integer> entries) {
        stages.clear(); stages.putAll(entries); generation = value;
    }
    public synchronized int stage(Object recipe) { return stages.getOrDefault(recipe, 100); }
}
