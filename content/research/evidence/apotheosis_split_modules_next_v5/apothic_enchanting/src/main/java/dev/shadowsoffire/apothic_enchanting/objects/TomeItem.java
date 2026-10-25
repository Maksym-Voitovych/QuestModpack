package dev.shadowsoffire.apothic_enchanting.objects;

import java.util.List;

import dev.shadowsoffire.apothic_enchanting.ApothicEnchanting;
import dev.shadowsoffire.apothic_enchanting.api.EnchantableItem;
import dev.shadowsoffire.apothic_enchanting.util.TooltipUtil;
import net.minecraft.ChatFormatting;
import net.minecraft.core.Holder;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.network.chat.Component;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResultHolder;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.BookItem;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.item.TooltipFlag;
import net.minecraft.world.item.enchantment.Enchantment;
import net.minecraft.world.item.enchantment.EnchantmentHelper;
import net.minecraft.world.item.enchantment.EnchantmentInstance;
import net.minecraft.world.level.Level;

public class TomeItem extends BookItem implements EnchantableItem {

    final ItemStack rep;

    public TomeItem(Item rep) {
        super(new Item.Properties());
        this.rep = new ItemStack(rep);
        ApothicEnchanting.TYPED_BOOKS.add(this);
    }

    @Override
    public boolean isBookEnchantable(ItemStack stack, ItemStack book) {
        return stack.getCount() == 1;
    }

    @Override
    @SuppressWarnings("deprecation")
    public boolean isPrimaryItemFor(ItemStack stack, Holder<Enchantment> enchantment) {
        if (this.rep.isEmpty()) {
            // The Tome of the Others accepts enchantments that are not available on any of the other tomes.
            return ApothicEnchanting.TYPED_BOOKS.stream().filter(b -> b != this).allMatch(b -> !b.isPrimaryItemFor(b.getDefaultInstance(), enchantment));
        }
        return enchantment.value().isPrimaryItem(this.rep);
    }

    @Override
    public void appendHoverText(ItemStack stack, TooltipContext ctx, List<Component> tooltip, TooltipFlag tooltipFlag) {
        tooltip.add(TooltipUtil.lang("info", BuiltInRegistries.ITEM.getKey(this).getPath()).withStyle(ChatFormatting.GRAY));
        if (stack.isEnchanted()) {
            tooltip.add(TooltipUtil.lang("info", "tome_error").withStyle(ChatFormatting.RED));
        }
    }

    @Override
    public InteractionResultHolder<ItemStack> use(Level world, Player player, InteractionHand hand) {
        ItemStack stack = player.getItemInHand(hand);
        if (stack.isEnchanted()) {
            ItemStack book = new ItemStack(Items.ENCHANTED_BOOK, stack.getCount());
            EnchantmentHelper.setEnchantments(book, EnchantmentHelper.getEnchantmentsForCrafting(stack));
            return InteractionResultHolder.consume(book);
        }
        return InteractionResultHolder.pass(stack);
    }

    @Override
    public ItemStack applyEnchantments(ItemStack stack, List<EnchantmentInstance> enchantments) {
        stack = stack.transmuteCopy(Items.ENCHANTED_BOOK);

        for (EnchantmentInstance inst : enchantments) {
            stack.enchant(inst.enchantment, inst.level);
        }

        return stack;
    }

}
