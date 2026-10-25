package dev.shadowsoffire.apothic_enchanting.util;

import java.util.UUID;

import javax.annotation.Nullable;

import com.mojang.authlib.GameProfile;

import dev.shadowsoffire.apothic_enchanting.ApothEnchClient;
import dev.shadowsoffire.placebo.color.GradientColor;
import dev.shadowsoffire.placebo.util.EnchantmentUtils;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Holder;
import net.minecraft.core.Holder.Kind;
import net.minecraft.core.Registry;
import net.minecraft.resources.ResourceKey;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.server.level.ServerPlayerGameMode;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.enchantment.Enchantment;
import net.minecraft.world.level.GameType;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.GameMasterBlock;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.state.BlockState;
import net.neoforged.fml.LogicalSide;
import net.neoforged.fml.loading.FMLEnvironment;
import net.neoforged.fml.util.thread.EffectiveSide;
import net.neoforged.neoforge.common.CommonHooks;
import net.neoforged.neoforge.common.UsernameCache;
import net.neoforged.neoforge.common.util.FakePlayer;
import net.neoforged.neoforge.common.util.FakePlayerFactory;
import net.neoforged.neoforge.event.EventHooks;
import net.neoforged.neoforge.event.level.BlockEvent.BreakEvent;
import net.neoforged.neoforge.server.ServerLifecycleHooks;

public class MiscUtil {

    /**
     * Gets the experience cost when enchanting at a particular slot. This computes the true xp cost as if you had exactly as many levels as the level cost.
     * <p>
     * For a slot S and level L, the costs are the following:<br>
     * S == 0 -> cost = XP(L)<br>
     * S == 1 -> cost = XP(L) + XP(L-1)<br>
     * S == 2 -> cost = XP(L) + XP(L-1) + XP(L-2)
     * <p>
     * And so on and so forth, if there were ever to be more than three slots.
     *
     * @param level The level of the slot
     * @param slot  The slot index
     * @return The cost, in experience points, of buying the enchantment in a particular slot.
     */
    public static int getExpCostForSlot(int level, int slot) {
        int cost = 0;
        for (int i = 0; i <= slot; i++) {
            cost += EnchantmentUtils.getExperienceForLevel(level - i);
        }
        return cost - 1; // Eating exactly the amount will put you one point below the level, so offset by one here.
    }

    /**
     * Since {@link GradientColor} goes 1:1 through the entire array, if we have a unidirectional gradient, we need to make it wrap around.
     * <p>
     * This is done by making a reversed copy and concatenating them together.
     *
     * @param data The original unidirectional gradient data.
     * @return A cyclical gradient.
     */
    public static int[] doubleUpGradient(int[] data) {
        int[] out = new int[data.length * 2];
        System.arraycopy(data, 0, out, 0, data.length);
        for (int i = data.length - 1; i >= 0; i--) {
            out[data.length * 2 - 1 - i] = data[i];
        }
        return out;
    }

    /**
     * Checks if the affix is still on cooldown, if a cooldown was set via {@link #startCooldown(ResourceLocation, int, LivingEntity)}
     */
    public static boolean isOnCooldown(ResourceLocation id, LivingEntity entity) {
        long cooldownEndTime = entity.getPersistentData().getLong("apothic_enchanting.cooldown." + id.toString());
        return cooldownEndTime > entity.level().getGameTime();
    }

    /**
     * Records the current time as a cooldown tracker. Used in conjunction with {@link #isOnCooldown(ResourceLocation, int, LivingEntity)}
     */
    public static void startCooldown(ResourceLocation id, LivingEntity entity, int cooldown) {
        entity.getPersistentData().putLong("apothic_enchanting.cooldown." + id.toString(), entity.level().getGameTime() + cooldown);
    }

