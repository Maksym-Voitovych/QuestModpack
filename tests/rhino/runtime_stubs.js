// Host fixtures only: these model APIs, not Minecraft or mod execution.
var __fixture = {callbacks: {}, commands: {}, messages: [], stages: {}, inventory: [],
  ledger: String(__savedLedgerJSON || ''), guardReady: false};
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
var __team = {getTeamId: function () { return 'fixture-team'; },
  isCompleted: function () { return true; }, getOnlineMembers: function () { return [__player]; }};
var __guard = {clearRuntime: function () { __fixture.guardReady = false; },
  setRulesJson: function () {}, setItemRulesJson: function () {}, setRecipeRulesJson: function () {}, setTeamProgress: function () {},
  apiVersion: function () { return 4; }, syncPlayer: function () {}, configureKeyRulesJson: function () {},
  hasProductionProof: function () { return true; }, setTeamKeyReady: function () {}, setPlayerTeam: function () {}, setReady: function () { __fixture.guardReady = true; },
  isReady: function () { return __fixture.guardReady; }};
var Java = {loadClass: function (name) {
  if (name === 'dev.ftb.mods.ftbquests.quest.ServerQuestFile') return {INSTANCE: {
    getQuest: function (id) { return {id: id}; }, getOrCreateTeamData: function () { return __team; }}};
  if (name === 'net.darkhax.gamestages.GameStageHelper') return {
    hasStage: function (player, stage) { return !!__fixture.stages[stage]; }};
  if (name === 'ua.aia2.guard.Aia2MachineGuard') return __guard;
  throw new Error('Unexpected Java class: ' + name);
}};
var JsonIO = {readString: function () { return __rulesJSON; }};
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
var PlayerEvents = {loggedIn: function (callback) { __fixture.callbacks.login = callback; }, tick: function () {}};
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
