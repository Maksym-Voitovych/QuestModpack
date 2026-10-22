// Access protection for direct player interactions. Cached machine recipes require a separate adapter.
function aia2ItemStage(id) {
  var gates = global.AIA2.rules.itemGates;
  id = String(id);
  if (Object.prototype.hasOwnProperty.call(gates, id)) return gates[id];
  return id.indexOf('minecraft:') === 0 ? 0 : 100;
}
function aia2BlockStage(id) {
  var gates = global.AIA2.rules.blockGates;
  if (!gates) throw new Error('[AIA2] Відсутня blockGates; оновіть конфігурацію разом зі скриптами.');
  id = String(id);
  if (Object.prototype.hasOwnProperty.call(gates, id)) return gates[id];
  return id.indexOf('minecraft:') === 0 ? 0 : 100;
}
function aia2Deny(event, player, required) {
  if (!required || global.AIA2.canAccess(player, required)) return false;
  event.cancel();
  if (player && player.isServerPlayer() && player.tickCount % 20 === 0) {
    player.tell(required >= 100 ? 'Ця можливість ще на перевірці й тимчасово вимкнена.' :
      (required === 99 ? 'Ця можливість доступна після завершення епохи 48.' : 'Потрібна епоха ' + required + '.'));
  }
  return true;
}
BlockEvents.placed(function (event) {
  if (aia2Deny(event, event.entity, aia2BlockStage(event.block.id))) return;
  if (global.AIA2Machines) global.AIA2Machines.claim(event.entity, event.block);
});
BlockEvents.rightClicked(function (event) {
  var required = Math.max(aia2BlockStage(event.block.id), aia2ItemStage(event.item.id));
  if (aia2Deny(event, event.player, required)) return;
  if (global.AIA2Machines) global.AIA2Machines.claim(event.player, event.block);
});
BlockEvents.broken(function (event) { aia2Deny(event, event.player, aia2BlockStage(event.block.id)); });
ItemEvents.rightClicked(function (event) { aia2Deny(event, event.player, aia2ItemStage(event.item.id)); });
ItemEvents.entityInteracted(function (event) { aia2Deny(event, event.player, aia2ItemStage(event.item.id)); });
NativeEvents.onEvent(Java.loadClass('net.neoforged.neoforge.event.entity.player.AttackEntityEvent'), function (event) {
  var player = event.getEntity();
  var required = aia2ItemStage(player.getMainHandItem().id);
  if (required && !global.AIA2.canAccess(player, required)) event.setCanceled(true);
});
NativeEvents.onEvent(Java.loadClass('net.neoforged.neoforge.event.entity.EntityTravelToDimensionEvent'), function (event) {
  var entity = event.getEntity();
  if (!entity.isServerPlayer()) return;
  var id = String(event.getDimension().location());
  var stage = global.AIA2.rules.dimensionGates[id] || 0;
  if (stage && !global.AIA2.canAccess(entity, stage)) {
    event.setCanceled(true);
    entity.tell('Вимір ' + id + ' ще не відкритий для вашої команди.');
  }
});
