package ua.aia2.guard;

import java.lang.reflect.Modifier;
import java.util.HashSet;
import java.util.Set;
import java.util.UUID;
import net.minecraft.core.RegistryAccess;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.level.ChunkPos;

/** Read-only, bounded observation of the native per-player station registry. */
public final class StationRegistrationWitness {
    private static final String HANDLER = "earth.terrarium.adastra.common.handlers.SpaceStationHandler";
    private static final String STATION = "earth.terrarium.adastra.common.handlers.base.SpaceStation";
    private static final int LIMIT = 4096;
    private static final int NAME_LIMIT = 16384;
    private static final int TOTAL_NAME_LIMIT = 1048576;

    private record Entry(ChunkPos position, String name) {}

    /** No native collection or mutable Component is retained. */
    public static final class Snapshot {
        private final ServerLevel level;
        private final UUID owner;
        private final Set<Entry> entries;
        private Snapshot(ServerLevel level, UUID owner, Set<Entry> entries) {
            this.level = level; this.owner = owner; this.entries = Set.copyOf(entries);
        }
        public boolean hasStation(ChunkPos position, Component name) {
            try {
                Entry expected = entry(position, name);
                return expected != null && entries.contains(expected);
            } catch (RuntimeException unsupported) { return false; }
        }
    }

    private StationRegistrationWitness() {}

    private static Entry entry(ChunkPos position, Component name) {
        if (position == null || name == null) return null;
        // Component.copy() alone shares nested components. Freeze the exact JSON
        // representation used by SpaceStationHandler's own persistence instead.
        String frozen = Component.Serializer.toJson(name.copy(), RegistryAccess.EMPTY);
        if (frozen == null || frozen.length() > NAME_LIMIT) return null;
        return new Entry(new ChunkPos(position.x, position.z), frozen);
    }

    /** Exact typed reflection deliberately avoids the handler's UUID overload. */
    public static Snapshot read(ServerPlayer player, ServerLevel level) {
        if (player == null || level == null || !level.getServer().isSameThread()) return null;
        try {
            Class<?> handler = Class.forName(HANDLER);
            var method = handler.getMethod("getOwnedSpaceStations", ServerPlayer.class, ServerLevel.class);
            if (method.getReturnType() != Set.class || !Modifier.isStatic(method.getModifiers())) return null;
            Object value = method.invoke(null, player, level);
            if (!(value instanceof Set<?> stations) || stations.size() > LIMIT) return null;
            Class<?> stationType = Class.forName(STATION);
            if (!stationType.isRecord()) return null;
            var position = stationType.getMethod("position");
            var name = stationType.getMethod("name");
            if (position.getReturnType() != ChunkPos.class || name.getReturnType() != Component.class) return null;
            var frozen = new HashSet<Entry>();
            int count = 0, nameUnits = 0;
            for (Object station : stations) {
                if (++count > LIMIT || station == null || station.getClass() != stationType) return null;
                Entry entry = entry((ChunkPos)position.invoke(station), (Component)name.invoke(station));
                if (entry == null || (nameUnits += entry.name().length()) > TOTAL_NAME_LIMIT || !frozen.add(entry)) return null;
            }
            return new Snapshot(level, player.getUUID(), frozen);
        } catch (ReflectiveOperationException | RuntimeException | LinkageError unsupported) {
            return null;
        }
    }

    /** A no-op native Set.add, removal, replacement or other owner/world cannot be adopted. */
    public static boolean added(Snapshot before, Snapshot after, ChunkPos position, Component name) {
        if (before == null || after == null || before.level != after.level || !before.owner.equals(after.owner)) return false;
        Entry expected;
        try { expected = entry(position, name); }
        catch (RuntimeException unsupported) { return false; }
        return expected != null && !before.entries.contains(expected)
                && after.entries.size() == before.entries.size() + 1
                && after.entries.contains(expected) && after.entries.containsAll(before.entries);
    }
}
