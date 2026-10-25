package dev.shadowsoffire.apothic_enchanting.table;

import net.minecraft.world.item.ItemStack;
import net.neoforged.neoforge.attachment.AttachmentType;
import net.neoforged.neoforge.common.Tags;
import net.neoforged.neoforge.items.ItemStackHandler;

public class EnchantmentTableItemHandler extends ItemStackHandler {

    public static final AttachmentType<EnchantmentTableItemHandler> TYPE = AttachmentType.serializable(EnchantmentTableItemHandler::new).build();

    public EnchantmentTableItemHandler() {
        super(1);
    }

    @Override
    @SuppressWarnings("deprecation")
    public boolean isItemValid(int slot, ItemStack stack) {
        return stack.is(Tags.Items.ENCHANTING_FUELS);
    };

}
