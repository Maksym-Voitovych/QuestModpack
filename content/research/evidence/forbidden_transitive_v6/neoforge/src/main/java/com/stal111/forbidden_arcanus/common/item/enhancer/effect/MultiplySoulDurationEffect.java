package com.stal111.forbidden_arcanus.common.item.enhancer.effect;

import com.mojang.serialization.Codec;
import com.mojang.serialization.MapCodec;
import com.mojang.serialization.codecs.RecordCodecBuilder;
import com.stal111.forbidden_arcanus.core.init.other.ModEnhancerEffects;

/**
 * @author stal111
 * @since 02.03.2024
 */
public record MultiplySoulDurationEffect(double multiplier) implements ValueModifierEffect<Integer> {

    public static final MapCodec<MultiplySoulDurationEffect> CODEC = RecordCodecBuilder.mapCodec(instance -> instance.group(
            Codec.doubleRange(0.0D, 10.0D).fieldOf("multiplier").forGetter(MultiplySoulDurationEffect::multiplier)
    ).apply(instance, MultiplySoulDurationEffect::new));

    @Override
    public Integer getModifiedValue(Integer originalValue) {
        return (int) (originalValue * this.multiplier);
    }

    @Override
    public EnhancerEffectType<? extends EnhancerEffect> getType() {
        return ModEnhancerEffects.MULTIPLY_SOUL_DURATION.get();
    }
}
