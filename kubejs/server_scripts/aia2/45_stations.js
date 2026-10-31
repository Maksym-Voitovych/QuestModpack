// Paid station construction proofs. No discovery of old native station entries.
var aia2StationBridge = Java.loadClass('ua.aia2.guard.StationProductionBridge');
var aia2StationConfig = JSON.parse(JsonIO.readString('kubejs/config/aia2_stations.json'));
var aia2StationConfigured = false;
var aia2StationFailure = '';
var aia2StationProjection = {};
var aia2StationTick = 0;

function aia2InitStations() {
  if (!global.AIA2Machines.isReady()) return false;
  try {
    if (aia2StationConfigured && aia2StationBridge.isConfigured()) return true;
    if (aia2StationConfig.schema !== 1 || !aia2StationConfig.rules || aia2StationConfig.rules.length !== 6) {
      throw new Error('Потрібні шість перевірених правил будівництва станцій.');
    }
    aia2StationBridge.configureJson(JSON.stringify(aia2StationConfig.rules));
    aia2StationConfigured = aia2StationBridge.isConfigured();
    aia2StationFailure = '';
    aia2StationProjection = {};
    return aia2StationConfigured;
  } catch (error) {
    aia2StationConfigured = false;
    // A rejected configuration cannot leave an older rule map collecting new
    // receipts. Durable SavedData is intentionally unaffected by clearRuntime.
    try { aia2StationBridge.clearRuntime(); }
    catch (clearError) { console.error('[AIA2] Не вдалося закрити докази станцій: ' + String(clearError)); }
    var message = String(error.message || error);
    if (message !== aia2StationFailure) console.error('[AIA2] Докази станцій закрито: ' + message);
    aia2StationFailure = message;
    return false;
  }
}

function aia2SyncStations(player) {
  if (!player || !player.isServerPlayer() || player.isFake()) return;
  var name = String(player.username);
  if (!/^[A-Za-z0-9_]{1,16}$/.test(name)) throw new Error('[AIA2] Некоректне ім’я гравця для доказу станції.');
  var ready = aia2InitStations();
  var team = '';
  var completed = -1;
  var lookupFailure = null;
  var proofs = {};
  if (ready) {
    try {
      team = global.AIA2.teamId(player);
      completed = global.AIA2.completed(player);
      // Validate every receipt before projecting any. A corrupt/unavailable
      // receipt store must revoke all old-team projections, even if a later
      // native lookup fails after earlier rules succeeded.
      aia2StationConfig.rules.forEach(function (rule) {
        proofs[rule.id] = rule.epoch <= completed + 1 &&
          aia2StationBridge.hasProof(player.server, team, rule.id);
      });
    }
    catch (error) { ready = false; lookupFailure = error; }
  }
  aia2StationConfig.rules.forEach(function (rule) {
    // A changed team never inherits the old team's proof, even if the item was transferred.
    var proof = ready && !!proofs[rule.id];
    var key = name + ':' + rule.id;
    var state = String(team) + ':' + proof;
    if (aia2StationProjection[key] !== state) {
      player.server.runCommandSilent('advancement ' + (proof ? 'grant ' : 'revoke ') + name + ' only ' + rule.advancement);
      aia2StationProjection[key] = state;
    }
  });
  if (lookupFailure) throw lookupFailure;
}

// Member mutation of the startup-created AIA2 container is supported by KubeJS.
// Core sync invokes this on immediate team changes, in addition to bounded polling.
global.AIA2.syncStations = aia2SyncStations;

ServerEvents.tick(function () {
  aia2StationTick++;
  if (aia2StationTick % 20 === 0) aia2InitStations();
});
ServerEvents.unloaded(function () {
  aia2StationConfigured = false;
  aia2StationProjection = {};
  aia2StationBridge.clearRuntime();
});
PlayerEvents.loggedIn(function (event) {
  aia2StationProjection = {};
  try { aia2SyncStations(event.player); }
  catch (error) { console.error('[AIA2] Не вдалося синхронізувати доказ станції: ' + String(error)); }
});
PlayerEvents.tick(function (event) {
  if (event.player.tickCount % 40 !== 0) return;
  try { aia2SyncStations(event.player); }
  catch (error) {
    if (event.player.tickCount % 200 === 0) console.error('[AIA2] Перевірка доказів станцій закрита: ' + String(error));
  }
});
