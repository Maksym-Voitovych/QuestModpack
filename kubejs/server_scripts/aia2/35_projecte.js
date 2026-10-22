// ProjectE 1.21.1 PE1.1.0, source-verified. Replaces the final EMC map after all mappers.
// This prevents other mappers and recipe inheritance from restoring progression-item EMC.
var AIA2EMCMap = Java.loadClass('moze_intel.projecte.emc.EMCMappingHandler');
var AIA2ItemInfo = Java.loadClass('moze_intel.projecte.api.ItemInfo');
var AIA2LongMap = Java.loadClass('it.unimi.dsi.fastutil.objects.Object2LongOpenHashMap');
var AIA2EMCAllowed = JSON.parse(JsonIO.readString('kubejs/config/aia2_emc_whitelist.json'));

NativeEvents.onEvent(Java.loadClass('moze_intel.projecte.api.event.EMCRemapEvent'), function () {
  var map = new AIA2LongMap();
  Object.keys(AIA2EMCAllowed).forEach(function (id) {
    var item = Item.of(id);
    if (item.isEmpty()) throw new Error('[AIA2] Невідомий EMC whitelist item: ' + id);
    map.put(AIA2ItemInfo.fromStack(item), AIA2EMCAllowed[id]);
  });
  // updateEmcValues updates data-component caches and does NOT refire EMCRemapEvent.
  // ProjectE's ordinary datapack sync sends this filtered map to clients afterwards.
  AIA2EMCMap.updateEmcValues(map);
  console.info('[AIA2] EMC: strict ordinary-material whitelist (' + Object.keys(AIA2EMCAllowed).length + ' entries).');
});

function aia2EMCRequest(event) {
  var info = event.getReducedInfo();
  var id = String(info.createStack().id);
  if (!AIA2EMCAllowed[id] || info.hasModifiedComponents() || !global.AIA2.canAccess(event.getPlayer(), 45)) {
    event.setCanceled(true);
  }
}
NativeEvents.onEvent(Java.loadClass('moze_intel.projecte.api.event.PlayerAttemptLearnEvent'), aia2EMCRequest);
NativeEvents.onEvent(Java.loadClass('moze_intel.projecte.api.event.PlayerAttemptCondenserSetEvent'), aia2EMCRequest);
