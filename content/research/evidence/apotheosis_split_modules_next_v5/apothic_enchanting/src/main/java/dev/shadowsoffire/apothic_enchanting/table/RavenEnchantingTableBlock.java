package dev.shadowsoffire.apothic_enchanting.table;

import javax.annotation.Nullable;

import dev.shadowsoffire.apothic_enchanting.ApothicEnchanting;
import net.minecraft.core.BlockPos;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.MenuProvider;
import net.minecraft.world.Nameable;
import net.minecraft.world.SimpleMenuProvider;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.inventory.ContainerLevelAccess;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.entity.EnchantingTableBlockEntity;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.BlockHitResult;

/**
 * End-game table that allows manually setting eterna/quanta/arcana.
 */
public class RavenEnchantingTableBlock extends ApothicEnchantingTableBlock implements BookTexturedTable {

    public static final ResourceLocation BOOK_TEXTURE_ID = ApothicEnchanting.loc("raven_book");

    public RavenEnchantingTableBlock(Properties props) {
        super(props);
    }

    @Override
    public ResourceLocation getBookTextureId() {
        return BOOK_TEXTURE_ID;
    }

    @Override
    @Nullable
    public MenuProvider getMenuProvider(BlockState state, Level world, BlockPos pos) {
        if (!(world.getBlockEntity(pos) instanceof EnchantingTableBlockEntity tile)) {
            return null;
        }
        Component title = ((Nameable) tile).getDisplayName();
        RavenTableStats stats = tile.getData(RavenTableStats.TYPE);
        EnchantmentTableItemHandler teInv = tile.getData(EnchantmentTableItemHandler.TYPE);
        return new SimpleMenuProvider((id, inv, player) -> new RavenEnchantmentMenu(id, inv, ContainerLevelAccess.create(world, pos), teInv, pos, stats), title);
    }

    /**
     * Opens the menu with a data buffer carrying the table position and the persisted stats, so the client-side
     * menu factory ({@code R.menuWithData} + {@link RavenEnchantmentMenu#fromBuf}) can reconstruct them.
     */
    @Override
    protected InteractionResult useWithoutItem(BlockState state, Level level, BlockPos pos, Player player, BlockHitResult hit) {
        if (level.isClientSide) {
            return InteractionResult.SUCCESS;
        }
        MenuProvider provider = state.getMenuProvider(level, pos);
        if (provider != null && level.getBlockEntity(pos) instanceof EnchantingTableBlockEntity tile) {
            RavenTableStats stats = tile.getData(RavenTableStats.TYPE);
            player.openMenu(provider, buf -> {
                buf.writeBlockPos(pos);
                buf.writeInt(stats.eterna());
                buf.writeInt(stats.quanta());
                buf.writeInt(stats.arcana());
            });
        }
        return InteractionResult.CONSUME;
    }

}
