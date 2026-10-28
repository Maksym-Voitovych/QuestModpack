package com.stal111.forbidden_arcanus.common.item.enhancer.effect;

import com.mojang.serialization.MapCodec;
import com.mojang.serialization.codecs.RecordCodecBuilder;
import com.stal111.forbidden_arcanus.common.item.enhancer.condition.EffectCondition;
import net.minecraft.world.level.Level;

import java.util.Collection;
import java.util.List;
import java.util.Optional;

public record ConditionalEnhancerEffect<T extends EnhancerEffect>(T effect, Optional<List<EffectCondition>> conditions) {

    public static <T extends EnhancerEffect> ConditionalEnhancerEffect<T> of(T effect) {
        return new ConditionalEnhancerEffect<>(effect, Optional.empty());
    }

    public static <T extends EnhancerEffect> ConditionalEnhancerEffect<T> of(T effect, List<EffectCondition> conditions) {
        return new ConditionalEnhancerEffect<>(effect, Optional.of(conditions));
    }

    public static <T extends EnhancerEffect> MapCodec<ConditionalEnhancerEffect<T>> codec(MapCodec<T> effectCodec) {
        return RecordCodecBuilder.mapCodec(instance -> instance.group(
                effectCodec.forGetter(ConditionalEnhancerEffect::effect),
                EffectCondition.DIRECT_CODEC.listOf().optionalFieldOf("conditions").forGetter(ConditionalEnhancerEffect::conditions)
        ).apply(instance, ConditionalEnhancerEffect::new));
    }

    public boolean checkConditions(Level level) {
        return this.conditions.stream().flatMap(Collection::stream).allMatch(condition -> condition.test(level));
    }
}
