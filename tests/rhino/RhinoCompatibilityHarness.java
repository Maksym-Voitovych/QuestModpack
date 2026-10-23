import dev.latvian.mods.rhino.Context;
import dev.latvian.mods.rhino.ContextFactory;
import dev.latvian.mods.rhino.NativeJavaMap;
import dev.latvian.mods.rhino.Scriptable;
import dev.latvian.mods.rhino.ScriptableObject;
import dev.latvian.mods.rhino.type.TypeInfo;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.HashMap;
import java.util.Map;

/** Actual Rhino engine, modeled KubeJS map wrapper and host APIs. No Minecraft claims. */
public final class RhinoCompatibilityHarness {
  static final String MESSAGE = "'global' cannot be assigned to in client or server scripts";
  static final String PIN = "2d95ef41d02cbaf82e72f2ee0e21a03f5d34557a";
  static final class ReadonlyGlobal extends NativeJavaMap {
    ReadonlyGlobal(Context cx, Scriptable scope, Map<String, Object> map) {
      super(cx, scope, map, map, TypeInfo.RAW_MAP);
    }
    @Override public void put(Context cx, String key, Scriptable start, Object value) { throw new IllegalStateException(MESSAGE); }
    @Override public void put(Context cx, int key, Scriptable start, Object value) { throw new IllegalStateException(MESSAGE); }
    @Override public void delete(Context cx, String key) { throw new IllegalStateException(MESSAGE); }
    @Override public void delete(Context cx, int key) { throw new IllegalStateException(MESSAGE); }
  }
  static Object eval(Context cx, Scriptable scope, String source) {
    return cx.evaluateString(scope, source, "harness", 1, null);
  }
  static void load(Context cx, Scriptable scope, Path path) throws Exception {
    cx.evaluateString(scope, Files.readString(path), path.toString(), 1, null);
  }
  static void check(boolean condition, String message) {
    if (!condition) throw new AssertionError(message);
  }
  static ScriptableObject server(Context cx, Map<String, Object> global, Path root, String saved) throws Exception {
    ScriptableObject scope = cx.initStandardObjects();
    cx.addToScope(scope, "global", new ReadonlyGlobal(cx, scope, global));
    cx.addToScope(scope, "__savedLedgerJSON", saved);
    cx.addToScope(scope, "__rulesJSON", Files.readString(root.resolve("kubejs/config/aia2_runtime.json")));
    check(Boolean.TRUE.equals(eval(cx, scope, "typeof globalThis === 'undefined'")), "build.85 has no globalThis");
    try { eval(cx, scope, "global.AIA2 = {}; "); throw new AssertionError("global must be read-only"); }
    catch (RuntimeException expected) { check(expected.toString().contains(MESSAGE), "expected map rejection"); }
    load(cx, scope, root.resolve("tests/rhino/runtime_stubs.js"));
    for (String name : new String[]{"00_core.js", "20_progression.js", "25_machine_guard.js"})
      load(cx, scope, root.resolve("kubejs/server_scripts/aia2/" + name));
    eval(cx, scope, "fixtureActivate();");
    return scope;
  }
  public static void main(String[] args) throws Exception {
    Path root = Path.of(args[0]);
    Map<String, Object> global = new HashMap<>();
    Context startupCx = new ContextFactory().enter();
    ScriptableObject startup = startupCx.initStandardObjects();
    cxAddWritable(startupCx, startup, global);
    load(startupCx, startup, root.resolve("kubejs/startup_scripts/aia2/00_shared_state.js"));
    Object core = global.get("AIA2Core"), api = global.get("AIA2"), machines = global.get("AIA2Machines");
    check(core != null && api != null && machines != null, "startup containers created");
    Context serverCx = new ContextFactory().enter();
    ScriptableObject first = server(serverCx, global, root, "");
    eval(serverCx, first, "fixtureForgeFirst(); global.AIA2.obsolete = true;");
    String saved = serverCx.toString(eval(serverCx, first, "__fixture.ledger"));
    check(saved.contains("\"completed\":1"), "serialized persistent team progress");
    Context reloadedCx = new ContextFactory().enter();
    ScriptableObject second = server(reloadedCx, global, root, saved);
    eval(reloadedCx, second, "fixtureAssert(global.AIA2.completed(__player) === 1, 'saved ledger rehydrated');" +
      "fixtureAssert(global.AIA2.obsolete === undefined, 'old closures cleared');" +
      "fixtureAssert(__fixture.stages.aia2_epoch_02, 'saved progress restores native stage mirror');");
    check(global.get("AIA2Core") == core && global.get("AIA2") == api && global.get("AIA2Machines") == machines,
      "startup aliases survive distinct server contexts");
    System.out.println("RhinoCompatibilityHarness: startup, readonly global, actual three modules, status, key transaction, stage mirror and reload assertions passed");
    System.out.println("Rhino source pin: " + PIN + " (2101.2.7-build.85)");
  }
  static void cxAddWritable(Context cx, Scriptable scope, Map<String, Object> global) {
    cx.addToScope(scope, "global", new NativeJavaMap(cx, scope, global, global, TypeInfo.RAW_MAP));
  }
}
