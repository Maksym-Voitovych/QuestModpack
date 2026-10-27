package ua.aia2.guard.mixin;

import java.util.function.BiPredicate;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Pseudo;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Redirect;
import ua.aia2.guard.ProjectEPassiveAccess;

/** Keep the native cleanup pass running; only unavailable supplies stop satisfying its predicate. */
@Pseudo
@Mixin(targets = "moze_intel.projecte.utils.PlayerHelper", remap = false)
abstract class ProjectEHotbarPredicateMixin {
    @Redirect(method = {"checkHotbar(Lnet/minecraft/world/entity/player/Player;Ljava/util/function/BiPredicate;)Z",
            "checkHotbarCurios(Lnet/minecraft/world/entity/player/Player;Ljava/util/function/BiPredicate;)Z"},
            at = @At(value = "INVOKE", target = "Ljava/util/function/BiPredicate;test(Ljava/lang/Object;Ljava/lang/Object;)Z"), remap = false, require = 1)
    private static boolean aia2$usableSupply(BiPredicate<Player, ItemStack> predicate, Object player, Object stack) {
        return player instanceof Player actor && stack instanceof ItemStack item
                && ProjectEPassiveAccess.mayUse(actor, item) && predicate.test(actor, item);
    }
}
