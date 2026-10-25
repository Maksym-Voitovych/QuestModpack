package dev.shadowsoffire.apothic_enchanting.enchantments.components;

import java.util.List;
import java.util.Optional;

import com.mojang.datafixers.util.Pair;
import com.mojang.serialization.Codec;
import com.mojang.serialization.codecs.RecordCodecBuilder;

import dev.shadowsoffire.apothic_enchanting.Ench;
import dev.shadowsoffire.apothic_enchanting.table.ApothEnchantmentHelper;
import dev.shadowsoffire.apothic_enchanting.util.MiscUtil;
import net.minecraft.core.Holder;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.util.RandomSource;
import net.minecraft.world.effect.MobEffect;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.item.enchantment.ConditionalEffect;
import net.minecraft.world.item.enchantment.Enchantment;
import net.minecraft.world.item.enchantment.effects.EnchantmentValueEffect;
import net.minecraft.world.level.storage.loot.LootContext;
import net.minecraft.world.level.storage.loot.parameters.LootContextParamSets;
import net.neoforged.neoforge.event.entity.living.LivingDamageEvent;

public record BerserkingComponent(List<ConditionalEffect<EnchantmentValueEffect>> hpCost, List<ConditionalEffect<VariableMobEffect>> mobEffects, List<ConditionalEffect<EnchantmentValueEffect>> cooldown) {

    public static final Codec<BerserkingComponent> CODEC = RecordCodecBuilder.create(inst -> inst.group(
        ConditionalEffect.codec(EnchantmentValueEffect.CODEC, LootContextParamSets.ENCHANTED_DAMAGE).listOf().fieldOf("hp_cost").forGetter(BerserkingComponent::hpCost),
        ConditionalEffect.codec(VariableMobEffect.CODEC, LootContextParamSets.ENCHANTED_DAMAGE).listOf().fieldOf("mob_effects").forGetter(BerserkingComponent::mobEffects),
        ConditionalEffect.codec(EnchantmentValueEffect.CODEC, LootContextParamSets.ENCHANTED_DAMAGE).listOf().fieldOf("cooldown").forGetter(BerserkingComponent::cooldown))
        .apply(inst, BerserkingComponent::new));

    /**
     * Handles the application of Berserker's Fury.
     */
    public static void attemptToGoBerserk(LivingDamageEvent.Post e) {
        LivingEntity target = e.getEntity();
        ResourceLocation key = BuiltInRegistries.ENCHANTMENT_EFFECT_COMPONENT_TYPE.getKey(Ench.EnchantEffects.BERSERKING);
        if (e.getSource().getEntity() != null && !MiscUtil.isOnCooldown(key, target)) {
            Pair<BerserkingComponent, Integer> data = ApothEnchantmentHelper.getHighestEquippedLevel(Ench.EnchantEffects.BERSERKING, target);
            if (data != null) {
                BerserkingComponent comp = data.getFirst();
                int level = data.getSecond();
                LootContext ctx = Enchantment.damageContext((ServerLevel) target.level(), level, target, e.getSource());

                float hpCost = ApothEnchantmentHelper.processValue(comp.hpCost, ctx, level, 0);
                target.invulnerableTime = 0;
                target.hurt(target.damageSources().source(Ench.DamageTypes.CORRUPTED), hpCost);

                Enchantment.applyEffects(comp.mobEffects, ctx, variableEffect -> {
                    target.addEffect(variableEffect.createEffectInstance(level, ctx.getRandom()));
                });

                MiscUtil.startCooldown(key, target, (int) ApothEnchantmentHelper.processValue(comp.cooldown(), ctx, level, 0));
            }
        }
    }

    /**
     * A primer for a mob effect instance where the duration and amplifier are dependent on an enchantment's value.
     */
    public static record VariableMobEffect(Holder<MobEffect> effect, List<EnchantmentValueEffect> duration, List<EnchantmentValueEffect> amplifier,
        boolean ambient, boolean visible, Optional<Boolean> showIcon) {

        public static final Codec<VariableMobEffect> CODEC = RecordCodecBuilder.create(inst -> inst.group(
            BuiltInRegistries.MOB_EFFECT.holderByNameCodec().fieldOf("mob_effect").forGetter(VariableMobEffect::effect),
            EnchantmentValueEffect.CODEC.listOf().fieldOf("duration").forGetter(VariableMobEffect::duration),
            EnchantmentValueEffect.CODEC.listOf().fieldOf("amplifier").forGetter(VariableMobEffect::amplifier),
            Codec.BOOL.optionalFieldOf("ambient", false).forGetter(VariableMobEffect::ambient),
            Codec.BOOL.optionalFieldOf("visible", true).forGetter(VariableMobEffect::visible),
            Codec.BOOL.optionalFieldOf("show_icon").forGetter(VariableMobEffect::showIcon))
            .apply(inst, VariableMobEffect::new));

        public MobEffectInstance createEffectInstance(int level, RandomSource rand) {
            int duration = (int) ApothEnchantmentHelper.processValue(this.duration, rand, level, 0);
            int amplifier = (int) ApothEnchantmentHelper.processValue(this.amplifier, rand, level, 0);
            return new MobEffectInstance(effect, duration, amplifier, ambient, visible, showIcon.orElse(visible));
        }

    }

}
