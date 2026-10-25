package dev.shadowsoffire.apothic_enchanting.objects;

import dev.shadowsoffire.apothic_enchanting.ApothEnchConfig;
import dev.shadowsoffire.apothic_enchanting.api.EnchantmentStatBlock;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.ParticleOptions;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.util.RandomSource;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.state.BlockState;

public class TypedShelfBlock extends Block implements EnchantmentStatBlock {

    protected final ParticleOptions particle;

    public TypedShelfBlock(Properties props, ParticleOptions particle) {
        super(props);
        this.particle = particle;
    }

    @Override
    public ParticleOptions getTableParticle(BlockState state) {
        return this.particle;
    }

    public static class SculkShelfBlock extends TypedShelfBlock {

        public SculkShelfBlock(Properties props, ParticleOptions particle) {
            super(props, particle);
        }

        @Override
        public void animateTick(BlockState state, Level level, BlockPos pos, RandomSource rand) {
            if (ApothEnchConfig.sculkShelfNoiseChance > 0 && rand.nextInt(ApothEnchConfig.sculkShelfNoiseChance) == 0) {
                level.playLocalSound(pos.getX(), pos.getY(), pos.getZ(), SoundEvents.SCULK_CATALYST_BLOOM, SoundSource.BLOCKS, 2.0F, 0.6F + rand.nextFloat() * 0.4F, true);
            }
        }

    }

}
