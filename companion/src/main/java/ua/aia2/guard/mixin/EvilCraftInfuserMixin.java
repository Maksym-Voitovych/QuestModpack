package ua.aia2.guard.mixin;

import java.util.Optional;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.crafting.Recipe;
import net.minecraft.world.level.block.entity.BlockEntity;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Pseudo;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;
import ua.aia2.guard.EvilCraftAccess;

@Pseudo
@Mixin(targets = "org.cyclops.evilcraft.blockentity.BlockEntityBloodInfuser", remap = false)
public abstract class EvilCraftInfuserMixin {
    @Inject(method = "getRecipe(Lnet/minecraft/world/item/ItemStack;)Ljava/util/Optional;",
            at = @At("RETURN"), cancellable = true, remap = false, require = 1)
    private void aia2$guardInfusion(ItemStack input, CallbackInfoReturnable<Optional<?>> callback) {
        Optional<?> selected = callback.getReturnValue();
        if (selected == null || selected.isEmpty()) return;
        if (!(selected.get() instanceof Recipe<?> recipe) || !EvilCraftAccess.mayInfuse((BlockEntity)(Object)this, recipe))
            callback.setReturnValue(Optional.empty());
    }
}
