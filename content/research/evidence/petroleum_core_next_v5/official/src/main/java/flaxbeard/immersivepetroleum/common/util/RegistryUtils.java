package flaxbeard.immersivepetroleum.common.util;

import flaxbeard.immersivepetroleum.ImmersivePetroleum;
import net.minecraft.core.Holder;
import net.minecraft.core.Registry;
import net.minecraft.core.particles.ParticleType;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.ResourceKey;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.tags.TagKey;
import net.minecraft.world.effect.MobEffect;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.inventory.MenuType;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.crafting.RecipeSerializer;
import net.minecraft.world.item.crafting.RecipeType;
import net.minecraft.world.level.biome.Biome;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.entity.BlockEntityType;
import net.minecraft.world.level.material.Fluid;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.fml.common.EventBusSubscriber.Bus;
import net.neoforged.neoforge.event.server.ServerStartingEvent;

import javax.annotation.Nonnull;
import javax.annotation.Nullable;
import java.util.List;
import java.util.Optional;

@EventBusSubscriber(modid = ImmersivePetroleum.MODID, bus = Bus.GAME)
public class RegistryUtils{
	private static Registry<Biome> BIOME_REGISTRY;
	
	@SubscribeEvent
	public static void serverStart(ServerStartingEvent event){
		BIOME_REGISTRY = event.getServer().registryAccess().registryOrThrow(Registries.BIOME);
	}
	
	@Nonnull
	public static ResourceLocation getRegistryNameOf(Item item){
		return BuiltInRegistries.ITEM.getKey(item);
	}
	
	@Nonnull
	public static ResourceLocation getRegistryNameOf(Block block){
		return BuiltInRegistries.BLOCK.getKey(block);
	}
	
	@Nonnull
	public static ResourceLocation getRegistryNameOf(Fluid fluid){
		return BuiltInRegistries.FLUID.getKey(fluid);
	}
	
	@Nullable
	public static Fluid getFluidFromRegistryName(ResourceLocation rl){
		ResourceKey<Fluid> resourceKey = ResourceKey.create(Registries.FLUID, rl);
		
		Holder<Fluid> holder = BuiltInRegistries.FLUID.getHolder(resourceKey).orElse(null);
		return holder != null ? holder.value() : null;
	}
	
	public static Optional<List<Holder<Biome>>> listBiomesInTag(TagKey<Biome> tag){
		return BIOME_REGISTRY.getTag(tag).map(holders -> holders.stream().toList());
	}
	
	@Nullable
	public static ResourceLocation getRegistryNameOf(SoundEvent soundEvent){
		return BuiltInRegistries.SOUND_EVENT.getKey(soundEvent);
	}
	
	@Nullable
	public static ResourceLocation getRegistryNameOf(MobEffect mobEffect){
		return BuiltInRegistries.MOB_EFFECT.getKey(mobEffect);
	}
	
	@Nonnull
	public static ResourceLocation getRegistryNameOf(EntityType<?> entityType){
		return BuiltInRegistries.ENTITY_TYPE.getKey(entityType);
	}
	
	@Nullable
	public static ResourceLocation getRegistryNameOf(BlockEntityType<?> blockEntityType){
		return BuiltInRegistries.BLOCK_ENTITY_TYPE.getKey(blockEntityType);
	}
	
	@Nullable
	public static ResourceLocation getRegistryNameOf(ParticleType<?> particleType){
		return BuiltInRegistries.PARTICLE_TYPE.getKey(particleType);
	}
	
	@Nullable
	public static ResourceLocation getRegistryNameOf(RecipeType<?> recipeType){
		return BuiltInRegistries.RECIPE_TYPE.getKey(recipeType);
	}
	
	@Nullable
	public static ResourceLocation getRegistryNameOf(RecipeSerializer<?> recipeSerializer){
		return BuiltInRegistries.RECIPE_SERIALIZER.getKey(recipeSerializer);
	}
	
	@Nullable
	public static ResourceLocation getRegistryNameOf(MenuType<?> menuType){
		return BuiltInRegistries.MENU.getKey(menuType);
	}
	
	private RegistryUtils(){
	}
}
