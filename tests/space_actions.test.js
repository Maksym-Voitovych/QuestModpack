// Actual progression scripts; Java/native receipts and FTB storage are modeled.
// These tests do not launch Minecraft or execute the Ad Astra manufacturing hook.
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const root = path.resolve(__dirname, '..');
const rules = JSON.parse(fs.readFileSync(path.join(root, 'kubejs/config/aia2_runtime.json')));
const script = name => fs.readFileSync(path.join(root, name), 'utf8');

function fixture(options = {}) {
  class Stack {
    constructor(id, count) { this.id = id; this.count = count; }
    copy() { return new Stack(this.id, this.count); }
    getCount() { return this.count; }
    shrink(count) { this.count -= count; }
    isEmpty() { return this.count <= 0 || this.id === 'minecraft:air'; }
  }
  let saved = options.saved || JSON.stringify({schema: 1, teams: {A: {completed: options.completed ?? 36}}});
  const proofs = options.proofs || new Set();
  const deniedQuests = new Set();
  const deniedKeyProofs = new Set();
  const readiness = new Map();
  const actionCalls = [];
  const messages = [];
  const commands = [];
  const players = [];
  let nativeFailure = false;
  let writeFailure = false;
  let login;
  const server = {persistentData: {
    getString() { return saved; },
    putString(key, value) {
      if (writeFailure) { writeFailure = false; throw new Error('modeled journal write failure'); }
      saved = String(value);
    }
  }, runCommandSilent(command) {
    commands.push(command);
    const match = /^gamestage (add|remove) ([A-Za-z0-9_]+) (\S+)(?: true)?$/.exec(command);
    if (match) {
      const player = players.find(p => p.username === match[2]);
      if (player) player.stages[match[1] === 'add' ? 'add' : 'delete'](match[3]);
    }
    return 0;
  }};
  const keyGuard = {
    setTeamKeyReady(team, epoch, branch, ready) { readiness.set(team + ':' + epoch + ':' + branch, !!ready); },
    hasProductionProof(serverArg, team, epoch, branch) {
      assert.equal(serverArg, server);
      return !deniedKeyProofs.has(team + ':' + epoch + ':' + branch);
    }
  };
  const actions = {hasRequiredActions(serverArg, team, epoch, branch) {
    assert.equal(serverArg, server);
    actionCalls.push({team, epoch, branch});
    if (nativeFailure) throw new Error('modeled native action journal unavailable');
    if (branch !== 'tech' || ![37, 38].includes(epoch)) return true;
    return (epoch === 37 ? [1, 2] : [3, 4]).every(tier => proofs.has(team + ':nasa_tier_' + tier + '_rocket'));
  }};
  const file = {
    getQuest(id) { return {id}; },
    teamData(player) { return {
      getTeamId() { return player.team; },
      isCompleted(quest) { return !deniedQuests.has(quest.id); },
      getOnlineMembers() { return players.filter(p => p.team === player.team); }
    }; }
  };
  const chain = {executes() { return this; }, then() { return this; }};
  const context = vm.createContext({global: {}, globalThis: undefined,
    console: {error(error) { messages.push(String(error)); }},
    Java: {loadClass(name) {
      if (name === 'ua.aia2.guard.RequiredSpaceActions') return actions;
      if (name === 'ua.aia2.guard.Aia2MachineGuard') return keyGuard;
      if (name === 'dev.ftb.mods.ftbquests.quest.ServerQuestFile') return {INSTANCE: file};
      if (name === 'ua.aia2.guard.FtbQuestBridge') return {getTeamData(questFile, player) { return questFile.teamData(player); }};
      assert.equal(name, 'net.darkhax.gamestages.GameStageHelper');
      return {hasStage(player, stage) { return player.stages.has(stage); }};
    }},
    JsonIO: {readString() { return JSON.stringify(rules); }},
    Item: {of(id, count = 1) { return new Stack(id, count); }},
    ServerEvents: {commandRegistry(callback) { callback({commands: {literal() { return chain; }}, register() {}}); }},
    PlayerEvents: {loggedIn(callback) { login = callback; }, tick() {}}
  });
  vm.runInContext(script('kubejs/startup_scripts/aia2/00_shared_state.js'), context);
  context.global = new Proxy(context.global, {
    set() { throw new Error('KubeJS server global is read-only'); },
    deleteProperty() { throw new Error('KubeJS server global is read-only'); }
  });
  vm.runInContext(script('kubejs/server_scripts/aia2/00_core.js'), context);
  Object.assign(context.global.AIA2Machines, {isReady() { return true; }, syncPlayer() {}});
  vm.runInContext(script('kubejs/server_scripts/aia2/20_progression.js'), context);
  const slots = Array.from({length: 36}, () => new Stack('minecraft:air', 0));
  const data = new Map();
  const player = {username: 'Alice', team: 'A', server, stages: new Set(), tickCount: 40,
    blockX: 0, blockY: 64, blockZ: 0,
    level: {getBlock() { return {id: 'minecraft:crafting_table'}; }},
    isServerPlayer() { return true; }, isFake() { return false; },
    getInventory() { return {getStackInSlot(i) { return slots[i]; }, setStackInSlot(i, stack) { slots[i] = stack; }}; },
    persistentData: {getString(key) { return data.get(key) || ''; }, putString(key, value) { data.set(key, value); }},
    containerMenu: {broadcastChanges() {}}, tell(message) { messages.push(String(message)); }
  };
  players.push(player);
  login({player});
  function supply(cost) {
    for (let i = 0; i < slots.length; i++) slots[i] = new Stack('minecraft:air', 0);
    Object.entries(cost).forEach(([id, count], i) => { slots[i] = new Stack(id, count); });
  }
  const state = () => JSON.parse(saved);
  return {context, player, server, slots, proofs, deniedQuests, deniedKeyProofs, readiness, actionCalls, messages, commands,
    supply, state, saved: () => saved, failNative(value = true) { nativeFailure = value; },
    failWrite() { writeFailure = true; },
    addTier(tier, team = 'A') { proofs.add(team + ':nasa_tier_' + tier + '_rocket'); },
    reboot() { return fixture({saved, proofs}); }
  };
}

