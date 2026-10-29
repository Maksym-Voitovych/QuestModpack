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
    // PE1.1.0 opens the menu in use(); openContainer belongs to a later,
    // unreleased Curios refactor that retained the same version properties.
    @Redirect(method = "use(Lnet/minecraft/world/level/Level;Lnet/minecraft/world/entity/player/Player;Lnet/minecraft/world/InteractionHand;)Lnet/minecraft/world/InteractionResultHolder;",
            at = @At(value = "INVOKE", target = "Lnet/minecraft/world/entity/player/Player;openMenu(Lnet/minecraft/world/MenuProvider;Ljava/util/function/Consumer;)Ljava/util/OptionalInt;"), remap = false, require = 1)
    private OptionalInt aia2$tabletOrigin(Player player, MenuProvider provider, Consumer<RegistryFriendlyByteBuf> writer) {
        return ProjectEPassiveAccess.openTablet((Item)(Object)this, player, provider, writer);
    }
}
