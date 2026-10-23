// priority: 10000
// The writable bootstrap lives in startup_scripts/aia2/00_shared_state.js.
// KubeJS 2101 exposes a read-only global Map in server scripts. Its existing
// plain JavaScript values remain mutable, so their members can be refreshed.
if (!global.AIA2Core || typeof global.AIA2Core.prepareKey !== 'function' ||
    !global.AIA2 || !global.AIA2Machines) {
  throw new Error('[AIA2] Не завантажено startup bootstrap. Встановіть 00_shared_state.js і повністю перезапустіть гру; /reload недостатньо.');
}
// Clear old closures on /reload or another world in the same JVM. Persistent
// team progress remains in server.persistentData and is never reset here.
[global.AIA2, global.AIA2Machines].forEach(function (container) {
  Object.keys(container).forEach(function (key) { delete container[key]; });
});
