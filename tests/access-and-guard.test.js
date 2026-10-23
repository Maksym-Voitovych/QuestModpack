// Integration contracts exercised against the actual KubeJS scripts.
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const root = path.resolve(__dirname, '..');
const scripts = path.join(root, 'kubejs/server_scripts/aia2');
const rules = JSON.parse(fs.readFileSync(path.join(root, 'kubejs/config/aia2_runtime.json')));
const load = (ctx, file) => vm.runInContext(fs.readFileSync(path.join(scripts, file), 'utf8'), ctx);
function readonlyGlobal(context) {
  context.global = new Proxy(context.global, {
    set() { throw new Error("'global' cannot be assigned to in client or server scripts"); },
    deleteProperty() { throw new Error("'global' cannot be assigned to in client or server scripts"); }
  });
  context.globalThis = undefined;
}

test('transformed blocks without item forms retain independent stage checks', () => {
  assert.equal(Object.keys(rules.blockGates).length, 16003);
  const blocks = {}, native = {};
  let completed = 0;
  const c = vm.createContext({global: {AIA2: {rules,
    canAccess(p, stage) { return p && !p.fake && stage <= completed + 1; }}},
    BlockEvents: Object.fromEntries(['placed', 'rightClicked', 'broken'].map(k => [k, cb => blocks[k] = cb])),
    ItemEvents: {rightClicked() {}, entityInteracted() {}},
    NativeEvents: {onEvent(cls, cb) { native[cls] = cb; }}, Java: {loadClass: x => x}
  });
  readonlyGlobal(c);
  load(c, '30_access.js');
  const p = {isServerPlayer() { return true; }, tickCount: 1};
  for (const id of ['bigreactors:energizerpowerportfe', 'tfmg:encased_steel_pipe']) {
    assert.equal(rules.itemGates[id], undefined, 'Regression must exercise a non-item block');
    assert.ok(rules.blockGates[id] > 1);
    let cancelled = false;
    const e = {player: p, block: {id}, cancel() { cancelled = true; }};
    blocks.broken(e); assert.equal(cancelled, true);
    completed = rules.blockGates[id] - 1;
    cancelled = false; blocks.broken(e); assert.equal(cancelled, false);
    completed = 0;
  }
  assert.equal(c.aia2BlockStage('unreviewed_mod:machine'), 100);
  assert.equal(c.aia2BlockStage('minecraft:air'), 0);
});

test('native melee event rejects a locked weapon before damage', () => {
  const native = {};
  let allowed = false;
  const c = vm.createContext({global: {AIA2: {rules, canAccess() { return allowed; }}},
    BlockEvents: {placed() {}, rightClicked() {}, broken() {}},
    ItemEvents: {rightClicked() {}, entityInteracted() {}},
    NativeEvents: {onEvent(cls, cb) { native[cls] = cb; }}, Java: {loadClass: x => x}});
  readonlyGlobal(c);
  load(c, '30_access.js');
  const attack = native['net.neoforged.neoforge.event.entity.player.AttackEntityEvent'];
  assert.equal(typeof attack, 'function');
  let cancelled = false;
  const e = {getEntity() { return {getMainHandItem() { return {id: 'draconicevolution:draconic_sword'}; }}; },
    setCanceled(v) { cancelled = v; }};
  attack(e); assert.equal(cancelled, true);
  allowed = true; cancelled = false; attack(e); assert.equal(cancelled, false);
});

function machines(installed = true) {
  const callbacks = {}, teamProgress = new Map(), playerTeams = new Map(), logs = [], calls = [];
  const server = {getPlayerList: () => ({getPlayers: () => []})};
  let ready = true, ledger = {schema: 1, teams: {offline: {completed: 17}, online: {completed: 2}}};
  const guard = {
    clearRuntime() { ready = false; teamProgress.clear(); calls.push('clear'); },
    setRulesJson(s) { assert.equal(Object.keys(JSON.parse(s)).length, 16003); calls.push('rules'); },
    setItemRulesJson(s) { assert.ok(Object.keys(JSON.parse(s)).length > 20000); },
    setRecipeRulesJson(s) { assert.ok(Object.keys(JSON.parse(s)).length > 40000); },
    setPlayerTeam(id, team) { playerTeams.set(id, team); },
    setTeamProgress(id, n) { teamProgress.set(id, n); }, setReady() { ready = true; }, isReady() { return ready; },
    getOwner(be) { return be.owner || ''; }, setOwner(be, team) { be.owner = team; calls.push('claim'); }
  };
  const c = vm.createContext({global: {AIA2: {rules,
    ledger() { if (ledger instanceof Error) throw ledger; return ledger; },
    teamId: p => p.team, completed: p => p.completed,
    canAccess: (p, stage) => !p.fake && stage <= p.completed + 1}, AIA2Machines: {}},
    Platform: {isLoaded(id) { assert.equal(id, 'aia2_machine_guard'); return installed; }},
    Java: {loadClass(id) { assert.equal(id, 'ua.aia2.guard.Aia2MachineGuard'); return guard; }},
    console: {warn: x => logs.push(x), error: x => logs.push(x)},
    ServerEvents: Object.fromEntries(['loaded', 'tick', 'unloaded'].map(k => [k, cb => callbacks[k] = cb]))});
  readonlyGlobal(c);
  load(c, '25_machine_guard.js');
  return {c, guard, callbacks, server, teamProgress, playerTeams, calls, logs, setLedger(v) { ledger = v; }};
}

