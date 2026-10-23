// KubeJS 2101 / FTB Quests 2101.1.36. No recipe.stage() or fictitious canUse hook.
var AIA2QuestFile = Java.loadClass('dev.ftb.mods.ftbquests.quest.ServerQuestFile');
var AIA2QuestBridge = Java.loadClass('ua.aia2.guard.FtbQuestBridge');
// Public API verified against Game Stages Reborn 15.1.1.
var AIA2StageHelper = Java.loadClass('net.darkhax.gamestages.GameStageHelper');
var AIA2Rules = JSON.parse(JsonIO.readString('kubejs/config/aia2_runtime.json'));
var AIA2StoreKey = 'aia2_runtime_v1';
var AIA2KeyGuard = Java.loadClass('ua.aia2.guard.Aia2MachineGuard');
// Cache by the authoritative serialized value and server identity. A changed value
// is revalidated; a damaged journal never becomes an empty/new progression.
var aia2LedgerCache = {server: null, text: null, state: null};
// This cache only suppresses repeated advancement commands. Native SavedData
// remains the authority; neither this projection nor an item can authorize a key.
var aia2BranchProjection = {};

function aia2Team(player) {
  var file = AIA2QuestFile.INSTANCE;
  if (!file) throw new Error('[AIA2] FTB Quests ще не завантажено.');
  // UUID overload takes a TEAM UUID, not a player's UUID. Select Entity in Java.
  var data = AIA2QuestBridge.getTeamData(file, player);
  if (!data) throw new Error('[AIA2] Не знайдено FTB-команду гравця.');
  return data;
}

function aia2State(server) {
  var text = String(server.persistentData.getString(AIA2StoreKey));
  if (aia2LedgerCache.server === server && aia2LedgerCache.text === text) return aia2LedgerCache.state;
  var state = !text ? {schema: 1, teams: {}} : global.AIA2Core.validateState(JSON.parse(text));
  aia2LedgerCache = {server: server, text: text, state: state};
  return state;
}

function aia2Save(server, state) {
  global.AIA2Core.validateState(state);
  var text = JSON.stringify(state);
  server.persistentData.putString(AIA2StoreKey, text);
  aia2LedgerCache = {server: server, text: text, state: state};
}

function aia2TeamRecord(player, state) {
  var id = String(aia2Team(player).getTeamId());
  if (!state.teams[id]) state.teams[id] = {completed: 0};
  return state.teams[id];
}

function aia2Completed(player) {
  return aia2TeamRecord(player, aia2State(player.server)).completed;
}

function aia2Name(player) {
  var name = String(player.username);
  if (!/^[A-Za-z0-9_]{1,16}$/.test(name)) throw new Error('[AIA2] Некоректне ім’я гравця.');
  return name;
}

function aia2Proofs(player, epoch) {
  var team = aia2Team(player);
  return epoch.milestoneQuestIds.map(function (id) {
    var quest = AIA2QuestFile.INSTANCE.getQuest(parseInt(id, 16));
    if (!quest) throw new Error('[AIA2] Не завантажено обов’язковий квест ' + id + '. Перевірте встановлення SNBT.');
    return team.isCompleted(quest);
  });
}

function aia2ExpansionProofs(player, epoch) {
  var team = aia2Team(player);
  (epoch.requiredQuestIds || []).forEach(function (id) {
    var quest = AIA2QuestFile.INSTANCE.getQuest(parseInt(id, 16));
    if (!quest) throw new Error('[AIA2] Не завантажено підсумкове випробування ' + id + '. Перевірте SNBT.');
    if (!team.isCompleted(quest)) throw new Error('[AIA2] Завершіть підсумкове випробування та обов’язкові модові гілки епохи ' + epoch.number + '.');
  });
}

function aia2AllQuests(player, ids) {
  var team = aia2Team(player);
  return ids.every(function (id) {
    var quest = AIA2QuestFile.INSTANCE.getQuest(parseInt(id, 16));
    if (!quest) throw new Error('[AIA2] Не завантажено квест гілки ' + id + '.');
    return team.isCompleted(quest);
  });
}

function aia2RefreshBranches(player) {
  if (!AIA2Rules.dualKeys || !global.AIA2Machines.isReady()) return;
  var completed = aia2Completed(player);
  if (completed === 48) return;
  var epoch = AIA2Rules.epochs[completed];
  var team = String(aia2Team(player).getTeamId());
  ['tech', 'arcane'].forEach(function (branch) {
    var ready = aia2AllQuests(player, epoch.branchQuestIds[branch]);
    AIA2KeyGuard.setTeamKeyReady(team, epoch.number, branch, ready);
    var proof = AIA2KeyGuard.hasProductionProof(player.server, team, epoch.number, branch);
    var name = aia2Name(player);
    var cacheKey = name + ':' + branch;
    var projection = team + ':' + epoch.number + ':' + proof;
    if (aia2BranchProjection[cacheKey] !== projection) {
      player.server.runCommandSilent('advancement ' + (proof ? 'grant ' : 'revoke ') + name +
        ' only aia2:production/' + branch + '_' + (epoch.number < 10 ? '0' : '') + epoch.number);
      aia2BranchProjection[cacheKey] = projection;
    }
  });
}

