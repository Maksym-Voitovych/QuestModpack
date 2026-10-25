package dev.shadowsoffire.apothic_enchanting.table;

import dev.shadowsoffire.apothic_enchanting.ApothicEnchanting;
import net.minecraft.resources.ResourceLocation;

public class ApothicEnchantingTableBlock extends ApothEnchantingTableBlock implements BookTexturedTable {

    public static final ResourceLocation BOOK_TEXTURE_ID = ApothicEnchanting.loc("apothic_book");

    public ApothicEnchantingTableBlock(Properties props) {
        super(props);
    }

    @Override
    public ResourceLocation getBookTextureId() {
        return BOOK_TEXTURE_ID;
    }

}