test('guard reload invalidates stale readiness then restores every team, including offline', () => {
  const b = machines();
  assert.equal(b.guard.isReady(), false);
  b.callbacks.loaded({server: b.server});
  assert.equal(b.c.global.AIA2Machines.isReady(), true);
  assert.equal(b.teamProgress.get('offline'), 17);
  assert.equal(b.teamProgress.get('online'), 2);
  b.c.global.AIA2Machines.syncPlayer({team: 'online', completed: 3, isServerPlayer: () => true, isFake: () => false, getUUID: () => 'uuid-Alice'});
  assert.equal(b.teamProgress.get('online'), 3);
  assert.equal(b.playerTeams.get('uuid-Alice'), 'online');
  b.callbacks.unloaded();
  assert.equal(b.guard.isReady(), false);
});

test('missing JAR is reported and never represented as an active guard', () => {
  const b = machines(false);
  b.callbacks.loaded({server: b.server});
  assert.equal(b.c.global.AIA2Machines.isReady(), false);
  assert.match(b.c.global.AIA2Machines.status(), /не активний/);
  assert.match(b.logs[0], /JAR/);
});

test('machine claim requires authorization, real player and unowned block entity', () => {
  const b = machines(); b.callbacks.loaded({server: b.server});
  const api = b.c.global.AIA2Machines;
  const be = {};
  const block = {id: 'create:mechanical_press', getEntity: () => be};
  const p = {team: 'online', completed: 3, getUUID() { return 'uuid-Alice'; }, isServerPlayer() { return true; }, isFake() { return false; }};
  api.claim({...p, completed: 0}, block); assert.equal(be.owner, undefined);
  api.claim({...p, isFake() { return true; }}, block); assert.equal(be.owner, undefined);
  api.claim(null, block); assert.equal(be.owner, undefined);
  api.claim(p, block); assert.equal(be.owner, 'online');
  api.claim({...p, team: 'visitor', completed: 48}, block); assert.equal(be.owner, 'online');
  assert.equal(b.calls.filter(x => x === 'claim').length, 1);
});

test('corrupt ledger leaves machine guard closed and avoids retry storms', () => {
  const b = machines(); b.setLedger(new Error('corrupt journal'));
  b.callbacks.loaded({server: b.server});
  assert.equal(b.guard.isReady(), false);
  const count = b.calls.length;
  for (let i = 0; i < 200; i++) b.callbacks.tick({server: b.server});
  assert.equal(b.calls.length, count);
  assert.match(b.logs[0], /corrupt journal/);
});

test('Create milestones require all four process proofs alongside deliveries', () => {
  const proofByEpoch = new Map([[2, [[2, ['create:water_wheel']]]],
    [4, [[1, ['create:mechanical_press']], [2, ['create:millstone', 'create:mechanical_mixer']]]]]);
  let count = 0;
  for (const [epoch, milestones] of proofByEpoch) {
    const chapter = JSON.parse(fs.readFileSync(path.join(root,
      'config/ftbquests/quests/chapters/aia2_epoch_' + String(epoch).padStart(2, '0') + '.snbt')));
    for (const [index, ids] of milestones) {
      const q = chapter.quests[index - 1];
      assert.ok(q.tasks.some(t => t.type === 'item'), 'Keep the material milestone too');
      assert.notEqual(q.min_required_tasks, 1, 'Must not turn the proofs into OR');
      assert.deepEqual(q.tasks.filter(t => t.type === 'advancement').map(t => t.advancement),
        ['aia2:stages/e' + String(epoch).padStart(2, '0'), ...ids]);
      count += ids.length;
    }
  }
  assert.equal(count, 4);
});
