// KubeJS 2101 RecipeViewerEvents (JEI integration), source-verified.
var aia2ClientRules = JSON.parse(JsonIO.readString('kubejs/config/aia2_runtime.json'));
RecipeViewerEvents.addInformation('item', function (event) {
  aia2ClientRules.epochs.forEach(function (epoch) {
    var lines = ['Завершіть шість обов’язкових квестів епохи ' + epoch.number + '.',
      'Біля звичайного верстака: /aia2 key',
      'Сервер перевіряє умови перед списанням матеріалів.'];
    Object.keys(epoch.cost).forEach(function (id) { lines.push(epoch.cost[id] + ' × ' + id); });
    lines.push('Ключ потрібен лише для завершення глави та створення наступного ключа.');
    event.add(epoch.key, lines);
  });
});
ItemEvents.modifyTooltips(function (event) {
  aia2ClientRules.epochs.forEach(function (epoch) {
    event.add(epoch.key, ['Епоха ' + epoch.number, 'Крафт біля верстака: /aia2 key',
      'Не використовується у звичайних рецептах.']);
  });
});
