package dev.shadowsoffire.apothic_enchanting.objects;

import dev.shadowsoffire.apothic_enchanting.Ench;
import dev.shadowsoffire.apothic_enchanting.api.EnchantmentStatBlock;
import net.minecraft.core.BlockPos;
import net.minecraft.world.level.LevelReader;
import net.minecraft.world.level.block.state.BlockState;

public class TreasureShelfBlock extends TypedShelfBlock implements EnchantmentStatBlock {

    public TreasureShelfBlock(Properties props) {
        super(props, Ench.Particles.ENCHANT_SCULK);
    }

    @Override
    public boolean allowsTreasure(BlockState state, LevelReader world, BlockPos pos) {
        return true;
    }

    @Override
    public float getEnchantPowerBonus(BlockState state, LevelReader level, BlockPos pos) {
        return 5;
    }

    @Override
    public float getMaxEnchantingPower(BlockState state, LevelReader world, BlockPos pos) {
        return 70;
    }

    @Override
    public float getQuantaBonus(BlockState state, LevelReader world, BlockPos pos) {
        return -15F;
    }

    @Override
    public float getArcanaBonus(BlockState state, LevelReader world, BlockPos pos) {
        return -15F;
    }

}
