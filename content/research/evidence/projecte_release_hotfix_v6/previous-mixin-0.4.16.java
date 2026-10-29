package ua.aia2.guard.mixin;

import java.util.OptionalInt;
import java.util.function.Consumer;
import net.minecraft.network.RegistryFriendlyByteBuf;
import net.minecraft.world.MenuProvider;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Pseudo;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Redirect;
import ua.aia2.guard.ProjectEPassiveAccess;

@Pseudo
@Mixin(targets = "moze_intel.projecte.gameObjs.items.TransmutationTablet", remap = false)
abstract class ProjectETabletSourceMixin {
    @Redirect(method = {"openContainer(Lnet/minecraft/world/entity/player/Player;)V",
            "openContainer(Lnet/minecraft/world/entity/player/Player;Lnet/minecraft/world/InteractionHand;I)V"},
            at = @At(value = "INVOKE", target = "Lnet/minecraft/world/entity/player/Player;openMenu(Lnet/minecraft/world/MenuProvider;Ljava/util/function/Consumer;)Ljava/util/OptionalInt;"), remap = false, require = 1)
    private OptionalInt aia2$tabletOrigin(Player player, MenuProvider provider, Consumer<RegistryFriendlyByteBuf> writer) {
        return ProjectEPassiveAccess.openTablet((Item)(Object)this, player, provider, writer);
    }
}
