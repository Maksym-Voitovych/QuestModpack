package ua.aia2.guard;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.WeakHashMap;
import java.util.function.BiConsumer;
import net.minecraft.core.Holder;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.ai.attributes.Attribute;
import net.minecraft.world.entity.ai.attributes.AttributeModifier;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;

/** Reconciles transient vanilla equipment attributes without changing any item or equipment cache. */
public final class ProjectEArmorAttributes {
    private record Key(Holder<Attribute> attribute, ResourceLocation id) {}
    private static final class Frame {
        List<ItemStack> equipment = List.of();
        long allowed;
        final Set<Key> suppressed = new HashSet<>();
    }
    private static final Map<Player, Frame> FRAMES = new WeakHashMap<>();
    private ProjectEArmorAttributes() {}

    private static boolean projecte(ItemStack stack) {
        return !stack.isEmpty() && BuiltInRegistries.ITEM.getKey(stack.getItem()).getNamespace().equals("projecte");
    }

    /** Only the NEW application edge is filtered. Vanilla removal always receives the original stack. */
    public static void apply(LivingEntity entity, ItemStack stack, EquipmentSlot slot,
                             BiConsumer<Holder<Attribute>, AttributeModifier> action) {
        if (entity instanceof Player player && projecte(stack)
                && !ProjectEPassiveAccess.mayUse(player, stack)) return;
        stack.forEachModifier(slot, action);
    }

    /** Called after vanilla's normal equipment update. Stable stacks/stages do no modifier writes. */
    public static void reconcile(Player player, Map<EquipmentSlot, ItemStack> vanillaChanges) {
        if (player.level().isClientSide()) return;
        EquipmentSlot[] slots = EquipmentSlot.values();
        Frame old = FRAMES.get(player);
        List<ItemStack> current = new ArrayList<>(slots.length);
        boolean hasProjectE = false;
        long allowed = 0;
        boolean same = old != null && old.equipment.size() == slots.length;
        for (EquipmentSlot slot : slots) {
            ItemStack stack = player.getItemBySlot(slot);
            current.add(stack);
            if (projecte(stack)) {
                hasProjectE = true;
                if (ProjectEPassiveAccess.mayUse(player, stack)) allowed |= 1L << slot.ordinal();
            }
            if (same && !ItemStack.matches(stack, old.equipment.get(slot.ordinal()))) same = false;
        }
        if (!hasProjectE && (old == null || old.suppressed.isEmpty())) { FRAMES.remove(player); return; }
        if (same && old.allowed == allowed && (vanillaChanges == null || vanillaChanges.isEmpty())) return;

        Frame frame = old == null ? new Frame() : old;
        Map<Key, List<AttributeModifier>> blocked = new HashMap<>();
        Map<Key, AttributeModifier> activeProjectE = new HashMap<>();
        Set<Key> otherActive = new HashSet<>();
        for (EquipmentSlot slot : slots) {
            ItemStack stack = current.get(slot.ordinal());
            if (stack.isEmpty()) continue;
            boolean pe = projecte(stack);
            boolean usable = !pe || (allowed & 1L << slot.ordinal()) != 0;
            stack.forEachModifier(slot, (attribute, modifier) -> {
                Key key = new Key(attribute, modifier.id());
                if (!pe) otherActive.add(key);
                else if (usable) activeProjectE.put(key, modifier);
                else blocked.computeIfAbsent(key, ignored -> new ArrayList<>()).add(modifier);
            });
        }

        for (var entry : blocked.entrySet()) {
            Key key = entry.getKey();
            // An unrelated equipped item with the same attribute ID keeps its own effect.
            if (otherActive.contains(key) || activeProjectE.containsKey(key)
                    || ProjectECurioAttributes.hasAllowedModifier(player, key.attribute(), key.id())) continue;
            frame.suppressed.add(key);
            var instance = player.getAttribute(key.attribute());
            if (instance != null) {
                AttributeModifier actual = instance.getModifier(key.id());
                if (actual != null && entry.getValue().contains(actual)) instance.removeModifier(key.id());
            }
        }
        var pending = frame.suppressed.iterator();
        while (pending.hasNext()) {
            Key key = pending.next();
            boolean curioActive = ProjectECurioAttributes.hasAllowedModifier(player, key.attribute(), key.id());
            if (blocked.containsKey(key) && !otherActive.contains(key) && !activeProjectE.containsKey(key)
                    && !curioActive) continue;
            AttributeModifier restored = activeProjectE.get(key);
            if (restored != null && !otherActive.contains(key) && !curioActive) {
                var instance = player.getAttribute(key.attribute());
                if (instance != null && instance.getModifier(key.id()) == null) instance.addTransientModifier(restored);
            }
            pending.remove();
        }
        frame.equipment = current.stream().map(ItemStack::copy).toList();
        frame.allowed = allowed;
        if (!hasProjectE && frame.suppressed.isEmpty()) FRAMES.remove(player);
        else FRAMES.put(player, frame);
    }
}
