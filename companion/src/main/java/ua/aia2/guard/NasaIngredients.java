package ua.aia2.guard;

import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Set;
import java.util.TreeSet;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.crafting.Ingredient;
import net.minecraft.world.item.crafting.Recipe;

/** Bounded current vanilla ingredient semantics, independent of Ingredient's cached item array. */
final class NasaIngredients {
    record Snapshot(List<List<String>> definitions, List<Set<Item>> accepted) {
        boolean matches(ItemStack[] inputs) {
            if (inputs.length != 14) return false;
            for (int slot = 0; slot < 14; slot++)
                if (inputs[slot].isEmpty() || !accepted.get(slot).contains(inputs[slot].getItem())) return false;
            return true;
        }
    }
    private NasaIngredients() {}

    static Snapshot read(Recipe<?> recipe) {
        if (recipe == null) return null;
        try {
            Object value = recipe.getClass().getMethod("ingredients").invoke(recipe);
            if (!(value instanceof List<?> ingredients) || ingredients.size() != 14) return null;
            var definitions = new ArrayList<List<String>>();
            var accepted = new ArrayList<Set<Item>>();
            int budget = 0;
            for (Object row : ingredients) {
                if (!(row instanceof Ingredient ingredient) || row.getClass() != Ingredient.class || ingredient.isCustom()) return null;
                Ingredient.Value[] values = ingredient.getValues();
                if (values.length == 0 || values.length > 64) return null;
                var names = new ArrayList<String>(); var items = new HashSet<Item>();
                for (Ingredient.Value part : values) {
                    if (part instanceof Ingredient.ItemValue item) {
                        if (item.item().isEmpty()) return null;
                        Item target = item.item().getItem();
                        names.add("item:" + BuiltInRegistries.ITEM.getKey(target)); items.add(target);
                    } else if (part instanceof Ingredient.TagValue tag) {
                        var current = BuiltInRegistries.ITEM.getTag(tag.tag());
                        var members = current.isPresent()
                                ? current.get().stream().limit(16385L - budget).toList() : List.<net.minecraft.core.Holder<Item>>of();
                        budget += members.size(); if (budget > 16384) return null;
                        var ids = new TreeSet<String>();
                        for (var member : members) {
                            ids.add(BuiltInRegistries.ITEM.getKey(member.value()).toString()); items.add(member.value());
                        }
                        names.add("tag:" + tag.tag().location() + ":" + current.isPresent() + ":" + ids);
                    } else return null;
                }
                definitions.add(List.copyOf(names)); accepted.add(Set.copyOf(items));
            }
            return new Snapshot(List.copyOf(definitions), List.copyOf(accepted));
        } catch (ReflectiveOperationException | RuntimeException unsupported) { return null; }
    }
}
