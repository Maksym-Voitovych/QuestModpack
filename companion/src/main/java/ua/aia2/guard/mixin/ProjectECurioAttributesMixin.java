package ua.aia2.guard.mixin;

import com.google.common.collect.LinkedHashMultimap;
import com.google.common.collect.Multimap;
import net.minecraft.core.Holder;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.entity.ai.attributes.Attribute;
import net.minecraft.world.entity.ai.attributes.AttributeModifier;
import net.minecraft.world.item.ItemStack;
import org.spongepowered.asm.mixin.Final;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Pseudo;
import org.spongepowered.asm.mixin.Shadow;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Coerce;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;
import ua.aia2.guard.ProjectECurioAttributes;

@Pseudo
@Mixin(targets = "moze_intel.projecte.integration.curios.CurioItemCapability", remap = false)
abstract class ProjectECurioAttributesMixin {
    @Shadow @Final private ItemStack stack;
    @Inject(method = "getAttributeModifiers(Ltop/theillusivec4/curios/api/SlotContext;Lnet/minecraft/resources/ResourceLocation;)Lcom/google/common/collect/Multimap;",
            at = @At("HEAD"), cancellable = true, remap = false, require = 1)
    private void aia2$usableCurioAttributes(@Coerce Object context, ResourceLocation id,
            CallbackInfoReturnable<Multimap<Holder<Attribute>, AttributeModifier>> callback) {
        if (!ProjectECurioAttributes.mayExpose(context, stack)) callback.setReturnValue(LinkedHashMultimap.create());
    }
}
