package ua.aia2.guard.mixin;

import net.minecraft.world.level.block.entity.BlockEntity;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Pseudo;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Coerce;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;
import ua.aia2.guard.AE2AssemblerAccess;

/** AE2 19.2.18 grid ticking executes outside the ordinary BlockEntityTicker. */
@Pseudo
@Mixin(targets = "appeng.blockentity.crafting.MolecularAssemblerBlockEntity", remap = false)
abstract class AE2MolecularAssemblerMixin {
    @Inject(method = "tickingRequest(Lappeng/api/networking/IGridNode;I)Lappeng/api/networking/ticking/TickRateModulation;",
            at = @At("HEAD"), cancellable = true, remap = false, require = 1)
    private void aia2$guardGridCraft(@Coerce Object node, int ticksSinceLastCall,
                                    CallbackInfoReturnable<Object> callback) {
        Object denied = AE2AssemblerAccess.deniedModulation((BlockEntity) (Object) this);
        if (denied != null) callback.setReturnValue(denied);
    }
}
