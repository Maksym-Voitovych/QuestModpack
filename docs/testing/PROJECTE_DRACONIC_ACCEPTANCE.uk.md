# ProjectE / Draconic: приймальна перевірка 0.4.9

Повний інстанс із цими модами у хмарі не запускався. 66+22 модельовані перевірки actual helper/handlers не доводять live optional dispatch. Мінімальний Minecraft перевіряє попередні native fixtures та SavedData, а не модові меню.

1. До 45 імпортовані table/tablet не дозволяють трансмутацію. На 45 звичайна table працює, tablet потребує 47. Fake Player не позичає синхронізовану команду.
2. На 45 відкрити table, вивчити дозволений gold_ingot і підготувати EMC. Не закриваючи UI, змінити команду або понизити епоху: pickup, ShiftClick, hotbar swap, drag і doubleclick не витрачають EMC й не видають output. Tablet47→45 перевірити окремо. Повернення доступу не скидає знань та EMC.
3. Cached output після /reload з EMC0, невідомим ID або зміненими raw components не видається. Slot має належати поточному TransmutationInventory; старі від’єднані slots не виробляють предметів.
4. Після EMCRemap фінальна мапа має 14 звичайних матеріалів; FuelMapper будується після фільтрації. Виключені alchemical/mobius/aeternalis fuels не утворюють нульову EMC upgrade chain. Фізичні crafting-рецепти залишаються.
5. На окремій копії зіпсувати whitelist або refresh: item map, fuel cache й Java extraction закриті з видимою помилкою. Наш код не викликає додатковий pruneStaleKnowledge.
6. Time Watch: пізній pedestal біля locked target іншої команди не запускає його. Дозволений target використовує власну recipe policy; вкладені виклики й exception повертають попередній контекст. Кожен bonus tick переоцінює доступ.
7. Passive armor, Curios, rings і world tools залишаються окремим відкритим аудитом. Не вважати цей блок універсальним захистом усіх предметів ProjectE.
8. Перевірити три Draconic fusion-рецепти в JEI та реальній конструкції: native catalyst/count/energy/tier/output незмінні, два нові входи, максимум 11 інжекторів. IO↔relay конверсії збережені; після /reload старий cached fusion не виконується.
9. Звірити build633 з reference source 3.1.4: commit не підтверджено. Lowest tier визначається серед зайнятих інжекторів; порожній Basic не знижує його.
10. Перевірити нові квести, українські описи, іконки, залежності та нагороди. Inventory/observation підтверджують лише заявлену підготовку. Reactor/Chaos випробування проводити на окремій копії світу.

Зберегти server/KubeJS logs, Recipe IDs, приклади старого прогресу й профіль TPS. Особисті worlds/logs/backups не додавати до Git.
