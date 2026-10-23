import dev.ftb.mods.ftbquests.api.QuestFile;
import dev.ftb.mods.ftbquests.quest.Chapter;
import dev.ftb.mods.ftbquests.quest.Quest;
import dev.ftb.mods.ftbquests.quest.QuestLink;
import dev.ftb.mods.ftbquests.quest.TeamData;
import dev.ftb.mods.ftbteams.api.Team;
import dev.latvian.mods.kubejs.plugin.builtin.wrapper.UUIDWrapper;
import dev.latvian.mods.rhino.Context;
import dev.latvian.mods.rhino.ContextFactory;
import dev.latvian.mods.rhino.NativeJavaClass;
import dev.latvian.mods.rhino.ScriptableObject;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.player.Player;
import net.neoforged.neoforge.common.util.FakePlayer;
import ua.aia2.guard.FtbQuestBridge;

import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Collection;
import java.util.HashMap;
import java.util.Map;
import java.util.Optional;
import java.util.UUID;
import java.util.function.Consumer;

/** Real Rhino85, exact FTB public interface, actual KubeJS UUID converter and production helper.
 * Minecraft entities and FTB data storage are explicit small fixtures, not a game launch. */
public final class FtbQuestInteropHarness {
    static final UUID PLAYER = UUID.fromString("00000000-0000-4000-8000-000000000001");
    static final UUID ALPHA = UUID.fromString("00000000-0000-4000-8000-000000000011");
    static final UUID BETA = UUID.fromString("00000000-0000-4000-8000-000000000012");
    static int assertions;
    public static final class QuestFileFixture implements QuestFile {
        public static final QuestFileFixture INSTANCE = new QuestFileFixture();
        final Map<UUID,TeamData> progress = new HashMap<>();
        final Map<UUID,UUID> membership = new HashMap<>();
        int uuidCalls;
        int entityCalls;
        boolean unavailable;
        boolean failed;
        @Override public TeamData getOrCreateTeamData(UUID id) {
            uuidCalls++;
            return progress.computeIfAbsent(id, TeamData::new);
        }
        @Override public TeamData getOrCreateTeamData(Team team) { return getOrCreateTeamData(team.getId()); }
        @Override public TeamData getOrCreateTeamData(Entity player) {
            entityCalls++;
            if (failed) throw new IllegalStateException("fixture FTB manager unavailable");
            if (unavailable) return null;
            UUID team = membership.get(player.getUUID());
            return team == null ? null : getOrCreateTeamData(team);
        }
        @Override public boolean isServerSide() { return true; }
        @Override public boolean canEdit() { return false; }
        @Override public TeamData getNullableTeamData(UUID id) { return progress.get(id); }
        @Override public Optional<TeamData> getTeamData(Player player) { return Optional.ofNullable(getOrCreateTeamData((Entity) player)); }
        @Override public Collection<TeamData> getAllTeamData() { return progress.values(); }
        @Override public void forAllChapters(Consumer<Chapter> consumer) {}
        @Override public void forAllQuests(Consumer<Quest> consumer) {}
        @Override public void forAllQuestLinks(Consumer<QuestLink> consumer) {}
    }
    static void check(boolean value, String message) {
        assertions++;
        if (!value) throw new AssertionError(message);
    }
    static Object eval(Context cx, ScriptableObject scope, String source) {
        return cx.evaluateString(scope, source, "ftb-team-interop", 1, null);
    }
    static void bind(Context cx, ScriptableObject scope, String name, Class<?> type) {
        cx.addToScope(scope, name, new NativeJavaClass(cx, scope, type));
    }
    public static void main(String[] args) throws Exception {
        var file = QuestFileFixture.INSTANCE;
        var player = new ServerPlayer(PLAYER);
        var oldTeam = new TeamData(ALPHA);
        oldTeam.completed = 13;
        file.progress.put(ALPHA, oldTeam);
        file.membership.put(PLAYER, ALPHA);
        var factory = new ContextFactory();
        // BuiltinKubeJSPlugin registers UUIDWrapper::fromString with an ALWAYS_VALID validator.
        // Omitting this KubeJS-specific registration would hide the real overload failure.
        factory.getTypeWrappers().register(UUID.class, (cx, value, target) -> UUIDWrapper.fromString(cx, value));
        var cx = factory.enter();
        var scope = cx.initStandardObjects();
        cx.addToScope(scope, "__file", file);
        cx.addToScope(scope, "__player", player);
        cx.addToScope(scope, "__fake", new FakePlayer(PLAYER));
        bind(cx, scope, "__Bridge", FtbQuestBridge.class);
        bind(cx, scope, "__FileClass", QuestFileFixture.class);
        check(Boolean.TRUE.equals(eval(cx, scope,
            "var ambiguous=false;try{__file.getOrCreateTeamData(__player);}catch(e){var m=String(e);ambiguous=m.indexOf('ambiguous')>=0&&m.indexOf('java.util.UUID')>=0&&m.indexOf('Entity')>=0;}ambiguous;")),
            "actual KubeJS UUID converter reproduces Entity/UUID ambiguity");
        check(file.entityCalls == 0 && file.uuidCalls == 0, "ambiguous resolution never executes an overload");
        check(Boolean.TRUE.equals(eval(cx, scope,
            "var wrong=__file.getOrCreateTeamData(__player.uuid);String(wrong.getTeamId())===String(__player.uuid)&&wrong.completed===0;")),
            "passing player UUID selects a different namespace and loses team progress");
        var resolved = FtbQuestBridge.getTeamData(file, player);
        check(resolved == oldTeam && ((TeamData) resolved).completed == 13, "typed production helper reuses existing real team progress");
        check(Boolean.TRUE.equals(eval(cx, scope,
            "String(__Bridge.getTeamData(__file,__player).getTeamId())==='" + ALPHA + "';")),
            "unique typed helper remains callable under broad UUID converter");
        check(file.entityCalls == 2, "helper explicitly invokes public Entity overload");
        file.membership.put(PLAYER, BETA);
        var changed = FtbQuestBridge.getTeamData(file, player);
        check(changed instanceof TeamData data && BETA.equals(data.getTeamId()) && data.completed == 0,
            "membership change does not inherit previous team's completion");
        check(oldTeam.completed == 13, "old team completion remains intact");
        file.membership.put(PLAYER, ALPHA);
        check(FtbQuestBridge.getTeamData(file, player) == oldTeam, "rejoining original team restores same data");
        check(Boolean.TRUE.equals(eval(cx, scope,
            "var denied=false;try{__Bridge.getTeamData(__file,__fake);}catch(e){denied=true;}denied;")), "fake player denied");
        check(Boolean.TRUE.equals(eval(cx, scope,
            "var denied=false;try{__Bridge.getTeamData({},__player);}catch(e){denied=true;}denied;")), "wrong API object denied without UUID fallback");
        file.unavailable = true;
        check(FtbQuestBridge.getTeamData(file, player) == null, "first-join not-ready returns no data instead of empty replacement");
        file.unavailable = false;
        file.failed = true;
        check(Boolean.TRUE.equals(eval(cx, scope,
            "var denied=false;try{__Bridge.getTeamData(__file,__player);}catch(e){denied=String(e).indexOf('current team data')>=0;}denied;")), "API invocation failure stays visible and closed");
        file.failed = false;
        // Execute the real script20 rather than testing only a newly invented helper call.
        eval(cx, scope,
            "var global={AIA2Core:{validateState:function(s){return s;},mayAccess:function(e,n){return e<=n+1;}},AIA2:{},AIA2Machines:{isReady:function(){return false;}}};"+
            "var JsonIO={readString:function(){return JSON.stringify({epochs:[],machineGuard:{mode:'required'}});}};"+
            "var Java={loadClass:function(n){if(n==='dev.ftb.mods.ftbquests.quest.ServerQuestFile')return __FileClass;if(n==='ua.aia2.guard.FtbQuestBridge')return __Bridge;return {};}};"+
            "var ServerEvents={commandRegistry:function(cb){}};var PlayerEvents={loggedIn:function(cb){},tick:function(cb){}};"+
            "var console={error:function(s){}};");
        cx.evaluateString(scope, Files.readString(Path.of(args[0]).resolve("kubejs/server_scripts/aia2/20_progression.js")), "20_progression.js", 1, null);
        check(Boolean.TRUE.equals(eval(cx, scope, "String(aia2Team(__player).getTeamId())==='" + ALPHA + "'")), "real progression script uses production helper");
        file.failed = true;
        check(Boolean.TRUE.equals(eval(cx, scope, "global.AIA2.canAccess(__player,1)===false")), "real access path denies failed FTB lookup");
        file.failed = false;
        check(oldTeam.completed == 13, "errors never reset existing FTB data");
        System.out.println("FtbQuestInteropHarness: " + assertions + " actual Rhino85/UUID-wrapper/production-helper assertions passed");
        System.out.println("Scope: unmodified FTB QuestFile interface and KubeJS UUIDWrapper; modeled Minecraft entities, FTB storage and script event host; no full Minecraft/FTB mod launch");
    }
}
