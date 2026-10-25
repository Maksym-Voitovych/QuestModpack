package dev.shadowsoffire.apothic_enchanting.asm;

import dev.shadowsoffire.apothic_enchanting.ApothicEnchanting;
import dev.shadowsoffire.apothic_enchanting.util.MiscUtil;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Holder;
import net.minecraft.core.registries.Registries;
import net.minecraft.util.Mth;
import net.minecraft.world.entity.projectile.FishingHook;
import net.minecraft.world.item.enchantment.Enchantment;

/**
 * Methods injected by Javascript Coremods.
 *
 * @author Shadows
 */
public class EnchHooks {

    /**
     * Replaces the call to {@link Enchantment#getMaxLevel()} in various classes.
     * Injected by coremods/ench/ench_info_redirector.js
     * 
     * @throws UnsupportedOperationException if the enchantment config file has not been loaded.
     */
    public static int getMaxLevel(Enchantment ench) {
        Holder<Enchantment> holder = MiscUtil.findHolder(Registries.ENCHANTMENT, ench);
        if (holder != null) {
            return ApothicEnchanting.getEnchInfo(holder).getMaxLevel();
        }
        return ench.getMaxLevel();
    }

    /**
     * Replaces the call to {@link Enchantment#getMaxLevel()} in loot-only classes.
     * Injected by coremods/ench/ench_info_loot_redirector.js
     * 
     * @throws UnsupportedOperationException if the enchantment config file has not been loaded.
     */
    public static int getMaxLootLevel(Enchantment ench) {
        Holder<Enchantment> holder = MiscUtil.findHolder(Registries.ENCHANTMENT, ench);
        if (holder != null) {
            return ApothicEnchanting.getEnchInfo(holder).getMaxLootLevel();
        }
        return ench.getMaxLevel();
    }

    /**
     * Calculates the delay for catching a fish. Ensures that the value never returns <= 0, so that it doesn't get infinitely locked.
     * Called at the end of {@link FishingBobberEntity#catchingFish(BlockPos)}
     * Injected by coremods/ench/fishing_hook.js
     */
    public static int getTicksCaughtDelay(FishingHook bobber) {
        int lowBound = Math.max(1, 100 - bobber.lureSpeed);
        int highBound = Math.max(lowBound, 600 - bobber.lureSpeed);
        return Mth.nextInt(bobber.level().getRandom(), lowBound, highBound);
    }

}
