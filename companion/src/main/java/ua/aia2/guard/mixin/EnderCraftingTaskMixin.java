package ua.aia2.guard.mixin;

import java.util.List;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.crafting.RecipeHolder;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Pseudo;
import org.spongepowered.asm.mixin.Shadow;
import org.spongepowered.asm.mixin.Unique;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;
import ua.aia2.guard.Aia2MachineGuard;
import ua.aia2.guard.EnderTaskAccess;
import ua.aia2.guard.ProductionMilestoneBridge;

@Pseudo
@Mixin(targets="com.enderio.enderio.foundation.task.CraftingMachineTask",remap=false)
abstract class EnderCraftingTaskMixin {
    @Shadow(remap=false) private RecipeHolder<?> recipe;
    @Shadow(remap=false) private List<?> outputs;
    @Shadow(remap=false) private boolean isComplete;
    @Unique private List<ItemStack> aia2$observed=List.of();

    @Inject(method="tick()V",at=@At("HEAD"),cancellable=true,remap=false,require=1)
    private void aia2$guardTask(CallbackInfo callback) {
        aia2$observed=List.of();
        if (isComplete || recipe==null) return;
        var current=EnderTaskAccess.resolve(recipe,Aia2MachineGuard.currentTickServerLevel());
        if (current==null || !Aia2MachineGuard.mayProcessRecipeInCurrentTick(current.value())) callback.cancel();
        else recipe=current;
    }

    @Inject(method="tick()V",at=@At(value="INVOKE",target="Lcom/enderio/enderio/foundation/MachineRecipe;matches(Lnet/minecraft/world/item/crafting/RecipeInput;Lnet/minecraft/world/level/Level;)Z"),
            cancellable=true,remap=false,require=1)
    private void aia2$guardDeterminedOutputs(CallbackInfo callback) {
        var items=EnderTaskAccess.copyItems(outputs);
        if (!EnderTaskAccess.mayOutput(Aia2MachineGuard.currentTickOwner(),items)) callback.cancel();
        else aia2$observed=items;
    }

    @Inject(method="tick()V",at=@At(value="INVOKE",target="Lcom/enderio/enderio/foundation/task/CraftingMachineTask;consumeInputs(Lcom/enderio/enderio/foundation/MachineRecipe;)V",shift=At.Shift.AFTER),remap=false,require=1)
    private void aia2$observeCompletion(CallbackInfo callback) {
        var owner=Aia2MachineGuard.currentTickOwner();
        if (owner!=null && recipe!=null) ProductionMilestoneBridge.finishedObservedMachine(owner,recipe.value(),aia2$observed);
        aia2$observed=List.of();
    }
}
