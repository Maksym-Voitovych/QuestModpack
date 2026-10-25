package flaxbeard.immersivepetroleum.common.util;

import blusunrize.immersiveengineering.api.Lib;
import flaxbeard.immersivepetroleum.ImmersivePetroleum;
import net.minecraft.client.resources.model.ModelResourceLocation;
import net.minecraft.resources.ResourceLocation;
import net.neoforged.neoforge.internal.versions.neoforge.NeoForgeVersion;

public class ResourceUtils{
	public static ResourceLocation ip(String path){
		return ResourceLocation.fromNamespaceAndPath(ImmersivePetroleum.MODID, path);
	}
	
	public static ModelResourceLocation ipModel(String modelPath){
		return ModelResourceLocation.standalone(ip(modelPath));
	}
	
	public static ResourceLocation ie(String path){
		return ResourceLocation.fromNamespaceAndPath(Lib.MODID, path);
	}
	
	public static ResourceLocation common(String path){
		return ResourceLocation.fromNamespaceAndPath("c", path);
	}
	
	public static ResourceLocation mc(String path){
		return ResourceLocation.fromNamespaceAndPath(ResourceLocation.DEFAULT_NAMESPACE, path);
	}
	
	public static ResourceLocation forge(String path){
		return ResourceLocation.fromNamespaceAndPath(NeoForgeVersion.MOD_ID, path);
	}
	
	public static ResourceLocation ct(String path){
		return ResourceLocation.fromNamespaceAndPath("crafttweaker", path);
	}
}
