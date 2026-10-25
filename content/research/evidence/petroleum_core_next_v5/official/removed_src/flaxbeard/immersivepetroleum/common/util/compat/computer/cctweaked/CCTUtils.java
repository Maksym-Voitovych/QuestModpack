package flaxbeard.immersivepetroleum.common.util.compat.computer.cctweaked;

import flaxbeard.immersivepetroleum.common.util.RegistryUtils;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.item.ItemStack;
import net.neoforged.neoforge.fluids.FluidStack;

import java.util.HashMap;
import java.util.Map;

public class CCTUtils{
	public static Map<String, Object> itemToMap(ItemStack stack){
		ResourceLocation rl = RegistryUtils.getRegistryNameOf(stack.getItem());
		String regName = rl == null ? null : rl.toString();
		
		Map<String, Object> outputMap = new HashMap<>();
		outputMap.put("name", regName);
		outputMap.put("count", stack.getCount());
		return outputMap;
	}
	
	public static Map<String, Object> fluidToMap(FluidStack stack){
		ResourceLocation rl = RegistryUtils.getRegistryNameOf(stack.getFluid());
		String regName = rl == null ? null : rl.toString();
		
		Map<String, Object> outputMap = new HashMap<>();
		outputMap.put("name", regName);
		outputMap.put("amount", stack.getAmount());
		return outputMap;
	}
}