test('all completed old FTB quests and old key receipts cannot replace NASA actions before new spending', () => {
  for (const completed of [36, 37]) {
    const b = fixture({completed}), epoch = rules.epochs[completed];
    b.supply(epoch.transitionCost);
    const inventory = JSON.stringify(b.slots), saved = b.saved();
    assert.throws(() => b.context.aia2Forge(b.player, false));
    assert.equal(JSON.stringify(b.slots), inventory);
    assert.equal(b.saved(), saved);
    assert.equal(b.readiness.get('A:' + epoch.number + ':tech'), false);
  }
});

test('two era-specific current-team receipts enable technology while the independent magic branch remains usable', () => {
  for (const [completed, tiers, wrong] of [[36, [1, 2], [3, 4]], [37, [3, 4], [1, 2]]]) {
    const b = fixture({completed}), epoch = completed + 1;
    assert.equal(b.readiness.get('A:' + epoch + ':tech'), false);
    assert.equal(b.readiness.get('A:' + epoch + ':arcane'), true);
    wrong.forEach(tier => b.addTier(tier));
    b.context.aia2RefreshBranches(b.player);
    assert.equal(b.readiness.get('A:' + epoch + ':tech'), false);
    b.addTier(tiers[0]); b.context.aia2RefreshBranches(b.player);
    assert.equal(b.readiness.get('A:' + epoch + ':tech'), false);
    b.addTier(tiers[1]); b.context.aia2RefreshBranches(b.player);
    assert.equal(b.readiness.get('A:' + epoch + ':tech'), true);
    assert.equal(b.readiness.get('A:' + epoch + ':arcane'), true);
  }
});

