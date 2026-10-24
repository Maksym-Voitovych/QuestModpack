// The real script executes in a host fixture; this is not a Minecraft event test.
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const root = path.resolve(__dirname, '..');
const source = fs.readFileSync(path.join(root, 'kubejs/server_scripts/aia2/40_mechanics.js'), 'utf8');
const config = JSON.parse(fs.readFileSync(path.join(root, 'kubejs/config/aia2_mechanics.json')));

function fixture(customConfig = config) {
  const callbacks = {}, commands = [], errors = [], calls = [];
  const proofs = new Set();
  let guardReady = false, configured = false, configureError = null, lookupError = null, proofError = null;
  const bridge = {
    configureJson(value) {
      calls.push('configure');
      if (configureError) throw configureError;
      assert.deepEqual(JSON.parse(value), customConfig.rules);
      configured = true;
    },
    isConfigured() { return configured; },
    hasProof(server, team, id) {
      calls.push('proof:' + team + ':' + id);
      if (proofError) throw proofError;
      return proofs.has(team + ':' + id);
    },
    clearRuntime() { calls.push('clear'); configured = false; }
  };
  const server = {runCommandSilent(command) { commands.push(command); return 0; }};
  const player = {username: 'Alice', team: 'team-a', completed: 23, tickCount: 40, server,
    inventory: [], isServerPlayer() { return true; }, isFake() { return false; }};
  const aliases = {AIA2: {
    teamId(p) { if (lookupError) throw lookupError; return p.team; },
    completed(p) { if (lookupError) throw lookupError; return p.completed; }
  }, AIA2Machines: {isReady() { return guardReady; }}};
  const context = vm.createContext({global: new Proxy(aliases, {
    set() { throw new Error('KubeJS server global map is read-only'); },
    deleteProperty() { throw new Error('KubeJS server global map is read-only'); }
  }), globalThis: undefined,
    Java: {loadClass(name) { assert.equal(name, 'ua.aia2.guard.ProductionMilestoneBridge'); return bridge; }},
    JsonIO: {readString(filename) { assert.equal(filename, 'kubejs/config/aia2_mechanics.json'); return JSON.stringify(customConfig); }},
    console: {error(value) { errors.push(String(value)); }},
    ServerEvents: {tick(cb) { callbacks.serverTick = cb; }, unloaded(cb) { callbacks.unloaded = cb; }},
    PlayerEvents: {loggedIn(cb) { callbacks.login = cb; }, tick(cb) { callbacks.playerTick = cb; }}
  });
  const result = {context, aliases, callbacks, commands, errors, calls, bridge, server, player, proofs,
    ready(value = true) { guardReady = value; },
    resetNative() { configured = false; },
    failConfigure(error) { configureError = error; },
    failLookup(error) { lookupError = error; },
    failProof(error) { proofError = error; },
    reload() { vm.runInContext(source, context, {filename: '40_mechanics.js'}); },
    sync(p = player) { return aliases.AIA2.syncMechanics(p); }
  };
  result.reload();
  return result;
}

const grants = b => b.commands.filter(command => command.startsWith('advancement grant '));
const revokes = b => b.commands.filter(command => command.startsWith('advancement revoke '));

test('mechanics config waits for native guard and installs through the startup-created member', () => {
  const b = fixture();
  assert.equal(typeof b.aliases.AIA2.syncMechanics, 'function');
  assert.equal(b.context.globalThis, undefined);
  b.sync();
  assert.equal(b.calls.includes('configure'), false);
  assert.equal(grants(b).length, 0);
  assert.equal(revokes(b).length, 4);
  b.ready(); b.sync();
  assert.equal(b.calls.filter(call => call === 'configure').length, 1);
  assert.equal(grants(b).length, 0, 'Configuration itself is not evidence of production');
});

test('native receipts are scoped by team and current epoch; item possession never supplies one', () => {
  const b = fixture(); b.ready();
  b.player.completed = 3;
  b.player.inventory = config.rules.map(rule => ({id: rule.output, count: 64}));
  b.sync();
  assert.equal(grants(b).length, 0);
  for (const rule of config.rules) b.proofs.add('team-a:' + rule.id);
  b.sync();
  assert.deepEqual(grants(b), ['advancement grant Alice only aia2:mechanics/andesite_mixing']);
  b.player.completed = 9; b.sync();
  assert.equal(grants(b).length, 2);
  assert.equal(grants(b)[1], 'advancement grant Alice only aia2:mechanics/brass_mixing');
  assert.equal(b.calls.some(call => call.includes('infused_alloy')), false, 'Future proof queries remain bounded by the current epoch');
});

