// Native serializers are preserved; no unsupported recipe.stage() calls.
ServerEvents.recipes(function (event) {
  var bundle = JSON.parse(JsonIO.readString('kubejs/config/aia2_recipes.json'));
  bundle.remove.forEach(function (id) { event.remove({id: id}); });
  bundle.add.forEach(function (entry) {
    if (entry.json.type === 'create:mixing') {
      // Verified KubeJS Create 2101 schema: results, ingredients, optional time/heat.
      event.recipes.create.mixing(entry.json.results, entry.json.ingredients).id(entry.id);
    } else {
      // Exact native JSON is the supported path for preserving mod-specific wrappers,
      // components, native catalysts, energy, ritual activation and multiblock tiers.
      event.custom(entry.json).id(entry.id);
    }
  });
  // Keys use the server-side atomic forge. Never register an ungated vanilla key recipe.
  for (var n = 1; n <= 48; n++) {
    event.remove({output: 'kubejs:aia2_epoch_key_' + (n < 10 ? '0' : '') + n});
  }
});
