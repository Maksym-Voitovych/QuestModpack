package ua.aia2.guard;

import java.lang.reflect.InvocationTargetException;
import java.lang.reflect.Method;
import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.neoforged.neoforge.items.IItemHandler;

/** Guards the native capability dispatch, without changing stored stacks or cooldowns. */
public final class ProjectEStorageAccess {
    private static final ClassValue<Method> BAG = method("IAlchBagItem", "updateInAlchBag", IItemHandler.class, Player.class, ItemStack.class);
    private static final ClassValue<Method> CHEST = method("IAlchChestItem", "updateInAlchChest", Level.class, BlockPos.class, ItemStack.class);
    private static final ClassValue<Method> PEDESTAL = method("IPedestalItem", "updateInPedestal", ItemStack.class, Level.class, BlockPos.class, BlockEntity.class);
    private ProjectEStorageAccess() {}

    private static ClassValue<Method> method(String contract, String name, Class<?>... arguments) {
        return new ClassValue<>() {
            @Override protected Method computeValue(Class<?> type) {
                try {
                    Class<?> api = Class.forName("moze_intel.projecte.api.capabilities.item." + contract, false, type.getClassLoader());
                    if (!api.isAssignableFrom(type)) throw new IllegalArgumentException("Capability does not implement " + contract);
                    // Invoke through the public API, not a possibly private addon implementation.
                    return api.getMethod(name, arguments);
                }
                catch (ReflectiveOperationException unavailable) {
                    throw new IllegalStateException("Unsupported ProjectE passive capability " + name, unavailable);
                }
            }
        };
    }

    private static boolean invoke(Method method, Object capability, Object... arguments) {
        try { return Boolean.TRUE.equals(method.invoke(capability, arguments)); }
        catch (InvocationTargetException nativeFailure) {
            // A denied call returns false. An actual native error must remain visible.
            Throwable cause = nativeFailure.getCause();
            if (cause instanceof RuntimeException error) throw error;
            if (cause instanceof Error error) throw error;
            throw new IllegalStateException("ProjectE passive capability failed", cause);
        } catch (ReflectiveOperationException unavailable) {
            throw new IllegalStateException("Could not invoke ProjectE passive capability", unavailable);
        }
    }

    public static boolean bag(Object capability, IItemHandler inventory, Player player, ItemStack stack) {
        if (capability == null || inventory == null || player == null || stack == null || stack.isEmpty()) return false;
        if (!player.level().isClientSide()) {
            // All 16 installed bag colors are epoch45. Gating only the inner item
            // would let an imported bag run an earlier addon's capability before45.
            if (!(player instanceof ServerPlayer server)) return false;
            String team = Aia2MachineGuard.synchronizedPlayerTeam(server);
            if (team.isBlank() || !Aia2MachineGuard.mayObserveStage(team, 45)) return false;
        }
        if (!ProjectEPassiveAccess.mayUse(player, stack)) return false;
        BlockEntity parent = Aia2MachineGuard.enterTick(null);
        try { return invoke(BAG.get(capability.getClass()), capability, inventory, player, stack); }
        finally { Aia2MachineGuard.exitTick(parent); }
    }

    public static boolean chest(Object capability, Level level, BlockPos pos, ItemStack stack, BlockEntity receiver) {
        if (capability == null || level == null || pos == null || stack == null || stack.isEmpty()) return false;
        if (!canonical(level, pos, receiver) || !ProjectEPassiveAccess.mayUseStored(receiver, stack)) return false;
        BlockEntity parent = Aia2MachineGuard.enterTick(receiver);
        try { return invoke(CHEST.get(capability.getClass()), capability, level, pos, stack); }
        finally { Aia2MachineGuard.exitTick(parent); }
    }

    public static boolean pedestal(Object capability, ItemStack stack, Level level, BlockPos pos, BlockEntity receiver) {
        if (capability == null || level == null || pos == null || stack == null || stack.isEmpty()
                || !canonical(level, pos, receiver) || !ProjectEPassiveAccess.mayUseStored(receiver, stack)) return false;
        BlockEntity parent = Aia2MachineGuard.enterTick(receiver);
        try { return invoke(PEDESTAL.get(capability.getClass()), capability, stack, level, pos, receiver); }
        finally { Aia2MachineGuard.exitTick(parent); }
    }

    private static boolean canonical(Level level, BlockPos pos, BlockEntity receiver) {
        return receiver != null && receiver.getLevel() == level && receiver.getBlockPos().equals(pos)
                && level.getBlockEntity(pos) == receiver;
    }
}