test('another team never inherits NASA receipts even when its old FTB tasks are complete', () => {
  const b = fixture({saved: JSON.stringify({schema: 1, teams: {A: {completed: 36}, B: {completed: 36}}})});
  b.addTier(1); b.addTier(2); b.context.aia2RefreshBranches(b.player);
  assert.equal(b.readiness.get('A:37:tech'), true);
  b.player.team = 'B'; b.context.aia2RefreshBranches(b.player);
  assert.equal(b.readiness.get('B:37:tech'), false);
  assert.equal(b.readiness.get('B:37:arcane'), true);
});

test('native action lookup failure clears both cached branch permissions before surfacing the error', () => {
  const b = fixture(); b.addTier(1); b.addTier(2); b.context.aia2RefreshBranches(b.player);
  assert.equal(b.readiness.get('A:37:tech'), true);
  assert.equal(b.readiness.get('A:37:arcane'), true);
  const saved = b.saved(), inventory = JSON.stringify(b.slots);
  b.failNative();
  assert.throws(() => b.context.aia2RefreshBranches(b.player), /native action journal unavailable/);
  assert.equal(b.readiness.get('A:37:tech'), false);
  assert.equal(b.readiness.get('A:37:arcane'), false);
  assert.equal(b.saved(), saved);
  assert.equal(JSON.stringify(b.slots), inventory);
});

test('a previously paid legacy pending transition completes without new actions, new charge or provenance fabrication', () => {
  for (const pending of [37, 38]) {
    const b = fixture({saved: JSON.stringify({schema: 1, teams: {A: {completed: pending - 1, pending}}})});
    const inventory = JSON.stringify(b.slots);
    assert.equal(b.context.aia2FinishPending(b.player), true);
    assert.equal(b.state().teams.A.completed, pending);
    assert.equal(b.state().teams.A.pending, undefined);
    assert.equal(b.state().teams.A.pendingActionContract, undefined);
    assert.equal(JSON.stringify(b.slots), inventory);
    assert.equal(b.proofs.size, 0);
  }
});

test('newly paid pending transitions persist their action contract and cannot complete with missing receipts', () => {
  for (const [completed, tiers] of [[36, [1, 2]], [37, [3, 4]]]) {
    const b = fixture({completed}), epoch = rules.epochs[completed];
    tiers.forEach(tier => b.addTier(tier));
    b.deniedQuests.add(parseInt(epoch.finalQuestId, 16));
    b.supply(epoch.transitionCost);
    assert.equal(b.context.aia2Forge(b.player, false), 1);
    assert.deepEqual(b.state().teams.A, {completed, pending: completed + 1, pendingActionContract: 1});
    const saved = b.saved(), inventory = JSON.stringify(b.slots);
    b.deniedQuests.clear(); b.proofs.clear();
    assert.equal(b.context.aia2FinishPending(b.player), false);
    assert.equal(b.saved(), saved);
    assert.equal(JSON.stringify(b.slots), inventory);
    const fresh = b.reboot();
    assert.equal(fresh.context.aia2FinishPending(fresh.player), false);
    assert.equal(fresh.saved(), saved);
    tiers.forEach(tier => fresh.addTier(tier));
    assert.equal(fresh.context.aia2FinishPending(fresh.player), true);
    assert.deepEqual(fresh.state().teams.A, {completed: completed + 1});
  }
});

test('old paid pending does not wait for a key quest newly blocked by added dependencies', () => {
  for (const pending of [37, 38]) {
    const b = fixture({saved: JSON.stringify({schema: 1, teams: {A: {completed: pending - 1, pending}}})});
    const epoch = rules.epochs[pending - 1];
    b.deniedQuests.add(parseInt(epoch.branchKeyQuestIds.tech, 16));
    b.deniedQuests.add(parseInt(epoch.branchKeyQuestIds.arcane, 16));
    assert.equal(b.context.aia2FinishPending(b.player), true);
    assert.equal(b.state().teams.A.completed, pending);
    assert.equal(b.proofs.size, 0);
  }
});

