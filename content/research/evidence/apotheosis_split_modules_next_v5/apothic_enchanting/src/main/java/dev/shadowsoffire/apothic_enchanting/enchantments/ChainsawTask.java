package dev.shadowsoffire.apothic_enchanting.enchantments;

import java.util.ArrayDeque;
import java.util.Queue;
import java.util.UUID;

import dev.shadowsoffire.apothic_enchanting.ApothicEnchanting;
import dev.shadowsoffire.apothic_enchanting.Ench;
import dev.shadowsoffire.apothic_enchanting.util.MiscUtil;
import dev.shadowsoffire.placebo.util.PlaceboTaskQueue;
import dev.shadowsoffire.placebo.util.PlaceboTaskQueue.Status;
import it.unimi.dsi.fastutil.ints.Int2ObjectMap;
import it.unimi.dsi.fastutil.ints.Int2ObjectOpenHashMap;
import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.tags.BlockTags;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.enchantment.EnchantmentHelper;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.state.BlockState;
import net.neoforged.neoforge.event.level.BlockEvent.BreakEvent;

public class ChainsawTask implements PlaceboTaskQueue.Task {

    UUID owner;
    ItemStack axe;
    ServerLevel level;
    Int2ObjectMap<Queue<BlockPos>> hits = new Int2ObjectOpenHashMap<>();
    int ticks = 0;

    private ChainsawTask(UUID owner, ItemStack axe, Level level, BlockPos pos) {
        this.owner = owner;
        this.axe = axe;
        this.level = (ServerLevel) level;
        this.hits.computeIfAbsent(pos.getY(), i -> new ArrayDeque<>()).add(pos);
    }

    @Override
    public Status execute() {
        if (++this.ticks % 2 != 0) {
            return Status.RUNNING;
        }

        if (this.axe.isEmpty()) {
            return Status.COMPLETED;
        }

        int minY = this.hits.keySet().intStream().min().getAsInt();
        Queue<BlockPos> queue = this.hits.get(minY);
        int breaks = 0;
        while (!queue.isEmpty()) {
            BlockPos pos = queue.poll();
            for (BlockPos p : BlockPos.betweenClosed(pos.offset(-1, 0, -1), pos.offset(1, 1, 1))) {
                if (p.equals(pos)) continue;
                BlockState state = this.level.getBlockState(p);
                if (state.is(BlockTags.LOGS)) {
                    MiscUtil.breakExtraBlock(this.level, p, this.axe, this.owner);
                    if (!this.level.getBlockState(p).is(BlockTags.LOGS)) { // Ensure a change happened
                        this.hits.computeIfAbsent(p.getY(), i -> new ArrayDeque<>()).add(p.immutable());
                        breaks++;
                    }
                }
            }
            if (breaks > 5) break;
        }
        if (queue.isEmpty()) this.hits.remove(minY);

        return this.hits.isEmpty() ? Status.COMPLETED : Status.RUNNING;
    }

    public static void attemptChainsaw(BreakEvent e) {
        Player player = e.getPlayer();
        Level level = player.level();
        ItemStack stack = player.getMainHandItem();
        boolean hasChainsaw = EnchantmentHelper.has(stack, Ench.EnchantEffects.CHAINSAW);
        if (player.getClass() == ServerPlayer.class && hasChainsaw && !level.isClientSide && isTree(level, e.getPos(), e.getState())) {
            if (!player.getAbilities().instabuild) PlaceboTaskQueue.submitTask(ApothicEnchanting.loc("chainsaw_task"), new ChainsawTask(player.getUUID(), stack, level, e.getPos()));
        }
    }

    private static boolean isTree(Level level, BlockPos pos, BlockState state) {
        if (!state.is(BlockTags.LOGS)) return false;
        while (state.is(BlockTags.LOGS)) {
            state = level.getBlockState(pos = pos.above());
        }
        for (BlockPos p : BlockPos.betweenClosed(pos.offset(-2, -2, -2), pos.offset(2, 2, 2))) {
            if (level.getBlockState(p).is(BlockTags.LEAVES)) return true;
        }
        return false;
    }

}
