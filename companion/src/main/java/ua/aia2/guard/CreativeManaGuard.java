package ua.aia2.guard;

import net.minecraft.core.component.DataComponents;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.component.CustomData;
import net.minecraft.world.level.block.entity.BlockEntity;

import java.util.ArrayList;
import java.util.List;

/** Botania Revived1.0.2: finite and creative tablets share a registry ID. */
public final class CreativeManaGuard {
    private static final ResourceLocation TABLET = ResourceLocation.fromNamespaceAndPath("botania", "mana_tablet");

    private CreativeManaGuard() {}

    public static boolean isCreativeTablet(ItemStack stack) {
        return !stack.isEmpty() && TABLET.equals(BuiltInRegistries.ITEM.getKey(stack.getItem()))
                && stack.getOrDefault(DataComponents.CUSTOM_DATA, CustomData.EMPTY).copyTag().getBoolean("creative");
    }

    /** Preserve the native list and stack identities unless a locked variant is present. */
    public static List<ItemStack> filterPlayerSupplies(Player player, List<ItemStack> sources) {
        if (sources == null || sources.isEmpty() || Aia2MachineGuard.mayUsePostgameMana(player)) return sources;
        ArrayList<ItemStack> filtered = null;
        for (int index = 0; index < sources.size(); index++) {
            ItemStack stack = sources.get(index);
            if (isCreativeTablet(stack)) {
                if (filtered == null) filtered = new ArrayList<>(sources.subList(0, index));
            } else if (filtered != null) filtered.add(stack);
        }
        return filtered == null ? sources : filtered;
    }

    /** A thrown/imported tablet must not bypass the player's restriction through a pool. */
    public static boolean mayExchangeWithPool(BlockEntity pool, ItemStack stack) {
        if (!isCreativeTablet(stack)) return true;
        if (pool == null || pool.getLevel() == null) return false;
        return pool.getLevel().isClientSide() || pool.getLevel() instanceof ServerLevel
                && Aia2MachineGuard.mayObserveStage(Aia2MachineGuard.getOwner(pool), 99);
    }
}
