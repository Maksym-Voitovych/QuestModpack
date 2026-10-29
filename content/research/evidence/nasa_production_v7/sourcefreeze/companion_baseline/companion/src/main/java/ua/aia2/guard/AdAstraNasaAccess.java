package ua.aia2.guard;

import java.lang.reflect.Field;
import java.lang.reflect.Method;
import java.util.Set;
import java.util.concurrent.ConcurrentHashMap;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.Container;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.inventory.AbstractContainerMenu;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.crafting.Recipe;
import net.minecraft.world.item.crafting.RecipeInput;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.neoforged.neoforge.common.util.FakePlayer;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

/** Ad Astra 1.16.26: guard cached NASA recipes before either native craft caller. */
public final class AdAstraNasaAccess {
    private static final String MACHINE = "earth.terrarium.adastra.common.blockentities.machines.NasaWorkbenchBlockEntity";
    private static final String MENU = "earth.terrarium.adastra.common.menus.machines.NasaWorkbenchMenu";
    private static final String RECIPE = "earth.terrarium.adastra.common.recipes.machines.NasaWorkbenchRecipe";
    private static final Logger LOGGER = LoggerFactory.getLogger(AdAstraNasaAccess.class);
    private static final Set<Class<?>> WARNED = ConcurrentHashMap.newKeySet();
    private static final ClassValue<Field> CACHED_RECIPE = new ClassValue<>() {
        @Override protected Field computeValue(Class<?> type) {
            try {
                for (Class<?> owner = type; owner != null; owner = owner.getSuperclass()) {
                    if (!owner.getName().equals(MACHINE)) continue;
                    Field field = owner.getDeclaredField("recipe");
                    field.setAccessible(true);
                    return field;
                }
                throw new NoSuchFieldException("NASA cached recipe");
            } catch (ReflectiveOperationException failure) {
                throw new IllegalStateException("Unsupported Ad Astra NASA recipe cache", failure);
            }
        }
    };
    private static final ClassValue<Method> RESULT = new ClassValue<>() {
        @Override protected Method computeValue(Class<?> type) {
            try {
                if (!type.getName().equals(RECIPE)) throw new NoSuchMethodException("NASA recipe record");
                return type.getMethod("result");
            } catch (ReflectiveOperationException failure) {
                throw new IllegalStateException("Unsupported Ad Astra NASA result", failure);
            }
        }
    };
    private static final ClassValue<Method> ENTITY = new ClassValue<>() {
        @Override protected Method computeValue(Class<?> type) {
            try { return type.getMethod("getEntity"); }
            catch (ReflectiveOperationException failure) {
                throw new IllegalStateException("Unsupported Ad Astra NASA menu", failure);
            }
        }
    };

    private record Input(Container container) implements RecipeInput {
        @Override public ItemStack getItem(int slot) { return container.getItem(slot); }
        @Override public int size() { return 14; }
    }

    private AdAstraNasaAccess() {}

    private static boolean isType(Class<?> type, String expected) {
        for (Class<?> owner = type; owner != null; owner = owner.getSuperclass())
            if (owner.getName().equals(expected)) return true;
        return false;
    }

    private static boolean canonical(BlockEntity machine) {
        return machine != null && isType(machine.getClass(), MACHINE)
                && machine.getLevel() instanceof ServerLevel level && level.getServer().isSameThread()
                && !machine.isRemoved() && level.hasChunkAt(machine.getBlockPos())
                && level.getBlockEntity(machine.getBlockPos()) == machine && Aia2MachineGuard.isReady()
                && !Aia2MachineGuard.getOwner(machine).isBlank();
    }

    private static boolean unsupported(Object host, Exception failure) {
        if (host != null && WARNED.add(host.getClass()))
            LOGGER.error("[AIA2] Ad Astra NASA access denied: unsupported native state in {}", host.getClass().getName(), failure);
        return false;
    }

    /** Preview selection may run before slot14 has been populated, so it is not a payment proof. */
    public static boolean maySelect(BlockEntity machine) { return check(machine, false); }

    /** Called before particles, dropped output, slot writes or native14slot consumption. */
    public static boolean mayFinish(BlockEntity machine) { return check(machine, true); }

    @SuppressWarnings("unchecked")
    private static boolean check(BlockEntity machine, boolean requirePreview) {
        if (machine == null || machine.getLevel() == null) return false;
        if (machine.getLevel().isClientSide()) return true;
        if (!canonical(machine) || !(machine instanceof Container container) || container.getContainerSize() != 15)
            return false;
        try {
            Object cached = CACHED_RECIPE.get(machine.getClass()).get(machine);
            if (!(cached instanceof Recipe<?> recipe) || !cached.getClass().getName().equals(RECIPE)) return false;
            // The guard's generation-aware identity index rejects removed/reloaded cached objects.
            if (!Aia2MachineGuard.mayProcessRecipe(machine, recipe)) return false;
            Object value = RESULT.get(cached.getClass()).invoke(cached);
            if (!(value instanceof ItemStack output) || output.isEmpty()) return false;
            String id = net.minecraft.core.registries.BuiltInRegistries.ITEM.getKey(output.getItem()).toString();
            if (id.matches("kubejs:aia2_(tech|arcane|epoch)_key_[0-9]{2}") || KeyProductionBridge.isKeyOutput(id)
                    || !Aia2MachineGuard.mayProduce(machine, output)) return false;
            if (!((Recipe<RecipeInput>)recipe).matches(new Input(container), machine.getLevel())) return false;
            if (requirePreview) {
                ItemStack preview = container.getItem(14);
                if (preview.isEmpty() || preview.getCount() != output.getCount()
                        || !ItemStack.isSameItemSameComponents(preview, output)) return false;
            }
            return true;
        } catch (ReflectiveOperationException | RuntimeException failure) {
            return unsupported(machine, failure);
        }
    }

    public static boolean isNasaMenu(Object menu) { return menu != null && isType(menu.getClass(), MENU); }

    /** The native base menu always returns true; validate its final, original block entity. */
    public static boolean mayUseMenu(Object menu, Player player) {
        if (!isNasaMenu(menu) || player == null) return false;
        if (player.level().isClientSide()) return true;
        if (!(player instanceof ServerPlayer real) || real instanceof FakePlayer
                || !(menu instanceof AbstractContainerMenu) || player.containerMenu != menu) return false;
        try {
            Object value = ENTITY.get(menu.getClass()).invoke(menu);
            if (!(value instanceof BlockEntity machine) || !canonical(machine) || machine.getLevel() != player.level())
                return false;
            String team = Aia2MachineGuard.synchronizedPlayerTeam(real);
            return !team.isBlank() && team.equals(Aia2MachineGuard.getOwner(machine))
                    && Aia2MachineGuard.mayTick(machine) && Container.stillValidBlockEntity(machine, player)
                    && real.serverLevel().mayInteract(real, machine.getBlockPos());
        } catch (ReflectiveOperationException | RuntimeException failure) {
            return unsupported(menu, failure);
        }
    }
}
