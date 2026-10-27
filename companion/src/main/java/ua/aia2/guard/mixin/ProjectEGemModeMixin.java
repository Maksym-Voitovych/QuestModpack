package ua.aia2.guard.mixin;

import net.minecraft.world.InteractionHand;
import net.neoforged.neoforge.network.handling.IPayloadContext;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Pseudo;
import org.spongepowered.asm.mixin.Final;
import org.spongepowered.asm.mixin.Shadow;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;
import ua.aia2.guard.ProjectEPassiveAccess;

@Pseudo
@Mixin(targets = "moze_intel.projecte.network.packets.to_server.UpdateGemModePKT", remap = false)
abstract class ProjectEGemModeMixin {
    @Shadow(remap = false) @Final private InteractionHand hand;
    @Inject(method = "handle(Lnet/neoforged/neoforge/network/handling/IPayloadContext;)V", at = @At("HEAD"), cancellable = true, remap = false, require = 1)
    private void aia2$modeMutation(IPayloadContext context, CallbackInfo callback) {
        var player = context.player();
        if (!ProjectEPassiveAccess.mayUse(player, player.getItemInHand(hand))) callback.cancel();
    }
}
