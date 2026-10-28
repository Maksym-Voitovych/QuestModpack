package ua.aia2.guard.mixin;

import net.minecraft.core.BlockPos;
import java.util.List;
import net.minecraft.core.HolderLookup;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.world.item.crafting.RecipeHolder;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.state.BlockState;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Pseudo;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Coerce;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.Redirect;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;
import ua.aia2.guard.ClibanoAccess;

@Pseudo
@Mixin(targets = "com.stal111.forbidden_arcanus.common.block.entity.clibano.ClibanoMainBlockEntity", remap = false)
public abstract class ClibanoMachineMixin {
    @Inject(method = "serverTick(Lnet/minecraft/world/level/Level;Lnet/minecraft/core/BlockPos;Lnet/minecraft/world/level/block/state/BlockState;Lcom/stal111/forbidden_arcanus/common/block/entity/clibano/ClibanoMainBlockEntity;)V",
            at = @At("HEAD"), cancellable = true, remap = false, require = 1)
    private static void aia2$tick(Level level, BlockPos pos, BlockState state, @Coerce Object machine, CallbackInfo callback) {
        if (!ClibanoAccess.inTick((BlockEntity)machine)) {
            ClibanoAccess.tick(level, pos, state, (BlockEntity)machine); callback.cancel();
        }
    }
    @Redirect(method = "serverTick(Lnet/minecraft/world/level/Level;Lnet/minecraft/core/BlockPos;Lnet/minecraft/world/level/block/state/BlockState;Lcom/stal111/forbidden_arcanus/common/block/entity/clibano/ClibanoMainBlockEntity;)V",
            at = @At(value = "INVOKE", target = "Lcom/stal111/forbidden_arcanus/common/block/entity/clibano/logic/ClibanoSmeltLogic;tick(Z)V"), remap = false, require = 1)
    private static void aia2$burningOnly(@Coerce Object logic, boolean lit) { ClibanoAccess.cook(logic, lit); }
    @Redirect(method = "serverTick(Lnet/minecraft/world/level/Level;Lnet/minecraft/core/BlockPos;Lnet/minecraft/world/level/block/state/BlockState;Lcom/stal111/forbidden_arcanus/common/block/entity/clibano/ClibanoMainBlockEntity;)V",
            at = @At(value = "INVOKE", target = "Lcom/stal111/forbidden_arcanus/common/block/entity/clibano/logic/ClibanoSmeltLogic;updateRecipes(Ljava/util/List;)V"), remap = false, require = 1)
    private static void aia2$plannedRecipes(@Coerce Object logic, List<?> selected) { ClibanoAccess.updateRecipes(logic, selected); }
    @Inject(method = "canSmelt(Lnet/minecraft/world/item/crafting/RecipeHolder;Lcom/stal111/forbidden_arcanus/common/block/entity/clibano/ClibanoInputSlot;)Z",
            at = @At("HEAD"), cancellable = true, remap = false, require = 1)
    private void aia2$canSmelt(RecipeHolder<?> holder, @Coerce Object slot, CallbackInfoReturnable<Boolean> callback) {
        if (!ClibanoAccess.maySmelt((BlockEntity)(Object)this, holder, slot)) callback.setReturnValue(false);
    }
    @Inject(method = "finishRecipe(Lnet/minecraft/world/item/crafting/RecipeHolder;Lcom/stal111/forbidden_arcanus/common/block/entity/clibano/ClibanoInputSlot;)V",
            at = @At("HEAD"), cancellable = true, remap = false, require = 1)
    private void aia2$beginFinish(RecipeHolder<?> holder, @Coerce Object slot, CallbackInfo callback) {
        if (!ClibanoAccess.mayFinish((BlockEntity)(Object)this, holder, slot)) callback.cancel();
    }
    @Inject(method = "finishRecipe(Lnet/minecraft/world/item/crafting/RecipeHolder;Lcom/stal111/forbidden_arcanus/common/block/entity/clibano/ClibanoInputSlot;)V",
            at = @At("RETURN"), remap = false, require = 1)
    private void aia2$finished(RecipeHolder<?> holder, @Coerce Object slot, CallbackInfo callback) {
        ClibanoAccess.finished((BlockEntity)(Object)this, holder, slot);
    }
    @Inject(method = "loadAdditional(Lnet/minecraft/nbt/CompoundTag;Lnet/minecraft/core/HolderLookup$Provider;)V",
            at = @At("HEAD"), remap = false, require = 1)
    private void aia2$load(CompoundTag tag, HolderLookup.Provider provider, CallbackInfo callback) {
        ClibanoAccess.load((BlockEntity)(Object)this, tag);
    }
    @Inject(method = "loadAdditional(Lnet/minecraft/nbt/CompoundTag;Lnet/minecraft/core/HolderLookup$Provider;)V",
            at = @At("RETURN"), remap = false, require = 1)
    private void aia2$loaded(CompoundTag tag, HolderLookup.Provider provider, CallbackInfo callback) {
        ClibanoAccess.loaded((BlockEntity)(Object)this);
    }
    @Inject(method = "saveAdditional(Lnet/minecraft/nbt/CompoundTag;Lnet/minecraft/core/HolderLookup$Provider;)V",
            at = @At("RETURN"), remap = false, require = 1)
    private void aia2$save(CompoundTag tag, HolderLookup.Provider provider, CallbackInfo callback) {
        ClibanoAccess.save((BlockEntity)(Object)this, tag);
    }
}
