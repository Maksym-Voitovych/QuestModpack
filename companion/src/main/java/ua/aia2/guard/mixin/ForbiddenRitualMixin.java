package ua.aia2.guard.mixin;

import java.util.Optional;
import java.util.function.Function;
import net.minecraft.core.HolderLookup;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.item.ItemStack;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Pseudo;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Coerce;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.Redirect;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;
import ua.aia2.guard.ForbiddenPaidState;
import ua.aia2.guard.ForbiddenRitualAccess;

@Pseudo
@Mixin(targets = "com.stal111.forbidden_arcanus.common.block.entity.forge.ritual.RitualManager", remap = false)
public abstract class ForbiddenRitualMixin {
    @Redirect(method = "startRitual(Lnet/minecraft/server/level/ServerPlayer;Lcom/stal111/forbidden_arcanus/common/block/entity/forge/essence/EssencesStorage;)Z",
            at = @At(value = "INVOKE", target = "Ljava/util/Optional;map(Ljava/util/function/Function;)Ljava/util/Optional;"), remap = false, require = 1)
    private Optional<?> aia2$start(Optional<?> selected, Function<Object, Object> mapper,
                                  ServerPlayer player, @Coerce Object storage) {
        return ForbiddenRitualAccess.start(this, player, storage, selected, mapper);
    }
    // Re-entry is scoped in a real Java try/finally, including native exceptions and nested calls.
    @Inject(method = "tick()Ljava/util/Optional;", at = @At("HEAD"), cancellable = true, remap = false, require = 1)
    private void aia2$tick(CallbackInfoReturnable<Optional<ItemStack>> callback) {
        if (!ForbiddenRitualAccess.inTick(this)) callback.setReturnValue(ForbiddenRitualAccess.tick(this));
    }
    @Inject(method = "finishRitual(Lcom/stal111/forbidden_arcanus/common/block/entity/forge/ritual/ActiveRitualData;)Lnet/minecraft/world/item/ItemStack;",
            at = @At("HEAD"), cancellable = true, remap = false, require = 1)
    private void aia2$finish(@Coerce Object active, CallbackInfoReturnable<ItemStack> callback) {
        if (!ForbiddenRitualAccess.mayCommit(this)) callback.setReturnValue(ItemStack.EMPTY);
    }
    @Inject(method = "failRitual()Lnet/minecraft/world/item/ItemStack;", at = @At("HEAD"), cancellable = true, remap = false, require = 1)
    private void aia2$fail(CallbackInfoReturnable<ItemStack> callback) {
        if (!ForbiddenRitualAccess.mayCommit(this)) callback.setReturnValue(ItemStack.EMPTY);
    }
    @Inject(method = "load(Lnet/minecraft/nbt/CompoundTag;Lnet/minecraft/core/HolderLookup$Provider;)V",
            at = @At("HEAD"), remap = false, require = 1)
    private void aia2$load(CompoundTag tag, HolderLookup.Provider provider, CallbackInfo callback) {
        ForbiddenPaidState.load(this, tag);
    }
    @Inject(method = "save(Lnet/minecraft/nbt/CompoundTag;Lnet/minecraft/core/HolderLookup$Provider;)Lnet/minecraft/nbt/CompoundTag;",
            at = @At("HEAD"), remap = false, require = 1)
    private void aia2$beforeSave(CompoundTag tag, HolderLookup.Provider provider, CallbackInfoReturnable<CompoundTag> callback) {
        ForbiddenRitualAccess.beforeSave(this);
    }
    @Inject(method = "save(Lnet/minecraft/nbt/CompoundTag;Lnet/minecraft/core/HolderLookup$Provider;)Lnet/minecraft/nbt/CompoundTag;",
            at = @At("RETURN"), remap = false, require = 1)
    private void aia2$afterSave(CompoundTag tag, HolderLookup.Provider provider, CallbackInfoReturnable<CompoundTag> callback) {
        ForbiddenRitualAccess.afterSave(this, callback.getReturnValue());
    }
}
