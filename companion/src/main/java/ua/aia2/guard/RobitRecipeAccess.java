package ua.aia2.guard;

import java.lang.reflect.InvocationTargetException;
import java.lang.reflect.Method;
import java.util.UUID;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.item.crafting.Recipe;

/** Mekanism 10.7.19.85 Robit smelting is entity-ticked, not a BlockEntityTicker. */
public final class RobitRecipeAccess {
    private record Owner(ServerLevel level, String team) {}
    private static final ScopedRecipeOwner<Owner> OWNER = new ScopedRecipeOwner<>();
    private static final ClassValue<Method> OWNER_METHOD = new ClassValue<>() {
        @Override protected Method computeValue(Class<?> type) {
            try { return type.getMethod("getOwnerUUID"); }
            catch (NoSuchMethodException error) { throw new IllegalStateException("Unsupported Mekanism Robit owner API", error); }
        }
    };
    private static final ClassValue<Method> MONITOR_METHOD = new ClassValue<>() {
        @Override protected Method computeValue(Class<?> type) {
            try { return type.getMethod("updateAndProcess"); }
            catch (NoSuchMethodException error) { throw new IllegalStateException("Unsupported Mekanism recipe monitor API", error); }
        }
    };

    private RobitRecipeAccess() {}

    /** Called only at the exact Robit monitor invocation, before recipe energy/input use. */
    public static boolean updateAndProcess(Object robitObject, Object monitor) {
        if (!(robitObject instanceof Entity robit) || !(robit.level() instanceof ServerLevel level)) return false;
        final Owner owner;
        final Method operation;
        try {
            Object id = OWNER_METHOD.get(robit.getClass()).invoke(robit);
            if (!(id instanceof UUID ownerId)) return false;
            String team = Aia2MachineGuard.resolveCurrentTeam(ownerId);
            if (team == null || !Aia2MachineGuard.mayUseItemByTeam("mekanism:robit", team)) return false;
            owner = new Owner(level, team);
            operation = MONITOR_METHOD.get(monitor.getClass());
        } catch (ReflectiveOperationException | RuntimeException unavailable) {
            return false;
        }
        // Fail closed for unsupported bindings, but preserve native exceptions and
        // restore ownership when the original Mekanism operation itself fails.
        return OWNER.call(owner, () -> invokeMonitor(operation, monitor));
    }

    private static boolean invokeMonitor(Method operation, Object monitor) {
        try { return Boolean.TRUE.equals(operation.invoke(monitor)); }
        catch (InvocationTargetException nativeFailure) {
            Throwable cause = nativeFailure.getCause();
            if (cause instanceof Error error) throw error;
            if (cause instanceof RuntimeException error) throw error;
            throw new IllegalStateException("Mekanism native recipe monitor failed", cause);
        } catch (ReflectiveOperationException unavailable) {
            return false;
        }
    }

    public static boolean hasContext() { return OWNER.current() != null; }

    public static boolean mayProcess(Recipe<?> recipe) {
        Owner owner = OWNER.current();
        return owner != null && Aia2MachineGuard.mayProcessOwnedRecipe(owner.level(), owner.team(), recipe);
    }

    public static void clear() { OWNER.clear(); }
}
