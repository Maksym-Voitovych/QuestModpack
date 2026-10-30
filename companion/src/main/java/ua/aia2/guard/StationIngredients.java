package ua.aia2.guard;

import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Set;
import java.util.TreeSet;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.crafting.Ingredient;

/** Current, bounded vanilla Ingredient semantics; never trusts cached Ingredient item arrays. */
final class StationIngredients {
    record Snapshot(List<Integer> counts, List<List<String>> definitions, List<Set<Item>> accepted) {}
    private StationIngredients() {}
    static Snapshot read(Object recipe) {
        try {
            if (!recipe.getClass().getName().equals("earth.terrarium.adastra.common.recipes.SpaceStationRecipe")) return null;
            Object rows = recipe.getClass().getMethod("ingredients").invoke(recipe);
            if (!(rows instanceof List<?> list) || list.isEmpty() || list.size() > 64) return null;
            var counts = new ArrayList<Integer>(); var definitions = new ArrayList<List<String>>();
            var accepted = new ArrayList<Set<Item>>(); int total = 0, members = 0;
            for (Object row : list) {
                if (row == null || !row.getClass().getName().equals("earth.terrarium.adastra.common.recipes.base.IngredientHolder")) return null;
                Object amount = row.getClass().getMethod("count").invoke(row);
                if (!(amount instanceof Integer count) || count < 1 || count > 4096 || (total += count) > 16384) return null;
                Object raw = row.getClass().getMethod("ingredient").invoke(row);
                if (!(raw instanceof Ingredient ingredient) || raw.getClass() != Ingredient.class || ingredient.isCustom()) return null;
                var values = ingredient.getValues(); if (values.length == 0 || values.length > 64) return null;
                var names = new ArrayList<String>(); var items = new HashSet<Item>();
                for (var part : values) {
                    if (part instanceof Ingredient.ItemValue item) {
                        if (item.item().isEmpty()) return null;
                        Item target = item.item().getItem(); items.add(target); names.add("item:" + BuiltInRegistries.ITEM.getKey(target));
                    } else if (part instanceof Ingredient.TagValue tag) {
                        var current = BuiltInRegistries.ITEM.getTag(tag.tag());
                        var found = current.isPresent() ? current.get().stream().limit(16385L - members).toList() : List.<net.minecraft.core.Holder<Item>>of();
                        if ((members += found.size()) > 16384) return null;
                        var ids = new TreeSet<String>();
                        for (var member : found) { items.add(member.value()); ids.add(BuiltInRegistries.ITEM.getKey(member.value()).toString()); }
                        names.add("tag:" + tag.tag().location() + ":" + current.isPresent() + ":" + ids);
                    } else return null;
                }
                counts.add(count); definitions.add(List.copyOf(names)); accepted.add(Set.copyOf(items));
            }
            return new Snapshot(List.copyOf(counts), List.copyOf(definitions), List.copyOf(accepted));
        } catch (ReflectiveOperationException | RuntimeException unsupported) { return null; }
    }
}
