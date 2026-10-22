// Run: node --test tests/runtime.test.js
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const root = path.resolve(__dirname, '..');
const scripts = path.join(root, 'kubejs/server_scripts/aia2');
const rules = JSON.parse(fs.readFileSync(path.join(root, 'kubejs/config/aia2_runtime.json')));
const recipes = JSON.parse(fs.readFileSync(path.join(root, 'kubejs/config/aia2_recipes.json')));

function core() {
  const context = vm.createContext({global: {}});
  vm.runInContext(fs.readFileSync(path.join(scripts, '00_core.js'), 'utf8'), context);
  return context.global.AIA2Core;
}
function stacks(epoch) {
  return Object.entries(epoch.cost).map(([id, count]) => ({id, count}));
}

test('all 48 exact key transactions consume nine units and only the immediate predecessor', () => {
  const c = core();
  rules.epochs.forEach((epoch, index) => {
    const inventory = stacks(epoch);
    const before = JSON.stringify(inventory);
    const plan = c.prepareKey(epoch, index, [true, true, true, true, true, true], inventory);
    assert.equal(plan.completed, index + 1);
    assert.equal(plan.outputId, epoch.key);
    assert.equal(plan.deductions.reduce((n, d) => n + d.count, 0), 9);
    assert.equal(JSON.stringify(inventory), before, 'planning must not mutate inventory');
    const previous = Object.keys(epoch.cost).filter(x => x.includes('epoch_key_'));
    assert.deepEqual(previous, index ? [rules.epochs[index - 1].key] : []);
  });
});
test('missing one mandatory milestone blocks every key before consumption', () => {
  const c = core();
  rules.epochs.forEach((e, i) => {
    for (let absent = 0; absent < 6; absent++) {
      const proof = Array(6).fill(true); proof[absent] = false;
      assert.throws(() => c.prepareKey(e, i, proof, stacks(e)), /шість/);
    }
  });
});
test('missing materials, full inventory, replay, and forged epoch order are rejected', () => {
  const c = core(), e = rules.epochs[0], good = Array(6).fill(true);
  assert.throws(() => c.prepareKey(e, 0, good, []), /Не вистачає/);
  const full = stacks(e).map(s => ({id: s.id, count: s.count + 1}));
  while (full.length < 36) full.push({id: 'minecraft:dirt', count: 64});
  assert.throws(() => c.prepareKey(e, 0, good, full), /слот/);
  assert.throws(() => c.prepareKey(e, 1, good, stacks(e)), /порядок/);
  assert.throws(() => c.prepareKey(rules.epochs[47], 48, good, []), /порядок/);
});
test('split ingredient stacks are handled without removing unrelated items', () => {
  const c = core(), e = rules.epochs[0];
  const slots = [];
  for (const [id, count] of Object.entries(e.cost)) for (let i = 0; i < count; i++) slots.push({id, count: 1});
  slots.push({id: 'minecraft:diamond', count: 17});
  const plan = c.prepareKey(e, 0, Array(6).fill(true), slots);
  assert.equal(plan.deductions.length, 9);
  assert.equal(plan.deductions.some(d => slots[d.slot].id === 'minecraft:diamond'), false);
});
test('state survives JSON reload; corrupt state never silently resets progress', () => {
  const c = core();
  const state = {schema: 1, teams: {a: {completed: 17}, b: {completed: 0}}};
  assert.equal(c.validateState(JSON.parse(JSON.stringify(state))).teams.a.completed, 17);
  for (const value of [-1, 49, 1.5, '48', null]) {
    assert.throws(() => c.validateState({schema: 1, teams: {a: {completed: value}}}));
  }
  assert.throws(() => c.validateState({schema: 2, teams: {}}));
});
test('stage access and post-final access have distinct boundaries', () => {
  const c = core();
  assert.equal(c.mayAccess(2, 0), false);
  assert.equal(c.mayAccess(2, 1), true);
  assert.equal(c.mayAccess(99, 47), false);
  assert.equal(c.mayAccess(99, 48), true);
});
test('recipe handler installs 91 recipes, uses Create addon, and exposes no ungated key recipe', () => {
  const added = [], removed = [];
  let createCalls = 0;
  const event = {
    remove(filter) { removed.push(filter); },
    custom(json) { return {id(id) { added.push({id, json}); }}; },
    recipes: {create: {mixing(results, ingredients) {
      createCalls++;
      return {id(id) { added.push({id, json: {type: 'create:mixing', results, ingredients}}); }};
    }}}
  };
  const context = vm.createContext({JsonIO: {readString() { return JSON.stringify(recipes); }}, ServerEvents: {recipes(cb) { cb(event); }}});
  vm.runInContext(fs.readFileSync(path.join(scripts, '10_recipes.js'), 'utf8'), context);
  assert.equal(added.length, 91);
  assert.equal(new Set(added.map(r => r.id)).size, 91);
  assert.equal(createCalls, 1);
  assert.equal(added.some(r => JSON.stringify(r.json).includes('aia2_epoch_key_')), false);
  assert.equal(removed.filter(r => r.output && r.output.includes('epoch_key_')).length, 48);
  assert.ok(removed.some(r => r.id === 'create_mekanism_improvements:antimatter_pellet'));
  assert.ok(removed.some(r => r.id === 'create_mekanism_improvements:pollonium_pellet'));
});

