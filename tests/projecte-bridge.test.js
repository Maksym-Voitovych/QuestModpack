const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const root = path.resolve(__dirname, '..');
const source = fs.readFileSync(path.join(root, 'kubejs/server_scripts/aia2/35_projecte.js'), 'utf8');
const whitelist = fs.readFileSync(path.join(root, 'kubejs/config/aia2_emc_whitelist.json'), 'utf8');
function setup({missingBridge = false, config = whitelist} = {}) {
  const callbacks = new Map(), logs = [], mapped = [];
  class LongMap extends Map {}
  const context = vm.createContext({global: {AIA2: {canAccess() { return true; }}},
    JsonIO: {readString() { return config; }},
    Item: {of(id) { return {id, isEmpty() { return false; }}; }},
    NativeEvents: {onEvent(name, cb) { callbacks.set(name, cb); }},
    console: {info: m => logs.push(m), error: m => logs.push(m)},
    Java: {loadClass(name) {
      if (name.endsWith('EMCMappingHandler')) return {updateEmcValues(map) { mapped.push(map); }};
      if (name.endsWith('ItemInfo')) return {fromStack(stack) { return stack.id; }};
      if (name.endsWith('Object2LongOpenHashMap')) return LongMap;
      if (name.endsWith('RhinoLongMapBridge')) {
        if (missingBridge) throw new Error('Class not found: RhinoLongMapBridge');
        return {putValue(map, key, value) { assert.ok(Number.isSafeInteger(value) && value > 0); map.set(key, value); }};
      }
      return name;
    }}});
  vm.runInContext(source, context);
  return {callbacks, mapped, logs, context,
    remap() { return callbacks.get('moze_intel.projecte.api.event.EMCRemapEvent')(); },
    request(id = 'minecraft:gold_ingot') {
      let canceled = false;
      callbacks.get('moze_intel.projecte.api.event.PlayerAttemptLearnEvent')({
        getReducedInfo() { return {createStack() { return {id}; }, hasModifiedComponents() { return false; }}; },
        getPlayer() { return {}; }, setCanceled(v) { canceled = v; }});
      return canceled;
    }};
}

test('ProjectE rejects learning until a complete primitive-long whitelist is installed', () => {
  const b = setup();
  assert.equal(b.request(), true);
  b.remap();
  assert.equal(b.mapped.at(-1).size, 14);
  assert.equal(b.mapped.at(-1).get('minecraft:gold_ingot'), 2048);
  assert.equal(b.request(), false);
  assert.equal(b.request('kubejs:aia2_epoch_key_48'), true);
});

test('missing native bridge still registers protections and replaces inherited EMC with an empty map', () => {
  const b = setup({missingBridge: true});
  assert.throws(() => b.remap(), /Class not found/);
  assert.equal(b.mapped.at(-1).size, 0);
  assert.equal(b.request(), true);
  assert.match(b.logs.join('\n'), /EMC закрито/);
});

test('malformed or invalid whitelist cannot retain a partial or inherited EMC map', () => {
  for (const config of ['{malformed', '[]', '{"minecraft:stone":1,"minecraft:gold_ingot":-1}', '{"minecraft:gold_ingot":1.5}']) {
    const b = setup({config});
    assert.throws(() => b.remap());
    assert.equal(b.mapped.at(-1).size, 0);
    assert.equal(b.request(), true);
  }
});
