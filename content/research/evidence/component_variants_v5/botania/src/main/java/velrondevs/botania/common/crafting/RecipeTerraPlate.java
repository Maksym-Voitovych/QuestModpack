package velrondevs.botania.common.crafting;

import com.mojang.serialization.Codec;
import com.mojang.serialization.MapCodec;
import com.mojang.serialization.codecs.RecordCodecBuilder;

import it.unimi.dsi.fastutil.ints.IntOpenHashSet;

import net.minecraft.core.HolderLookup;
import net.minecraft.core.NonNullList;
import net.minecraft.network.RegistryFriendlyByteBuf;
import net.minecraft.network.codec.ByteBufCodecs;
import net.minecraft.network.codec.StreamCodec;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.crafting.Ingredient;
import net.minecraft.world.item.crafting.RecipeInput;
import net.minecraft.world.item.crafting.RecipeSerializer;
import net.minecraft.world.level.Level;

import org.jetbrains.annotations.NotNull;

import velrondevs.botania.api.recipe.TerrestrialAgglomerationRecipe;
import velrondevs.botania.common.crafting.recipe.RecipeUtils;
import velrondevs.botania.registry.BotaniaRecipeTypes;

public class RecipeTerraPlate implements TerrestrialAgglomerationRecipe {
	private final int mana;
	private final NonNullList<Ingredient> inputs;
	private final ItemStack output;

	public RecipeTerraPlate(int mana, NonNullList<Ingredient> inputs, ItemStack output) {
		this.mana = mana;
		this.inputs = inputs;
		this.output = output;
	}

	@Override
	public int getMana() {
		return mana;
	}

	@Override
	public boolean matches(RecipeInput inv, @NotNull Level world) {
		int nonEmptySlots = 0;
		for (int i = 0; i < inv.size(); i++) {
			if (!inv.getItem(i).isEmpty()) {
				if (inv.getItem(i).getCount() > 1) {
					return false;
				}
				nonEmptySlots++;
			}
		}

		IntOpenHashSet usedSlots = new IntOpenHashSet(inv.size());
		return RecipeUtils.matches(inputs, inv, usedSlots) && usedSlots.size() == nonEmptySlots;
	}

	@NotNull
	@Override
	public ItemStack assemble(@NotNull RecipeInput inv, @NotNull HolderLookup.Provider registries) {
		return output.copy();
	}

	@NotNull
	@Override
	public ItemStack getResultItem(@NotNull HolderLookup.Provider registries) {
		return output;
	}

	@NotNull
	@Override
	public NonNullList<Ingredient> getIngredients() {
		return inputs;
	}

	@NotNull
	@Override
	public RecipeSerializer<RecipeTerraPlate> getSerializer() {
		return BotaniaRecipeTypes.TERRA_PLATE_SERIALIZER;
	}

	public static class Serializer implements RecipeSerializer<RecipeTerraPlate> {
		public static final MapCodec<RecipeTerraPlate> CODEC = RecordCodecBuilder.mapCodec(instance -> instance.group(
				Codec.INT.fieldOf("mana").forGetter(RecipeTerraPlate::getMana),
				RecipeUtils.INGREDIENTS_CODEC.fieldOf("ingredients").forGetter(RecipeTerraPlate::getIngredients),
				ItemStack.STRICT_CODEC.fieldOf("result").forGetter(recipe -> recipe.output)
		).apply(instance, (mana, inputs, output) -> new RecipeTerraPlate(mana, NonNullList.of(Ingredient.EMPTY, inputs.toArray(new Ingredient[0])), output)));
		public static final StreamCodec<RegistryFriendlyByteBuf, RecipeTerraPlate> STREAM_CODEC = StreamCodec.composite(
				ByteBufCodecs.VAR_INT, RecipeTerraPlate::getMana,
				RecipeUtils.INGREDIENTS_STREAM_CODEC, RecipeTerraPlate::getIngredients,
				ItemStack.STREAM_CODEC, recipe -> recipe.output,
				(mana, inputs, output) -> new RecipeTerraPlate(mana, NonNullList.of(Ingredient.EMPTY, inputs.toArray(new Ingredient[0])), output));

		@Override
		public MapCodec<RecipeTerraPlate> codec() {
			return CODEC;
		}

		@Override
		public StreamCodec<RegistryFriendlyByteBuf, RecipeTerraPlate> streamCodec() {
			return STREAM_CODEC;
		}
	}
}
