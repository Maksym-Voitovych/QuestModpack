// Native recipe completion proofs, not possession/observation tasks.
var aia2MechanicBridge = Java.loadClass('ua.aia2.guard.ProductionMilestoneBridge');
var aia2MechanicConfig = JSON.parse(JsonIO.readString('kubejs/config/aia2_mechanics.json'));
var aia2MechanicConfigured = false;
var aia2MechanicFailure = '';
var aia2MechanicProjection = {};
var aia2MechanicTick = 0;

function aia2InitMechanics() {
  if (!global.AIA2Machines.isReady()) return false;
  try {
    if (aia2MechanicConfigured && aia2MechanicBridge.isConfigured()) return true;
    if (aia2MechanicConfig.schema !== 1 || !aia2MechanicConfig.rules || aia2MechanicConfig.rules.length !== 6) {
      throw new Error('Потрібні шість перевірених правил виробничих спостережень.');
    }
    aia2MechanicBridge.configureJson(JSON.stringify(aia2MechanicConfig.rules));
    aia2MechanicConfigured = aia2MechanicBridge.isConfigured();
    aia2MechanicFailure = '';
    aia2MechanicProjection = {};
    return aia2MechanicConfigured;
  } catch (error) {
    aia2MechanicConfigured = false;
    // A rejected configuration cannot leave an older rule map collecting new
    // receipts. Durable SavedData is intentionally unaffected by clearRuntime.
    try { aia2MechanicBridge.clearRuntime(); }
    catch (clearError) { console.error('[AIA2] Не вдалося закрити виробничі спостереження: ' + String(clearError)); }
    var message = String(error.message || error);
    if (message !== aia2MechanicFailure) console.error('[AIA2] Виробничі докази закрито: ' + message);
    aia2MechanicFailure = message;
    return false;
  }
}

function aia2SyncMechanics(player) {
  if (!player || !player.isServerPlayer() || player.isFake()) return;
  var name = String(player.username);
  if (!/^[A-Za-z0-9_]{1,16}$/.test(name)) throw new Error('[AIA2] Некоректне ім’я гравця для виробничого доказу.');
  var ready = aia2InitMechanics();
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
      aia2MechanicConfig.rules.forEach(function (rule) {
        proofs[rule.id] = rule.epoch <= completed + 1 &&
          aia2MechanicBridge.hasProof(player.server, team, rule.id);
      });
    }
    catch (error) { ready = false; lookupFailure = error; }
  }
  aia2MechanicConfig.rules.forEach(function (rule) {
    // A changed team never inherits the old team's proof, even if the item was transferred.
    var proof = ready && !!proofs[rule.id];
    var key = name + ':' + rule.id;
    var state = String(team) + ':' + proof;
    if (aia2MechanicProjection[key] !== state) {
      player.server.runCommandSilent('advancement ' + (proof ? 'grant ' : 'revoke ') + name + ' only ' + rule.advancement);
      aia2MechanicProjection[key] = state;
    }
  });
  if (lookupFailure) throw lookupFailure;
}

// Member mutation of the startup-created AIA2 container is supported by KubeJS.
// Core sync invokes this on immediate team changes, in addition to bounded polling.
global.AIA2.syncMechanics = aia2SyncMechanics;

ServerEvents.tick(function () {
  aia2MechanicTick++;
  if (aia2MechanicTick % 20 === 0) aia2InitMechanics();
});
ServerEvents.unloaded(function () {
  aia2MechanicConfigured = false;
  aia2MechanicProjection = {};
  aia2MechanicBridge.clearRuntime();
});
PlayerEvents.loggedIn(function (event) {
  aia2MechanicProjection = {};
  try { aia2SyncMechanics(event.player); }
  catch (error) { console.error('[AIA2] Не вдалося синхронізувати виробничий доказ: ' + String(error)); }
});
PlayerEvents.tick(function (event) {
  if (event.player.tickCount % 40 !== 0) return;
  try { aia2SyncMechanics(event.player); }
  catch (error) {
    if (event.player.tickCount % 200 === 0) console.error('[AIA2] Перевірка виробничих доказів закрита: ' + String(error));
  }
});
