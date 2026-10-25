package dev.shadowsoffire.apothic_enchanting.mixin.client;

import java.util.function.Function;

import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Redirect;

import com.mojang.blaze3d.vertex.PoseStack;
import com.mojang.blaze3d.vertex.VertexConsumer;

import dev.shadowsoffire.apothic_enchanting.table.BookTexturedTable;
import net.minecraft.client.renderer.MultiBufferSource;
import net.minecraft.client.renderer.RenderType;
import net.minecraft.client.renderer.blockentity.EnchantTableRenderer;
import net.minecraft.client.renderer.texture.TextureAtlas;
import net.minecraft.client.resources.model.Material;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.level.block.entity.EnchantingTableBlockEntity;

@Mixin(value = EnchantTableRenderer.class, remap = false)
public class EnchantTableRendererMixin {

    /**
     * Swaps the floating book texture when the table block implements {@link BookTexturedTable}.
     * The substituted material uses the same blocks atlas, so custom book textures are stitched via
     * {@code assets/minecraft/atlases/blocks.json}.
     */
    @Redirect(
        method = "render(Lnet/minecraft/world/level/block/entity/EnchantingTableBlockEntity;FLcom/mojang/blaze3d/vertex/PoseStack;Lnet/minecraft/client/renderer/MultiBufferSource;II)V",
        at = @At(
            value = "INVOKE",
            target = "Lnet/minecraft/client/resources/model/Material;buffer(Lnet/minecraft/client/renderer/MultiBufferSource;Ljava/util/function/Function;)Lcom/mojang/blaze3d/vertex/VertexConsumer;"),
        require = 1)
    private VertexConsumer apoth_swapBookTexture(Material material, MultiBufferSource buffers, Function<ResourceLocation, RenderType> renderTypeGetter,
        EnchantingTableBlockEntity be, float partialTick, PoseStack poseStack, MultiBufferSource bufferSource, int packedLight, int packedOverlay) {
        if (be.getBlockState().getBlock() instanceof BookTexturedTable table) {
            material = new Material(TextureAtlas.LOCATION_BLOCKS, table.getBookTextureId().withPrefix("entity/"));
        }
        return material.buffer(buffers, renderTypeGetter);
    }

}
