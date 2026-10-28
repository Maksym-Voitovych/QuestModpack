package com.stal111.forbidden_arcanus.common.block.entity.clibano;

import com.mojang.serialization.Codec;
import net.minecraft.util.ExtraCodecs;

import java.util.Arrays;
import java.util.List;

public record ClibanoCookingTimes(List<Integer> cookingTimes) {

    public static final Codec<ClibanoCookingTimes> CODEC = ExtraCodecs.POSITIVE_INT.xmap(ClibanoCookingTimes::of, clibanoCookingTimes -> clibanoCookingTimes.cookingTimes().getFirst());

    public static ClibanoCookingTimes of(int defaultTime) {
        var list = Arrays.stream(ClibanoFireType.values())
                .map(fireType -> (int) (defaultTime / fireType.getCookingSpeedMultiplier()))
                .toList();

        return new ClibanoCookingTimes(list);
    }

    public int get(ClibanoFireType fireType) {
        return this.cookingTimes().get(fireType.ordinal());
    }
}
