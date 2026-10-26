import dev.latvian.mods.rhino.Context;
import dev.latvian.mods.rhino.ContextFactory;
import dev.latvian.mods.rhino.NativeJavaClass;
import dev.latvian.mods.rhino.ScriptableObject;
import dev.latvian.mods.rhino.util.RemapForJS;
import it.unimi.dsi.fastutil.objects.Object2LongMap;
import it.unimi.dsi.fastutil.objects.Object2LongOpenHashMap;
import ua.aia2.guard.RhinoLongMapBridge;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.UUID;
import java.util.List;

/** Real Rhino85 + fastutil + production bridge/scripts; Minecraft/FTB/ProjectE APIs modeled. */
public final class GuardInteropHarness {
    static final UUID ID = UUID.fromString("00000000-0000-4000-8000-000000000001");
    public static final class PlayerFixture {
        @RemapForJS("getUuid") public UUID getUUID() { return ID; }
        public boolean isServerPlayer() { return true; }
        public boolean isFake() { return false; }
    }
    public static final class QuestFileFixture {
        public static final QuestFileFixture INSTANCE = new QuestFileFixture();
        public static boolean loaded = true;
        public Object getQuest(long id) { return loaded ? Long.valueOf(id) : null; }
    }
    public static final class GuardFixture {
        static boolean ready;
        static UUID synced;
        static int clears;
        public static int apiVersion() { return 4; }
        public static void clearRuntime() { ready = false; clears++; }
        public static void setRulesJson(String json) {}
        public static void setItemRulesJson(String json) {}
        public static void setRecipeRulesJson(String json) {}
        public static void configureKeyRulesJson(String json) {}
        public static void setTeamProgress(String id, int n) {}
        public static void syncPlayer(PlayerFixture player, String team, int n) { synced = player.getUUID(); }
        public static void setReady() { ready = true; }
        public static boolean isReady() { return ready; }
    }
    public record ItemKey(String id) {}
    public static final class StackFixture {
        final String id;
        StackFixture(String id) { this.id = id; }
        public String getId() { return id; }
        public boolean isEmpty() { return false; }
    }
    public static final class ItemFactory {
        public static StackFixture of(String id) { return new StackFixture(id); }
    }
    public static final class ItemInfoFixture {
        public static ItemKey fromStack(StackFixture stack) { return new ItemKey(stack.id); }
    }
    public static final class EMCFixture {
        static Object2LongMap<Object> last;
        public static int updateEmcValues(Object2LongMap<Object> map) { last = map; return map.size(); }
    }
    public static final class AccessFixture {
        static boolean ready;
        public static void pause() { ready = false; }
        public static void configureWhitelistJson(String json) {
            check(com.google.gson.JsonParser.parseString(json).getAsJsonObject().size() == 14, "complete native output whitelist supplied");
            check(FuelFixture.size == 2, "fuel cache refresh precedes Java output readiness");
            ready = true;
        }
    }
    public static final class HolderSetFixture {
        public static List<Object> empty() { return List.of(); }
    }
    public static final class FuelFixture {
        static int size;
        static boolean fail;
        public static void loadMap() {
            if (fail) throw new IllegalStateException("synthetic fuel refresh failure");
            check(EMCFixture.last != null && EMCFixture.last.size() == 14, "final EMC map precedes fuel rebuild");
            size = (EMCFixture.last.containsKey(new ItemKey("minecraft:coal")) ? 1 : 0)
                    + (EMCFixture.last.containsKey(new ItemKey("minecraft:charcoal")) ? 1 : 0);
        }
        public static void setFuelMap(List<Object> empty) {
            check(empty.isEmpty(), "failed remap uses an empty fuel map"); size = 0;
        }
    }
    static Object eval(Context cx, ScriptableObject scope, String source) {
        return cx.evaluateString(scope, source, "guard-interop", 1, null);
    }
    static void check(boolean value, String message) { if (!value) throw new AssertionError(message); }
    static void load(Context cx, ScriptableObject scope, Path file) throws Exception {
        cx.evaluateString(scope, Files.readString(file), file.toString(), 1, null);
    }
    static void bindClass(Context cx, ScriptableObject scope, String name, Class<?> type) {
        cx.addToScope(scope, name, new NativeJavaClass(cx, scope, type));
    }
    public static void main(String[] args) throws Exception {
        Path root = Path.of(args[0]);
        Context cx = new ContextFactory().enter();
        ScriptableObject scope = cx.initStandardObjects();
        bindClass(cx, scope, "__Guard", GuardFixture.class);
        bindClass(cx, scope, "__Quest", QuestFileFixture.class);
        bindClass(cx, scope, "__Map", Object2LongOpenHashMap.class);
        bindClass(cx, scope, "__Long", Long.class);
        bindClass(cx, scope, "__LongBridge", RhinoLongMapBridge.class);
        bindClass(cx, scope, "__ItemInfo", ItemInfoFixture.class);
        bindClass(cx, scope, "__EMC", EMCFixture.class);
        bindClass(cx, scope, "__Access", AccessFixture.class);
        bindClass(cx, scope, "__Fuel", FuelFixture.class);
        bindClass(cx, scope, "__HolderSet", HolderSetFixture.class);
        bindClass(cx, scope, "__ItemFactory", ItemFactory.class);
        cx.addToScope(scope, "__player", new PlayerFixture());
        cx.addToScope(scope, "__rulesJSON", Files.readString(root.resolve("kubejs/config/aia2_runtime.json")));
        cx.addToScope(scope, "__emcJSON", Files.readString(root.resolve("kubejs/config/aia2_emc_whitelist.json")));
        eval(cx, scope, "function check(v,m){if(!v)throw new Error(m);}" +
            "var events={},nativeEvents={};var logs=[];var corrupt=false;" +
            "var __rules=JSON.parse(__rulesJSON);" +
            "if(!__rules.dualKeys){__rules.dualKeys=[];for(var i=0;i<96;i++)__rules.dualKeys.push({});}" +
            "var global={AIA2:{rules:__rules,ledger:function(){if(corrupt)throw new Error('damaged ledger');return {schema:1,teams:{fixture:{completed:7}}};}," +
            "teamId:function(){return 'fixture';},completed:function(){return 7;},canAccess:function(){return true;}},AIA2Machines:{}};" +
            "var server={getPlayerList:function(){return {getPlayers:function(){return [__player];}};}};" +
            "var Platform={isLoaded:function(){return true;}};" +
            "var Java={loadClass:function(n){if(n==='ua.aia2.guard.Aia2MachineGuard')return __Guard;" +
            "if(n==='dev.ftb.mods.ftbquests.quest.ServerQuestFile')return __Quest;" +
            "if(n==='it.unimi.dsi.fastutil.objects.Object2LongOpenHashMap')return __Map;" +
            "if(n==='ua.aia2.guard.RhinoLongMapBridge')return __LongBridge;" +
            "if(n==='ua.aia2.guard.ProjectEAccess')return __Access;" +
            "if(n==='moze_intel.projecte.emc.FuelMapper')return __Fuel;" +
            "if(n==='net.minecraft.core.HolderSet')return __HolderSet;" +
            "if(n==='moze_intel.projecte.api.ItemInfo')return __ItemInfo;" +
            "if(n==='moze_intel.projecte.emc.EMCMappingHandler')return __EMC;return n;}};" +
            "var ServerEvents={loaded:function(cb){events.loaded=cb;},tick:function(cb){events.tick=cb;},unloaded:function(cb){events.unloaded=cb;}};" +
            "var NativeEvents={onEvent:function(type,cb){nativeEvents[type]=cb;}};" +
            "var Item={of:function(id){return __ItemFactory.of(id);}};" +
            "var JsonIO={readString:function(path){return __emcJSON;}};" +
            "var console={error:function(s){logs.push(String(s));},warn:function(s){logs.push(String(s));},info:function(s){logs.push(String(s));}};");
        check(Boolean.TRUE.equals(eval(cx, scope, "var bad=false;try{__player.getUUID();}catch(e){bad=true;}bad;")), "Mojang getUUID is unavailable in JS");
        check(Boolean.TRUE.equals(eval(cx, scope, "String(__player.uuid)==='" + ID + "'")), "uuid is an object bean property");
        check(Boolean.TRUE.equals(eval(cx, scope, "var bad=false;try{__player.uuid();}catch(e){bad=true;}bad;")), "calling uuid reproduces user's error");
        load(cx, scope, root.resolve("kubejs/server_scripts/aia2/25_machine_guard.js"));
        eval(cx, scope, "events.loaded({server:server});check(!global.AIA2Machines.isReady(),'must defer ServerStarting');events.tick({server:server});check(global.AIA2Machines.isReady(),'typed native bridge initializes');");
        check(ID.equals(GuardFixture.synced), "actual Java helper receives real remapped Java player and UUID");
        GuardFixture.clearRuntime();
        eval(cx, scope, "events.tick({server:server});check(global.AIA2Machines.isReady(),'native reset recovered');");
        eval(cx, scope, "corrupt=true;"); GuardFixture.clearRuntime();
        eval(cx, scope, "events.tick({server:server});check(!global.AIA2Machines.isReady(),'damaged ledger closes guard');");
        int clears = GuardFixture.clears;
        eval(cx, scope, "for(var i=0;i<1000;i++)events.tick({server:server});");
        check(clears == GuardFixture.clears, "fatal error does not retry forever");
        check(Boolean.TRUE.equals(eval(cx, scope, "var bad=false;try{new __Map().put('ordinary',128);}catch(e){bad=String(e).indexOf('ambiguous')>=0;}bad;")), "unboxed fastutil call reproduces ambiguity");
        check(Boolean.TRUE.equals(eval(cx, scope, "var bad=false;try{new __Map().put('ordinary',__Long.valueOf('128'));}catch(e){bad=String(e).indexOf('ambiguous')>=0;}bad;")), "boxing does not solve overloaded fastutil call");
        load(cx, scope, root.resolve("kubejs/server_scripts/aia2/35_projecte.js"));
        eval(cx, scope, "nativeEvents['moze_intel.projecte.api.event.EMCRemapEvent']();");
        check(EMCFixture.last != null && EMCFixture.last.size() == 14, "all ordinary EMC whitelist entries installed");
        check(EMCFixture.last.getLong(new ItemKey("minecraft:gold_ingot")) == 2048, "primitive long value survives real Rhino bridge");
        check(AccessFixture.ready && FuelFixture.size == 2, "actual Rhino invokes unique native lifecycle methods without overload ambiguity");
        eval(cx, scope, "AIA2EMCAllowed['minecraft:gold_ingot']=0;var failed=false;try{nativeEvents['moze_intel.projecte.api.event.EMCRemapEvent']();}catch(e){failed=true;}check(failed,'invalid whitelist remains visible error');");
        check(EMCFixture.last.isEmpty(), "bad whitelist clears inherited EMC instead of leaving a bypass");
        check(!AccessFixture.ready && FuelFixture.size == 0, "bad whitelist closes extraction and clears fuel cache");
        FuelFixture.fail = true;
        eval(cx, scope, "AIA2EMCAllowed['minecraft:gold_ingot']=2048;var failed=false;try{nativeEvents['moze_intel.projecte.api.event.EMCRemapEvent']();}catch(e){failed=true;}check(failed,'fuel refresh failure remains visible');");
        check(EMCFixture.last.isEmpty() && !AccessFixture.ready && FuelFixture.size == 0, "failed rebuild cannot retain inherited values or stale fuels");
        System.out.println("GuardInteropHarness: actual Rhino85 remapping, typed UUID sync, deferred initialization, native reset, fatal ledger and real fastutil primitive bridge passed");
        System.out.println("Scope: real scripts/engine/fastutil/production RhinoLongMapBridge; Minecraft/FTB/ProjectE API fixtures only");
    }
}
