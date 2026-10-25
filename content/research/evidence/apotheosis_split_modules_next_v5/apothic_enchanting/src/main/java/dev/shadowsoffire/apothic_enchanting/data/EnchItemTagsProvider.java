package dev.shadowsoffire.apothic_enchanting.data;

import java.util.concurrent.CompletableFuture;

import org.jetbrains.annotations.Nullable;

import dev.shadowsoffire.apothic_enchanting.ApothicEnchanting;
import dev.shadowsoffire.apothic_enchanting.Ench;
import net.minecraft.core.Holder;
import net.minecraft.core.HolderLookup.Provider;
import net.minecraft.data.PackOutput;
import net.minecraft.data.tags.ItemTagsProvider;
import net.minecraft.data.tags.TagsProvider;
import net.minecraft.tags.ItemTags;
import net.minecraft.tags.TagKey;
import net.minecraft.world.item.Item;
import net.minecraft.world.level.block.Block;
import net.neoforged.neoforge.common.Tags;
import net.neoforged.neoforge.common.data.ExistingFileHelper;

public class EnchItemTagsProvider extends ItemTagsProvider {

    public static final TagKey<Item> TOMES = ItemTags.create(ApothicEnchanting.loc("tomes"));

    public EnchItemTagsProvider(PackOutput output, CompletableFuture<Provider> lookupProvider, @Nullable ExistingFileHelper existingFileHelper) {
        super(output, lookupProvider, CompletableFuture.completedFuture(TagsProvider.TagLookup.empty()), ApothicEnchanting.MODID, existingFileHelper);
    }

    @Override
    protected void addTags(Provider registries) {
        this.tag(Tags.Items.BOOKSHELVES).add(
            asItem(Ench.Blocks.BASIC_BOOKSHELF),
            asItem(Ench.Blocks.BEESHELF),
            asItem(Ench.Blocks.DORMANT_DEEPSHELF),
            asItem(Ench.Blocks.MELONSHELF),
            asItem(Ench.Blocks.STONESHELF));

        this.tag(TOMES).add(
            Ench.Items.BOOTS_TOME.value(),
            Ench.Items.BOW_TOME.value(),
            Ench.Items.CHESTPLATE_TOME.value(),
            Ench.Items.EXTRACTION_TOME.value(),
            Ench.Items.FISHING_TOME.value(),
            Ench.Items.HELMET_TOME.value(),
            Ench.Items.IMPROVED_SCRAP_TOME.value(),
            Ench.Items.LEGGINGS_TOME.value(),
            Ench.Items.OTHER_TOME.value(),
            Ench.Items.PICKAXE_TOME.value(),
            Ench.Items.SCRAP_TOME.value(),
            Ench.Items.WEAPON_TOME.value());

        this.tag(ItemTags.BOOKSHELF_BOOKS).addTag(TOMES);
    }

    private static Item asItem(Holder<Block> block) {
        return block.value().asItem();
    }
}
