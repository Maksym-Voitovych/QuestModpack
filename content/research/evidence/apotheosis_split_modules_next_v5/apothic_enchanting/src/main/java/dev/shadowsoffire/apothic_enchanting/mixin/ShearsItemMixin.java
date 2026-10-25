package dev.shadowsoffire.apothic_enchanting.mixin;

import org.spongepowered.asm.mixin.Mixin;

import net.minecraft.core.Holder;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.ShearsItem;
import net.minecraft.world.item.enchantment.Enchantment;
import net.minecraft.world.item.enchantment.Enchantments;

@Mixin(ShearsItem.class)
public class ShearsItemMixin extends Item {

    public ShearsItemMixin(Properties pProperties) {
        super(pProperties);
    }

    @Override
    public boolean supportsEnchantment(ItemStack stack, Holder<Enchantment> ench) {
        return super.supportsEnchantment(stack, ench) || ench.is(Enchantments.UNBREAKING) || ench.is(Enchantments.EFFICIENCY) || ench.is(Enchantments.FORTUNE);
    }

    @Override
    public int getEnchantmentValue() {
        return 15;
    }

}
