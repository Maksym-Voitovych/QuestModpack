package dev.shadowsoffire.apothic_enchanting.table.infusion;

import com.mojang.serialization.MapCodec;
import com.mojang.serialization.codecs.RecordCodecBuilder;

import dev.shadowsoffire.apothic_enchanting.table.EnchantingStatRegistry.Stats;
import net.minecraft.network.RegistryFriendlyByteBuf;
import net.minecraft.network.codec.StreamCodec;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.crafting.Ingredient;
import net.minecraft.world.item.crafting.RecipeSerializer;

public class KeepNBTInfusionRecipe extends InfusionRecipe {

    public static final Serializer SERIALIZER = new Serializer();

    public KeepNBTInfusionRecipe(ItemStack output, Ingredient input, Stats requirements, Stats maxRequirements) {
        super(output, input, requirements, maxRequirements);
    }

    @Override
    public ItemStack assemble(ItemStack input, float eterna, float quanta, float arcana) {
        ItemStack out = this.getOutput().copy();
        if (!input.isComponentsPatchEmpty()) {
            out.applyComponentsAndValidate(input.getComponentsPatch());
        }
        return out;
    }

    @Override
    public RecipeSerializer<?> getSerializer() {
        return KeepNBTInfusionRecipe.SERIALIZER;
    }

    public static class Serializer implements RecipeSerializer<KeepNBTInfusionRecipe> {

        public static final MapCodec<KeepNBTInfusionRecipe> CODEC = RecordCodecBuilder.mapCodec(inst -> inst.group(
            ItemStack.CODEC.fieldOf("result").forGetter(InfusionRecipe::getOutput),
            Ingredient.CODEC_NONEMPTY.fieldOf("input").forGetter(InfusionRecipe::getInput),
            Stats.CODEC.fieldOf("requirements").forGetter(InfusionRecipe::getRequirements),
            Stats.CODEC.optionalFieldOf("max_requirements", NO_MAX).forGetter(InfusionRecipe::getMaxRequirements))
            .apply(inst, KeepNBTInfusionRecipe::new));

        public static final StreamCodec<RegistryFriendlyByteBuf, KeepNBTInfusionRecipe> STREAM_CODEC = StreamCodec.composite(
            ItemStack.STREAM_CODEC, InfusionRecipe::getOutput,
            Ingredient.CONTENTS_STREAM_CODEC, InfusionRecipe::getInput,
            Stats.STREAM_CODEC, InfusionRecipe::getRequirements,
            Stats.STREAM_CODEC, InfusionRecipe::getMaxRequirements,
            KeepNBTInfusionRecipe::new);

        @Override
        public MapCodec<KeepNBTInfusionRecipe> codec() {
            return CODEC;
        }

        @Override
        public StreamCodec<RegistryFriendlyByteBuf, KeepNBTInfusionRecipe> streamCodec() {
            return STREAM_CODEC;
        }

    }

}
