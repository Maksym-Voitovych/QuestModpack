package ua.aia2.guard;

import java.util.Optional;
import java.util.UUID;

/** Reflection contract checks with public synthetic interfaces, not a live FTB server. */
public final class LiveTeamResolverTest {
    public interface PublicApi {
        boolean isManagerLoaded();
        PublicManager getManager();
    }
    public interface PublicManager {
        Optional<PublicTeam> getTeamForPlayerID(UUID player);
    }
    public interface PublicTeam {
        UUID getTeamId();
    }
    public static final class Entry {
        static PublicApi current;
        public static PublicApi api() { return current; }
    }
    private static boolean loaded;
    private static UUID team;
    private static boolean throwError;
    private static int assertions;

    private static void expect(boolean condition, String message) {
        assertions++;
        if (!condition) throw new AssertionError(message);
    }

    public static void main(String[] arguments) throws Exception {
        var resolver = new LiveTeamResolver(new LiveTeamResolver.ApiMethods(Entry.class.getMethod("api"),
                PublicApi.class.getMethod("isManagerLoaded"), PublicApi.class.getMethod("getManager"),
                PublicManager.class.getMethod("getTeamForPlayerID", UUID.class), PublicTeam.class.getMethod("getTeamId")));
        UUID player = UUID.randomUUID();
        expect(resolver.resolve(player) == null, "Absent API instance denies");
        Entry.current = new PublicApi() {
            public boolean isManagerLoaded() { return loaded; }
            public PublicManager getManager() {
                return id -> {
                    if (throwError) throw new IllegalStateException("Simulated manager failure");
                    return team == null ? Optional.empty() : Optional.of(() -> team);
                };
            }
        };
        expect(resolver.resolve(player) == null, "Unloaded manager denies");
        loaded = true;
        expect(resolver.resolve(player) == null, "Absent player team denies");
        team = UUID.randomUUID();
        String original = team.toString();
        expect(original.equals(resolver.resolve(player)), "Public interface methods work on nonpublic implementation");
        team = UUID.randomUUID();
        expect(team.toString().equals(resolver.resolve(player)), "Membership change is visible immediately");
        expect(!original.equals(resolver.resolve(player)), "Previous membership is never cached");
        throwError = true;
        expect(resolver.resolve(player) == null, "Manager errors deny without stale fallback");
        throwError = false;
        expect(team.toString().equals(resolver.resolve(player)), "Manager recovery reads current membership");
        expect(resolver.resolve(null) == null, "Absent player denies");
        System.out.println("LiveTeamResolverTest: " + assertions + " assertions passed (synthetic public API; FTB runtime not launched)");
    }
}