    /**
     * Vanilla Copy: {@link ServerPlayerGameMode#destroyBlock} <br>
     * Attempts to harvest a block as if the player with the given uuid
     * harvested it while holding the passed item.
     *
     * @param level    The level the block is in.
     * @param pos      The position of the block.
     * @param mainhand The main hand item that the player is supposibly holding.
     * @param source   The UUID of the breaking player.
     * @return If the block was successfully broken.
     */
    public static boolean breakExtraBlock(ServerLevel level, BlockPos pos, ItemStack mainhand, @Nullable UUID source) {
        BlockState state = level.getBlockState(pos);
        FakePlayer player;
        if (source != null) {
            player = FakePlayerFactory.get(level, new GameProfile(source, UsernameCache.getLastKnownUsername(source)));
            Player realPlayer = level.getPlayerByUUID(source);
            player.removeAllEffects();
            if (realPlayer != null) {
                // Move the fakeplayer to the position of the real player, if one is known
                player.setPos(realPlayer.position());
                // Clone all mob effects from the real player. Prevents issues with Occultism's Trees
                for (MobEffectInstance effect : realPlayer.getActiveEffects()) {
                    player.forceAddEffect(new MobEffectInstance(effect), null);
                }
            }
        }
        else {
            player = FakePlayerFactory.getMinecraft(level);
        }

        player.getInventory().items.set(player.getInventory().selected, mainhand);

        if (state.getDestroySpeed(level, pos) < 0 || !state.canHarvestBlock(level, pos, player)) {
            return false;
        }

        GameType type = player.getAbilities().instabuild ? GameType.CREATIVE : GameType.SURVIVAL;
        BreakEvent exp = CommonHooks.fireBlockBreak(level, type, player, pos, state);
        if (exp.isCanceled()) {
            return false;
        }
        else {
            BlockEntity blockEntity = level.getBlockEntity(pos);
            Block block = state.getBlock();
            if (block instanceof GameMasterBlock && !player.canUseGameMasterBlocks()) {
                level.sendBlockUpdated(pos, state, state, 3);
                return false;
            }
            else if (player.blockActionRestricted(level, pos, type)) {
                return false;
            }
            else {
                BlockState newState = block.playerWillDestroy(level, pos, state, player);
                if (player.getAbilities().instabuild) {
                    removeBlock(level, player, pos, newState, false);
                    return true;
                }
                else {
                    ItemStack tool = player.getMainHandItem();
                    ItemStack toolCopy = tool.copy();
                    boolean canHarvest = newState.canHarvestBlock(level, pos, player);
                    tool.mineBlock(level, newState, pos, player);
                    boolean removed = removeBlock(level, player, pos, newState, canHarvest);

                    if (canHarvest && removed) {
                        block.playerDestroy(level, player, pos, newState, blockEntity, toolCopy);
                    }

                    if (tool.isEmpty() && !toolCopy.isEmpty()) {
                        EventHooks.onPlayerDestroyItem(player, toolCopy, InteractionHand.MAIN_HAND);
                    }

                    return true;
                }
            }
        }
    }

    /**
     * Vanilla Copy: {@link ServerPlayerGameMode#removeBlock(BlockPos, BlockState, boolean)}
     *
     * @param level      The world
     * @param player     The removing player
     * @param pos        The block location
     * @param canHarvest If the player can actually harvest this block.
     * @return If the block was actually removed.
     */
    public static boolean removeBlock(ServerLevel level, ServerPlayer player, BlockPos pos, BlockState state, boolean canHarvest) {
        boolean removed = state.onDestroyedByPlayer(level, pos, player, canHarvest, level.getFluidState(pos));
        if (removed) {
            state.getBlock().destroy(level, pos, state);
        }
        return removed;
    }

    public static String getEnchDescKey(Holder<Enchantment> ench) {
        return ench.getKey().location().toLanguageKey("enchantment") + ".desc";
    }

    /**
     * Attempts to lookup a holder for an object using the current global state.
     */
    @Nullable
    public static <T> Holder<T> findHolder(ResourceKey<? extends Registry<T>> registryKey, T obj) {
        LogicalSide side = EffectiveSide.get();

        // Attempt to lookup from the side indicated by LogicalSide
        Holder<T> holder = side.isClient() ? findHolderFromClient(registryKey, obj) : findHolderFromServer(registryKey, obj);
        if (holder != null) {
            return holder;
        }

        // Try the other one if that attempt failed
        return side.isClient() ? findHolderFromServer(registryKey, obj) : findHolderFromClient(registryKey, obj);
    }

    @Nullable
    public static <T> Holder<T> findHolderFromServer(ResourceKey<? extends Registry<T>> registryKey, T obj) {
        MinecraftServer server = ServerLifecycleHooks.getCurrentServer();
        if (server != null) {
            Registry<T> registry = server.registries().compositeAccess().registry(registryKey).orElse(null);
            if (registry != null) {
                Holder<T> holder = registry.wrapAsHolder(obj);
                if (holder.kind() == Kind.REFERENCE) {
                    return holder;
                }
            }
        }
        return null;
    }

    @Nullable
    public static <T> Holder<T> findHolderFromClient(ResourceKey<? extends Registry<T>> registryKey, T obj) {
        if (FMLEnvironment.dist.isClient()) {
            Registry<T> registry = ApothEnchClient.findClientRegistry(registryKey);
            if (registry != null) {
                Holder<T> holder = registry.wrapAsHolder(obj);
                if (holder.kind() == Kind.REFERENCE) {
                    return holder;
                }
            }
        }
        return null;
    }

}
