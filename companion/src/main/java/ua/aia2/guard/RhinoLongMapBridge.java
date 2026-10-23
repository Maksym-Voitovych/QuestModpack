package ua.aia2.guard;

import it.unimi.dsi.fastutil.objects.Object2LongMap;

/** A single primitive signature avoids Rhino ambiguity between Map/boxed fastutil bridges. */
public final class RhinoLongMapBridge {
    private RhinoLongMapBridge() {}
    public static void putValue(Object2LongMap<Object> map, Object key, long value) {
        if (map == null || key == null || value <= 0) {
            throw new IllegalArgumentException("An EMC entry requires a map, item key and positive long value");
        }
        map.put(key, value);
    }
}
