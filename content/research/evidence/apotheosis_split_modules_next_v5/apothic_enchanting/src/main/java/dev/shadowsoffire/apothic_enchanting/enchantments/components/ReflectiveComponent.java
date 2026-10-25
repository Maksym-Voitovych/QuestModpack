package dev.shadowsoffire.apothic_enchanting.enchantments.components;

import com.mojang.serialization.Codec;
import com.mojang.serialization.codecs.RecordCodecBuilder;

import net.minecraft.world.item.enchantment.LevelBasedValue;

public record ReflectiveComponent(LevelBasedValue procChance, LevelBasedValue reflectRatio) {

    public static final Codec<ReflectiveComponent> CODEC = RecordCodecBuilder.create(inst -> inst.group(
        LevelBasedValue.CODEC.fieldOf("proc_chance").forGetter(ReflectiveComponent::procChance),
        LevelBasedValue.CODEC.fieldOf("reflect_ratio").forGetter(ReflectiveComponent::reflectRatio))
        .apply(inst, ReflectiveComponent::new));
}
