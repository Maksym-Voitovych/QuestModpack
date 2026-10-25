package dev.shadowsoffire.apothic_enchanting.table;

import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.level.block.EnchantingTableBlock;

/**
 * Custom interface to be implemented on a {@link EnchantingTableBlock} subclass that allows it to override the texture used to render the floating book.
 */
public interface BookTexturedTable {

    ResourceLocation getBookTextureId();

    /**
     * Variant of {@link #getBookTextureId()} that rewrites the texture to the format used in the screen.
     */
    default ResourceLocation getBookGuiTexture() {
        ResourceLocation id = this.getBookTextureId();
        return id.withPath("textures/entity/" + id.getPath() + ".png");
    }

}
