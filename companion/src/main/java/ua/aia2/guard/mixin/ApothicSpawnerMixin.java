package ua.aia2.guard.mixin;

import net.minecraft.core.BlockPos;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.ItemInteractionResult;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.BlockHitResult;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Pseudo;
import org.spongepowered.asm.mixin.Unique;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;
import ua.aia2.guard.Aia2MachineGuard;

/** Apothic Spawners 1.4.0 applies modifiers before consuming their held runes. */
@Pseudo
@Mixin(targets = "dev.shadowsoffire.apothic_spawners.block.ApothSpawnerBlock", remap = false)
abstract class ApothicSpawnerMixin {
    @Inject(method = "useItemOn(Lnet/minecraft/world/item/ItemStack;Lnet/minecraft/world/level/block/state/BlockState;Lnet/minecraft/world/level/Level;Lnet/minecraft/core/BlockPos;Lnet/minecraft/world/entity/player/Player;Lnet/minecraft/world/InteractionHand;Lnet/minecraft/world/phys/BlockHitResult;)Lnet/minecraft/world/ItemInteractionResult;",
            at = @At("HEAD"), cancellable = true, remap = false, require = 1)
    private void aia2$guardRune(ItemStack stack, BlockState state, Level level, BlockPos pos,
                                Player player, InteractionHand hand, BlockHitResult hit,
                                CallbackInfoReturnable<ItemInteractionResult> callback) {
        if (!(level instanceof ServerLevel)) return;
        ItemStack other = player.getItemInHand(hand == InteractionHand.MAIN_HAND ? InteractionHand.OFF_HAND : InteractionHand.MAIN_HAND);
        if (!aia2$mayUseRune(player, stack) || !aia2$mayUseRune(player, other)) {
            callback.setReturnValue(ItemInteractionResult.FAIL);
        }
    }

    @Unique private static boolean aia2$mayUseRune(Player player, ItemStack stack) {
        var id = BuiltInRegistries.ITEM.getKey(stack.getItem());
        boolean rune = id.getNamespace().equals("apotheosis") &&
                (id.getPath().endsWith("spawner_rune") || id.getPath().endsWith("spawner_upgrade_rune"));
        return !rune || Aia2MachineGuard.mayCraft(player, stack);
    }
}
