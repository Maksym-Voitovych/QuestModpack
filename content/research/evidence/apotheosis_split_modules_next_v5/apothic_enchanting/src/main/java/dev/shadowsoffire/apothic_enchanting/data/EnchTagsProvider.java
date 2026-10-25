package dev.shadowsoffire.apothic_enchanting.data;

import java.util.concurrent.CompletableFuture;

import org.jetbrains.annotations.Nullable;

import dev.shadowsoffire.apothic_enchanting.ApothicEnchanting;
import dev.shadowsoffire.apothic_enchanting.Ench;
import net.minecraft.core.HolderLookup.Provider;
import net.minecraft.data.PackOutput;
import net.minecraft.data.tags.EnchantmentTagsProvider;
import net.minecraft.tags.EnchantmentTags;
import net.minecraft.world.item.enchantment.Enchantments;
import net.neoforged.neoforge.common.data.ExistingFileHelper;

public class EnchTagsProvider extends EnchantmentTagsProvider {

    public EnchTagsProvider(PackOutput output, CompletableFuture<Provider> lookupProvider, @Nullable ExistingFileHelper existingFileHelper) {
        super(output, lookupProvider, ApothicEnchanting.MODID, existingFileHelper);
    }

    @Override
    protected void addTags(Provider provider) {
        this.tag(EnchantmentTags.CURSE).add(
            Ench.Enchantments.BERSERKERS_FURY,
            Ench.Enchantments.LIFE_MENDING);

        this.tag(EnchantmentTags.NON_TREASURE).add(
            Ench.Enchantments.BERSERKERS_FURY,
            Ench.Enchantments.BOON_OF_THE_EARTH,
            Ench.Enchantments.CHAINSAW,
            Ench.Enchantments.CHROMATIC,
            Ench.Enchantments.CRESCENDO_OF_BOLTS,
            Ench.Enchantments.ENDLESS_QUIVER,
            Ench.Enchantments.GROWTH_SERUM,
            Ench.Enchantments.ICY_THORNS,
            Ench.Enchantments.KNOWLEDGE_OF_THE_AGES,
            Ench.Enchantments.LIFE_MENDING,
            Ench.Enchantments.MINERS_FERVOR,
            Ench.Enchantments.NATURES_BLESSING,
            Ench.Enchantments.REBOUNDING,
            Ench.Enchantments.REFLECTIVE_DEFENSES,
            Ench.Enchantments.SCAVENGER,
            Ench.Enchantments.SHIELD_BASH,
            Ench.Enchantments.STABLE_FOOTING,
            Ench.Enchantments.TEMPTING,
            Ench.Enchantments.WORKER_EXPLOITATION);

        // Make Sharpness and Protection non-exclusive - we also override them for the same reason.
        this.tag(EnchantmentTags.DAMAGE_EXCLUSIVE).remove(Enchantments.SHARPNESS);
        this.tag(EnchantmentTags.ARMOR_EXCLUSIVE).remove(Enchantments.PROTECTION);
    }

}
