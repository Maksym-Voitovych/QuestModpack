package dev.shadowsoffire.apothic_enchanting.enchantments.entity_effects;

import com.mojang.serialization.MapCodec;
import com.mojang.serialization.codecs.RecordCodecBuilder;

import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.item.enchantment.EnchantedItemInUse;
import net.minecraft.world.item.enchantment.LevelBasedValue;
import net.minecraft.world.item.enchantment.effects.EnchantmentEntityEffect;
import net.minecraft.world.phys.Vec3;

public record ReboundingEffect(LevelBasedValue range, LevelBasedValue horizontalStrength, LevelBasedValue verticalStrength) implements EnchantmentEntityEffect {

    public static final MapCodec<ReboundingEffect> CODEC = RecordCodecBuilder.mapCodec(inst -> inst.group(
        LevelBasedValue.CODEC.fieldOf("range").forGetter(ReboundingEffect::range),
        LevelBasedValue.CODEC.fieldOf("horizontal_strength").forGetter(ReboundingEffect::horizontalStrength),
        LevelBasedValue.CODEC.fieldOf("vertical_strength").forGetter(ReboundingEffect::verticalStrength))
        .apply(inst, ReboundingEffect::new));

    @Override
    public void apply(ServerLevel level, int enchantmentLevel, EnchantedItemInUse item, Entity entity, Vec3 origin) {
        if (entity.distanceToSqr(origin) <= range.calculate(enchantmentLevel)) {
            Vec3 vec = new Vec3(entity.getX() - origin.x(), entity.getY() - origin.y(), entity.getZ() - origin.z());
            entity.push(vec.x * horizontalStrength.calculate(enchantmentLevel), vec.y * verticalStrength.calculate(enchantmentLevel), vec.z * horizontalStrength.calculate(enchantmentLevel));
        }
    }

    @Override
    public MapCodec<? extends EnchantmentEntityEffect> codec() {
        return CODEC;
    }

}
