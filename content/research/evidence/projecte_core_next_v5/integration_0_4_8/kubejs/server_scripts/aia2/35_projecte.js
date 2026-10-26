// ProjectE 1.21.1 PE1.1.0, source-verified. Replaces the final EMC map after all mappers.
// This prevents other mappers and recipe inheritance from restoring progression-item EMC.
var AIA2EMCMap = Java.loadClass('moze_intel.projecte.emc.EMCMappingHandler');
var AIA2ItemInfo = Java.loadClass('moze_intel.projecte.api.ItemInfo');
var AIA2LongMap = Java.loadClass('it.unimi.dsi.fastutil.objects.Object2LongOpenHashMap');
// One primitive signature avoids Rhino's ambiguous fastutil put(Object,long/Long) overloads.
var AIA2EMCBridge = null;
var AIA2ProjectEAccess = null;
var AIA2FuelMapper = null;
var AIA2EMCSetupError = '';
var AIA2EMCAllowed = {};
var AIA2EMCReady = false;
try {
  AIA2EMCBridge = Java.loadClass('ua.aia2.guard.RhinoLongMapBridge');
  AIA2ProjectEAccess = Java.loadClass('ua.aia2.guard.ProjectEAccess');
  AIA2ProjectEAccess.pause();
  AIA2FuelMapper = Java.loadClass('moze_intel.projecte.emc.FuelMapper');
  AIA2EMCAllowed = JSON.parse(JsonIO.readString('kubejs/config/aia2_emc_whitelist.json'));
  if (!AIA2EMCAllowed || Array.isArray(AIA2EMCAllowed) || typeof AIA2EMCAllowed !== 'object') {
    throw new Error('EMC whitelist має бути об’єктом JSON.');
  }
} catch (error) {
  AIA2EMCSetupError = String(error.message || error);
  console.error('[AIA2] ProjectE: whitelist не готовий, EMC буде закрито: ' + AIA2EMCSetupError);
}

NativeEvents.onEvent(Java.loadClass('moze_intel.projecte.api.event.EMCRemapEvent'), function () {
  AIA2EMCReady = false;
  if (AIA2ProjectEAccess) AIA2ProjectEAccess.pause();
  var map = new AIA2LongMap();
  try {
    if (AIA2EMCSetupError) throw new Error(AIA2EMCSetupError);
    Object.keys(AIA2EMCAllowed).forEach(function (id) {
      var value = Number(AIA2EMCAllowed[id]);
      if (!isFinite(value) || value <= 0 || Math.floor(value) !== value || value > 9007199254740991) {
        throw new Error('[AIA2] Некоректний додатний цілий EMC для ' + id + '.');
      }
      var item = Item.of(id);
      if (item.isEmpty()) throw new Error('[AIA2] Невідомий EMC whitelist item: ' + id);
      AIA2EMCBridge.putValue(map, AIA2ItemInfo.fromStack(item), value);
    });
    // Native FuelMapper was built BEFORE this event, using inherited EMC.
    // Replace that stale cache only after the filtered final map is installed.
    AIA2EMCMap.updateEmcValues(map);
    AIA2FuelMapper.loadMap();
    AIA2ProjectEAccess.configureWhitelistJson(JSON.stringify(AIA2EMCAllowed));
  } catch (error) {
    // A failed whitelist must not leave ProjectE's inherited, unrestricted EMC map active.
    AIA2EMCMap.updateEmcValues(new AIA2LongMap());
    if (AIA2ProjectEAccess) AIA2ProjectEAccess.pause();
    if (AIA2FuelMapper) AIA2FuelMapper.loadMap();
    console.error('[AIA2] ProjectE: EMC закрито через помилку whitelist/Java API. Встановіть поточний Machine Guard JAR: ' + String(error));
    throw error;
  }
  // updateEmcValues updates data-component caches and does NOT refire EMCRemapEvent.
  // ProjectE's ordinary datapack sync sends this filtered map to clients afterwards.
  AIA2EMCReady = true;
  console.info('[AIA2] EMC: strict ordinary-material whitelist (' + Object.keys(AIA2EMCAllowed).length + ' entries).');
});

function aia2EMCRequest(event) {
  var info = event.getReducedInfo();
  var id = String(info.createStack().id);
  if (!AIA2EMCReady || AIA2EMCSetupError || !AIA2EMCAllowed[id] || info.hasModifiedComponents() || !global.AIA2.canAccess(event.getPlayer(), 45)) {
    event.setCanceled(true);
  }
}
NativeEvents.onEvent(Java.loadClass('moze_intel.projecte.api.event.PlayerAttemptLearnEvent'), aia2EMCRequest);
NativeEvents.onEvent(Java.loadClass('moze_intel.projecte.api.event.PlayerAttemptCondenserSetEvent'), aia2EMCRequest);