function aia2FinishPending(player) {
  var state = aia2State(player.server);
  var record = aia2TeamRecord(player, state);
  if (!record.pending) return false;
  if (!global.AIA2Machines.isReady()) return false;
  var epoch = AIA2Rules.epochs[record.pending - 1];
  var team = String(aia2Team(player).getTeamId());
  if (!AIA2KeyGuard.hasProductionProof(player.server, team, epoch.number, 'tech') ||
      !AIA2KeyGuard.hasProductionProof(player.server, team, epoch.number, 'arcane')) return false;
  if (!aia2AllQuests(player, epoch.requiredQuestIds) || !aia2AllQuests(player, epoch.milestoneQuestIds) ||
      !aia2AllQuests(player, [epoch.finalQuestId, epoch.branchKeyQuestIds.tech, epoch.branchKeyQuestIds.arcane])) return false;
  var previous = record.completed;
  var pending = record.pending;
  try {
    record.completed = pending;
    delete record.pending;
    aia2Save(player.server, state);
  } catch (error) { record.completed = previous; record.pending = pending; throw error; }
  aia2Team(player).getOnlineMembers().forEach(function (member) { aia2Sync(member); });
  player.tell('Фінальний квест епохи ' + pending + ' завершено. Наступний етап відкрито; командний прогрес збережено.');
  return true;
}

function aia2Sync(player) {
  var n = aia2Completed(player);
  var record = aia2TeamRecord(player, aia2State(player.server));
  if (global.AIA2Machines) global.AIA2Machines.syncPlayer(player);
  var name = aia2Name(player);
  var server = player.server;
  // Revoke this package's advancement projection on team changes; leave unrelated progress intact.
  for (var i = 1; i <= 48; i++) {
    var suffix = (i < 10 ? '0' : '') + i;
    server.runCommandSilent('advancement ' + (i <= n || record.pending === i ? 'grant ' : 'revoke ') + name + ' only aia2:keys/e' + suffix);
    if (AIA2Rules.dualKeys) {
      ['tech', 'arcane'].forEach(function (branch) {
        // Past epochs are grandfathered; only a native current-team receipt
        // can project a manufacturing advancement for an unfinished epoch.
        var proof = i <= n || global.AIA2Machines.isReady() && AIA2KeyGuard.hasProductionProof(server, String(aia2Team(player).getTeamId()), i, branch);
        server.runCommandSilent('advancement ' + (proof ? 'grant ' : 'revoke ') + name + ' only aia2:production/' + branch + '_' + suffix);
      });
    }
    if (AIA2Rules.gameStagesMirror) {
      var doneStage = 'aia2_done_' + suffix;
      var epochStage = 'aia2_epoch_' + suffix;
      var available = i <= Math.min(n+1, 48);
      if (AIA2StageHelper.hasStage(player, doneStage) !== (i <= n)) {
        server.runCommandSilent('gamestage ' + (i <= n ? 'add ' : 'remove ') + name + ' ' + doneStage + ' true');
      }
      if (AIA2StageHelper.hasStage(player, epochStage) !== available) {
        server.runCommandSilent('gamestage ' + (available ? 'add ' : 'remove ') + name + ' ' + epochStage + ' true');
      }
      // Advancement progress is permanent by default; revoke this package's
      // projection on team changes or missing native stages. Command result 0
      // is NOT a stage boolean: Reborn returns 0 on successful add/check too.
      var verified = available && AIA2StageHelper.hasStage(player, epochStage);
      server.runCommandSilent('advancement ' + (verified ? 'grant ' : 'revoke ') + name + ' only aia2:stages/e' + suffix);
    }
  }
  player.persistentData.putString('aia2_last_team', String(aia2Team(player).getTeamId()));
  aia2RefreshBranches(player);
}

function aia2AtWorkbench(player) {
  for (var x = -3; x <= 3; x++) for (var y = -2; y <= 2; y++) for (var z = -3; z <= 3; z++) {
    if (String(player.level.getBlock(player.blockX+x, player.blockY+y, player.blockZ+z).id) === 'minecraft:crafting_table') return true;
  }
  return false;
}

