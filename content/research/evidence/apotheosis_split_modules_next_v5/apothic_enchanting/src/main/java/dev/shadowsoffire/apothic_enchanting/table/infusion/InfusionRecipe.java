package dev.shadowsoffire.apothic_enchanting.table.infusion;

import javax.annotation.Nullable;

import com.mojang.serialization.MapCodec;
import com.mojang.serialization.codecs.RecordCodecBuilder;

import dev.shadowsoffire.apothic_enchanting.Ench;
import dev.shadowsoffire.apothic_enchanting.table.EnchantingStatRegistry.Stats;
import net.minecraft.core.HolderLookup;
import net.minecraft.network.RegistryFriendlyByteBuf;
import net.minecraft.network.codec.StreamCodec;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.crafting.Ingredient;
import net.minecraft.world.item.crafting.Recipe;
import net.minecraft.world.item.crafting.RecipeHolder;
import net.minecraft.world.item.crafting.RecipeInput;
import net.minecraft.world.item.crafting.RecipeSerializer;
import net.minecraft.world.item.crafting.RecipeType;
import net.minecraft.world.level.Level;

public class InfusionRecipe implements Recipe<RecipeInput> {

    public static final Stats NO_MAX = new Stats(-1, -1, -1, -1, -1);

    public static final Serializer SERIALIZER = new Serializer();

    protected final ItemStack output;
    protected final Ingredient input;
    protected final Stats requirements, maxRequirements;

    /**
     * Defines an Infusion Enchanting recipe.
     *
     * @param id           The Recipe ID
     * @param output       The output ItemStack
     * @param input        The input Ingredient
     * @param requirements The Level, Quanta, and Arcana requirements respectively.
     * @param displayLevel The level to show on the fake "Infusion" Enchantment that will show up.
     */
    public InfusionRecipe(ItemStack output, Ingredient input, Stats requirements, Stats maxRequirements) {
        this.output = output;
        this.input = input;
        this.requirements = requirements;
        this.maxRequirements = maxRequirements;

        if (maxRequirements.eterna() != -1 && requirements.eterna() > maxRequirements.eterna()) throw new UnsupportedOperationException("Invalid min/max eterna bounds (min > max).");
        if (maxRequirements.quanta() != -1 && requirements.quanta() > maxRequirements.quanta()) throw new UnsupportedOperationException("Invalid min/max quanta bounds (min > max).");
        if (maxRequirements.arcana() != -1 && requirements.arcana() > maxRequirements.arcana()) throw new UnsupportedOperationException("Invalid min/max arcana bounds (min > max).");
    }

    public boolean matches(ItemStack input, float eterna, float quanta, float arcana) {
        if (this.maxRequirements.eterna() > -1 && eterna > this.maxRequirements.eterna() ||
            this.maxRequirements.quanta() > -1 && quanta > this.maxRequirements.quanta() ||
            this.maxRequirements.arcana() > -1 && arcana > this.maxRequirements.arcana()) {
            return false;
        }
        return this.input.test(input) && eterna >= this.requirements.eterna() && quanta >= this.requirements.quanta() && arcana >= this.requirements.arcana();
    }

    public Stats getRequirements() {
        return this.requirements;
    }

    public Stats getMaxRequirements() {
        return this.maxRequirements;
    }

    public Ingredient getInput() {
        return this.input;
    }

    public ItemStack getOutput() {
        return this.output;
    }

    public ItemStack assemble(ItemStack input, float eterna, float quanta, float arcana) {
        return this.output.copy();
    }

    @Override
    public RecipeSerializer<?> getSerializer() {
        return InfusionRecipe.SERIALIZER;
    }

    @Override
    public RecipeType<?> getType() {
        return Ench.RecipeTypes.INFUSION;
    }

    public static class Serializer implements RecipeSerializer<InfusionRecipe> {

        public static final MapCodec<InfusionRecipe> CODEC = RecordCodecBuilder.mapCodec(inst -> inst.group(
            ItemStack.CODEC.fieldOf("result").forGetter(InfusionRecipe::getOutput),
            Ingredient.CODEC_NONEMPTY.fieldOf("input").forGetter(InfusionRecipe::getInput),
            Stats.CODEC.fieldOf("requirements").forGetter(InfusionRecipe::getRequirements),
            Stats.CODEC.optionalFieldOf("max_requirements", NO_MAX).forGetter(InfusionRecipe::getMaxRequirements))
            .apply(inst, InfusionRecipe::new));

        public static final StreamCodec<RegistryFriendlyByteBuf, InfusionRecipe> STREAM_CODEC = StreamCodec.composite(
            ItemStack.STREAM_CODEC, InfusionRecipe::getOutput,
            Ingredient.CONTENTS_STREAM_CODEC, InfusionRecipe::getInput,
            Stats.STREAM_CODEC, InfusionRecipe::getRequirements,
            Stats.STREAM_CODEC, InfusionRecipe::getMaxRequirements,
            InfusionRecipe::new);

        @Override
        public MapCodec<InfusionRecipe> codec() {
            return CODEC;
        }

        @Override
        public StreamCodec<RegistryFriendlyByteBuf, InfusionRecipe> streamCodec() {
            return STREAM_CODEC;
        }

    }

    @Nullable
    public static InfusionRecipe findMatch(Level level, ItemStack input, float eterna, float quanta, float arcana) {
        return level.getRecipeManager().getAllRecipesFor(Ench.RecipeTypes.INFUSION).stream()
            .map(RecipeHolder::value)
            .sorted((r1, r2) -> -Float.compare(r1.requirements.eterna(), r2.requirements.eterna()))
            .filter(r -> r.matches(input, eterna, quanta, arcana))
            .findFirst().orElse(null);
    }

    @Nullable
    public static InfusionRecipe findItemMatch(Level level, ItemStack toEnchant) {
        return level.getRecipeManager().getAllRecipesFor(Ench.RecipeTypes.INFUSION).stream()
            .map(RecipeHolder::value)
            .filter(r -> r.getInput().test(toEnchant))
            .findFirst().orElse(null);
    }

    @Override
    @Deprecated
    public boolean matches(RecipeInput pContainer, Level pLevel) {
        return false;
    }

    @Override
    @Deprecated
    public ItemStack assemble(RecipeInput pContainer, HolderLookup.Provider regs) {
        return ItemStack.EMPTY;
    }

    @Override
    @Deprecated
    public boolean canCraftInDimensions(int pWidth, int pHeight) {
        return false;
    }

    @Override
    @Deprecated
    public ItemStack getResultItem(HolderLookup.Provider regs) {
        return this.output;
    }

}
