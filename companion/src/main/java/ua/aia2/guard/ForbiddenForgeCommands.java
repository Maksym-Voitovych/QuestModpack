package ua.aia2.guard;

import com.mojang.brigadier.arguments.IntegerArgumentType;
import net.minecraft.commands.Commands;
import net.minecraft.network.chat.Component;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.event.RegisterCommandsEvent;

/** Explicit, nearby diagnostic/recovery. Cancellation is operator-only and keeps a bounded NBT backup. */
@EventBusSubscriber(modid = Aia2MachineGuard.MOD_ID)
public final class ForbiddenForgeCommands {
    private ForbiddenForgeCommands() {}
    @SubscribeEvent
    public static void register(RegisterCommandsEvent event) {
        var root = Commands.literal("aia2forge");
        for (String action : new String[] {"status", "cancel"}) {
            var branch = Commands.literal(action);
            if (action.equals("cancel")) branch.requires(source -> source.hasPermission(2));
            branch.then(Commands.argument("x", IntegerArgumentType.integer()).then(
                    Commands.argument("y", IntegerArgumentType.integer()).then(
                    Commands.argument("z", IntegerArgumentType.integer()).executes(ctx -> {
                        var player = ctx.getSource().getPlayerOrException();
                        int x = IntegerArgumentType.getInteger(ctx, "x"), y = IntegerArgumentType.getInteger(ctx, "y"), z = IntegerArgumentType.getInteger(ctx, "z");
                        String result = action.equals("cancel") ? ForbiddenRitualAccess.cancel(player, x, y, z) : ForbiddenRitualAccess.status(player, x, y, z);
                        ctx.getSource().sendSuccess(() -> Component.literal(result), false); return 1;
                    }))));
            root.then(branch);
        }
        event.getDispatcher().register(root);
    }
}
