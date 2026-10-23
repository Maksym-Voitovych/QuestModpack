package ua.aia2.guard;

import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.Entity;
import net.neoforged.neoforge.common.util.FakePlayer;

import java.lang.reflect.InvocationTargetException;
import java.lang.reflect.Method;

/**
 * Gives Rhino a single typed entry point instead of FTB's overloaded method.
 * A player's UUID must never be passed to the UUID overload: that overload
 * expects a team UUID, whereas the Entity overload resolves current membership.
 * Reflection uses the public interface, so no FTB compile dependency is needed.
 */
public final class FtbQuestBridge {
    private static volatile Method playerTeamData;

    private FtbQuestBridge() {}

    /** Null means FTB Teams has not made this player's team available yet. */
    public static Object getTeamData(Object questFile, ServerPlayer player) {
        if (questFile == null || player == null || player instanceof FakePlayer) {
            throw new IllegalArgumentException("FTB quest lookup requires a quest file and a real server player");
        }
        try {
            Method selected = playerTeamData;
            if (selected == null) {
                Class<?> api = Class.forName("dev.ftb.mods.ftbquests.api.QuestFile");
                selected = api.getMethod("getOrCreateTeamData", Entity.class);
                playerTeamData = selected;
            }
            if (!selected.getDeclaringClass().isInstance(questFile)) {
                throw new IllegalArgumentException("FTB quest file does not implement its public QuestFile API");
            }
            return selected.invoke(questFile, player);
        } catch (InvocationTargetException failure) {
            throw new IllegalStateException("FTB Quests could not resolve the player's current team data",
                    failure.getCause());
        } catch (ReflectiveOperationException | LinkageError failure) {
            throw new IllegalStateException("FTB Quests public Entity team-data API is unavailable", failure);
        }
    }
}
