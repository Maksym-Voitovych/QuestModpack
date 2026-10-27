package ua.aia2.guard.mixin;

import net.minecraft.world.entity.Entity;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.context.UseOnContext;
import net.minecraft.world.level.Level;
import net.minecraft.world.InteractionResult;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;
import ua.aia2.guard.ProjectEPassiveAccess;

@Mixin(ItemStack.class)
abstract class ProjectEItemStackUseMixin {
    @Inject(method = "inventoryTick(Lnet/minecraft/world/level/Level;Lnet/minecraft/world/entity/Entity;IZ)V", at = @At("HEAD"), cancellable = true, require = 1)
    private void aia2$wearerTick(Level level, Entity entity, int slot, boolean selected, CallbackInfo callback) {
        ItemStack stack = (ItemStack)(Object)this;
        if (!level.isClientSide() && ProjectEPassiveAccess.isProjectE(stack)
                && !ProjectEPassiveAccess.mayUseEntity(entity, stack)) callback.cancel();
    }
    @Inject(method = {"useOn(Lnet/minecraft/world/item/context/UseOnContext;)Lnet/minecraft/world/InteractionResult;",
            "onItemUseFirst(Lnet/minecraft/world/item/context/UseOnContext;)Lnet/minecraft/world/InteractionResult;"},
            at = @At("HEAD"), cancellable = true, require = 1)
    private void aia2$worldUse(UseOnContext context, CallbackInfoReturnable<InteractionResult> callback) {
        ItemStack stack = (ItemStack)(Object)this;
        if (!context.getLevel().isClientSide() && ProjectEPassiveAccess.isProjectE(stack)
                && !ProjectEPassiveAccess.mayUse(context.getPlayer(), stack)) callback.setReturnValue(InteractionResult.FAIL);
    }
}
