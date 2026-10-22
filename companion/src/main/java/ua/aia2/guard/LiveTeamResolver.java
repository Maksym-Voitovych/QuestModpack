package ua.aia2.guard;

import java.lang.reflect.Method;
import java.util.Optional;
import java.util.UUID;

/** Uses only FTB Teams' public API interfaces; caches methods, never memberships. */
public final class LiveTeamResolver {
    private volatile ApiMethods methods;

    public LiveTeamResolver() {
    }

    LiveTeamResolver(ApiMethods methods) {
        this.methods = methods;
    }

    record ApiMethods(Method api, Method isManagerLoaded, Method getManager,
                      Method getTeamForPlayer, Method getTeamId) {
    }

    public void clear() {
        methods = null;
    }

    public String resolve(UUID playerId) {
        if (playerId == null) return null;
        try {
            ApiMethods resolved = methods;
            if (resolved == null) {
                Class<?> entry = Class.forName("dev.ftb.mods.ftbteams.api.FTBTeamsAPI");
                Class<?> api = Class.forName("dev.ftb.mods.ftbteams.api.FTBTeamsAPI$API");
                Class<?> manager = Class.forName("dev.ftb.mods.ftbteams.api.TeamManager");
                Class<?> team = Class.forName("dev.ftb.mods.ftbteams.api.Team");
                resolved = new ApiMethods(entry.getMethod("api"), api.getMethod("isManagerLoaded"),
                        api.getMethod("getManager"), manager.getMethod("getTeamForPlayerID", UUID.class),
                        team.getMethod("getTeamId"));
                methods = resolved;
            }
            Object api = resolved.api().invoke(null);
            if (api == null || !Boolean.TRUE.equals(resolved.isManagerLoaded().invoke(api))) return null;
            Object manager = resolved.getManager().invoke(api);
            if (manager == null) return null;
            Object result = resolved.getTeamForPlayer().invoke(manager, playerId);
            if (!(result instanceof Optional<?> team) || team.isEmpty()) return null;
            Object id = resolved.getTeamId().invoke(team.get());
            return id instanceof UUID uuid ? uuid.toString() : null;
        } catch (ReflectiveOperationException | RuntimeException | LinkageError unavailable) {
            // Never fall back to an old team's privileges after an API failure.
            return null;
        }
    }
}
