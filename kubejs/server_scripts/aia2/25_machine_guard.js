// API 4 is required. Initialization starts on the first server tick, after
// FTB Quests' SERVER_STARTED load; failed initialization always stays closed.
var AIA2MachineGuard = null;
var AIA2GuardQuestFile = null;
var aia2MachineReady = false;
var aia2GuardTick = 0;
var aia2GuardState = {phase: 'awaiting_tick', attempts: 0, nextAttempt: 1,
  retryable: true, lastError: '', version: 0, blockRules: 0, itemRules: 0, recipeRules: 0};
var aia2GuardMaxAttempts = 6;
try {
  if (Platform.isLoaded('aia2_machine_guard')) {
    AIA2MachineGuard = Java.loadClass('ua.aia2.guard.Aia2MachineGuard');
    AIA2GuardQuestFile = Java.loadClass('dev.ftb.mods.ftbquests.quest.ServerQuestFile');
    AIA2MachineGuard.clearRuntime();
  } else {
    aia2GuardState.phase = 'missing_jar';
    aia2GuardState.retryable = false;
    aia2GuardState.lastError = 'Не встановлено AIA2 Machine Guard JAR.';
    console.error('[AIA2] ' + aia2GuardState.lastError);
  }
} catch (aia2LoadFailure) {
  aia2GuardState.phase = 'class_loading';
  aia2GuardState.retryable = false;
  aia2GuardState.lastError = String(aia2LoadFailure);
  console.error('[AIA2] Machine Guard: помилка завантаження Java API: ' + aia2GuardState.lastError);
}

function aia2GuardTransient(message, cause) {
  var error = new Error(message + (cause ? ': ' + String(cause) : ''));
  error.aia2GuardTransient = true;
  return error;
}

function aia2MachineFailure(error, phase) {
  aia2MachineReady = false;
  try { if (AIA2MachineGuard) AIA2MachineGuard.clearRuntime(); }
  catch (clearError) { console.error('[AIA2] Machine Guard: не вдалося очистити Java-стан: ' + String(clearError)); }
  aia2GuardState.phase = phase || 'failed';
  aia2GuardState.lastError = String(error.message || error);
  aia2GuardState.retryable = !!error.aia2GuardTransient && aia2GuardState.attempts < aia2GuardMaxAttempts;
  aia2GuardState.nextAttempt = aia2GuardTick + Math.min(20 * Math.pow(2, Math.max(0, aia2GuardState.attempts - 1)), 200);
  console.error('[AIA2] Machine Guard зупинено [' + aia2GuardState.phase + ', спроба ' +
    aia2GuardState.attempts + '/' + aia2GuardMaxAttempts + ']: ' + aia2GuardState.lastError +
    (aia2GuardState.retryable ? '. Повторна перевірка буде автоматично.' : '. Усуньте причину та виконайте /aia2 guard retry або /reload.') +
    ' Захист залишається закритим.');
}

function aia2MirrorMachinePlayer(player) {
  if (!player || !player.isServerPlayer() || player.isFake()) return;
  var team;
  try { team = global.AIA2.teamId(player); }
  catch (error) { throw aia2GuardTransient('FTB-команда гравця ще не готова', error); }
  // Typed Java receives the real ServerPlayer and calls getUUID() internally.
  // KubeJS remaps that method to getUuid(); do not call its Mojang name in JS.
  AIA2MachineGuard.syncPlayer(player, team, global.AIA2.completed(player));
}

function aia2InitMachines(server) {
  if (!AIA2MachineGuard) return;
  aia2GuardState.attempts++;
  var phase = 'api_version';
  try {
    AIA2MachineGuard.clearRuntime();
    aia2GuardState.version = Number(AIA2MachineGuard.apiVersion());
    if (aia2GuardState.version !== 4) throw new Error('Потрібен Machine Guard API 4; встановіть JAR із поточного пакета.');
    phase = 'rules';
    var rules = global.AIA2.rules;
    if (!rules || !rules.epochs || rules.epochs.length !== 48) throw new Error('Відсутні правила всіх 48 епох.');
    ['blockGates', 'itemGates', 'recipeGates'].forEach(function (name) {
      if (!rules[name] || !Object.keys(rules[name]).length) throw new Error('Відсутня повна карта ' + name + '. Встановіть повний пакет оновлення.');
    });
    phase = 'ftb_readiness';
    var file = AIA2GuardQuestFile.INSTANCE;
    if (!file || !file.getQuest(parseInt(rules.epochs[0].finalQuestId, 16))) {
      throw aia2GuardTransient('FTB Quests ще не завантажив базову главу; перевірте SNBT, якщо помилка повторюється');
    }
    phase = 'ledger';
    var state = global.AIA2.ledger(server);
    phase = 'rules';
    AIA2MachineGuard.setRulesJson(JSON.stringify(rules.blockGates));
    AIA2MachineGuard.setItemRulesJson(JSON.stringify(rules.itemGates));
    AIA2MachineGuard.setRecipeRulesJson(JSON.stringify(rules.recipeGates));
    if (!rules.dualKeys || rules.dualKeys.length !== 96) throw new Error('Відсутні 96 правил подвійних ключів. Встановіть повний пакет оновлення.');
    AIA2MachineGuard.configureKeyRulesJson(JSON.stringify(rules.dualKeys));
    phase = 'team_progress';
    Object.keys(state.teams).forEach(function (team) {
      AIA2MachineGuard.setTeamProgress(team, state.teams[team].completed);
    });
    phase = 'player_sync';
    server.getPlayerList().getPlayers().forEach(function (player) { aia2MirrorMachinePlayer(player); });
    phase = 'native_ready';
    AIA2MachineGuard.setReady();
    if (!AIA2MachineGuard.isReady()) throw new Error('Java API не підтвердило готовність усіх політик.');
    aia2MachineReady = true;
    aia2GuardState.phase = 'active';
    aia2GuardState.retryable = false;
    aia2GuardState.lastError = '';
    aia2GuardState.blockRules = Object.keys(rules.blockGates).length;
    aia2GuardState.itemRules = Object.keys(rules.itemGates).length;
    aia2GuardState.recipeRules = Object.keys(rules.recipeGates).length;
    console.info('[AIA2] Machine Guard активовано: API ' + aia2GuardState.version + ', блоків ' +
      aia2GuardState.blockRules + ', предметів ' + aia2GuardState.itemRules + ', рецептів ' + aia2GuardState.recipeRules + '.');
  } catch (error) {
    if (phase === 'api_version') error = new Error('Несумісний Machine Guard JAR. Оновіть JAR до API 4 та повністю перезапустіть гру й сервер: ' + String(error.message || error));
    aia2MachineFailure(error, phase);
  }
}

