// Host fixtures only: these model APIs, not Minecraft or mod execution.
var __fixture = {callbacks: {}, commands: {}, messages: [], stages: {}, inventory: [],
  ledger: String(__savedLedgerJSON || ''), guardReady: false, team: 'fixture-team',
  stationCommands: [], stationConfigured: false, stationConfigureCalls: 0, stationLookupCalls: [],
  stationProofs: __savedStationReceiptsJSON ? JSON.parse(String(__savedStationReceiptsJSON)) : {},
  stationConfigureFailure: false, stationFailureId: '', stationAssertions: 0};
function fixtureAssert(value, message) { if (!value) throw new Error('ASSERTION: ' + message); }
function fixtureStack(id, count) {
  return {id: id, count: count, copy: function () { return fixtureStack(this.id, this.count); },
    getCount: function () { return this.count; }, shrink: function (n) { this.count -= n; },
    isEmpty: function () { return this.count <= 0 || this.id === 'minecraft:air'; }};
}
var __server = {persistentData: {
  getString: function () { return __fixture.ledger; },
  putString: function (key, value) { __fixture.ledger = String(value); }
}, runCommandSilent: function (command) {
  if (/^advancement (grant|revoke) Alice only aia2:stations\//.test(String(command)))
    __fixture.stationCommands.push(String(command));
  var match = /^gamestage (add|remove) [A-Za-z0-9_]+ (\S+)(?: true)?$/.exec(command);
  if (match) { if (match[1] === 'add') __fixture.stages[match[2]] = true; else delete __fixture.stages[match[2]]; }
  return 0;
}, getPlayerList: function () { return {getPlayers: function () { return [__player]; }}; }};
var __player = {username: 'Alice', server: __server, blockX: 0, blockY: 64, blockZ: 0,
  isServerPlayer: function () { return true; }, isFake: function () { return false; },
  uuid: 'fixture-player',
  level: {getBlock: function () { return {id: 'minecraft:crafting_table'}; }},
  getInventory: function () { return {
    getStackInSlot: function (i) { return __fixture.inventory[i]; },
    setStackInSlot: function (i, stack) { __fixture.inventory[i] = stack; }
  }; },
  persistentData: {getString: function () { return ''; }, putString: function () {}},
  containerMenu: {broadcastChanges: function () {}},
  tell: function (message) { __fixture.messages.push(String(message)); }};
var __team = {getTeamId: function () { return __fixture.team; },
  isCompleted: function () { return true; }, getOnlineMembers: function () { return [__player]; }};
var __guard = {clearRuntime: function () { __fixture.guardReady = false; },
  setRulesJson: function () {}, setItemRulesJson: function () {}, setRecipeRulesJson: function () {}, setDimensionRulesJson: function () {}, setTeamProgress: function () {},
  apiVersion: function () { return 4; }, syncPlayer: function () {}, configureKeyRulesJson: function () {},
  hasProductionProof: function () { return true; }, setTeamKeyReady: function () {}, setPlayerTeam: function () {}, setReady: function () { __fixture.guardReady = true; },
  isReady: function () { return __fixture.guardReady; }};
var Java = {loadClass: function (name) {
  if (name === 'ua.aia2.guard.FtbQuestBridge') return {getTeamData: function (file, player) { return file.getOrCreateTeamData(player); }};
  if (name === 'dev.ftb.mods.ftbquests.quest.ServerQuestFile') return {INSTANCE: {
    getQuest: function (id) { return {id: id}; }, getOrCreateTeamData: function () { return __team; }}};
  if (name === 'net.darkhax.gamestages.GameStageHelper') return {
    hasStage: function (player, stage) { return !!__fixture.stages[stage]; }};
  if (name === 'ua.aia2.guard.Aia2MachineGuard') return __guard;
  if (name === 'ua.aia2.guard.StationProductionBridge') return __stationBridge;
  throw new Error('Unexpected Java class: ' + name);
}};
var JsonIO = {readString: function (path) {
  if (path === 'kubejs/config/aia2_stations.json') return __stationRulesJSON;
  fixtureAssert(path === 'kubejs/config/aia2_runtime.json', 'known configuration path');
  return __rulesJSON;
}};
var Platform = {isLoaded: function (name) { return name === 'aia2_machine_guard'; }};
var Item = {of: function (id, count) { return fixtureStack(id, count || 1); }};
var console = {error: function (s) { __fixture.messages.push(String(s)); }, warn: function () {}, info: function () {}};
function fixtureCommand(name) { return {executes: function (callback) {
  __fixture.commands[name] = callback; return this;
}, then: function () { return this; }}; }
var ServerEvents = {
  commandRegistry: function (callback) { callback({commands: {literal: fixtureCommand}, register: function () {}}); },
  loaded: function (callback) { __fixture.callbacks.loaded = callback; },
  unloaded: function (callback) { __fixture.callbacks.unloaded = callback; },
  tick: function (callback) { __fixture.callbacks.serverTick = callback; }};
var PlayerEvents = {loggedIn: function (callback) { __fixture.callbacks.login = callback; },
  tick: function (callback) { __fixture.callbacks.playerTick = callback; }};
function fixtureCommandContext() { return {source: {getPlayer: function () { return __player; }}}; }
function fixtureActivate() {
  __fixture.callbacks.loaded({server: __server});
  __fixture.callbacks.serverTick({server: __server});
  __fixture.callbacks.login({player: __player});
  fixtureAssert(global.AIA2Machines.isReady(), 'Machine Guard initialized');
  fixtureAssert(__fixture.commands.status(fixtureCommandContext()) === 1, '/aia2 status succeeds');
}
function fixtureForgeFirst() {
  var epoch = global.AIA2.rules.epochs[0];
  for (var i = 0; i < 36; i++) __fixture.inventory[i] = fixtureStack('minecraft:air', 0);
  var cost = epoch.transitionCost || epoch.cost;
  Object.keys(cost).forEach(function (id, i) { __fixture.inventory[i] = fixtureStack(id, cost[id]); });
  fixtureAssert(__fixture.commands.key(fixtureCommandContext()) === 1, '/aia2 key succeeds');
  fixtureAssert(global.AIA2.completed(__player) === 1, 'ledger completed epoch one');
  fixtureAssert(__fixture.stages.aia2_epoch_02, 'Game Stages mirror advanced');
  var keys = __fixture.inventory.filter(function (s) { return s.id === epoch.key && s.count === 1; });
  fixtureAssert(keys.length === 1, 'one key issued');
  fixtureAssert(!global.AIA2.canAccess(__player, 3), 'future epoch blocked');
}


// Only the Java bridge boundary is modeled. The real45_stations.js above it is
// interpreted by the pinned Rhino85 core with a read-only top-level global map.
var __stationBridge = {
  configureJson: function (json) {
    __fixture.stationConfigureCalls++;
    if (__fixture.stationConfigureFailure) throw new Error('station configuration host failure');
    fixtureAssert(JSON.stringify(JSON.parse(String(json))) === JSON.stringify(JSON.parse(String(__stationRulesJSON)).rules),
      'actual station script supplies all six exact rule rows');
    __fixture.stationConfigured = true;
  },
  isConfigured: function () { return __fixture.stationConfigured; },
  hasProof: function (server, team, id) {
    fixtureAssert(server === __server, 'station receipt lookup uses current server');
    __fixture.stationLookupCalls.push(String(team) + ':' + String(id));
    if (__fixture.stationFailureId === String(id)) throw new Error('station journal host failure');
    return !!__fixture.stationProofs[String(team) + ':' + String(id)];
  },
  clearRuntime: function () { __fixture.stationConfigured = false; }
};
function fixtureStationAssert(value, message) {
  fixtureAssert(value, message); __fixture.stationAssertions++;
}
function fixtureStationCompleted(value) {
  var state = aia2State(__server);
  aia2TeamRecord(__player, state).completed = value;
  aia2Save(__server, state);
}
function fixtureStationCount(action) {
  return __fixture.stationCommands.filter(function (command) {
    return command.indexOf('advancement ' + action + ' ') === 0;
  }).length;
}
function fixtureStationChecks() {
  var originalLedger = __fixture.ledger;
  var rules = JSON.parse(String(__stationRulesJSON)).rules;
  fixtureStationAssert(rules.length === 6, 'six station world-action rules supplied');
  fixtureStationAssert(typeof global.AIA2.syncStations === 'function', 'station API mutates startup-created member');
  fixtureStationAssert(typeof globalThis === 'undefined', 'station script does not need globalThis');
  __fixture.guardReady = false;
  global.AIA2.syncStations(__player);
  fixtureStationAssert(__fixture.stationConfigureCalls === 0, 'configuration waits for Machine Guard');
  fixtureStationAssert(fixtureStationCount('grant') === 0 && fixtureStationCount('revoke') === 6,
    'unready guard revokes all station projections');
  __fixture.guardReady = true;
  global.AIA2.syncStations(__player);
  fixtureStationAssert(__fixture.stationConfigureCalls === 1, 'station native config installed once after readiness');
  fixtureStationAssert(fixtureStationCount('grant') === 0, 'configuration is not station production evidence');
  rules.forEach(function (rule) { __fixture.stationProofs['fixture-team:' + rule.id] = true; });
  __fixture.stationCommands = [];
  global.AIA2.syncStations(__player);
  fixtureStationAssert(fixtureStationCount('grant') === 0, 'saved receipt does not bypass current era');
  fixtureStationCompleted(36);
  __fixture.stationLookupCalls = [];
  global.AIA2.syncStations(__player);
  fixtureStationAssert(fixtureStationCount('grant') === 3, 'epoch37 enables only first three station receipts');
  fixtureStationAssert(__fixture.stationLookupCalls.length === 3, 'future orbit receipts not queried');
  fixtureStationCompleted(37);
  global.AIA2.syncStations(__player);
  fixtureStationAssert(fixtureStationCount('grant') === 6, 'epoch38 enables remaining three receipts');
  __fixture.stationCommands = [];
  for (var i = 0; i < 100; i++) global.AIA2.syncStations(__player);
  fixtureStationAssert(__fixture.stationCommands.length === 0 && __fixture.stationConfigureCalls === 1,
    'unchanged polling produces no command or configuration churn');
  __fixture.team = 'new-team'; fixtureStationCompleted(37);
  // Exercise the actual core hook, not a second implementation of its wiring.
  aia2Sync(__player);
  fixtureStationAssert(fixtureStationCount('grant') === 0 && fixtureStationCount('revoke') === 6,
    'actual core team sync revokes old-team station projection');
  __fixture.team = 'fixture-team'; __fixture.stationCommands = [];
  aia2Sync(__player);
  fixtureStationAssert(fixtureStationCount('grant') === 6, 'returning original team restores own modeled durable receipts');
  __fixture.stationCommands = []; __fixture.stationFailureId = rules[5].id;
  var caught = false;
  try { global.AIA2.syncStations(__player); } catch (error) { caught = String(error).indexOf('journal host failure') >= 0; }
  fixtureStationAssert(caught, 'native receipt error is surfaced');
  fixtureStationAssert(fixtureStationCount('grant') === 0 && fixtureStationCount('revoke') === 6,
    'later receipt lookup failure revokes all projections before throwing');
  __fixture.stationFailureId = ''; global.AIA2.syncStations(__player);
  __fixture.stationCommands = []; __fixture.stationConfigured = false;
  __fixture.stationConfigureFailure = true;
  var errorsBefore = __fixture.messages.length;
  global.AIA2.syncStations(__player); global.AIA2.syncStations(__player);
  fixtureStationAssert(fixtureStationCount('grant') === 0 && fixtureStationCount('revoke') === 6,
    'configuration failure closes projection');
  fixtureStationAssert(__fixture.messages.length === errorsBefore + 1, 'repeated identical configuration error logged once');
  fixtureStationAssert(!__stationBridge.isConfigured(), 'failed native configuration clears runtime rule readiness');
  __fixture.stationConfigureFailure = false; global.AIA2.syncStations(__player);
  __fixture.stationCommands = [];
  __fixture.callbacks.login({player: __player});
  fixtureStationAssert(fixtureStationCount('grant') === 6, 'actual station login callback refreshes receipt projection');
  __fixture.stationCommands = []; __player.tickCount = 41;
  __fixture.callbacks.playerTick({player: __player});
  fixtureStationAssert(__fixture.stationCommands.length === 0, 'station player poll bounded to forty ticks');
  __player.tickCount = 40;
  __fixture.callbacks.playerTick({player: __player});
  fixtureStationAssert(__fixture.stationCommands.length === 0, 'bounded station poll keeps cached projection');
  var proofCount = Object.keys(__fixture.stationProofs).length;
  __fixture.callbacks.unloaded();
  fixtureStationAssert(!__stationBridge.isConfigured() && Object.keys(__fixture.stationProofs).length === proofCount,
    'actual unload callback clears runtime but preserves modeled native journal');
  var beforeConfig = __fixture.stationConfigureCalls;
  for (var tick = 0; tick < 20; tick++) __fixture.callbacks.serverTick();
  fixtureStationAssert(__fixture.stationConfigureCalls === beforeConfig + 1, 'actual twenty-tick callback restores native configuration');
  __fixture.ledger = originalLedger; __fixture.team = 'fixture-team';
  // Restore unrelated original tests to their original progress and stage state.
  aia2Sync(__player);
}
function fixtureStationReloadChecks() {
  fixtureStationAssert(Object.keys(__fixture.stationProofs).length === 6,
    'separate modeled native station journal reloaded into fresh server context');
  fixtureStationAssert(typeof global.AIA2.syncStations === 'function', 'station closure installed after core clears old members');
  var oldLedger = __fixture.ledger;
  fixtureStationCompleted(37); __fixture.stationCommands = [];
  aia2Sync(__player);
  fixtureStationAssert(fixtureStationCount('grant') === 6, 'fresh server context projects original-team station receipts');
  __fixture.team = 'new-team'; fixtureStationCompleted(37); __fixture.stationCommands = [];
  aia2Sync(__player);
  fixtureStationAssert(fixtureStationCount('grant') === 0 && fixtureStationCount('revoke') === 6,
    'fresh context cannot inherit receipts on another team');
  __fixture.ledger = oldLedger; __fixture.team = 'fixture-team'; aia2Sync(__player);
  fixtureStationAssert(global.AIA2.completed(__player) === 1, 'station scenarios preserve original saved epoch progress');
}
