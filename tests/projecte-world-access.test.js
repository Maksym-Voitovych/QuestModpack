// Production BlockEvents.broken must reject imported tools before vanilla mineBlock/AOE.
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const root = path.resolve(__dirname, '..');
const rules = JSON.parse(fs.readFileSync(path.join(root, 'kubejs/config/aia2_runtime.json')));
const script = fs.readFileSync(path.join(root, 'kubejs/server_scripts/aia2/30_access.js'), 'utf8');
function environment() {
  const handlers = {};
  const context = vm.createContext({
    global: {AIA2: {rules, canAccess(player, stage) { return player && !player.fake && player.live === player.synced && stage <= player.completed + 1; }}},
    BlockEvents: Object.fromEntries(['placed', 'rightClicked', 'broken'].map(name => [name, action => handlers[name] = action])),
    ItemEvents: {rightClicked() {}, entityInteracted() {}},
    NativeEvents: {onEvent() {}}, Java: {loadClass: value => value}
  });
  context.global = new Proxy(context.global, {set() { throw new Error('Readonly KubeJS global'); }});
  context.globalThis = undefined;
  vm.runInContext(script, context);
  return handlers;
}
function player(completed, tool, extra = {}) {
  return {completed, live: 'a', synced: 'a', fake: false, tickCount: 1,
    isServerPlayer() { return true; }, getMainHandItem() { return {id: tool}; }, ...extra};
}
function broken(handlers, actor, block = 'minecraft:stone') {
  let canceled = false;
  handlers.broken({player: actor, block: {id: block}, cancel() { canceled = true; }});
  return canceled;
}

test('future ProjectE mining tool cannot trigger normal mineBlock through an early vanilla block', () => {
  const handlers = environment();
  const tool = 'projecte:rm_pick';
  assert.ok(rules.itemGates[tool] > 1, 'Must exercise an installed stage-gated tool');
  assert.equal(broken(handlers, player(0, tool)), true);
  assert.equal(broken(handlers, player(rules.itemGates[tool] - 1, tool)), false);
});

test('break policy uses the higher of actual block and actual mainhand item floors', () => {
  const handlers = environment();
  const tool = 'projecte:rm_pick';
  const block = 'draconicevolution:energy_core';
  assert.ok(rules.blockGates[block] > 1);
  const required = Math.max(rules.itemGates[tool], rules.blockGates[block]);
  assert.equal(broken(handlers, player(required - 2, tool), block), true);
  assert.equal(broken(handlers, player(required - 1, tool), block), false);
  assert.equal(broken(handlers, player(0, 'minecraft:wooden_pickaxe')), false);
  assert.equal(broken(handlers, player(0, 'minecraft:air')), false);
});

test('imported tool denies fake players, stale teams and unclassified modded stacks', () => {
  const handlers = environment();
  assert.equal(broken(handlers, player(48, 'projecte:rm_pick', {fake: true})), true);
  assert.equal(broken(handlers, player(48, 'projecte:rm_pick', {live: 'other'})), true);
  assert.equal(broken(handlers, player(48, 'unknown_addon:unreviewed_tool')), true);
});
