package com.stal111.forbidden_arcanus.common.block.entity.clibano.residue;

import com.mojang.serialization.Codec;
import com.mojang.serialization.codecs.RecordCodecBuilder;
import net.minecraft.core.Holder;

/**
 * @author stal111
 * @since 05.02.2024
 */
public record ResidueChance(Holder<ResidueType> type, double chance) {

    public static final Codec<ResidueChance> CODEC = RecordCodecBuilder.create(instance -> instance.group(
            ResidueType.CODEC.fieldOf("type").forGetter(ResidueChance::type),
            Codec.DOUBLE.fieldOf("chance").forGetter(ResidueChance::chance)
    ).apply(instance, ResidueChance::new));
}
