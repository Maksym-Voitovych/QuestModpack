package ua.aia2.guard;

import com.google.gson.JsonParser;
import java.lang.reflect.Field;
import java.lang.reflect.Method;
import java.util.HashMap;
import java.util.Map;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;

/** Current output policy for an already-open ProjectE transmutation menu. */
public final class ProjectEAccess {
    private static volatile Map<String, Long> allowed = Map.of();
    private record EmcApi(Object proxy, Method value) {}
    private static volatile EmcApi api;
    private record MenuFields(Field hand, Field stack, Field inventory) {}
    private static final ClassValue<MenuFields> MENUS = new ClassValue<>() {
        @Override protected MenuFields computeValue(Class<?> type) {
            try { return new MenuFields(type.getField("hand"), field(type, "stack"), type.getField("transmutationInventory")); }
            catch (ReflectiveOperationException unavailable) { throw new IllegalStateException("Unsupported ProjectE menu", unavailable); }
        }
    };
    private static final ClassValue<Field> INVENTORY = new ClassValue<>() {
        @Override protected Field computeValue(Class<?> type) {
            for (Class<?> owner = type; owner != null; owner = owner.getSuperclass()) {
                try { Field field = owner.getDeclaredField("inv"); field.setAccessible(true); return field; }
                catch (NoSuchFieldException next) { /* The exact native output slot owns this field. */ }
            }
            throw new IllegalStateException("Unsupported ProjectE output slot");
        }
    };
    private ProjectEAccess() {}

    private static Field field(Class<?> type, String name) throws NoSuchFieldException {
        for (Class<?> owner = type; owner != null; owner = owner.getSuperclass()) {
            try { var field = owner.getDeclaredField(name); field.setAccessible(true); return field; }
            catch (NoSuchFieldException next) { /* Exact inherited native field. */ }
        }
        throw new NoSuchFieldException(name);
    }

    /** Called before rebuilding EMC; old cached output slots must fail closed immediately. */
    public static void pause() { allowed = Map.of(); }

    /** Unique signature, supplied only after the final EMC map and fuel cache succeed. */
    public static void configureWhitelistJson(String json) {
        pause();
        var parsed = JsonParser.parseString(json);
        if (!parsed.isJsonObject() || parsed.getAsJsonObject().isEmpty()) throw new IllegalArgumentException("ProjectE whitelist requires an object");
        var checked = new HashMap<String, Long>();
        for (var entry : parsed.getAsJsonObject().entrySet()) {
            String id = entry.getKey(); var value = entry.getValue();
            if (!value.isJsonPrimitive() || !value.getAsJsonPrimitive().isNumber()
                    || ResourceLocation.tryParse(id) == null || !BuiltInRegistries.ITEM.containsKey(ResourceLocation.parse(id))) {
                throw new IllegalArgumentException("Invalid ProjectE whitelist entry " + id);
            }
            double raw = value.getAsDouble(); long exact = value.getAsLong();
            if (!Double.isFinite(raw) || raw != exact || exact <= 0 || exact > 9007199254740991L
                    || KeyProductionBridge.isKeyOutput(id) || id.matches("kubejs:aia2_(tech|arcane|epoch)_key_[0-9]{2}")) {
                throw new IllegalArgumentException("Invalid ProjectE whitelist amount/key " + id);
            }
            checked.put(id, exact);
        }
        allowed = Map.copyOf(checked);
    }

    public static boolean isTransmutation(Object menu) {
        if (menu == null) return false;
        for (Class<?> type = menu.getClass(); type != null; type = type.getSuperclass()) {
            if (type.getName().equals("moze_intel.projecte.gameObjs.container.TransmutationContainer")) return true;
        }
        return false;
    }

    public static boolean mayUseMenu(Player player) {
        if (player == null) return false;
        if (player.level().isClientSide()) return true;
        if (!(player instanceof ServerPlayer server) || allowed.isEmpty()) return false;
        String team = Aia2MachineGuard.synchronizedPlayerTeam(server);
        return !team.isBlank() && Aia2MachineGuard.mayObserveStage(team, 45);
    }

    public static boolean mayExtract(Player player, ItemStack output) {
        if (player != null && player.level().isClientSide()) return true;
        if (!mayUseMenu(player) || output == null || output.isEmpty() || !output.getComponentsPatch().isEmpty()) return false;
        String id = BuiltInRegistries.ITEM.getKey(output.getItem()).toString();
        Long expected = allowed.get(id);
        if (expected == null || KeyProductionBridge.isKeyOutput(id) || !Aia2MachineGuard.mayCraft(player, output)) return false;
        try {
            EmcApi current = api;
            if (current == null) {
                Class<?> type = Class.forName("moze_intel.projecte.api.proxy.IEMCProxy");
                current = new EmcApi(type.getField("INSTANCE").get(null), type.getMethod("getValue", ItemStack.class));
                api = current;
            }
            Object value = current.value().invoke(current.proxy(), output);
            return value instanceof Number number && number.longValue() == expected;
        } catch (ReflectiveOperationException | RuntimeException unavailable) { return false; }
    }

    /** Recheck the actual held-tablet tier as well as the common table stage. */
    public static boolean mayUseContainer(Player player, Object menu) {
        if (!isTransmutation(menu) || !mayUseMenu(player)) return false;
        try {
            var fields = MENUS.get(menu.getClass());
            if (fields.hand().get(menu) == null) return true;
            return fields.stack().get(menu) instanceof ItemStack stack && !stack.isEmpty()
                    && Aia2MachineGuard.mayCraft(player, stack);
        } catch (ReflectiveOperationException | RuntimeException unavailable) { return false; }
    }

    public static boolean mayExtractSlot(Object slot, ItemStack output) {
        try {
            Object inventory = INVENTORY.get(slot.getClass()).get(slot);
            Object player = inventory.getClass().getField("player").get(inventory);
            return player instanceof Player owner && mayUseContainer(owner, owner.containerMenu)
                    && MENUS.get(owner.containerMenu.getClass()).inventory().get(owner.containerMenu) == inventory
                    && mayExtract(owner, output);
        } catch (ReflectiveOperationException | RuntimeException unavailable) { return false; }
    }
}
