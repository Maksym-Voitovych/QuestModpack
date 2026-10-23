// KubeJS 2101 RecipeViewerEvents (JEI integration), source-verified.
var aia2ClientRules = JSON.parse(JsonIO.readString('kubejs/config/aia2_runtime.json'));
var aia2ComponentInfo = JSON.parse(JsonIO.readString('kubejs/config/aia2_components.json'));
RecipeViewerEvents.addInformation('item', function (event) {
  aia2ClientRules.epochs.forEach(function (epoch) {
    var lines = (epoch.lore || []).concat(['Завершіть основні віхи та підсумкове випробування епохи ' + epoch.number + '.',
      'Біля звичайного верстака: /aia2 key',
      'Сервер перевіряє умови перед списанням матеріалів.']);
    var cost = epoch.transitionCost || epoch.cost;
    Object.keys(cost).forEach(function (id) { lines.push(cost[id] + ' × ' + id); });
    lines.push('Ключ потрібен лише для завершення глави та створення наступного ключа.');
    event.add(epoch.key, lines);
  });
  aia2ComponentInfo.items.forEach(function (component) {
    event.add(component.id, [component.description_uk, 'Процес: ' + component.process,
      'Потрібна епоха: ' + component.epoch + '. Склад і порядок дивіться у рецептах JEI.']);
  });
});
ItemEvents.modifyTooltips(function (event) {
  aia2ClientRules.epochs.forEach(function (epoch) {
    event.add(epoch.key, (epoch.lore || []).concat(['Епоха ' + epoch.number, 'Крафт біля верстака: /aia2 key',
      'Не використовується у звичайних рецептах.']));
  });
  aia2ComponentInfo.items.forEach(function (component) {
    event.add(component.id, [component.description_uk, 'Епоха ' + component.epoch]);
  });
});
