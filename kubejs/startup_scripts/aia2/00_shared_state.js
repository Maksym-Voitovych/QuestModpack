// priority: 10000
// KubeJS 2101 only permits top-level global writes in startup scripts.
// These stable object identities survive server-script reloads. No world data is stored here.
// Pure transactional logic. The same code is exercised by tests/runtime.test.js.
global.AIA2Core = (function () {
  function fail(message) { throw new Error('[AIA2] ' + message); }
  function validateState(state) {
    if (!state || state.schema !== 1 || !state.teams || typeof state.teams !== 'object' || Array.isArray(state.teams)) {
      fail('Несумісний журнал прогресії. Не скидайте його автоматично.');
    }
    Object.keys(state.teams).forEach(function (id) {
      if (!state.teams[id] || typeof state.teams[id] !== 'object' || Array.isArray(state.teams[id])) {
        fail('Пошкоджений запис команди ' + id);
      }
      var n = state.teams[id].completed;
      if (typeof n !== 'number' || n % 1 !== 0 || n < 0 || n > 48) fail('Пошкоджений стан команди ' + id);
      var pending = state.teams[id].pending;
      if (pending !== undefined && (typeof pending !== 'number' || pending % 1 !== 0 || pending !== n + 1 || pending > 48)) {
        fail('Пошкоджений незавершений перехід команди ' + id);
      }
    });
    return state;
  }
  function prepareKey(epoch, completed, questCompletion, slots) {
    if (!epoch || epoch.number !== completed + 1 || completed < 0 || completed >= 48) fail('Порушено порядок епох.');
    if (questCompletion.length !== 6 || !questCompletion.every(function (v) { return v === true; })) {
      fail('Спочатку завершіть усі шість обов’язкових завдань цієї епохи.');
    }
    var remaining = {};
    Object.keys(epoch.cost).forEach(function (id) {
      var count = epoch.cost[id];
      if (typeof count !== 'number' || count < 1 || count % 1 !== 0) fail('Некоректна формула ключа.');
      remaining[id] = count;
    });
    var result = slots.map(function (s) { return {id: s.id, count: s.count}; });
    var deductions = [];
    result.forEach(function (s, index) {
      var n = Math.min(s.count, remaining[s.id] || 0);
      if (n > 0) {
        s.count -= n;
        remaining[s.id] -= n;
        deductions.push({slot: index, count: n});
      }
    });
    var missing = Object.keys(remaining).filter(function (id) { return remaining[id] > 0; });
    if (missing.length) fail('Не вистачає: ' + missing.map(function (id) { return remaining[id] + ' × ' + id; }).join(', '));
    var outputSlot = -1;
    for (var i = 0; i < result.length; i++) {
      if (result[i].count === 0 || result[i].id === 'minecraft:air') { outputSlot = i; break; }
    }
    if (outputSlot < 0) fail('Звільніть один слот у головному інвентарі.');
    return {deductions: deductions, outputSlot: outputSlot, outputId: epoch.key, completed: epoch.number};
  }
  function mayAccess(required, completed) {
    if (!required) return true;
    if (required === 99) return completed === 48;
    return required >= 1 && required <= completed + 1;
  }
  return {validateState: validateState, prepareKey: prepareKey, mayAccess: mayAccess};
})();

// Server scripts update members of these containers; they never replace global entries.
global.AIA2 = {};
global.AIA2Machines = {};