test('an immediate core team sync revokes old-team manufacturing projections', () => {
  const b = fixture(); b.ready();
  for (const rule of config.rules) b.proofs.add('team-a:' + rule.id);
  b.sync(); assert.equal(grants(b).length, 4);
  b.commands.length = 0; b.player.team = 'team-b'; b.sync();
  assert.equal(grants(b).length, 0);
  assert.equal(revokes(b).length, 4);
  b.player.team = 'team-a'; b.sync();
  assert.equal(grants(b).length, 4, 'Returning to the original team restores its original durable evidence');
});

test('unchanged receipt polling caches advancement commands and avoids repeated configuration', () => {
  const b = fixture(); b.ready(); b.proofs.add('team-a:infused_alloy'); b.sync();
  b.commands.length = 0;
  for (let i = 0; i < 100; i++) b.sync();
  assert.equal(b.commands.length, 0);
  assert.equal(b.calls.filter(call => call === 'configure').length, 1);
  b.player.tickCount = 41; b.callbacks.playerTick({player: b.player});
  assert.equal(b.commands.length, 0);
});

test('malformed schema or native configuration failure stays closed and reports each error once', () => {
  for (const failure of ['schema', 'native']) {
    const b = fixture(failure === 'schema' ? {...config, schema: 2} : config);
    b.ready();
    if (failure === 'native') b.failConfigure(new Error('native fixture configuration failed'));
    b.sync(); b.sync();
    assert.equal(grants(b).length, 0);
    assert.equal(revokes(b).length, 4);
    assert.equal(b.errors.length, 1);
    assert.match(b.errors[0], /закрито/);
  }
});

test('failed FTB lookup revokes all own projections and does not reset native team receipts', () => {
  const b = fixture(); b.ready();
  for (const rule of config.rules) b.proofs.add('team-a:' + rule.id);
  b.sync(); b.commands.length = 0;
  b.failLookup(new Error('FTB fixture not ready'));
  assert.throws(() => b.sync(), /FTB fixture not ready/);
  assert.equal(revokes(b).length, 4);
  assert.equal(b.proofs.size, 4);
  b.failLookup(null); b.sync();
  assert.equal(grants(b).length, 4);
});

test('runtime reset and script reload restore durable receipts through fresh native configuration', () => {
  const b = fixture(); b.ready(); b.proofs.add('team-a:andesite_mixing'); b.sync();
  b.resetNative(); b.sync();
  assert.equal(b.calls.filter(call => call === 'configure').length, 2);
  const alias = b.aliases.AIA2;
  b.reload(); b.commands.length = 0; b.sync();
  assert.equal(b.aliases.AIA2, alias, 'Server reload must not replace a top-level global entry');
  assert.deepEqual(grants(b), ['advancement grant Alice only aia2:mechanics/andesite_mixing']);
  assert.equal(b.proofs.size, 1);
  b.callbacks.unloaded();
  assert.equal(b.bridge.isConfigured(), false);
  assert.equal(b.proofs.size, 1, 'Runtime cleanup never deletes authoritative world receipts');
});

test('fake players cannot query native receipts or project advancement rewards', () => {
  const b = fixture(); b.ready(); b.player.isFake = () => true;
  b.sync(); b.callbacks.login({player: b.player}); b.callbacks.playerTick({player: b.player});
  assert.equal(b.commands.length, 0);
  assert.equal(b.calls.length, 0);
});

test('native receipt errors during a team change revoke old-team projections before surfacing failure', () => {
  const b = fixture(); b.ready();
  for (const rule of config.rules) b.proofs.add('team-a:' + rule.id);
  b.sync(); b.commands.length = 0;
  b.player.team = 'team-b'; b.failProof(new Error('native fixture receipt storage failed'));
  assert.throws(() => b.sync(), /native fixture receipt storage failed/);
  assert.equal(revokes(b).length, 4, 'An unavailable native ledger must never retain another team’s projected proof');
  assert.equal(grants(b).length, 0);
});
