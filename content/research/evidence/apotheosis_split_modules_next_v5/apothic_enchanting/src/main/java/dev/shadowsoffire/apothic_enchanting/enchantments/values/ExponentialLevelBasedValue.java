package dev.shadowsoffire.apothic_enchanting.enchantments.values;

import com.mojang.serialization.Codec;
import com.mojang.serialization.MapCodec;
import com.mojang.serialization.codecs.RecordCodecBuilder;

import net.minecraft.world.item.enchantment.LevelBasedValue;

/**
 * Computes base^exp, where exp defaults to the level if not provided.
 */
public record ExponentialLevelBasedValue(float base, LevelBasedValue exponent) implements LevelBasedValue {

    public static final MapCodec<ExponentialLevelBasedValue> CODEC = RecordCodecBuilder.mapCodec(inst -> inst.group(
        Codec.FLOAT.fieldOf("base").forGetter(ExponentialLevelBasedValue::base),
        LevelBasedValue.CODEC.optionalFieldOf("exponent", LevelBasedValue.perLevel(1)).forGetter(ExponentialLevelBasedValue::exponent))
        .apply(inst, ExponentialLevelBasedValue::new));

    public ExponentialLevelBasedValue(float base) {
        this(base, LevelBasedValue.perLevel(1));
    }

    @Override
    public float calculate(int level) {
        return (float) Math.pow(base, exponent.calculate(level));
    }

    @Override
    public MapCodec<? extends LevelBasedValue> codec() {
        return CODEC;
    }

}
