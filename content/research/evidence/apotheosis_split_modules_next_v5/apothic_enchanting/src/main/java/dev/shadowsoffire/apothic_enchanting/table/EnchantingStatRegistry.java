package dev.shadowsoffire.apothic_enchanting.table;

import java.util.ArrayList;
import java.util.Collections;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;

import com.google.gson.Gson;
import com.google.gson.GsonBuilder;
import com.mojang.serialization.Codec;
import com.mojang.serialization.codecs.RecordCodecBuilder;

import dev.shadowsoffire.apothic_enchanting.ApothicEnchanting;
import dev.shadowsoffire.apothic_enchanting.api.EnchantmentStatBlock;
import dev.shadowsoffire.apothic_enchanting.table.EnchantingStatRegistry.BlockStats;
import dev.shadowsoffire.placebo.codec.CodecProvider;
import dev.shadowsoffire.placebo.reload.DynamicRegistry;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Holder;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.registries.Registries;
import net.minecraft.network.FriendlyByteBuf;
import net.minecraft.network.codec.ByteBufCodecs;
import net.minecraft.network.codec.StreamCodec;
import net.minecraft.tags.TagKey;
import net.minecraft.world.level.LevelReader;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.state.BlockState;

public class EnchantingStatRegistry extends DynamicRegistry<BlockStats> {

    public static final Gson GSON = new GsonBuilder().setPrettyPrinting().create();
    public static final EnchantingStatRegistry INSTANCE = new EnchantingStatRegistry();
    private final Map<Block, Stats> statsPerBlock = new HashMap<>();

    protected EnchantingStatRegistry() {
        super(ApothicEnchanting.LOGGER, "enchanting_stats", true, false);
    }

    @Override
    protected void registerBuiltinCodecs() {
        this.registerDefaultCodec(ApothicEnchanting.loc("enchanting_stats"), BlockStats.CODEC);
    }

    @Override
    protected void beginReload(ReloadType type) {
        super.beginReload(type);
        this.statsPerBlock.clear();
    }

    @Override
    protected void onReload(ReloadType type) {
        super.onReload(type);
        for (BlockStats bStats : this.registry.values()) {
            bStats.blocks.forEach(b -> this.statsPerBlock.put(b, bStats.stats));
        }
    }

    /**
     * Retrieves the Eterna value for a specific block.
     * This can be provided by a stat file, or {@link BlockState#getEnchantPowerBonus}
     * 1 Eterna = +1 level in the enchanting table.
     */
    public static float getEterna(BlockState state, LevelReader level, BlockPos pos) {
        Block block = state.getBlock();
        if (INSTANCE.statsPerBlock.containsKey(block)) return INSTANCE.statsPerBlock.get(block).eterna;
        return state.getEnchantPowerBonus(level, pos) * 2;
    }

    /**
     * Retrieves the Max Eterna value for a specific block.
     * This can be provided by a stat file, or {@link EnchantmentStatBlock#getMaxEnchantingPower}
     * 1F of Eterna = 2 Levels in the enchanting table.
     */
    public static float getMaxEterna(BlockState state, LevelReader level, BlockPos pos) {
        Block block = state.getBlock();
        if (INSTANCE.statsPerBlock.containsKey(block)) return INSTANCE.statsPerBlock.get(block).maxEterna;
        return ((EnchantmentStatBlock) block).getMaxEnchantingPower(state, level, pos);

    }

    /**
     * Retrieves the Quanta value for a specific block.
     * This can be provided by a stat file, or {@link EnchantmentStatBlock#getQuantaBonus}
     * 1F of Quanta = 1% of Quanta in the enchanting table.
     */
    public static float getQuanta(BlockState state, LevelReader level, BlockPos pos) {
        Block block = state.getBlock();
        if (INSTANCE.statsPerBlock.containsKey(block)) return INSTANCE.statsPerBlock.get(block).quanta;
        return ((EnchantmentStatBlock) block).getQuantaBonus(state, level, pos);
    }