function bridge() {
  class Stack {
    constructor(id, count) { this.id = id; this.count = count; }
    copy() { return new Stack(this.id, this.count); }
    getCount() { return this.count; }
    shrink(n) { this.count -= n; }
    isEmpty() { return this.count <= 0 || this.id === 'minecraft:air'; }
  }
  const nbt = new Map(), commands = [], players = [];
  const server = {persistentData: {getString(k) { return nbt.get(k) || ''; }, putString(k, v) { nbt.set(k, v); }}, runCommandSilent(c) {
    commands.push(c);
    const match = /^gamestage (add|remove) ([A-Za-z0-9_]+) (\S+)(?: true)?$/.exec(c);
    if (match) {
      const target = players.find(p => p.username === match[2]);
      if (target) target.nativeStages[match[1] === 'add' ? 'add' : 'delete'](match[3]);
    }
    return 0; // Game Stages Reborn returns zero even for successful commands.
  }};
  let loginHandler;
  let fault = false;
  let allProofs = true;
  const file = {
    getQuest(id) { return {id}; },
    getOrCreateTeamData(player) { return {
      getTeamId() { return player.team; },
      isCompleted() { return allProofs; },
      getOnlineMembers() { return players.filter(p => p.team === player.team); }
    }; }
  };
  const chain = {executes() { return this; }, then() { return this; }};
  const context = vm.createContext({global: {AIA2Machines: {isReady() { return true; }, syncPlayer() {}}}, console,
    Java: {loadClass(name) {
      if (name === 'dev.ftb.mods.ftbquests.quest.ServerQuestFile') return {INSTANCE: file};
      assert.equal(name, 'net.darkhax.gamestages.GameStageHelper');
      return {hasStage(player, stage) { return player.nativeStages.has(stage); }};
    }},
    JsonIO: {readString() { return JSON.stringify(rules); }},
    Item: {of(id, count = 1) { return new Stack(id, count); }},
    ServerEvents: {commandRegistry(cb) { cb({commands: {literal() { return chain; }}, register() {}}); }},
    PlayerEvents: {loggedIn(cb) { loginHandler = cb; }, tick() {}}
  });
  for (const name of ['00_core.js', '20_progression.js']) vm.runInContext(fs.readFileSync(path.join(scripts, name), 'utf8'), context);
  function player(name, team) {
    const slots = Array.from({length: 36}, () => new Stack('minecraft:air', 0));
    const data = new Map();
    const p = {username: name, team, server, blockX: 0, blockY: 64, blockZ: 0,
      level: {getBlock() { return {id: 'minecraft:crafting_table'}; }},
      isServerPlayer() { return true; }, isFake() { return false; },
      getInventory() { return {getStackInSlot(i) { return slots[i]; }, setStackInSlot(i, stack) {
        if (fault) { fault = false; throw new Error('simulated inventory failure'); }
        slots[i] = stack;
      }}; },
      persistentData: {getString(k) { return data.get(k) || ''; }, putString(k, v) { data.set(k, v); }},
      containerMenu: {broadcastChanges() {}}, tell() {}, slots, nativeStages: new Set()
    };
    players.push(p); loginHandler({player: p}); return p;
  }
  function supply(p, e) {
    p.slots.fill(null);
    for (let i = 0; i < 36; i++) p.slots[i] = new Stack('minecraft:air', 0);
    Object.entries(e.cost).forEach(([id, count], i) => { p.slots[i] = new Stack(id, count); });
  }
  return {context, player, supply, commands, nbt, setFault() { fault = true; }, setProofs(v) { allProofs = v; }};
}

