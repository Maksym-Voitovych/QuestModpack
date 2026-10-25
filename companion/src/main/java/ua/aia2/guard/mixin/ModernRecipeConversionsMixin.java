package ua.aia2.guard.mixin;

import net.minecraft.core.RegistryAccess;
import net.minecraft.world.item.crafting.RecipeHolder;
import net.minecraft.world.level.ItemLike;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Pseudo;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Coerce;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;
import ua.aia2.guard.ModernRecipeProxyAccess;

@Pseudo
@Mixin(targets="aztech.modern_industrialization.machines.recipe.RecipeConversions",remap=false)
abstract class ModernRecipeConversionsMixin {
    @Inject(method="ofSmelting(Lnet/minecraft/world/item/crafting/RecipeHolder;Laztech/modern_industrialization/machines/recipe/MachineRecipeType;Lnet/minecraft/core/RegistryAccess;)Lnet/minecraft/world/item/crafting/RecipeHolder;",
            at=@At("RETURN"),remap=false,require=1)
    private static void aia2$trackSmelting(RecipeHolder<?> source,@Coerce Object type,RegistryAccess registry,
                                         CallbackInfoReturnable<RecipeHolder<?>> callback) {
        ModernRecipeProxyAccess.registerConversion(source,callback.getReturnValue(),"smelting");
    }
    @Inject(method="ofStonecutting(Lnet/minecraft/world/item/crafting/RecipeHolder;Laztech/modern_industrialization/machines/recipe/MachineRecipeType;Lnet/minecraft/core/RegistryAccess;)Lnet/minecraft/world/item/crafting/RecipeHolder;",
            at=@At("RETURN"),remap=false,require=1)
    private static void aia2$trackCutting(RecipeHolder<?> source,@Coerce Object type,RegistryAccess registry,
                                        CallbackInfoReturnable<RecipeHolder<?>> callback) {
        ModernRecipeProxyAccess.registerConversion(source,callback.getReturnValue(),"stonecutting");
    }
    @Inject(method="ofCompostable(Lnet/minecraft/world/level/ItemLike;)Lnet/minecraft/world/item/crafting/RecipeHolder;",
            at=@At("RETURN"),remap=false,require=1)
    private static void aia2$trackCompost(ItemLike input,CallbackInfoReturnable<RecipeHolder<?>> callback) {
        ModernRecipeProxyAccess.registerCompost(input,callback.getReturnValue());
    }
}
