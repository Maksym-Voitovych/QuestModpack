package dev.shadowsoffire.apothic_enchanting.advancements;

import java.util.Optional;

import com.mojang.serialization.Codec;
import com.mojang.serialization.codecs.RecordCodecBuilder;

import net.minecraft.advancements.critereon.ContextAwarePredicate;
import net.minecraft.advancements.critereon.EntityPredicate;
import net.minecraft.advancements.critereon.ItemPredicate;
import net.minecraft.advancements.critereon.MinMaxBounds.Doubles;
import net.minecraft.advancements.critereon.MinMaxBounds.Ints;
import net.minecraft.advancements.critereon.SimpleCriterionTrigger;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.item.ItemStack;

public class EnchantedTrigger extends SimpleCriterionTrigger<EnchantedTrigger.TriggerInstance> {

    @Override
    public Codec<TriggerInstance> codec() {
        return TriggerInstance.CODEC;
    }

    public void trigger(ServerPlayer player, ItemStack stack, int level, float eterna, float quanta, float arcana, boolean stable) {
        this.trigger(player, inst -> inst.test(stack, level, eterna, quanta, arcana, stable));
    }

    public static record TriggerInstance(Optional<ContextAwarePredicate> player, Optional<ItemPredicate> item, Ints levels, Doubles eterna, Doubles quanta, Doubles arcana, Optional<Boolean> stable)
        implements SimpleCriterionTrigger.SimpleInstance {

        public static final Codec<TriggerInstance> CODEC = RecordCodecBuilder.create(inst -> inst
            .group(
                EntityPredicate.ADVANCEMENT_CODEC.optionalFieldOf("player").forGetter(TriggerInstance::player),
                ItemPredicate.CODEC.optionalFieldOf("item").forGetter(TriggerInstance::item),
                Ints.CODEC.optionalFieldOf("levels", Ints.ANY).forGetter(TriggerInstance::levels),
                Doubles.CODEC.optionalFieldOf("eterna", Doubles.ANY).forGetter(TriggerInstance::eterna),
                Doubles.CODEC.optionalFieldOf("quanta", Doubles.ANY).forGetter(TriggerInstance::quanta),
                Doubles.CODEC.optionalFieldOf("arcana", Doubles.ANY).forGetter(TriggerInstance::arcana),
                Codec.BOOL.optionalFieldOf("stable").forGetter(TriggerInstance::stable))
            .apply(inst, TriggerInstance::new));

        public boolean test(ItemStack stack, int level, float eterna, float quanta, float arcana, boolean stable) {
            return (this.item.isEmpty() || this.item.get().test(stack))
                && this.levels.matches(level)
                && this.eterna.matches(eterna)
                && this.quanta.matches(quanta)
                && this.arcana.matches(arcana)
                && (this.stable.isEmpty() || this.stable.get() == stable);
        }

    }

}
