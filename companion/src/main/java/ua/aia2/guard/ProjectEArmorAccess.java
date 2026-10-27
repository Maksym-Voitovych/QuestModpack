package ua.aia2.guard;

import java.util.ArrayList;
import java.util.List;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;

/** Views used by native ProjectE armor calculations; the actual equipment is untouched. */
public final class ProjectEArmorAccess {
    private ProjectEArmorAccess() {}

    public static Iterable<ItemStack> armor(LivingEntity entity) {
        Iterable<ItemStack> original = entity.getArmorSlots();
        if (!(entity instanceof Player player)) return original;
        List<ItemStack> result = new ArrayList<>();
        boolean changed = false;
        for (ItemStack stack : original) {
            if (ProjectEPassiveAccess.mayUse(player, stack)) result.add(stack);
            else changed = true;
        }
        return changed ? List.copyOf(result) : original;
    }

    public static ItemStack equipment(Player player, EquipmentSlot slot) {
        ItemStack original = player.getItemBySlot(slot);
        return ProjectEPassiveAccess.mayUse(player, original) ? original : ItemStack.EMPTY;
    }

    public static boolean mayUseGemAbility(Player player, EquipmentSlot slot) {
        ItemStack original = player.getItemBySlot(slot);
        String expected = switch (slot) {
            case HEAD -> "projecte:gem_helmet";
            case CHEST -> "projecte:gem_chestplate";
            default -> "";
        };
        return !expected.isEmpty() && !original.isEmpty()
                && expected.equals(BuiltInRegistries.ITEM.getKey(original.getItem()).toString())
                && ProjectEPassiveAccess.mayUse(player, original);
    }
}
