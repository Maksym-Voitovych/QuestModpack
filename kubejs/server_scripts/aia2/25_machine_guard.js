// Optional bridge to the source-pinned NeoForge companion in companion/.
// 'required' mode refuses further key forging if this adapter isn't initialized.
var AIA2MachineGuard = null;
if (Platform.isLoaded('aia2_machine_guard')) {
  AIA2MachineGuard = Java.loadClass('ua.aia2.guard.Aia2MachineGuard');
}
var aia2MachineReady = false;
var aia2MachineInitAttempted = false;

function aia2MachineFailure(error) {
  aia2MachineReady = false;
  if (AIA2MachineGuard) AIA2MachineGuard.clearRuntime();
  console.error('[AIA2] Machine Guard зупинено: ' + String(error));
}

function aia2MirrorMachinePlayer(player) {
  if (!player || !player.isServerPlayer() || player.isFake()) return;
  var team = global.AIA2.teamId(player);
  AIA2MachineGuard.setTeamProgress(team, global.AIA2.completed(player));
  AIA2MachineGuard.setPlayerTeam(String(player.getUUID()), team);
}

function aia2InitMachines(server) {
  aia2MachineInitAttempted = true;
  aia2MachineReady = false;
  if (!AIA2MachineGuard) {
    console.warn('[AIA2] AIA2 Machine Guard JAR не встановлено. Захист тіку машин не активний.');
    return;
  }
  try {
    AIA2MachineGuard.clearRuntime();
    if (!global.AIA2.rules.blockGates) throw new Error('Відсутня повна карта blockGates.');
    AIA2MachineGuard.setRulesJson(JSON.stringify(global.AIA2.rules.blockGates));
    AIA2MachineGuard.setItemRulesJson(JSON.stringify(global.AIA2.rules.itemGates));
    var state = global.AIA2.ledger(server);
    Object.keys(state.teams).forEach(function (team) {
      AIA2MachineGuard.setTeamProgress(team, state.teams[team].completed);
    });
    server.getPlayerList().getPlayers().forEach(function (player) { aia2MirrorMachinePlayer(player); });
    AIA2MachineGuard.setReady();
    aia2MachineReady = true;
  } catch (error) { aia2MachineFailure(error); }
}

global.AIA2Machines = {
  isReady: function () {
    return !!(AIA2MachineGuard && aia2MachineReady && AIA2MachineGuard.isReady());
  },
  status: function () {
    if (this.isReady()) return 'Machine Guard: активний для стандартних block-entity ticks і звичайного крафту.';
    return 'Machine Guard: не активний; повного захисту машин немає.';
  },
  syncPlayer: function (player) {
    if (!this.isReady()) return;
    try {
      aia2MirrorMachinePlayer(player);
    } catch (error) { aia2MachineFailure(error); }
  },
  claim: function (player, block) {
    if (!this.isReady() || !player || !player.isServerPlayer() || player.isFake()) return;
    var required = global.AIA2.rules.blockGates[String(block.id)] || 0;
    if (!required || !global.AIA2.canAccess(player, required)) return;
    var entity = block.getEntity();
    if (!entity) return;
    try {
      var team = global.AIA2.teamId(player);
      aia2MirrorMachinePlayer(player);
      var owner = String(AIA2MachineGuard.getOwner(entity));
      // Existing ownership persists across unload/restart; visitors cannot steal it.
      if (!owner) AIA2MachineGuard.setOwner(entity, team);
    } catch (error) { aia2MachineFailure(error); }
  }
};

ServerEvents.loaded(function (event) { aia2InitMachines(event.server); });
// Reloading server scripts doesn't run ServerEvents.loaded; lazily reinitialize
// on the next server tick and first invalidate any old Java ledger projection.
if (AIA2MachineGuard) AIA2MachineGuard.clearRuntime();
ServerEvents.tick(function (event) {
  if (AIA2MachineGuard && !aia2MachineReady && !AIA2MachineGuard.isReady()) {
    // One attempt per script load. Failure remains closed until /reload/restart.
    if (aia2MachineInitAttempted) return;
    aia2MachineInitAttempted = true;
    aia2InitMachines(event.server);
  }
});
ServerEvents.unloaded(function () {
  aia2MachineReady = false;
  if (AIA2MachineGuard) AIA2MachineGuard.clearRuntime();
});
