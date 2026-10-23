// Run: node --test tests/runtime.test.js
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const root = path.resolve(__dirname, '..');
const scripts = path.join(root, 'kubejs/server_scripts/aia2');
const startup = path.join(root, 'kubejs/startup_scripts/aia2/00_shared_state.js');

function readonlyGlobal(context) {
  context.global = new Proxy(context.global, {
    set() { throw new Error("'global' cannot be assigned to in client or server scripts"); },
    deleteProperty() { throw new Error("'global' cannot be assigned to in client or server scripts"); }
  });
  context.globalThis = undefined;
}
function bootstrap(context) {
  vm.runInContext(fs.readFileSync(startup, 'utf8'), context);
  readonlyGlobal(context);
}

const rules = JSON.parse(fs.readFileSync(path.join(root, 'kubejs/config/aia2_runtime.json')));
const recipes = JSON.parse(fs.readFileSync(path.join(root, 'kubejs/config/aia2_recipes.json')));

function core() {
  const context = vm.createContext({global: {}});
  bootstrap(context);
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
test('recipe handler installs every audited recipe, uses Create addon, and exposes no ungated key recipe', () => {
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
  assert.equal(added.length, recipes.add.length);
  assert.equal(new Set(added.map(r => r.id)).size, recipes.add.length);
  assert.equal(createCalls, recipes.add.filter(r => r.json.type === 'create:mixing').length);
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
  const deniedQuests = new Set();
  const file = {
    getQuest(id) { return {id}; },
    getOrCreateTeamData(player) { return {
      getTeamId() { return player.team; },
      isCompleted(quest) { return allProofs && !deniedQuests.has(quest.id); },
      getOnlineMembers() { return players.filter(p => p.team === player.team); }
    }; }
  };
  const chain = {executes() { return this; }, then() { return this; }};
  const context = vm.createContext({global: {}, console,
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
  bootstrap(context);
  vm.runInContext(fs.readFileSync(path.join(scripts, '00_core.js'), 'utf8'), context);
  Object.assign(context.global.AIA2Machines, {isReady() { return true; }, syncPlayer() {}});
  vm.runInContext(fs.readFileSync(path.join(scripts, '20_progression.js'), 'utf8'), context);
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
  return {context, player, supply, commands, nbt, deniedQuests, setFault() { fault = true; }, setProofs(v) { allProofs = v; }};
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
  b.setProofs(false); assert.throws(() => b.context.aia2Forge(p), /шість|підсумкове випробування/);
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
  readonlyGlobal(context);
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
    b.context.global.AIA2Machines.isReady = function () { return false; };
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


test('server scripts use startup-created containers with a read-only global map', () => {
  const b = bridge();
  assert.throws(() => vm.runInContext('global.AIA2 = {};', b.context), /cannot be assigned/);
  assert.equal(b.context.globalThis, undefined);
  assert.equal(typeof b.context.global.AIA2Core.prepareKey, 'function');
  assert.equal(typeof b.context.global.AIA2.completed, 'function');
});

test('server reload keeps alias identities and saved team progress while replacing old closures', () => {
  const b = bridge(), p = b.player('Alice', 'A');
  b.supply(p, rules.epochs[0]); b.context.aia2Forge(p);
  const coreAlias = b.context.global.AIA2Core, apiAlias = b.context.global.AIA2;
  const machinesAlias = b.context.global.AIA2Machines;
  apiAlias.obsolete = true;
  vm.runInContext(fs.readFileSync(path.join(scripts, '00_core.js'), 'utf8'), b.context);
  Object.assign(machinesAlias, {isReady() { return true; }, syncPlayer() {}});
  vm.runInContext(fs.readFileSync(path.join(scripts, '20_progression.js'), 'utf8'), b.context);
  assert.equal(b.context.global.AIA2Core, coreAlias);
  assert.equal(b.context.global.AIA2, apiAlias);
  assert.equal(b.context.global.AIA2Machines, machinesAlias);
  assert.equal(apiAlias.obsolete, undefined);
  assert.equal(b.context.aia2Completed(p), 1);
  b.supply(p, rules.epochs[1]); b.context.aia2Forge(p);
  assert.equal(b.context.aia2Completed(p), 2);
});

test('missing startup bootstrap fails with an actionable restart error', () => {
  const context = vm.createContext({global: {}});
  readonlyGlobal(context);
  assert.throws(() => vm.runInContext(fs.readFileSync(path.join(scripts, '00_core.js'), 'utf8'), context),
    /startup bootstrap.*повністю перезапустіть/);
});

test('new required branch proof blocks only a new key and never spends ingredients', () => {
  const b = bridge(), p = b.player('Alice', 'A');
  const first = b.context.AIA2Rules.epochs[0];
  const previous = first.requiredQuestIds;
  first.requiredQuestIds = ['0000000000000042'];
  b.deniedQuests.add(66);
  b.supply(p, first);
  const before = JSON.stringify(p.slots);
  assert.throws(() => b.context.aia2Forge(p), /підсумкове випробування/);
  assert.equal(JSON.stringify(p.slots), before);
  assert.equal(b.context.aia2Completed(p), 0);
  b.deniedQuests.delete(66);
  b.context.aia2Forge(p);
  b.deniedQuests.add(66);
  const recovery = {cost: {...first.cost, 'minecraft:crafting_table': 1}};
  b.supply(p, recovery);
  assert.equal(b.context.aia2Forge(p, true), 1, 'Existing legal progress is not invalidated by new branches');
  assert.equal(b.context.aia2Completed(p), 1);
  first.requiredQuestIds = previous;
});

test('ledger cache validates changed serialized state and separates server identities', () => {
  const b = bridge(), p = b.player('Alice', 'A');
  const one = b.context.aia2State(p.server);
  assert.equal(b.context.aia2State(p.server), one);
  b.nbt.set('aia2_runtime_v1', JSON.stringify({schema: 1, teams: {A: {completed: 12}}}));
  assert.equal(b.context.aia2Completed(p), 12);
  assert.notEqual(b.context.aia2State(p.server), one);
  const other = {persistentData: {getString() { return ''; }}};
  assert.equal(Object.keys(b.context.aia2State(other).teams).length, 0);
  assert.equal(b.context.aia2Completed(p), 12);
});

test('all custom registrations have unique IDs, explicit models and real texture files', () => {
  const registered = new Map();
  const context = vm.createContext({StartupEvents: {registry(kind, callback) {
    assert.equal(kind, 'item');
    callback({create(id) {
      assert.equal(registered.has(id), false, 'Duplicate custom registration: ' + id);
      const record = {}; registered.set(id, record);
      const builder = {
        displayName(name) { record.name = name; return this; },
        maxStackSize(n) { record.stack = n; return this; },
        fireResistant() { return this; },
        texture(texture) { record.texture = texture; return this; }
      };
      return builder;
    }});
  }}});
  for (const file of ['00_epoch_keys.js', '10_components.js']) {
    vm.runInContext(fs.readFileSync(path.join(root, 'kubejs/startup_scripts/aia2', file), 'utf8'), context);
  }
  assert.equal(registered.size, 293);
  for (const [id, record] of registered) {
    assert.ok(record.name && record.texture && record.stack > 0, id);
    const [namespace, item] = id.split(':');
    const model = JSON.parse(fs.readFileSync(path.join(root, 'kubejs/assets', namespace, 'models/item', item + '.json')));
    assert.equal(model.textures.layer0, record.texture);
    const [textureNS, texture] = record.texture.split(':');
    assert.ok(fs.existsSync(path.join(root, 'kubejs/assets', textureNS, 'textures', texture + '.png')), record.texture);
    if (id.includes('epoch_key_')) assert.equal(record.stack, 1);
  }
});
