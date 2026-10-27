package ua.aia2.guard;

import java.util.OptionalInt;
import java.util.function.Consumer;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.network.RegistryFriendlyByteBuf;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.MenuProvider;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.block.entity.BlockEntity;

/** Permission for the actual wearer or receiving storage, independent of EMC map readiness. */
public final class ProjectEPassiveAccess {
    private ProjectEPassiveAccess() {}
    public static boolean isProjectE(ItemStack stack) {
        return stack != null && !stack.isEmpty() && BuiltInRegistries.ITEM.getKey(stack.getItem()).getNamespace().equals("projecte");
    }
    public static boolean mayUse(Player player, ItemStack stack) {
        if (player == null || stack == null || stack.isEmpty()) return false;
        if (player.level().isClientSide()) return true;
        if (!(player instanceof ServerPlayer server) || !Aia2MachineGuard.isReady()) return false;
        String team = Aia2MachineGuard.synchronizedPlayerTeam(server);
        return !team.isBlank() && (!isProjectE(stack) || Aia2MachineGuard.mayObserveStage(team, 45))
                && Aia2MachineGuard.mayCraft(player, stack);
    }
    public static boolean mayUseEntity(Entity entity, ItemStack stack) {
        return entity instanceof Player player && mayUse(player, stack);
    }
    /** The native Curios shortcut has no hand; retain its real tablet floor on the resulting menu. */
    public static OptionalInt openTablet(Item item, Player player, MenuProvider provider,
                                         Consumer<RegistryFriendlyByteBuf> writer) {
        ItemStack source = new ItemStack(item);
        if (!mayUse(player, source)) return OptionalInt.empty();
        var previous = player.containerMenu;
        OptionalInt opened = player.openMenu(provider, writer);
        if (opened.isPresent() && player.containerMenu != previous) {
            String id = BuiltInRegistries.ITEM.getKey(item).toString();
            ProjectEAccess.markMenuSource(player.containerMenu, Math.max(45, Aia2MachineGuard.getRequiredItemStage(id)));
        }
        return opened;
    }
    public static boolean mayUseStored(BlockEntity receiver, ItemStack stack) {
        if (receiver == null || stack == null || stack.isEmpty()
                || !(receiver.getLevel() instanceof ServerLevel level) || receiver.isRemoved()
                || !level.getServer().isSameThread() || !level.hasChunkAt(receiver.getBlockPos())
                || level.getBlockEntity(receiver.getBlockPos()) != receiver || !Aia2MachineGuard.isReady()) return false;
        return Aia2MachineGuard.mayProduce(receiver, stack);
    }
}
