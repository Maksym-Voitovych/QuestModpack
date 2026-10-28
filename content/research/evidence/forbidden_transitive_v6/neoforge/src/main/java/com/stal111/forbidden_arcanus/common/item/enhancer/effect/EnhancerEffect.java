package com.stal111.forbidden_arcanus.common.item.enhancer.effect;

import com.mojang.serialization.Codec;
import com.stal111.forbidden_arcanus.core.registry.FARegistries;

/**
 * @author stal111
 * @since 2023-02-18
 */
public interface EnhancerEffect {

    Codec<ConditionalEnhancerEffect<? extends EnhancerEffect>> DIRECT_CODEC = Codec.lazyInitialized(FARegistries.ENHANCER_EFFECT_REGISTRY::byNameCodec)
            .dispatch(effect -> effect.effect().getType(), EnhancerEffectType::codec);

    EnhancerEffectType<? extends EnhancerEffect> getType();
}
