// API 4: these are real native recipes, backed by persistent manufacturing receipts.
var aia2DualKeyInfo = JSON.parse(JsonIO.readString('kubejs/config/aia2_dual_keys.json'));
RecipeViewerEvents.addInformation('item', function (event) {
  aia2DualKeyInfo.items.forEach(function (key) {
    event.add(key.id, ['Епоха ' + key.epoch + '. ' + (key.branch === 'tech' ? 'Технологічна гілка.' : 'Магія та дослідження.'),
      'Спочатку завершіть обов’язкові квести відповідної гілки.',
      'Справжній виробничий процес: ' + key.process + '. Рецепт: ' + key.recipeId + '.',
      'Сервер записує завершений крафт після витрати інгредієнтів. /give та передача ключа іншої команди не створюють такого запису.',
      'Обидва ключі потрібні біля верстака для /aia2 key. Наступна стадія відкривається після фінального квесту FTB.']);
  });
});
ItemEvents.modifyTooltips(function (event) {
  aia2DualKeyInfo.items.forEach(function (key) {
    event.add(key.id, ['Ключ епохи ' + key.epoch + ': ' + (key.branch === 'tech' ? 'технології' : 'магія та дослідження'),
      'Потрібен власний командний запис виготовлення. Звичайне отримання предмета не зараховується.']);
  });
});
