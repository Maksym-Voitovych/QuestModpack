package ua.aia2.guard.mixin;

import net.minecraft.world.entity.player.Player;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;
import ua.aia2.guard.ProjectECurioAttributes;

@Mixin(Player.class)
abstract class ProjectECurioReconcileMixin {
    @Inject(method = "tick()V", at = @At("TAIL"), require = 1)
    private void aia2$currentCurioPolicy(CallbackInfo callback) {
        ProjectECurioAttributes.reconcile((Player)(Object)this);
    }
}