function aia2Forge(player, restore) {
  if (!player || !player.isServerPlayer() || player.isFake()) throw new Error('[AIA2] Потрібен справжній серверний гравець.');
  if (AIA2Rules.machineGuard && AIA2Rules.machineGuard.mode === 'required' &&
      (!global.AIA2Machines || !global.AIA2Machines.isReady())) {
    throw new Error('[AIA2] Строгий захист машин не готовий. Адміністратор має встановити й перевірити AIA2 Machine Guard.');
  }
  if (!aia2AtWorkbench(player)) throw new Error('[AIA2] Станьте не далі трьох блоків від звичайного верстака.');
  var state = aia2State(player.server);
  var record = aia2TeamRecord(player, state);
  if (!restore && record.completed === 48) throw new Error('[AIA2] Команда вже завершила всі 48 епох.');
  if (!restore && record.pending) throw new Error('[AIA2] Артефакт уже виготовлено. Очікується завершення фінального квесту FTB; повторного списання не буде.');
  if (restore && record.completed === 0) throw new Error('[AIA2] Ще немає законно створеного ключа для відновлення.');
  var epoch = AIA2Rules.epochs[record.completed - (restore ? 1 : 0)];
  var stage = 'aia2_epoch_' + (epoch.number < 10 ? '0' : '') + epoch.number;
  if (!AIA2StageHelper.hasStage(player, stage)) {
    throw new Error('[AIA2] Відсутня стадія ' + stage + '. Виконайте /aia2 sync та перевірте Game Stages Reborn.');
  }
  // Existing completed epochs are grandfathered. Recovery never grants a new epoch.
  if (!restore) aia2ExpansionProofs(player, epoch);
  if (!restore && AIA2Rules.dualKeys) {
    aia2RefreshBranches(player);
    var teamId = String(aia2Team(player).getTeamId());
    ['tech', 'arcane'].forEach(function (branch) {
      if (!aia2AllQuests(player, epoch.branchQuestIds[branch]) ||
          !AIA2KeyGuard.hasProductionProof(player.server, teamId, epoch.number, branch)) {
        throw new Error('[AIA2] Потрібне справжнє виготовлення ключа ' + branch + ' після завершення відповідної гілки. /give не є доказом.');
      }
    });
    // Keep the legacy nine-unit formula exclusively for paid recovery.
    epoch = {number: epoch.number, key: epoch.key, cost: epoch.transitionCost,
      milestoneQuestIds: epoch.milestoneQuestIds, finalQuestId: epoch.finalQuestId};
  }
  if (restore) {
    var cost = {};
    Object.keys(epoch.cost).forEach(function (id) {
      if (id.indexOf('kubejs:aia2_epoch_key_') !== 0 && id !== 'minecraft:crafting_table') cost[id] = epoch.cost[id];
    });
    cost['minecraft:crafting_table'] = 1;
    epoch = {number: epoch.number, key: epoch.key, cost: cost, milestoneQuestIds: epoch.milestoneQuestIds};
  }
  var inventory = player.getInventory();
  var snapshot = [];
  var simple = [];
  for (var i = 0; i < 36; i++) {
    var stack = inventory.getStackInSlot(i).copy();
    snapshot.push(stack);
    simple.push({id: String(stack.id), count: stack.getCount()});
  }
  if (restore && simple.some(function (s) { return s.id === epoch.key && s.count > 0; })) {
    throw new Error('[AIA2] Цей ключ уже є у вашому головному інвентарі.');
  }
  // Nothing has been consumed yet; failure of any condition leaves every item intact.
  var plan = global.AIA2Core.prepareKey(epoch, record.completed - (restore ? 1 : 0), aia2Proofs(player, epoch), simple);
  var output = Item.of(plan.outputId, 1);
  if (output.isEmpty()) throw new Error('[AIA2] Предмет ключа не зареєстровано. Потрібен повний перезапуск гри.');
  var previous = record.completed;
  try {
    plan.deductions.forEach(function (d) {
      var stack = snapshot[d.slot].copy();
      stack.shrink(d.count);
      inventory.setStackInSlot(d.slot, stack);
    });
    inventory.setStackInSlot(plan.outputSlot, output);
    if (!restore && AIA2Rules.dualKeys) record.pending = plan.completed;
    else record.completed = plan.completed;
    aia2Save(player.server, state);
  } catch (error) {
    for (var slot = 0; slot < 36; slot++) inventory.setStackInSlot(slot, snapshot[slot]);
    record.completed = previous;
    if (!restore) delete record.pending;
    throw error;
  }
  player.containerMenu.broadcastChanges();
  var team = aia2Team(player);
  team.getOnlineMembers().forEach(function (member) { aia2Sync(member); });
  player.tell(restore ? 'Відновлено вже законно створений ключ ' + epoch.number + '. Нові епохи не відкриті.' :
    'Артефакт епохи ' + epoch.number + ' створено. Завершіть фінальний квест FTB для відкриття наступної епохи.');
  // If FTB has already processed the proven advancement, finish now. Otherwise
  // the persisted pending transition is retried on player ticks after completion.
  if (!restore && AIA2Rules.dualKeys) aia2FinishPending(player);
  return 1;
}

