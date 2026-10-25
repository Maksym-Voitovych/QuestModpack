package dev.shadowsoffire.apothic_enchanting.data;

import java.util.concurrent.CompletableFuture;

import dev.shadowsoffire.apothic_enchanting.ApothicEnchanting;
import dev.shadowsoffire.apothic_enchanting.Ench;
import dev.shadowsoffire.placebo.datagen.LegacyRecipeProvider;
import net.minecraft.core.HolderLookup;
import net.minecraft.core.component.DataComponents;
import net.minecraft.data.PackOutput;
import net.minecraft.data.recipes.RecipeOutput;
import net.minecraft.network.chat.Component;
import net.minecraft.network.chat.Style;
import net.minecraft.tags.ItemTags;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.item.alchemy.Potions;
import net.minecraft.world.item.crafting.Ingredient;
import net.minecraft.world.level.block.Blocks;
import net.neoforged.neoforge.common.Tags;

public class EnchRecipeProvider extends LegacyRecipeProvider {

    public EnchRecipeProvider(PackOutput output, CompletableFuture<HolderLookup.Provider> registries) {
        super(output, registries, ApothicEnchanting.MODID);
    }

    @Override
    protected void genRecipes(RecipeOutput recipeOutput, HolderLookup.Provider registries) {
        addShaped(Ench.Blocks.HELLSHELF, 3, 3,
            Blocks.NETHER_BRICKS, Blocks.NETHER_BRICKS, Blocks.NETHER_BRICKS,
            Items.BLAZE_ROD, Tags.Items.BOOKSHELVES, potionIngredient(Potions.REGENERATION),
            Blocks.NETHER_BRICKS, Blocks.NETHER_BRICKS, Blocks.NETHER_BRICKS);

        addShaped(Ench.Items.PRISMATIC_WEB, 3, 3,
            null, Items.PRISMARINE_SHARD, null,
            Items.PRISMARINE_SHARD, Blocks.COBWEB, Items.PRISMARINE_SHARD,
            null, Items.PRISMARINE_SHARD, null);

        ItemStack book = new ItemStack(Items.BOOK);
        ItemStack stick = new ItemStack(Items.STICK);
        ItemStack blaze = new ItemStack(Items.BLAZE_ROD);
        addShaped(new ItemStack(Ench.Items.HELMET_TOME, 5), 3, 2, book, book, book, book, blaze, book);
        addShaped(new ItemStack(Ench.Items.CHESTPLATE_TOME, 8), 3, 3, book, blaze, book, book, book, book, book, book, book);
        addShaped(new ItemStack(Ench.Items.LEGGINGS_TOME, 7), 3, 3, book, null, book, book, blaze, book, book, book, book);
        addShaped(new ItemStack(Ench.Items.BOOTS_TOME, 4), 3, 2, book, null, book, book, blaze, book);
        addShaped(new ItemStack(Ench.Items.WEAPON_TOME, 2), 1, 3, book, book, new ItemStack(Items.BLAZE_POWDER));
        addShaped(new ItemStack(Ench.Items.PICKAXE_TOME, 3), 3, 3, book, book, book, null, blaze, null, null, stick, null);
        addShaped(new ItemStack(Ench.Items.FISHING_TOME, 2), 3, 3, null, null, blaze, null, stick, book, stick, null, book);
        addShaped(new ItemStack(Ench.Items.BOW_TOME, 3), 3, 3, null, stick, book, blaze, null, book, null, stick, book);
        addShapeless(new ItemStack(Ench.Items.OTHER_TOME, 6), book, book, book, book, book, book, blaze);
        addShaped(new ItemStack(Ench.Items.SCRAP_TOME, 8), 3, 3, book, book, book, book, Blocks.ANVIL, book, book, book, book);

        addShaped(Ench.Blocks.BLAZING_HELLSHELF, 3, 3,
            null, Items.FIRE_CHARGE, null,
            Items.FIRE_CHARGE, Ench.Blocks.INFUSED_HELLSHELF, Items.FIRE_CHARGE,
            Items.BLAZE_POWDER, Items.BLAZE_POWDER, Items.BLAZE_POWDER);

        addShaped(Ench.Blocks.GLOWING_HELLSHELF, 3, 3,
            null, Blocks.GLOWSTONE, null,
            null, Ench.Blocks.INFUSED_HELLSHELF, null,
            Blocks.GLOWSTONE, null, Blocks.GLOWSTONE);

        addShaped(Ench.Blocks.SEASHELF, 3, 3,
            Blocks.PRISMARINE_BRICKS, Blocks.PRISMARINE_BRICKS, Blocks.PRISMARINE_BRICKS,
            potionIngredient(Potions.WATER), Tags.Items.BOOKSHELVES, Items.PUFFERFISH,
            Blocks.PRISMARINE_BRICKS, Blocks.PRISMARINE_BRICKS, Blocks.PRISMARINE_BRICKS);

        addShaped(Ench.Blocks.CRYSTAL_SEASHELF, 3, 3,
            null, Items.PRISMARINE_CRYSTALS, null,
            null, Ench.Blocks.INFUSED_SEASHELF, null,
            Items.PRISMARINE_CRYSTALS, null, Items.PRISMARINE_CRYSTALS);

        addShaped(Ench.Blocks.HEART_SEASHELF, 3, 3,
            null, Items.HEART_OF_THE_SEA, null,
            Items.PRISMARINE_SHARD, Ench.Blocks.INFUSED_SEASHELF, Items.PRISMARINE_SHARD,
            Items.PRISMARINE_SHARD, Items.PRISMARINE_SHARD, Items.PRISMARINE_SHARD);

        addShaped(Ench.Blocks.BEESHELF, 3, 3,
            Items.HONEYCOMB, Items.BEEHIVE, Items.HONEYCOMB,
            Items.HONEY_BLOCK, Tags.Items.BOOKSHELVES, Items.HONEY_BLOCK,
            Items.HONEYCOMB, Items.BEEHIVE, Items.HONEYCOMB);

        addShaped(Ench.Blocks.MELONSHELF, 3, 3,
            Items.MELON, Items.MELON, Items.MELON,
            Items.GLISTERING_MELON_SLICE, Tags.Items.BOOKSHELVES, Items.GLISTERING_MELON_SLICE,
            Items.MELON, Items.MELON, Items.MELON);

        addShaped(Ench.Blocks.BASIC_BOOKSHELF, 3, 3,
            ItemTags.PLANKS, ItemTags.PLANKS, ItemTags.PLANKS,
            EnchItemTagsProvider.TOMES, EnchItemTagsProvider.TOMES, EnchItemTagsProvider.TOMES,
            ItemTags.PLANKS, ItemTags.PLANKS, ItemTags.PLANKS);

        addShaped(Ench.Blocks.APOTHIC_ENCHANTING_TABLE, 3, 3,
            null, EnchItemTagsProvider.TOMES, null,
            Items.DIAMOND, Items.OBSIDIAN, Items.DIAMOND,
            Items.OBSIDIAN, Items.OBSIDIAN, Items.OBSIDIAN);

        addShaped(Ench.Blocks.GEODE_SHELF, 3, 3,
            Items.CALCITE, Items.CALCITE, Items.CALCITE,
            Items.CALCITE, Tags.Items.BOOKSHELVES, Items.CALCITE,
            Items.CALCITE, Items.BUDDING_AMETHYST, Items.CALCITE);

        addShaped(Ench.Blocks.SIGHTSHELF, 3, 3,
            Tags.Items.STORAGE_BLOCKS_GOLD, Ench.Items.INFUSED_HELLSHELF, Tags.Items.STORAGE_BLOCKS_GOLD,
            potionIngredient(Potions.NIGHT_VISION), Items.ENDER_EYE, Items.SPYGLASS,
            Tags.Items.STORAGE_BLOCKS_GOLD, Ench.Items.INFUSED_HELLSHELF, Tags.Items.STORAGE_BLOCKS_GOLD);

        Ingredient nightVisPot = potionIngredient(Potions.LONG_NIGHT_VISION);
        addShaped(Ench.Blocks.SIGHTSHELF_T2, 3, 3,
            Items.EMERALD_BLOCK, Tags.Items.INGOTS_NETHERITE, Items.EMERALD_BLOCK,
            nightVisPot, Ench.Items.SIGHTSHELF, nightVisPot,
            Items.EMERALD_BLOCK, Tags.Items.INGOTS_NETHERITE, Items.EMERALD_BLOCK);

        addShaped(Ench.Blocks.ENDSHELF, 3, 3,
            Items.END_STONE_BRICKS, Items.END_STONE_BRICKS, Items.END_STONE_BRICKS,
            Ench.Items.INFUSED_BREATH, Tags.Items.BOOKSHELVES, Tags.Items.ENDER_PEARLS,
            Items.END_STONE_BRICKS, Items.END_STONE_BRICKS, Items.END_STONE_BRICKS);

        addShaped(Ench.Blocks.PEARL_ENDSHELF, 3, 3,
            Items.END_ROD, null, Items.END_ROD,
            Tags.Items.ENDER_PEARLS, Ench.Items.ENDSHELF, Tags.Items.ENDER_PEARLS,
            Items.END_ROD, null, Items.END_ROD);

        addShaped(Ench.Blocks.DRACONIC_ENDSHELF, 3, 3,
            null, Items.DRAGON_HEAD, null,
            Tags.Items.ENDER_PEARLS, Ench.Items.ENDSHELF, Tags.Items.ENDER_PEARLS,
            Tags.Items.ENDER_PEARLS, Tags.Items.ENDER_PEARLS, Tags.Items.ENDER_PEARLS);

        addShaped(Items.COBWEB, 3, 3,
            Tags.Items.STRINGS, Tags.Items.STRINGS, Tags.Items.STRINGS,
            Tags.Items.STRINGS, Items.HONEYCOMB, Tags.Items.STRINGS,
            Tags.Items.STRINGS, Tags.Items.STRINGS, Tags.Items.STRINGS);

        addShaped(Ench.Items.TREASURE_SHELF, 3, 3,
            Tags.Items.STORAGE_BLOCKS_GOLD, Ench.Items.DEEPSHELF, Tags.Items.STORAGE_BLOCKS_GOLD,
            Tags.Items.GEMS_DIAMOND, Tags.Items.STORAGE_BLOCKS_EMERALD, Tags.Items.GEMS_DIAMOND,
            Tags.Items.STORAGE_BLOCKS_GOLD, Ench.Items.DEEPSHELF, Tags.Items.STORAGE_BLOCKS_GOLD);

        addShaped(Ench.Items.INERT_TRIDENT, 3, 3,
            Items.NAUTILUS_SHELL, Items.NAUTILUS_SHELL, Items.NAUTILUS_SHELL,
            null, Items.HEART_OF_THE_SEA, null,
            null, Tags.Items.INGOTS_IRON, null);

        ItemStack pufferfish = new ItemStack(Items.PUFFERFISH);
        pufferfish.set(DataComponents.CUSTOM_NAME, Component.translatable("\"%s\"", pufferfish.getHoverName()).withStyle(Style.EMPTY.withItalic(false)));
        addShaped(pufferfish, 3, 3,
            null, Items.BAMBOO, null,
            Items.BAMBOO, ItemTags.FISHES, Items.BAMBOO,
            null, Items.BAMBOO, null);

        addShapeless(Ench.Items.FLIMSY_ENDER_LEAD, Tags.Items.ENDER_PEARLS, Items.LEAD, Items.GOLD_INGOT);
    }
}
