package ua.aia2.guard.mixin;

import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.item.crafting.RecipeHolder;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.state.BlockState;
import net.neoforged.neoforge.items.IItemHandler;
import net.neoforged.neoforge.items.ItemStackHandler;
import org.spongepowered.asm.mixin.Final;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Pseudo;
import org.spongepowered.asm.mixin.Shadow;
import org.spongepowered.asm.mixin.Unique;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Coerce;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;
import ua.aia2.guard.Aia2MachineGuard;
import ua.aia2.guard.RootsAltarAccess;
import ua.aia2.guard.RootsRitualProof;

/** Roots 1.5.10 consumes a temporary container before clearing the real altar. */
@Pseudo
@Mixin(targets = "elucent.rootsclassic.block.altar.AltarBlockEntity", remap = false)
abstract class RootsAltarMixin implements RootsAltarAccess {
    @Shadow @Final public ItemStackHandler inventory;
    @Shadow(remap = false) public abstract RecipeHolder<?> getCurrentRitual();
    @Shadow(remap = false) public abstract void setCurrentRitual(RecipeHolder<?> holder);
    @Shadow(remap = false) public abstract int getProgress();
    @Shadow(remap = false) public abstract void setProgress(int progress);
    @Unique private RootsRitualProof.Attempt aia2$attempt;

    @Override public IItemHandler aia2$getInventory() { return inventory; }
    @Override public RootsRitualProof.Attempt aia2$getAttempt() { return aia2$attempt; }
    @Override public void aia2$setAttempt(RootsRitualProof.Attempt attempt) { aia2$attempt = attempt; }

    @Inject(method = "serverTick(Lnet/minecraft/world/level/Level;Lnet/minecraft/core/BlockPos;Lnet/minecraft/world/level/block/state/BlockState;Lelucent/rootsclassic/block/altar/AltarBlockEntity;)V",
            at = @At("HEAD"), cancellable = true, remap = false, require = 1)
    private static void aia2$beginRitualTick(Level level, BlockPos pos, BlockState state,
                                           @Coerce Object tile, CallbackInfo callback) {
        RootsAltarAccess access = (RootsAltarAccess) tile;
        access.aia2$setAttempt(null); // Discard state left by an exceptional native effect.
        if (!(level instanceof ServerLevel)) return;
        RecipeHolder<?> holder = access.getCurrentRitual();
        if (holder == null || access.getProgress() <= 0) return;
        BlockEntity altar = (BlockEntity) tile;
        if (!Aia2MachineGuard.mayProcessRecipe(altar, holder.value())) {
            access.setProgress(0);
            access.setCurrentRitual(null);
            callback.cancel(); // Inputs remain; native activation already spent incense.
            return;
        }
        if (access.getProgress() == 1) {
            access.aia2$setAttempt(RootsRitualProof.begin(altar, holder.value(), access.aia2$getInventory()));
        }
    }

    @Inject(method = "serverTick(Lnet/minecraft/world/level/Level;Lnet/minecraft/core/BlockPos;Lnet/minecraft/world/level/block/state/BlockState;Lelucent/rootsclassic/block/altar/AltarBlockEntity;)V",
            at = @At(value = "INVOKE", target = "Lelucent/rootsclassic/block/altar/AltarBlockEntity;emptyAltar()V", shift = At.Shift.AFTER),
            remap = false, require = 1)
    private static void aia2$recordConsumedRitual(Level level, BlockPos pos, BlockState state,
                                                @Coerce Object tile, CallbackInfo callback) {
        RootsAltarAccess access = (RootsAltarAccess) tile;
        RootsRitualProof.Attempt attempt = access.aia2$getAttempt();
        access.aia2$setAttempt(null);
        RootsRitualProof.finish((BlockEntity) tile, access.aia2$getInventory(), attempt);
    }
}