test('legacy paid pending still requires both genuine native key receipts', () => {
  for (const branch of ['tech', 'arcane']) {
    const b = fixture({saved: JSON.stringify({schema: 1, teams: {A: {completed: 36, pending: 37}}})});
    b.deniedKeyProofs.add('A:37:' + branch);
    const saved = b.saved();
    assert.equal(b.context.aia2FinishPending(b.player), false);
    assert.equal(b.saved(), saved);
  }
});

test('manufacturing receipt lookup errors also revoke both old readiness flags', () => {
  const b = fixture(); b.addTier(1); b.addTier(2); b.context.aia2RefreshBranches(b.player);
  b.context.AIA2KeyGuard.hasProductionProof = () => { throw new Error('key journal unavailable'); };
  assert.throws(() => b.context.aia2RefreshBranches(b.player), /key journal unavailable/);
  assert.equal(b.readiness.get('A:37:tech'), false);
  assert.equal(b.readiness.get('A:37:arcane'), false);
});

test('validating pending action contracts rejects orphaned or unknown markers without accepting a reset', () => {
  const b = fixture(), validate = b.context.global.AIA2Core.validateState;
  for (const marker of [0, 2, '1', null, {}, []]) {
    const saved = {schema: 1, teams: {A: {completed: 36, pending: 37, pendingActionContract: marker}}};
    assert.throws(() => validate(saved));
  }
  assert.throws(() => validate({schema: 1, teams: {A: {completed: 36, pendingActionContract: 1}}}));
  const historical = {schema: 1, teams: {A: {completed: 36, pending: 37}}};
  assert.equal(validate(historical), historical);
  const current = {schema: 1, teams: {A: {completed: 36, pending: 37, pendingActionContract: 1}}};
  assert.equal(validate(current), current);
});

test('journal commit failure restores inventory and removes both newly introduced pending fields', () => {
  const b = fixture(); b.addTier(1); b.addTier(2); b.supply(rules.epochs[36].transitionCost);
  const inventory = JSON.stringify(b.slots), saved = b.saved();
  b.failWrite();
  assert.throws(() => b.context.aia2Forge(b.player, false), /journal write failure/);
  assert.equal(JSON.stringify(b.slots), inventory);
  assert.equal(b.saved(), saved);
  const record = b.context.aia2TeamRecord(b.player, b.context.aia2State(b.server));
  assert.equal(record.completed, 36);
  assert.equal(record.pending, undefined);
  assert.equal(record.pendingActionContract, undefined);
});

test('paid recovery of a completed space epoch remains grandfathered and never fabricates NASA actions', () => {
  for (const completed of [37, 38]) {
    const b = fixture({completed}), epoch = rules.epochs[completed - 1];
    const cost = Object.fromEntries(Object.entries(epoch.cost).filter(([id]) => !id.startsWith('kubejs:aia2_epoch_key_')));
    cost['minecraft:crafting_table'] = 1;
    b.supply(cost);
    assert.equal(b.context.aia2Forge(b.player, true), 1);
    assert.deepEqual(b.state().teams.A, {completed});
    assert.equal(b.slots.filter(stack => stack.id === epoch.key && stack.count === 1).length, 1);
    assert.equal(b.proofs.size, 0);
  }
});

test('earlier epochs retain their existing transition contract without a space-action marker', () => {
  const b = fixture({completed: 0});
  b.supply(rules.epochs[0].transitionCost);
  assert.equal(b.context.aia2Forge(b.player, false), 1);
  assert.deepEqual(b.state().teams.A, {completed: 1});
  assert.equal(b.proofs.size, 0);
});
