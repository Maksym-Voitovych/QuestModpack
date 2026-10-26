package ua.aia2.guard.mixin;

import java.util.Optional;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.item.crafting.Recipe;
import net.minecraft.world.item.crafting.RecipeHolder;
import net.minecraft.world.item.crafting.RecipeInput;
import net.minecraft.world.item.crafting.RecipeManager;
import net.minecraft.world.item.crafting.RecipeType;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.entity.BlockEntity;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Pseudo;
import org.spongepowered.asm.mixin.Shadow;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.Redirect;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;
import ua.aia2.guard.Aia2MachineGuard;
import ua.aia2.guard.EnderTaskAccess;

@Pseudo
@Mixin(targets="com.enderio.enderio.content.machines.tank.FluidTankBlockEntity",remap=false)
abstract class EnderTankMixin {
    @Shadow(remap=false) private Optional<RecipeHolder<?>> currentRecipe;

    @Inject(method="tryTankRecipe()V",at=@At("HEAD"),cancellable=true,remap=false,require=1)
    private void aia2$guardCachedTank(CallbackInfo callback) {
        if (currentRecipe.isEmpty()) return;
        var owner=(BlockEntity)(Object)this;
        if (!(owner.getLevel() instanceof ServerLevel level)) return;
        var current=EnderTaskAccess.resolve(currentRecipe.get(),level);
        if (current==null || !Aia2MachineGuard.mayProcessRecipe(owner,current.value())
                || !Aia2MachineGuard.mayProduce(owner,EnderTaskAccess.template(current.value(),level))) callback.cancel();
        else currentRecipe=Optional.of(current);
    }

    @Redirect(method={"onInventoryContentsChanged(I)V","onTankContentsChanged()V"},at=@At(value="INVOKE",target="Lnet/minecraft/world/item/crafting/RecipeManager;getRecipeFor(Lnet/minecraft/world/item/crafting/RecipeType;Lnet/minecraft/world/item/crafting/RecipeInput;Lnet/minecraft/world/level/Level;)Ljava/util/Optional;"),remap=false,require=1)
    private <I extends RecipeInput,T extends Recipe<I>> Optional<RecipeHolder<T>> aia2$ownLookup(
            RecipeManager manager,RecipeType<T> type,I input,Level world) {
        return EnderTaskAccess.lookup((BlockEntity)(Object)this,manager,type,input,world);
    }
}
