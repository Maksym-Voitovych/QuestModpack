package ua.aia2.guard.mixin;

import java.util.Optional;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.entity.BlockEntity;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Pseudo;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Coerce;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;
import ua.aia2.guard.ForbiddenRitualAccess;

@Pseudo
@Mixin(targets = "com.stal111.forbidden_arcanus.common.block.entity.forge.HephaestusForgeBlockEntity", remap = false)
public abstract class ForbiddenForgeInputMixin {
    @Inject(method = "getInput(Lnet/minecraft/world/level/Level;Lnet/minecraft/world/item/ItemStack;Lcom/stal111/forbidden_arcanus/common/block/entity/forge/essence/EssenceType;)Ljava/util/Optional;",
            at = @At("HEAD"), cancellable = true, remap = false, require = 1)
    private void aia2$input(Level level, ItemStack stack, @Coerce Object essenceType, CallbackInfoReturnable<Optional<?>> callback) {
        if (!ForbiddenRitualAccess.mayConsumeEssence((BlockEntity)(Object)this, stack)) callback.setReturnValue(Optional.empty());
    }
}
