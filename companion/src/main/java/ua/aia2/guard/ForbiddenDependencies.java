package ua.aia2.guard;

import com.google.gson.JsonArray;
import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import com.mojang.serialization.Codec;
import com.mojang.serialization.JsonOps;
import java.lang.reflect.InvocationTargetException;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.HexFormat;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import java.util.TreeMap;
import net.minecraft.core.Holder;
import net.minecraft.core.HolderLookup;
import net.minecraft.core.HolderSet;
import net.minecraft.core.Registry;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.nbt.Tag;
import net.minecraft.resources.RegistryOps;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.crafting.Ingredient;

/** Bounded, current-registry dependencies of the exact Forbidden Arcanus 2.6.1 ritual types.
 * No Ingredient item cache or HolderSet identity is used as reload evidence.
 */
public final class ForbiddenDependencies {
    public static final String ACTIVE_TAG = "aia2_gameplay_dependencies_v1";
    private static final String BASE = "com.stal111.forbidden_arcanus.common.";
    private static final Set<String> EFFECTS = Set.of("ModifyRequiredEssenceEffect", "MultiplyRequiredEssenceEffect", "MultiplySoulDurationEffect");
    private static final int MAX_MEMBERS = 16384, MAX_TAGS = 64, MAX_ENHANCERS = 64;
    private static final int MAX_VALUES = 64, MAX_EFFECTS = 64, MAX_CONDITIONS = 32;
    public record Snapshot(String fingerprint, boolean hasDependencies) {
        public Snapshot {
            require(fingerprint != null && fingerprint.matches("[0-9a-f]{64}"), "невірний відбиток залежностей");
        }
    }
    private static final class Budget {
        int members;
        void take(int count) {
            members += count;
            require(members <= MAX_MEMBERS, "завеликі залежності ритуалу");
        }
    }
    private record Rule(Set<Item> items, int amount) {
        boolean test(ItemStack stack) { return !stack.isEmpty() && items.contains(stack.getItem()); }
    }
    private ForbiddenDependencies() {}
    private static void require(boolean condition, String message) {
        if (!condition) throw new IllegalArgumentException(message);
    }
    private static Object call(Object value, String method) {
        try { return value.getClass().getMethod(method).invoke(value); }
        catch (InvocationTargetException failure) { throw new IllegalArgumentException("не вдалося прочитати залежності ритуалу", failure.getCause()); }
        catch (ReflectiveOperationException failure) { throw new IllegalArgumentException("непідтримуване визначення залежностей ритуалу", failure); }
    }
    private static String id(Holder<?> holder) { return holder.unwrapKey().orElseThrow(() -> new IllegalArgumentException("незареєстрований підсилювач")).location().toString(); }
    private static JsonArray strings(Iterable<String> values) {
        JsonArray result = new JsonArray(); values.forEach(result::add); return result;
    }
    private static Rule ingredient(Ingredient ingredient, int amount, Map<String, JsonElement> tags, Budget budget) {
        require(!ingredient.isCustom(), "непідтримуваний custom ingredient ритуалу");
        Ingredient.Value[] values = ingredient.getValues();
        require(values.length > 0 && values.length <= MAX_VALUES, "непідтримуваний список ingredient ритуалу");
        Set<Item> accepted = new HashSet<>();
        for (Ingredient.Value value : values) {
            if (value instanceof Ingredient.ItemValue item) {
                require(!item.item().isEmpty(), "порожній ingredient ритуалу");
                accepted.add(item.item().getItem());
            } else if (value instanceof Ingredient.TagValue tag) {
                String key = tag.tag().location().toString();
                // Read the CURRENT tag binding. Native Ingredient#getItems() can retain the old array.
                Optional<HolderSet.Named<Item>> current = BuiltInRegistries.ITEM.getTag(tag.tag());
                List<Holder<Item>> members = current.isEmpty() ? List.of()
                        : current.get().stream().limit(MAX_MEMBERS - budget.members + 1L).toList();
                budget.take(members.size());
                var names = new java.util.TreeSet<String>();
                for (Holder<Item> member : members) {
                    names.add(BuiltInRegistries.ITEM.getKey(member.value()).toString());
                    accepted.add(member.value());
                }
                JsonObject binding = new JsonObject(); binding.addProperty("present", current.isPresent());
                binding.add("members", strings(names)); tags.put(key, binding);
                require(tags.size() <= MAX_TAGS, "забагато тегів ритуалу");
            } else throw new IllegalArgumentException("невідоме значення ingredient ритуалу");
        }
        return new Rule(accepted, amount);
    }
    private static List<Holder<?>> holders(HolderSet<?> set, Budget budget) {
        List<? extends Holder<?>> list = set.stream().limit(MAX_ENHANCERS + 1L).toList();
        require(list.size() <= MAX_ENHANCERS, "забагато підсилювачів ритуалу");
        budget.take(list.size()); return new ArrayList<>(list);
    }
    @SuppressWarnings("unchecked")
    private static JsonElement enhancer(Holder<?> holder, Registry<Object> registry, HolderLookup.Provider provider) {
        Object value = holder.value();
        require(registry.get(ResourceLocation.parse(id(holder))) == value, "застаріле визначення підсилювача");
        require(value.getClass().getName().equals(BASE + "item.enhancer.EnhancerDefinition"), "невідомий тип підсилювача");
        List<?> effects = (List<?>)call(value, "effects");
        require(effects.size() <= MAX_EFFECTS, "забагато ефектів підсилювача");
        for (Object conditional : effects) {
            require(conditional.getClass().getName().equals(BASE + "item.enhancer.effect.ConditionalEnhancerEffect"), "невідомий умовний ефект підсилювача");
            Object effect = call(conditional, "effect");
            require(EFFECTS.contains(effect.getClass().getSimpleName())
                    && effect.getClass().getName().equals(BASE + "item.enhancer.effect." + effect.getClass().getSimpleName()), "непідтримуваний ефект підсилювача");
            Optional<?> conditions = (Optional<?>)call(conditional, "conditions");
            if (conditions.isPresent()) {
                List<?> list = (List<?>)conditions.get();
                require(list.size() <= MAX_CONDITIONS, "забагато умов підсилювача");
                for (Object condition : list) require(condition.getClass().getName().equals(BASE + "item.enhancer.condition.TimeCondition"), "непідтримувана умова підсилювача");
            }
        }
        try {
            Codec<Object> codec = (Codec<Object>)value.getClass().getField("CODEC").get(null);
            return codec.encodeStart(RegistryOps.create(JsonOps.INSTANCE, provider), value).getOrThrow();
        } catch (ReflectiveOperationException failure) { throw new IllegalArgumentException("не вдалося закодувати підсилювач", failure); }
    }
    private static final class JsonBudget { int nodes, characters; }
    private static void bounded(JsonElement data, int depth, JsonBudget budget) {
        require(depth <= 32 && ++budget.nodes <= 65536, "завелике або надто вкладене визначення залежностей");
        if (data.isJsonObject()) {
            require(data.getAsJsonObject().size() <= 128, "завеликий об'єкт залежностей");
            for (var entry : data.getAsJsonObject().entrySet()) {
                budget.characters += entry.getKey().length(); bounded(entry.getValue(), depth + 1, budget);
            }
        } else if (data.isJsonArray()) {
            require(data.getAsJsonArray().size() <= MAX_MEMBERS, "завеликий масив залежностей");
            for (JsonElement value : data.getAsJsonArray()) bounded(value, depth + 1, budget);
        } else if (data.isJsonPrimitive()) {
            int length = data.getAsString().length();
            require(length <= 4096, "завелике значення залежностей"); budget.characters += length;
        }
        require(budget.characters <= 262144, "завеликий текст визначення залежностей");
    }
    private static JsonElement ordered(JsonElement data) {
        if (data.isJsonObject()) {
            JsonObject result = new JsonObject();
            data.getAsJsonObject().keySet().stream().sorted().forEach(k -> result.add(k, ordered(data.getAsJsonObject().get(k)))); return result;
        }
        if (data.isJsonArray()) {
            JsonArray result = new JsonArray(); data.getAsJsonArray().forEach(v -> result.add(ordered(v))); return result;
        }
        return data;
    }
    private static String hash(JsonElement data) {
        bounded(data, 0, new JsonBudget());
        try { return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(ordered(data).toString().getBytes(StandardCharsets.UTF_8))); }
        catch (java.security.NoSuchAlgorithmException impossible) { throw new AssertionError(impossible); }
    }

    /** Validate current vanilla input matching as well as definitions, BEFORE native callbacks/payment. */
    public static Snapshot capture(Object ritual, Registry<Object> enhancers, List<?> installed,
                                   HolderLookup.Provider provider, List<ItemStack> pedestals, ItemStack main) {
        require(ritual.getClass().getName().equals(BASE + "block.entity.forge.ritual.Ritual"), "невідомий тип ритуалу");
        Budget budget = new Budget(); Map<String, JsonElement> itemTags = new TreeMap<>();
        Rule primary = ingredient((Ingredient)call(ritual, "mainIngredient"), 1, itemTags, budget);
        List<?> inputs = (List<?>)call(ritual, "inputs");
        require(!inputs.isEmpty() && inputs.size() <= 8 && pedestals.size() <= 128, "непідтримуваний розмір ритуалу");
        List<Rule> rules = new ArrayList<>();
        for (Object input : inputs) {
            require(input.getClass().getName().equals(BASE + "block.entity.forge.ritual.RitualInput"), "невідомий тип входу ритуалу");
            int amount = ((Number)call(input, "amount")).intValue();
            require(amount > 0 && amount <= 128, "непідтримувана кількість входів ритуалу");
            rules.add(ingredient((Ingredient)call(input, "ingredient"), amount, itemTags, budget));
        }
        require(primary.test(main), "основний предмет не відповідає поточним тегам ритуалу");
        List<ItemStack> remaining = new ArrayList<>(pedestals);
        for (Rule rule : rules) {
            int found = 0; var iterator = remaining.iterator();
            while (iterator.hasNext() && found < rule.amount) if (rule.test(iterator.next())) { iterator.remove(); found++; }
            require(found == rule.amount, "п'єдестали не відповідають поточним тегам ритуалу");
        }
        require(remaining.stream().allMatch(ItemStack::isEmpty), "зайві входи ритуалу");

        Object requirements = call(ritual, "requirements");
        require(requirements.getClass().getName().equals(BASE + "block.entity.forge.ritual.RitualRequirements"), "невідомий тип вимог ритуалу");
        HolderSet<?> required = (HolderSet<?>)call(requirements, "enhancers");
        List<Holder<?>> requiredMembers = holders(required, budget);
        JsonObject dependency = new JsonObject(), tags = new JsonObject(), definitions = new JsonObject();
        itemTags.forEach(tags::add); dependency.add("item_tags", tags);
        if (required.unwrapKey().isPresent()) {
            var key = required.unwrapKey().get();
            // Re-resolve even when the old Named object survives a tag/registry reload.
            @SuppressWarnings("unchecked")
            var typedKey = (net.minecraft.tags.TagKey<Object>)key;
            HolderSet<?> current = enhancers.getTag(typedKey).orElseThrow(() -> new IllegalArgumentException("тег підсилювачів відсутній"));
            List<Holder<?>> currentMembers = holders(current, budget);
            Set<String> names = new java.util.TreeSet<>(), nativeNames = new HashSet<>();
            currentMembers.forEach(h -> names.add(id(h))); requiredMembers.forEach(h -> nativeNames.add(id(h)));
            require(names.equals(nativeNames), "застарілий тег вимог підсилювачів");
            for (Holder<?> old : requiredMembers) require(enhancers.get(ResourceLocation.parse(id(old))) == old.value(), "застаріле визначення вимоги підсилювача");
            dependency.addProperty("enhancer_tag", key.location().toString()); dependency.add("enhancer_members", strings(names));
            requiredMembers = currentMembers;
        }
        require(installed.size() <= 4, "забагато встановлених підсилювачів");
        Map<String, JsonElement> used = new TreeMap<>();
        List<Holder<?>> all = new ArrayList<>(requiredMembers);
        for (Object entry : installed) {
            require(entry instanceof Holder<?>, "невідомий встановлений підсилювач");
            all.add((Holder<?>)entry);
        }
        for (Holder<?> holder : all) {
            String name = id(holder);
            require(enhancers.get(ResourceLocation.parse(name)) == holder.value(), "застаріле визначення підсилювача");
            if (!used.containsKey(name)) {
                JsonElement encoded = enhancer(holder, enhancers, provider);
                bounded(encoded, 0, new JsonBudget()); used.put(name, encoded);
            }
        }
        used.forEach(definitions::add);
        dependency.add("enhancers", definitions);
        return new Snapshot(hash(dependency), !itemTags.isEmpty() || required.unwrapKey().isPresent() || !used.isEmpty());
    }
    /** Only attach at verified native payment. Never upgrade an old receipt from today's datapack. */
    public static void attach(CompoundTag active, Snapshot snapshot) {
        require(active != null && !active.contains(ACTIVE_TAG), "залежності оплати вже існують");
        CompoundTag tag = new CompoundTag(); tag.putInt("schema", 1); tag.putString("fingerprint", snapshot.fingerprint);
        active.put(ACTIVE_TAG, tag);
    }
    public static boolean matches(Tag retained, Snapshot snapshot) {
        if (!(retained instanceof CompoundTag active)) return false;
        if (!active.contains(ACTIVE_TAG)) return !snapshot.hasDependencies;
        if (!(active.get(ACTIVE_TAG) instanceof CompoundTag tag)) return false;
        return tag.getAllKeys().equals(Set.of("schema", "fingerprint")) && tag.contains("schema", Tag.TAG_INT)
                && tag.getInt("schema") == 1 && tag.contains("fingerprint", Tag.TAG_STRING)
                && snapshot.fingerprint.equals(tag.getString("fingerprint"));
    }
}
