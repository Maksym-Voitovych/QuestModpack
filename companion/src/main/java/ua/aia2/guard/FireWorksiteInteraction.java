package ua.aia2.guard;

import net.minecraft.core.Direction;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.item.Items;
import net.neoforged.bus.api.EventPriority;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.common.util.FakePlayer;
import net.neoforged.neoforge.event.entity.player.PlayerInteractEvent;

@EventBusSubscriber(modid = Aia2MachineGuard.MOD_ID)
public final class FireWorksiteInteraction {
    private FireWorksiteInteraction() {}
    @SubscribeEvent(priority = EventPriority.LOWEST)
    public static void claim(PlayerInteractEvent.RightClickBlock event) {
        if (!(event.getEntity() instanceof ServerPlayer player) || !(event.getLevel() instanceof ServerLevel level)
                || !player.isShiftKeyDown() || event.getFace() != Direction.UP
                || !event.getItemStack().is(Items.FLINT_AND_STEEL)
                || !FireWorksiteAccess.isWorksiteBase(level, event.getPos())) return;
        event.setCanceled(true);
        event.setCancellationResult(InteractionResult.SUCCESS);
        if (player instanceof FakePlayer || !player.getAbilities().mayBuild
                || !level.mayInteract(player, event.getPos())
                || !player.mayUseItemAt(event.getPos(), Direction.UP, event.getItemStack())) return;
        player.displayClientMessage(Component.literal(FireWorksiteAccess.claim(player, event.getPos())), false);
    }
}
