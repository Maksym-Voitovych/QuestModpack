package ua.aia2.guard;

import com.mojang.brigadier.arguments.IntegerArgumentType;
import net.minecraft.commands.Commands;
import net.minecraft.core.BlockPos;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.event.RegisterCommandsEvent;

/** Explicit nearby diagnostics and operator recovery; never an installer migration. */
@EventBusSubscriber(modid = Aia2MachineGuard.MOD_ID)
public final class ClibanoCommands {
    private ClibanoCommands() {}
    private static BlockEntity owned(ServerPlayer player, BlockPos pos) {
        if (player == null || player.blockPosition().distSqr(pos) > 64 || !player.serverLevel().hasChunkAt(pos)) return null;
        BlockEntity clicked = player.serverLevel().getBlockEntity(pos);
        BlockEntity main = ClibanoOwnership.resolveMain(clicked);
        if (main == null || !player.serverLevel().mayInteract(player, pos)) return null;
        String team = Aia2MachineGuard.synchronizedPlayerTeam(player);
        return !team.isBlank() && team.equals(Aia2MachineGuard.getOwner(main)) ? main : null;
    }
    @SubscribeEvent
    public static void register(RegisterCommandsEvent event) {
        var root = Commands.literal("aia2clibano");
        for (String action : new String[] {"status", "cancel", "quarantine-residues"}) {
            var branch = Commands.literal(action);
            if (!action.equals("status")) branch.requires(source -> source.hasPermission(2));
            branch.then(Commands.argument("x", IntegerArgumentType.integer()).then(
                    Commands.argument("y", IntegerArgumentType.integer()).then(
                    Commands.argument("z", IntegerArgumentType.integer()).executes(ctx -> {
                        ServerPlayer player = ctx.getSource().getPlayerOrException();
                        BlockPos pos = new BlockPos(IntegerArgumentType.getInteger(ctx, "x"),
                                IntegerArgumentType.getInteger(ctx, "y"), IntegerArgumentType.getInteger(ctx, "z"));
                        BlockEntity main = owned(player, pos);
                        String message = main == null ? "Підійдіть до цілісної Clibano своєї команди; спочатку призначте власника через ПКМ по рамці."
                                : action.equals("cancel") ? ClibanoAccess.cancelProgress(player, main)
                                : action.equals("quarantine-residues") ? ClibanoAccess.quarantineResidues(player, main) : ClibanoAccess.status(main);
                        ctx.getSource().sendSuccess(() -> Component.literal(message), false); return main == null ? 0 : 1;
                    }))));
            root.then(branch);
        }
        event.getDispatcher().register(root);
    }
}
