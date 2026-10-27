package ua.aia2.guard.mixin;

import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.block.entity.BlockEntity;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Pseudo;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Coerce;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;
import ua.aia2.guard.EvilCraftAccess;

@Pseudo
@Mixin(targets = "org.cyclops.evilcraft.blockentity.tickaction.spiritreanimator.ReanimateTickAction", remap = false)
abstract class EvilCraftReanimatorMixin {
    @Inject(method = "onTick(Lorg/cyclops/evilcraft/blockentity/BlockEntitySpiritReanimator;Lnet/minecraft/world/item/ItemStack;II)V",
            at = @At("HEAD"), cancellable = true, remap = false, require = 1)
    private void aia2$guardReanimation(@Coerce Object receiver, ItemStack input, int slot, int tick, CallbackInfo callback) {
        if (!(receiver instanceof BlockEntity owner) || !EvilCraftAccess.mayReanimate(owner)) callback.cancel();
    }
}
