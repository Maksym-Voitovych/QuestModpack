package dev.shadowsoffire.apothic_enchanting.objects;

import java.util.ArrayList;
import java.util.Collections;
import java.util.HashSet;
import java.util.List;
import java.util.OptionalInt;
import java.util.Set;

import dev.shadowsoffire.apothic_enchanting.Ench;
import dev.shadowsoffire.apothic_enchanting.api.EnchantmentStatBlock;
import dev.shadowsoffire.apothic_enchanting.util.TooltipUtil;
import dev.shadowsoffire.placebo.network.VanillaPacketDispatcher;
import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Holder;
import net.minecraft.core.HolderLookup;
import net.minecraft.core.particles.ParticleOptions;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.Connection;
import net.minecraft.network.chat.Component;
import net.minecraft.network.protocol.game.ClientboundBlockEntityDataPacket;
import net.minecraft.tags.ItemTags;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.ItemInteractionResult;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item.TooltipContext;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.item.TooltipFlag;
import net.minecraft.world.item.enchantment.Enchantment;
import net.minecraft.world.item.enchantment.EnchantmentHelper;
import net.minecraft.world.item.enchantment.ItemEnchantments;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.LevelReader;
import net.minecraft.world.level.block.ChiseledBookShelfBlock;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.entity.BlockEntityType;
import net.minecraft.world.level.block.entity.ChiseledBookShelfBlockEntity;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.BlockHitResult;

public class FilteringShelfBlock extends ChiseledBookShelfBlock implements EnchantmentStatBlock {

    public FilteringShelfBlock(Properties pProperties) {
        super(pProperties);
    }

    @Override
    public Set<Holder<Enchantment>> getBlacklistedEnchantments(BlockState state, LevelReader world, BlockPos pos) {
        BlockEntity be = world.getBlockEntity(pos);
        if (be instanceof FilteringShelfTile shelf) {
            Set<Holder<Enchantment>> blacklist = new HashSet<>();
            for (ItemStack s : shelf.getEnchantedBooks()) {
                ItemEnchantments enchants = EnchantmentHelper.getEnchantmentsForCrafting(s);
                if (enchants.size() != 1) {
                    continue; // Only books with one enchantment are legal.
                }

                Holder<Enchantment> ench = enchants.keySet().stream().findFirst().orElse(null);
                if (ench != null) {
                    blacklist.add(ench);
                }
            }
            return blacklist;
        }
        return Collections.emptySet();
    }

    @Override
    public float getMaxEnchantingPower(BlockState state, LevelReader world, BlockPos pos) {
        return 30F;
    }

    @Override
    public float getEnchantPowerBonus(BlockState state, LevelReader level, BlockPos pos) {
        BlockEntity be = level.getBlockEntity(pos);
        if (be instanceof FilteringShelfTile shelf) {
            return shelf.getEnchantedBooks().size() * 0.5F;
        }
        return 0;
    }

    @Override
    public float getArcanaBonus(BlockState state, LevelReader world, BlockPos pos) {
        BlockEntity be = world.getBlockEntity(pos);
        if (be instanceof FilteringShelfTile shelf) {
            return shelf.getEnchantedBooks().size();
        }
        return 0;
    }

    @Override
    public ParticleOptions getTableParticle(BlockState state) {
        return Ench.Particles.ENCHANT_WATER;
    }

    @Override
    public ItemInteractionResult useItemOn(ItemStack stack, BlockState state, Level level, BlockPos pos, Player player, InteractionHand hand, BlockHitResult hitResult) {
        BlockEntity be = level.getBlockEntity(pos);
        if (be instanceof ChiseledBookShelfBlockEntity shelf) {
            if (!canInsert(stack)) {
                return ItemInteractionResult.PASS_TO_DEFAULT_BLOCK_INTERACTION;
            }

            OptionalInt slot = this.getHitSlot(hitResult, state);
            if (slot.isEmpty()) {
                return ItemInteractionResult.SKIP_DEFAULT_BLOCK_INTERACTION;
            }
            else if (state.getValue(SLOT_OCCUPIED_PROPERTIES.get(slot.getAsInt()))) {
                return ItemInteractionResult.PASS_TO_DEFAULT_BLOCK_INTERACTION;
            }
            else {
                addBook(level, pos, player, shelf, stack, slot.getAsInt());
                return ItemInteractionResult.sidedSuccess(level.isClientSide);
            }
        }

        return ItemInteractionResult.SKIP_DEFAULT_BLOCK_INTERACTION;
    }

    @Override
    public BlockEntity newBlockEntity(BlockPos pPos, BlockState pState) {
        return new FilteringShelfTile(pPos, pState);
    }

    @Override
    public void appendHoverText(ItemStack stack, TooltipContext context, List<Component> tooltip, TooltipFlag tooltipFlag) {
        tooltip.add(TooltipUtil.lang("info", "filtering_shelf").withStyle(ChatFormatting.GRAY));
    }

    public static boolean canInsert(ItemStack stack) {
        return stack.is(ItemTags.BOOKSHELF_BOOKS);
    }

    public static boolean isEnchantedBook(ItemStack stack) {
        return stack.is(Items.ENCHANTED_BOOK) && EnchantmentHelper.getEnchantmentsForCrafting(stack).size() == 1;
    }

    public static class FilteringShelfTile extends ChiseledBookShelfBlockEntity {

        public FilteringShelfTile(BlockPos pPos, BlockState pState) {
            super(pPos, pState);
        }

        @Override
        public boolean canPlaceItem(int pIndex, ItemStack pStack) {
            return canInsert(pStack);
        }

        @Override
        public BlockEntityType<?> getType() {
            return Ench.Tiles.FILTERING_SHELF.get();
        }

        public List<ItemStack> getBooks() {
            List<ItemStack> books = new ArrayList<>();
            for (int i = 0; i < 6; i++) {
                ItemStack stack = this.getItem(i);
                if (!stack.isEmpty()) books.add(stack);
            }
            return books;
        }

        public List<ItemStack> getEnchantedBooks() {
            return getBooks().stream().filter(FilteringShelfBlock::isEnchantedBook).toList();
        }

        @Override
        public CompoundTag getUpdateTag(HolderLookup.Provider registries) {
            CompoundTag tag = new CompoundTag();
            this.saveAdditional(tag, registries);
            return tag;
        }

        @Override
        public void onDataPacket(Connection net, ClientboundBlockEntityDataPacket pkt, HolderLookup.Provider registries) {
            this.loadAdditional(pkt.getTag(), registries);
        }

        @Override
        public ClientboundBlockEntityDataPacket getUpdatePacket() {
            return ClientboundBlockEntityDataPacket.create(this);
        }

        @Override
        public void setItem(int pSlot, ItemStack pStack) {
            super.setItem(pSlot, pStack);
            if (!this.level.isClientSide) {
                VanillaPacketDispatcher.dispatchTEToNearbyPlayers(this);
            }
        }

    }

}