test('real bridge logic completes all 48 epochs, persists them, and syncs named teammates', () => {
  const b = bridge(), p = b.player('Alice', 'A'), mate = b.player('Bob', 'A'), outsider = b.player('Eve', 'B');
  rules.epochs.forEach(e => { b.supply(p, e); assert.equal(b.context.aia2Forge(p), 1); });
  assert.equal(b.context.aia2Completed(p), 48);
  assert.equal(b.context.aia2Completed(mate), 48);
  assert.equal(b.context.aia2Completed(outsider), 0);
  assert.ok(b.commands.includes('advancement grant Bob only aia2:keys/e48'));
  assert.equal(b.commands.some(c => c.includes('@p')), false);
  assert.throws(() => b.context.aia2Forge(p), /48 епох/);
});
test('bridge refuses incomplete FTB evidence and rolls inventory back on commit failure', () => {
  const b = bridge(), p = b.player('Alice', 'A'); b.supply(p, rules.epochs[0]);
  const before = JSON.stringify(p.slots);
  b.setProofs(false); assert.throws(() => b.context.aia2Forge(p), /шість/);
  assert.equal(JSON.stringify(p.slots), before);
  b.setProofs(true); b.setFault(); assert.throws(() => b.context.aia2Forge(p), /simulated/);
  assert.equal(JSON.stringify(p.slots), before);
  assert.equal(b.context.aia2Completed(p), 0);
});
test('paid recovery restores only the last legitimate key without advancing the campaign', () => {
  const b = bridge(), p = b.player('Alice', 'A');
  assert.throws(() => b.context.aia2Forge(p, true), /немає/);
  b.supply(p, rules.epochs[0]); b.context.aia2Forge(p);
  b.supply(p, rules.epochs[1]); b.context.aia2Forge(p);
  const e = rules.epochs[1];
  assert.throws(() => b.context.aia2Forge(p, true), /уже є/);
  const recovery = {cost: Object.fromEntries(Object.entries(e.cost).filter(([id]) => !id.includes('epoch_key_')))};
  recovery.cost['minecraft:crafting_table'] = 1;
  b.supply(p, recovery); // simulate lost key, pay all native materials again
  assert.equal(b.context.aia2Forge(p, true), 1);
  assert.equal(b.context.aia2Completed(p), 2);
  assert.equal(p.slots.filter(s => s.id === e.key && s.count).length, 1);
});
test('server bridge rejects fake players and missing workbench', () => {
  const b = bridge(), p = b.player('Alice', 'A'); b.supply(p, rules.epochs[0]);
  p.isFake = () => true; assert.throws(() => b.context.aia2Forge(p), /справжній/);
  p.isFake = () => false; p.level.getBlock = () => ({id: 'minecraft:stone'});
  assert.throws(() => b.context.aia2Forge(p), /верстака/);
});
test('ProjectE remap hook replaces all inherited EMC with the finite whitelist', () => {
  const whitelist = JSON.parse(fs.readFileSync(path.join(root, 'kubejs/config/aia2_emc_whitelist.json')));
  const callbacks = new Map(); let actual;
  class LongMap extends Map { put(key, value) { this.set(key, value); } }
  const context = vm.createContext({console, global: {AIA2: {canAccess() { return true; }}},
    JsonIO: {readString() { return JSON.stringify(whitelist); }},
    Item: {of(id) { return {id, isEmpty() { return false; }}; }},
    NativeEvents: {onEvent(type, cb) { callbacks.set(type, cb); }},
    Java: {loadClass(name) {
      if (name.endsWith('EMCMappingHandler')) return {updateEmcValues(map) { actual = map; }};
      if (name.endsWith('ItemInfo')) return {fromStack(item) { return item.id; }};
      if (name.endsWith('Object2LongOpenHashMap')) return LongMap;
      return name;
    }}
  });
  vm.runInContext(fs.readFileSync(path.join(scripts, '35_projecte.js'), 'utf8'), context);
  callbacks.get('moze_intel.projecte.api.event.EMCRemapEvent')();
  assert.equal(actual.size, 14);
  assert.equal(actual.has('mekanism:pellet_antimatter'), false);
  assert.equal(actual.has('kubejs:aia2_epoch_key_01'), false);
  const callback = callbacks.get('moze_intel.projecte.api.event.PlayerAttemptLearnEvent');
  let canceled = false;
  callback({getReducedInfo() { return {createStack() { return {id: 'avaritia:infinity_ingot'}; }, hasModifiedComponents() { return false; }}; }, getPlayer() { return {}; }, setCanceled(v) { canceled = v; }});
  assert.equal(canceled, true);
});

