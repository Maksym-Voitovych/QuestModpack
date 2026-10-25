package ua.aia2.guard.mixin;

import net.minecraft.world.item.ItemStack;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Pseudo;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;
import ua.aia2.guard.Aia2MachineGuard;

/** Runs before both simulated and committed MI UU-matter transactions. */
@Pseudo
@Mixin(targets="aztech.modern_industrialization.machines.blockentities.ReplicatorMachineBlockEntity",remap=false)
abstract class ModernReplicatorMixin {
    @Inject(method="canReplicate(Lnet/minecraft/world/item/ItemStack;)Z",at=@At("HEAD"),
            cancellable=true,remap=false,require=1)
    private static void aia2$guardCopiedOutput(ItemStack output,CallbackInfoReturnable<Boolean> callback) {
        if (!Aia2MachineGuard.mayReplicateOutputInCurrentTick(output)) callback.setReturnValue(false);
    }
}
