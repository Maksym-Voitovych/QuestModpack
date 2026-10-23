# Rhino build.85 regression harness

This test runs the actual AIA2 startup bootstrap and all three affected server
modules in the real Rhino engine from **2101.2.7-build.85**. It uses host API
fixtures for FTB Quests, Game Stages, inventory, persistent data and the native
Machine Guard bridge. It does not launch Minecraft or prove mod event wiring.

Run with JDK 21 and Rhino plus its runtime Guava/Gson dependencies:

```sh
export JAVA_HOME=/path/to/jdk-21
export AIA2_RHINO_JAR=/path/to/rhino-2101.2.7-build.85.jar
export AIA2_RHINO_CLASSPATH=/path/to/guava.jar:/path/to/gson.jar
python -m unittest discover -s tests -p 'test_rhino_compat.py' -v
```

On the prepared cloud environment the test finds the source-built core and
cached dependencies in `/workspace/aia2-toolchains` automatically. A missing
external toolchain reports **SKIP**, not successful engine validation.

The harness checks:

- `globalThis` is absent in this exact engine version.
- Startup can populate its writable Java `HashMap`.
- Server scripts cannot assign top-level `global` properties.
- Startup-created nested JavaScript containers can be updated in separate
  server contexts without replacing their identities.
- The actual `00_core.js`, `20_progression.js` and `25_machine_guard.js` load.
- `/aia2 status`, first-key transaction, native stage projection and future
  epoch denial work against the host fixtures.
- Serialized team progress is reloaded into a fresh server context; stale API
  closures are cleared and stage projection is restored.

## Source provenance and scope

The official build.85 workflow is
[run 27170058218](https://github.com/kube-mods/rhino/actions/runs/27170058218),
at source commit
[`2d95ef41d02cbaf82e72f2ee0e21a03f5d34557a`](https://github.com/kube-mods/rhino/commit/2d95ef41d02cbaf82e72f2ee0e21a03f5d34557a).
Its `gradle.properties` declares `2101.2.7`; the build appends the workflow
run number `.85`. Later Rhino revisions implement `globalThis`, so testing the
latest branch would fail to reproduce the user's environment.

Published artifact endpoints returned HTTP 403 in the cloud environment.
Verification therefore compiled **unchanged Java core source** at that exact
commit with `javac --release 21`, including its non-assets resources. This is
a source-built engine, not a byte-identical copy of the installed mod JAR.
Compilation used Guava 32.1.2-jre, Gson 2.10.1, JetBrains annotations 24.1.0
and Nashorn core 15.4 (the latter satisfies an unused import in this source).
The resulting local JAR SHA-256 was
`cab40ada9ea05389837ded0707c8190693967d2f77f12f1d0f8439fa3f2cb321`.

To reproduce that build, check out the pinned commit; compile all Java files
under `src/main/java` with the above dependencies, copy non-assets resources
from `src/main/resources` into the class output, and package that output with
JDK `jar --create`. No Minecraft classes or game launch are required.

`ReadonlyGlobal` models the four rejecting `put/delete` methods of KubeJS
[`NativeJavaReadonlyMap`](https://github.com/KubeJS-Mods/KubeJS/blob/2101/src/main/java/dev/latvian/mods/kubejs/util/NativeJavaReadonlyMap.java)
over the actual Rhino `NativeJavaMap`. The fixture throws a plain Java
exception with the same message; it does not instantiate KubeJS's
`KubeRuntimeException` or source-line integration. KubeJS's builtin plugin
provides a writable startup map and `GlobalUnmodifiableMap` for server scripts.
The remaining mod APIs are explicit JavaScript fixtures in `runtime_stubs.js`.

The runtime JARs, compiled classes and dependency caches are external test
toolchains and are deliberately not committed to the modpack.
