package dev.shadowsoffire.apothic_enchanting.mixin;

import java.util.List;

import javax.annotation.Nullable;

import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

import dev.shadowsoffire.apothic_enchanting.enchantments.ShearsEnchantments;
import net.minecraft.core.BlockPos;
import net.minecraft.world.entity.animal.Sheep;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.enchantment.Enchantments;
import net.minecraft.world.level.Level;
import net.neoforged.neoforge.common.IShearable;

@Mixin(value = IShearable.class, remap = false)
public interface IShearableMixin {

    @Inject(method = "onSheared", at = @At("HEAD"), require = 1)
    default void apoth_handleShearFortune(@Nullable Player player, ItemStack item, Level world, BlockPos pos, CallbackInfoReturnable<List<ItemStack>> ci) {
        if (this instanceof Sheep sheep && !sheep.level().isClientSide) {
            int fortune = item.getEnchantmentLevel(world.holderOrThrow(Enchantments.FORTUNE));
            sheep.getPersistentData().putInt("apoth.sheep_fortune", fortune);
        }
    }

    @Inject(method = "onSheared", at = @At("RETURN"), cancellable = true, require = 1)
    default void apoth_handleShearEnchantments(@Nullable Player player, ItemStack item, Level world, BlockPos pos, CallbackInfoReturnable<List<ItemStack>> ci) {
        if (this instanceof Sheep sheep && !sheep.level().isClientSide) {
            ci.setReturnValue(ShearsEnchantments.applyExploitation(sheep, item, ci.getReturnValue()));
            ci.setReturnValue(ShearsEnchantments.applyChromatic(sheep, item, ci.getReturnValue()));
            ShearsEnchantments.applyGrowthSerum(sheep, item);
        }
    }

}
