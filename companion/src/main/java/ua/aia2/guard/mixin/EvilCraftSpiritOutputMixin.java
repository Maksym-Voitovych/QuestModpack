package ua.aia2.guard.mixin;

import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.block.entity.BlockEntity;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Pseudo;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;
import ua.aia2.guard.EvilCraftAccess;

@Pseudo
@Mixin(targets = "org.cyclops.evilcraft.blockentity.BlockEntitySpiritFurnace", remap = false)
public abstract class EvilCraftSpiritOutputMixin {
    @Inject(method = "onItemDrop(Lnet/minecraft/world/item/ItemStack;)V", at = @At("HEAD"),
            cancellable = true, remap = false, require = 1)
    private void aia2$guardSpiritLoot(ItemStack output, CallbackInfo callback) {
        if (!EvilCraftAccess.mayOutput((BlockEntity)(Object)this, output)) callback.cancel();
    }
}