test('required machine guard refuses key forging before spending when adapter is unavailable', () => {
  const b = bridge(), p = b.player('Alice', 'A'); b.supply(p, rules.epochs[0]);
  const before = JSON.stringify(p.slots);
  const previous = b.context.AIA2Rules.machineGuard.mode;
  try {
    b.context.AIA2Rules.machineGuard.mode = 'required';
    b.context.global.AIA2Machines = {isReady() { return false; }};
    assert.throws(() => b.context.aia2Forge(p), /захист машин не готовий/);
    assert.equal(JSON.stringify(p.slots), before);
    assert.equal(b.context.aia2Completed(p), 0);
    assert.equal(b.context.global.AIA2.canAccess(p, 2), false);
  } finally { b.context.AIA2Rules.machineGuard.mode = previous; }
});

test('damaged ledger denies staged access rather than escaping a cancellable event', () => {
  const b = bridge(), p = b.player('Alice', 'A');
  b.nbt.set('aia2_runtime_v1', JSON.stringify({schema: 1, teams: {A: {completed: 99}}}));
  assert.equal(b.context.global.AIA2.canAccess(p, 40), false);
  assert.match(b.nbt.get('aia2_runtime_v1'), /99/, 'Never reset corrupted state automatically');
});

test('native stages gate access and key forging even though command success returns zero', () => {
  const b = bridge(), p = b.player('Alice', 'A');
  assert.equal(p.nativeStages.has('aia2_epoch_01'), true);
  assert.equal(b.context.global.AIA2.canAccess(p, 1), true);
  b.supply(p, rules.epochs[0]);
  const before = JSON.stringify(p.slots);
  p.nativeStages.delete('aia2_epoch_01');
  assert.equal(b.context.global.AIA2.canAccess(p, 1), false);
  assert.throws(() => b.context.aia2Forge(p), /Відсутня стадія/);
  assert.equal(JSON.stringify(p.slots), before);
  b.context.aia2Sync(p);
  assert.equal(b.context.aia2Forge(p), 1);
  assert.equal(p.nativeStages.has('aia2_epoch_02'), true);
  assert.ok(b.commands.includes('advancement grant Alice only aia2:stages/e02'));
});

test('a gifted future stage cannot bypass the ledger; team change revokes stage proofs', () => {
  const b = bridge(), p = b.player('Alice', 'A');
  p.nativeStages.add('aia2_epoch_40');
  assert.equal(b.context.global.AIA2.canAccess(p, 40), false);
  b.context.aia2Sync(p);
  assert.equal(p.nativeStages.has('aia2_epoch_40'), false);
  b.supply(p, rules.epochs[0]); b.context.aia2Forge(p);
  p.team = 'NewTeam';
  assert.equal(b.context.global.AIA2.canAccess(p, 2), false);
  b.context.aia2Sync(p);
  assert.equal(p.nativeStages.has('aia2_epoch_02'), false);
  assert.ok(b.commands.includes('advancement revoke Alice only aia2:stages/e02'));
  assert.equal(b.context.aia2Completed(p), 0);
});
