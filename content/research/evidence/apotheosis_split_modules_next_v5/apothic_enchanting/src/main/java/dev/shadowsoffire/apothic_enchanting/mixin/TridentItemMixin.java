package dev.shadowsoffire.apothic_enchanting.mixin;

import org.spongepowered.asm.mixin.Mixin;

import net.minecraft.core.Holder;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.TridentItem;
import net.minecraft.world.item.enchantment.Enchantment;
import net.minecraft.world.item.enchantment.Enchantments;

@Mixin(value = TridentItem.class, remap = false)
public abstract class TridentItemMixin extends Item {

    public TridentItemMixin(Properties pProperties) {
        super(pProperties);
    }

    @Override
    public boolean supportsEnchantment(ItemStack stack, Holder<Enchantment> ench) {
        return super.supportsEnchantment(stack, ench) || ench.is(Enchantments.SHARPNESS) || ench.is(Enchantments.LOOTING) || ench.is(Enchantments.PIERCING);
    }

}
