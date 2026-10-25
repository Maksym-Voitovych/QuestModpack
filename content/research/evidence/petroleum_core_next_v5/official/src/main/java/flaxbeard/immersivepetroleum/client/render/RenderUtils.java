package flaxbeard.immersivepetroleum.client.render;

import com.mojang.blaze3d.vertex.ByteBufferBuilder;
import com.mojang.blaze3d.vertex.VertexConsumer;
import net.minecraft.client.gui.GuiGraphics;
import net.minecraft.client.renderer.MultiBufferSource;
import org.joml.Matrix4f;

public class RenderUtils{
	static final int BYTE_BUFFER_SIZE = 0x100000;
	static final ByteBufferBuilder BUFFER = new ByteBufferBuilder(BYTE_BUFFER_SIZE);
	public static MultiBufferSource.BufferSource immediate(){
		// This should probably be done individually
		// Like I have done for the Projector
		return MultiBufferSource.immediate(BUFFER);
	}
	
	public static void drawColouredRect(GuiGraphics graphics, int x, int y, int w, int h){
		Matrix4f mat = graphics.pose().last().pose();
		VertexConsumer buffer = graphics.bufferSource().getBuffer(IPRenderTypes.TRANSLUCENT_POSITION_COLOR);
		int color = 0xAF_000000;
		buffer.addVertex(mat, x, y + h, 0).setColor(color);
		buffer.addVertex(mat, x + w, y + h, 0).setColor(color);
		buffer.addVertex(mat, x + w, y, 0).setColor(color);
		buffer.addVertex(mat, x, y, 0).setColor(color);
	}
}