var aia2ServerAPI = {
  rules: AIA2Rules,
  completed: aia2Completed,
  ledger: aia2State,
  teamId: function (player) { return String(aia2Team(player).getTeamId()); },
  canAccess: function (player, epoch) {
    if (!epoch) return true;
    if (!player || !player.isServerPlayer() || player.isFake()) return false;
    try {
      if (epoch > 1 && AIA2Rules.machineGuard && AIA2Rules.machineGuard.mode === 'required' &&
          (!global.AIA2Machines || !global.AIA2Machines.isReady())) return false;
      if (!global.AIA2Core.mayAccess(epoch, aia2Completed(player))) return false;
      if (epoch >= 1 && epoch <= 48) {
        return AIA2StageHelper.hasStage(player, 'aia2_epoch_' + (epoch < 10 ? '0' : '') + epoch);
      }
      return epoch === 99 && AIA2StageHelper.hasStage(player, 'aia2_done_48');
    } catch (error) {
      // Native cancellable events must receive false even if a damaged ledger
      // throws; letting that exception escape would leave the event uncancelled.
      console.error('[AIA2] Доступ закрито через помилку журналу: ' + String(error));
      return false;
    }
  }
};

// Mutate the startup-created container; global itself is read-only here.
Object.keys(aia2ServerAPI).forEach(function (key) { global.AIA2[key] = aia2ServerAPI[key]; });

ServerEvents.commandRegistry(function (event) {
  var C = event.commands;
  function run(ctx, action) {
    var player = ctx.source.getPlayer();
    if (!player) return 0;
    try { return action(player); }
    catch (error) { player.tell(String(error.message || error)); return 0; }
  }
  event.register(C.literal('aia2')
    .executes(function (ctx) { return run(ctx, function (p) {
      p.tell('/aia2 status; /aia2 key — крафт біля верстака; /aia2 recover — відновлення останнього ключа; /aia2 sync.'); return 1;
    }); })
    .then(C.literal('status').executes(function (ctx) { return run(ctx, function (p) {
      var n = aia2Completed(p);
      p.tell(n === 48 ? 'Усі 48 епох завершено.' : 'Завершено: ' + n + '. Поточна епоха: ' + (n+1) + '.');
      if (global.AIA2Machines) p.tell(global.AIA2Machines.status());
      var pending = aia2TeamRecord(p, aia2State(p.server)).pending;
      if (pending) p.tell('Очікується фінальний квест епохи ' + pending + '; артефакт уже оплачено.');
      return 1;
    }); }))
    .then(C.literal('key').executes(function (ctx) { return run(ctx, function (p) { return aia2Forge(p, false); }); }))
    .then(C.literal('recover').executes(function (ctx) { return run(ctx, function (p) { return aia2Forge(p, true); }); }))
    .then(C.literal('guard').then(C.literal('retry').executes(function (ctx) { return run(ctx, function (p) {
      if (!ctx.source.hasPermission(2)) throw new Error('[AIA2] Повторну ініціалізацію дозволено адміністратору.');
      p.tell(global.AIA2Machines.retry(p.server) ? 'Заплановано повторну перевірку Machine Guard.' : global.AIA2Machines.status()); return 1;
    }); })))
    .then(C.literal('sync').executes(function (ctx) { return run(ctx, function (p) { aia2Sync(p); return 1; }); })));
});

PlayerEvents.loggedIn(function (event) { aia2Sync(event.player); });
PlayerEvents.tick(function (event) {
  var p = event.player;
  if (!p.isServerPlayer() || p.isFake()) return;
  if (p.tickCount % 40 === 0 && global.AIA2Machines.isReady()) {
    try { aia2RefreshBranches(p); aia2FinishPending(p); }
    catch (error) { if (p.tickCount % 200 === 0) console.error('[AIA2] Перевірка гілок закрита: ' + String(error)); }
  }
  var current = String(aia2Team(p).getTeamId());
  var n = Math.min(aia2Completed(p) + 1, 48);
  var stage = 'aia2_epoch_' + (n < 10 ? '0' : '') + n;
  if (String(p.persistentData.getString('aia2_last_team')) !== current ||
      (p.tickCount % 100 === 0 && !AIA2StageHelper.hasStage(p, stage))) aia2Sync(p);
});
