package owmii.powah.block.energizing;

import com.mojang.serialization.Codec;
import com.mojang.serialization.MapCodec;
import com.mojang.serialization.codecs.RecordCodecBuilder;
import java.util.ArrayList;
import java.util.Iterator;
import java.util.List;
import net.minecraft.core.HolderLookup;
import net.minecraft.core.NonNullList;
import net.minecraft.network.RegistryFriendlyByteBuf;
import net.minecraft.network.codec.ByteBufCodecs;
import net.minecraft.network.codec.StreamCodec;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.crafting.Ingredient;
import net.minecraft.world.item.crafting.Recipe;
import net.minecraft.world.item.crafting.RecipeInput;
import net.minecraft.world.item.crafting.RecipeSerializer;
import net.minecraft.world.item.crafting.RecipeType;
import net.minecraft.world.level.Level;
import owmii.powah.Powah;
import owmii.powah.recipe.Recipes;

public class EnergizingRecipe implements Recipe<RecipeInput> {
    public static final ResourceLocation ID = Powah.id("energizing");
    private final ItemStack output;
    private final long energy;
    private final NonNullList<Ingredient> ingredients;

    public static final MapCodec<EnergizingRecipe> CODEC = RecordCodecBuilder.mapCodec(builder -> builder.group(
            ItemStack.CODEC.fieldOf("result").forGetter(e -> e.output),
            Codec.LONG.fieldOf("energy").forGetter(e -> e.energy),
            Ingredient.LIST_CODEC_NONEMPTY
                    .fieldOf("ingredients")
                    .forGetter(e -> e.ingredients))
            .apply(builder, EnergizingRecipe::new));

    public static final StreamCodec<RegistryFriendlyByteBuf, EnergizingRecipe> STREAM_CODEC = StreamCodec.composite(
            ItemStack.STREAM_CODEC,
            EnergizingRecipe::getResultItem,
            ByteBufCodecs.VAR_LONG, EnergizingRecipe::getEnergy,
            Ingredient.CONTENTS_STREAM_CODEC.apply(ByteBufCodecs.list()),
            EnergizingRecipe::getIngredients,
            EnergizingRecipe::new);

    public EnergizingRecipe(ItemStack output, long energy, List<Ingredient> ingredients) {
        this.output = output;
        this.energy = energy;
        this.ingredients = NonNullList.copyOf(ingredients);
    }

    @Override
    public boolean matches(RecipeInput inv, Level world) {
        List<Ingredient> stacks = new ArrayList<>(getIngredients());
        for (int i = 1; i < inv.size(); i++) {
            ItemStack stack = inv.getItem(i);
            if (!stack.isEmpty()) {
                boolean flag = false;
                Iterator<Ingredient> itr = stacks.iterator();
                while (itr.hasNext()) {
                    Ingredient ingredient = itr.next();
                    if (ingredient.test(stack)) {
                        flag = true;
                        itr.remove();
                        break;
                    }
                }
                if (!flag) {
                    return false;
                }
            }
        }
        return stacks.isEmpty();
    }

    @Override
    public ItemStack assemble(RecipeInput inv, HolderLookup.Provider registry) {
        return this.output.copy();
    }

    @Override
    public boolean canCraftInDimensions(int width, int height) {
        return true;
    }

    public ItemStack getResultItem() {
        return output;
    }

    @Override
    public ItemStack getResultItem(HolderLookup.Provider registryAccess) {
        return this.output;
    }

    @Override
    public RecipeSerializer<?> getSerializer() {
        return Recipes.ENERGIZING_SERIALIZER.get();
    }

    @Override
    public RecipeType<?> getType() {
        return Recipes.ENERGIZING.get();
    }

    public long getEnergy() {
        return this.energy;
    }

    public long getScaledEnergy() {
        return Math.max(1, (long) (energy * Powah.config().general.energizing_energy_ratio));
    }

    @Override
    public NonNullList<Ingredient> getIngredients() {
        return this.ingredients;
    }

    @Override
    public boolean isSpecial() {
        return true;
    }

    public static class Serializer implements RecipeSerializer<EnergizingRecipe> {
        @Override
        public MapCodec<EnergizingRecipe> codec() {
            return CODEC;
        }

        @Override
        public StreamCodec<RegistryFriendlyByteBuf, EnergizingRecipe> streamCodec() {
            return STREAM_CODEC;
        }
    }
}
