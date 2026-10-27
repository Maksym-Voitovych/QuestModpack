package ua.aia2.guard;

import com.google.common.collect.LinkedHashMultimap;
import com.google.common.collect.Multimap;
import com.mojang.logging.LogUtils;
import java.lang.reflect.InvocationTargetException;
import java.lang.reflect.Method;
import java.util.HashMap;
import java.util.HashSet;
import java.util.Map;
import java.util.Set;
import java.util.WeakHashMap;
import net.minecraft.core.Holder;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.ai.attributes.Attribute;
import net.minecraft.world.entity.ai.attributes.AttributeModifier;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.neoforged.neoforge.capabilities.EntityCapability;
import net.neoforged.neoforge.items.IItemHandler;

/** Reconciles ProjectE's advertised Curio attributes against the actual active Curios inventory. */
public final class ProjectECurioAttributes {
    private record Key(Holder<Attribute> attribute, ResourceLocation id) {}
    private record Api(EntityCapability<IItemHandler, Void> inventory, Class<?> attributes, Method add) {}
    private static final Map<Player, Map<Key, Set<AttributeModifier>>> PREVIOUS = new WeakHashMap<>();
    private static volatile Api api;
    private static volatile boolean unavailable;
    private ProjectECurioAttributes() {}

    @SuppressWarnings("unchecked")
    private static Api api() {
        if (api != null || unavailable) return api;
        synchronized (ProjectECurioAttributes.class) {
            if (api != null || unavailable) return api;
            try {
                Class<?> integration = Class.forName("moze_intel.projecte.integration.IntegrationHelper");
                Class<?> attributes = Class.forName("moze_intel.projecte.integration.curios.IExposesCurioAttributes");
                api = new Api((EntityCapability<IItemHandler, Void>) integration.getField("CURIO_ITEM_HANDLER").get(null),
                        attributes, attributes.getMethod("addAttributes", Multimap.class));
            } catch (ClassNotFoundException absent) {
                unavailable = true; // ProjectE is optional in a minimal server.
            } catch (ReflectiveOperationException | LinkageError incompatible) {
                unavailable = true;
                LogUtils.getLogger().error("[AIA2] ProjectE Curios attribute API unavailable; native dispatch needs verification", incompatible);
            }
            return api;
        }
    }

    private static Multimap<Holder<Attribute>, AttributeModifier> modifiers(Api contract, ItemStack stack) {
        Multimap<Holder<Attribute>, AttributeModifier> result = LinkedHashMultimap.create();
        if (stack.isEmpty() || !contract.attributes().isInstance(stack.getItem())) return result;
        try { contract.add().invoke(stack.getItem(), result); }
        catch (InvocationTargetException nativeFailure) {
            Throwable cause = nativeFailure.getCause();
            if (cause instanceof RuntimeException failure) throw failure;
            if (cause instanceof Error failure) throw failure;
            throw new IllegalStateException("ProjectE Curio attributes failed", cause);
        } catch (ReflectiveOperationException incompatible) {
            throw new IllegalStateException("Cannot read ProjectE Curio attributes", incompatible);
        }
        return result;
    }

    /** Used by the optional Curio capability without a hard Curios class dependency. */
    public static boolean mayExpose(Object slotContext, ItemStack stack) {
        if (slotContext == null) return false;
        try {
            Object wearer = slotContext.getClass().getMethod("entity").invoke(slotContext);
            return wearer instanceof LivingEntity entity && ProjectEPassiveAccess.mayUseEntity(entity, stack);
        } catch (ReflectiveOperationException incompatible) {
            throw new IllegalStateException("Unsupported ProjectE Curio SlotContext", incompatible);
        }
    }

    /** Protects a modifier contributed by an independently usable active Curio. */
    public static boolean hasAllowedModifier(Player player, Holder<Attribute> attribute, ResourceLocation id) {
        Api contract = api();
        if (contract == null) return false;
        IItemHandler handler = player.getCapability(contract.inventory());
        if (handler == null) return false;
        for (int slot = 0; slot < handler.getSlots(); slot++) {
            ItemStack stack = handler.getStackInSlot(slot);
            if (stack.isEmpty() || !ProjectEPassiveAccess.mayUse(player, stack)) continue;
            for (var entry : modifiers(contract, stack).entries())
                if (entry.getKey().equals(attribute) && entry.getValue().id().equals(id)) return true;
        }
        return false;
    }

    /** Server tick only; modifiers are changed only when missing, stale or denied. Items are never changed. */
    public static void reconcile(Player player) {
        if (player.level().isClientSide()) return;
        Api contract = api();
        if (contract == null) return;
        Map<Key, Set<AttributeModifier>> known = new HashMap<>();
        Map<Key, AttributeModifier> desired = new HashMap<>();
        IItemHandler handler = player.getCapability(contract.inventory());
        if (handler != null) for (int slot = 0; slot < handler.getSlots(); slot++) {
            ItemStack stack = handler.getStackInSlot(slot);
            if (stack.isEmpty()) continue;
            boolean allowed = ProjectEPassiveAccess.mayUse(player, stack);
            for (var entry : modifiers(contract, stack).entries()) {
                Key key = new Key(entry.getKey(), entry.getValue().id());
                known.computeIfAbsent(key, ignored -> new HashSet<>()).add(entry.getValue());
                if (allowed) desired.put(key, entry.getValue());
            }
        }
        Map<Key, Set<AttributeModifier>> previous = PREVIOUS.remove(player);
        Map<Key, Set<AttributeModifier>> tracked = new HashMap<>();
        known.forEach((key, values) -> tracked.put(key, new HashSet<>(values)));
        if (previous != null) previous.forEach((key, values) ->
                tracked.computeIfAbsent(key, ignored -> new HashSet<>()).addAll(values));
        // Players without any current or previous ProjectE Curio attributes need no equipment scan.
        if (tracked.isEmpty()) return;

        Set<Key> equipment = new HashSet<>();
        for (EquipmentSlot slot : EquipmentSlot.values()) {
            ItemStack stack = player.getItemBySlot(slot);
            if (stack.isEmpty() || (ProjectEPassiveAccess.isProjectE(stack) && !ProjectEPassiveAccess.mayUse(player, stack))) continue;
            stack.forEachModifier(slot, (attribute, modifier) -> equipment.add(new Key(attribute, modifier.id())));
        }
        for (var entry : tracked.entrySet()) {
            Key key = entry.getKey();
            if (equipment.contains(key)) continue;
            var instance = player.getAttribute(key.attribute());
            if (instance == null) continue;
            AttributeModifier current = instance.getModifier(key.id());
            AttributeModifier allowed = desired.get(key);
            if (allowed != null) {
                // Never overwrite an unrelated modifier with an equal ID but different native value.
                if (current == null) instance.addTransientModifier(allowed);
            } else if (current != null && entry.getValue().contains(current)) instance.removeModifier(key.id());
        }
        if (!known.isEmpty()) PREVIOUS.put(player, known);
    }
}