    /**
     * Retrieves the Arcana value for a specific block.
     * This can be provided by a stat file, or {@link EnchantmentStatBlock#getArcanaBonus}
     * 1F of Arcana = 1% of Arcana in the enchanting table.
     */
    public static float getArcana(BlockState state, LevelReader level, BlockPos pos) {
        Block block = state.getBlock();
        if (INSTANCE.statsPerBlock.containsKey(block)) return INSTANCE.statsPerBlock.get(block).arcana;
        return ((EnchantmentStatBlock) block).getArcanaBonus(state, level, pos);
    }

    /**
     * Retrieves the number of bonus clues this block provides.
     * See {@link EnchantmentStatBlock#getBonusClues}
     */
    public static int getBonusClues(BlockState state, LevelReader level, BlockPos pos) {
        Block block = state.getBlock();
        if (INSTANCE.statsPerBlock.containsKey(block)) return INSTANCE.statsPerBlock.get(block).clues;
        return ((EnchantmentStatBlock) block).getBonusClues(state, level, pos);
    }

    /**
     * Data-backed enchanting stats. Objects may provide stats via this or by overriding methods in {@link EnchantmentStatBlock}.
     * 
     * @Param maxEterna The max value of eterna that may be contributed to. Uses a step-ladder system.
     * @param eterna The amount of eterna provided.
     * @param quanta The amount of quanta provided.
     * @param arcana The amount of arcana provided.
     * @param clues  The number of enchanting clues provided.
     */
    public static record Stats(float maxEterna, float eterna, float quanta, float arcana, int clues) {

        public static Codec<Stats> CODEC = RecordCodecBuilder.create(inst -> inst
            .group(
                Codec.FLOAT.optionalFieldOf("maxEterna", 30F).forGetter(Stats::maxEterna),
                Codec.FLOAT.optionalFieldOf("eterna", 0F).forGetter(Stats::eterna),
                Codec.FLOAT.optionalFieldOf("quanta", 0F).forGetter(Stats::quanta),
                Codec.FLOAT.optionalFieldOf("arcana", 0F).forGetter(Stats::arcana),
                Codec.INT.optionalFieldOf("clues", 0).forGetter(Stats::clues))
            .apply(inst, Stats::new));

        public static StreamCodec<FriendlyByteBuf, Stats> STREAM_CODEC = StreamCodec.composite(
            ByteBufCodecs.FLOAT, Stats::maxEterna,
            ByteBufCodecs.FLOAT, Stats::eterna,
            ByteBufCodecs.FLOAT, Stats::quanta,
            ByteBufCodecs.FLOAT, Stats::arcana,
            ByteBufCodecs.VAR_INT, Stats::clues,
            Stats::new);
    }

    public static class BlockStats implements CodecProvider<BlockStats> {

        public static Codec<BlockStats> CODEC = RecordCodecBuilder.create(inst -> inst
            .group(
                Codec.list(BuiltInRegistries.BLOCK.byNameCodec()).optionalFieldOf("blocks", Collections.emptyList()).forGetter(bs -> bs.blocks),
                TagKey.codec(Registries.BLOCK).optionalFieldOf("tag").forGetter(bs -> Optional.empty()),
                BuiltInRegistries.BLOCK.byNameCodec().optionalFieldOf("block").forGetter(bs -> Optional.empty()),
                Stats.CODEC.fieldOf("stats").forGetter(bs -> bs.stats))
            .apply(inst, BlockStats::new));

        public final List<Block> blocks;
        public final Stats stats;

        public BlockStats(List<Block> blocks, Optional<TagKey<Block>> tag, Optional<Block> block, Stats stats) {
            this.blocks = new ArrayList<>();
            if (!blocks.isEmpty()) {
                this.blocks.addAll(blocks);
            }
            if (tag.isPresent()) {
                this.blocks.addAll(EnchantingStatRegistry.INSTANCE.getContext().getTag(tag.get()).stream().map(Holder::value).toList());
            }
            if (block.isPresent()) {
                this.blocks.add(block.get());
            }
            this.stats = stats;
        }

        @Override
        public Codec<? extends BlockStats> getCodec() {
            return CODEC;
        }

    }

}