var aia2MachineAPI = {
  isReady: function () {
    return !!(AIA2MachineGuard && aia2MachineReady && AIA2MachineGuard.isReady());
  },
  status: function () {
    if (this.isReady()) return 'Machine Guard: активний; API ' + aia2GuardState.version + ', правил блоків ' +
      aia2GuardState.blockRules + ', предметів ' + aia2GuardState.itemRules + ', рецептів ' + aia2GuardState.recipeRules + '.';
    return 'Machine Guard: не активний [' + aia2GuardState.phase + ']. ' +
      (aia2GuardState.lastError || 'Очікується ініціалізація після запуску сервера.') +
      (aia2GuardState.retryable ? ' Заплановано повторну перевірку.' : ' Усуньте причину й виконайте /aia2 guard retry або /reload.') +
      ' Захист залишається закритим.';
  },
  diagnostics: function () {
    return {ready: this.isReady(), phase: aia2GuardState.phase, attempts: aia2GuardState.attempts,
      retryable: aia2GuardState.retryable, lastError: aia2GuardState.lastError, apiVersion: aia2GuardState.version};
  },
  retry: function (server) {
    if (!AIA2MachineGuard || this.isReady()) return false;
    // Explicit recovery request only; no large rule reparses inside command/login callbacks.
    aia2GuardState.attempts = 0;
    aia2GuardState.retryable = true;
    aia2GuardState.phase = 'awaiting_tick';
    aia2GuardState.nextAttempt = Math.max(aia2GuardState.nextAttempt, aia2GuardTick + 20);
    return true;
  },
  syncPlayer: function (player) {
    if (!this.isReady()) return;
    try { aia2MirrorMachinePlayer(player); }
    catch (error) { aia2GuardState.attempts = 1; aia2MachineFailure(error, 'player_sync'); }
  },
  claim: function (player, block) {
    if (!this.isReady() || !player || !player.isServerPlayer() || player.isFake()) return;
    var id = String(block.id);
    var required = global.AIA2.rules.blockGates[id];
    if (required === undefined) required = id.indexOf('minecraft:') === 0 ? 0 : 100;
    if (!global.AIA2.canAccess(player, required)) return;
    var entity = block.getEntity();
    if (!entity) return;
    try {
      var team = global.AIA2.teamId(player);
      aia2MirrorMachinePlayer(player);
      if (id.indexOf('forbidden_arcanus:clibano_') === 0) {
        AIA2MachineGuard.claimClibano(player, entity);
        return;
      }
      var owner = String(AIA2MachineGuard.getOwner(entity));
      if (!owner) AIA2MachineGuard.setOwner(entity, team);
    } catch (error) { aia2MachineFailure(error, 'machine_claim'); }
  }
};
Object.keys(aia2MachineAPI).forEach(function (key) { global.AIA2Machines[key] = aia2MachineAPI[key]; });

// LOADED fires at ServerStarting, before FTB Quests loads its files at
// SERVER_STARTED. Do not initialize from this callback.
ServerEvents.loaded(function (event) {
  if (AIA2MachineGuard && aia2GuardState.retryable) {
    aia2GuardState.phase = 'awaiting_tick';
    aia2GuardState.nextAttempt = aia2GuardTick + 1;
  }
});
ServerEvents.tick(function (event) {
  aia2GuardTick++;
  if (!AIA2MachineGuard) return;
  if (aia2MachineReady && !AIA2MachineGuard.isReady()) {
    aia2MachineReady = false;
    aia2GuardState.phase = 'native_reset';
    aia2GuardState.retryable = true;
    aia2GuardState.attempts = 0;
    aia2GuardState.nextAttempt = aia2GuardTick;
  }
  if (!aia2MachineReady && aia2GuardState.retryable && aia2GuardTick >= aia2GuardState.nextAttempt) aia2InitMachines(event.server);
});
ServerEvents.unloaded(function () {
  aia2MachineReady = false;
  aia2GuardState.phase = 'stopped';
  aia2GuardState.retryable = false;
  if (AIA2MachineGuard) AIA2MachineGuard.clearRuntime();
});
