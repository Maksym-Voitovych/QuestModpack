package dev.shadowsoffire.apothic_enchanting.objects;

import java.util.List;

import dev.shadowsoffire.apothic_enchanting.util.TooltipUtil;
import net.minecraft.ChatFormatting;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.player.Inventory;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.BookItem;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.item.TooltipFlag;
import net.minecraft.world.item.enchantment.EnchantmentHelper;
import net.minecraft.world.item.enchantment.ItemEnchantments;
import net.neoforged.neoforge.event.AnvilUpdateEvent;
import net.neoforged.neoforge.event.entity.player.AnvilRepairEvent;

public class ExtractionTomeItem extends BookItem {

    public ExtractionTomeItem(Item.Properties properties) {
        super(properties);
    }

    @Override
    public boolean isEnchantable(ItemStack stack) {
        return false;
    }

    @Override
    public void appendHoverText(ItemStack stack, TooltipContext context, List<Component> tooltip, TooltipFlag tooltipFlag) {
        if (stack.isEnchanted()) {
            return;
        }
        tooltip.add(TooltipUtil.lang("info", "extraction_tome").withStyle(ChatFormatting.GRAY));
        tooltip.add(TooltipUtil.lang("info", "extraction_tome2").withStyle(ChatFormatting.GRAY));
    }

    @Override
    public boolean isFoil(ItemStack pStack) {
        return true;
    }

    public static boolean updateAnvil(AnvilUpdateEvent ev) {
        ItemStack weapon = ev.getLeft();
        ItemStack book = ev.getRight();
        if (!(book.getItem() instanceof ExtractionTomeItem) || book.isEnchanted() || !weapon.isEnchanted()) {
            return false;
        }

        ItemEnchantments wepEnch = EnchantmentHelper.getEnchantmentsForCrafting(weapon);
        ItemStack out = new ItemStack(Items.ENCHANTED_BOOK);
        EnchantmentHelper.setEnchantments(out, wepEnch);
        ev.setMaterialCost(1);
        ev.setCost(wepEnch.size() * 16);
        ev.setOutput(out);
        return true;
    }

    protected static void giveItem(Player player, ItemStack stack) {
        if (!player.isAlive() || player instanceof ServerPlayer && ((ServerPlayer) player).hasDisconnected()) {
            player.drop(stack, false);
        }
        else {
            Inventory inventory = player.getInventory();
            if (inventory.player instanceof ServerPlayer) {
                inventory.placeItemBackInInventory(stack);
            }
        }
    }

    public static boolean updateRepair(AnvilRepairEvent ev) {
        ItemStack weapon = ev.getLeft();
        ItemStack book = ev.getRight();
        if (!(book.getItem() instanceof ExtractionTomeItem) || book.isEnchanted() || !weapon.isEnchanted()) return false;
        EnchantmentHelper.setEnchantments(weapon, ItemEnchantments.EMPTY);
        giveItem(ev.getEntity(), weapon);
        return true;
    }
}
