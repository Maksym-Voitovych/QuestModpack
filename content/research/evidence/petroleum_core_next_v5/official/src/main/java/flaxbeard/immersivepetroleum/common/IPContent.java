package flaxbeard.immersivepetroleum.common;

import blusunrize.immersiveengineering.api.IETags;
import blusunrize.immersiveengineering.api.multiblocks.MultiblockHandler;
import blusunrize.immersiveengineering.api.multiblocks.blocks.MultiblockRegistration;
import blusunrize.immersiveengineering.api.tool.ChemthrowerHandler;
import blusunrize.immersiveengineering.api.tool.ChemthrowerHandler.ChemthrowerEffect_Potion;
import blusunrize.immersiveengineering.common.register.IEMultiblockLogic;
import blusunrize.immersiveengineering.common.register.IEPotions;
import flaxbeard.immersivepetroleum.ImmersivePetroleum;
import flaxbeard.immersivepetroleum.api.IPTags;
import flaxbeard.immersivepetroleum.api.crafting.FlarestackHandler;
import flaxbeard.immersivepetroleum.api.crafting.LubricantHandler;
import flaxbeard.immersivepetroleum.api.crafting.LubricatedHandler;
import flaxbeard.immersivepetroleum.api.crafting.LubricatedHandler.LubricantEffect;
import flaxbeard.immersivepetroleum.client.particle.FlareFire;
import flaxbeard.immersivepetroleum.client.particle.FluidSpill;
import flaxbeard.immersivepetroleum.client.particle.IPParticleTypes;
import flaxbeard.immersivepetroleum.common.blocks.IPBlockItemBase;
import flaxbeard.immersivepetroleum.common.blocks.metal.FlarestackBlock;
import flaxbeard.immersivepetroleum.common.blocks.metal.GasGeneratorBlock;
import flaxbeard.immersivepetroleum.common.blocks.metal.SeismicSurveyBlock;
import flaxbeard.immersivepetroleum.common.blocks.multiblocks.CokerUnitMultiblock;
import flaxbeard.immersivepetroleum.common.blocks.multiblocks.DerrickMultiblock;
import flaxbeard.immersivepetroleum.common.blocks.multiblocks.DistillationTowerMultiblock;
import flaxbeard.immersivepetroleum.common.blocks.multiblocks.HydroTreaterMultiblock;
import flaxbeard.immersivepetroleum.common.blocks.multiblocks.OilTankMultiblock;
import flaxbeard.immersivepetroleum.common.blocks.multiblocks.PumpjackMultiblock;
import flaxbeard.immersivepetroleum.common.blocks.multiblocks.logic.DerrickLogic;
import flaxbeard.immersivepetroleum.common.blocks.multiblocks.logic.OilTankLogic;
import flaxbeard.immersivepetroleum.common.blocks.multiblocks.logic.PumpjackLogic;
import flaxbeard.immersivepetroleum.common.blocks.multiblocks.logic.coker.CokerUnitLogic;
import flaxbeard.immersivepetroleum.common.blocks.multiblocks.logic.distillation_tower.DistillationTowerLogic;
import flaxbeard.immersivepetroleum.common.blocks.multiblocks.logic.hydro_treater.HydroTreaterLogic;
import flaxbeard.immersivepetroleum.common.blocks.stone.AsphaltBlock;
import flaxbeard.immersivepetroleum.common.blocks.stone.AsphaltSlab;
import flaxbeard.immersivepetroleum.common.blocks.stone.AsphaltStairs;
import flaxbeard.immersivepetroleum.common.blocks.stone.ParaffinWaxBlock;
import flaxbeard.immersivepetroleum.common.blocks.stone.PetcokeBlock;
import flaxbeard.immersivepetroleum.common.blocks.stone.WellBlock;
import flaxbeard.immersivepetroleum.common.blocks.stone.WellPipeBlock;
import flaxbeard.immersivepetroleum.common.blocks.wooden.AutoLubricatorBlock;
import flaxbeard.immersivepetroleum.common.crafting.Serializers;
import flaxbeard.immersivepetroleum.common.entity.IPEntityTypes;
import flaxbeard.immersivepetroleum.common.fluids.CrudeOilFluid;
import flaxbeard.immersivepetroleum.common.fluids.DieselFluid;
import flaxbeard.immersivepetroleum.common.fluids.IPFluid;
import flaxbeard.immersivepetroleum.common.fluids.IPFluid.IPFluidEntry;
import flaxbeard.immersivepetroleum.common.fluids.NapalmFluid.NapalmFluidBlock;
import flaxbeard.immersivepetroleum.common.items.DebugItem;
import flaxbeard.immersivepetroleum.common.items.GasolineBottleItem;
import flaxbeard.immersivepetroleum.common.items.IPItemBase;
import flaxbeard.immersivepetroleum.common.items.IPUpgradeItem;
import flaxbeard.immersivepetroleum.common.items.MolotovItem;
import flaxbeard.immersivepetroleum.common.items.MotorboatItem;
import flaxbeard.immersivepetroleum.common.items.OilCanItem;
import flaxbeard.immersivepetroleum.common.items.ProjectorItem;
import flaxbeard.immersivepetroleum.common.items.SurveyResultItem;
import flaxbeard.immersivepetroleum.common.lubehandlers.CrusherLubricationHandler;
import flaxbeard.immersivepetroleum.common.lubehandlers.ExcavatorLubricationHandler;
import flaxbeard.immersivepetroleum.common.lubehandlers.PumpjackLubricationHandler;
import flaxbeard.immersivepetroleum.common.sound.IPSounds;
import flaxbeard.immersivepetroleum.common.util.IPEffects;
import flaxbeard.immersivepetroleum.common.util.damageSources.IPDamageSources;
import flaxbeard.immersivepetroleum.common.world.WorldGenFeatures;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.crafting.RecipeType;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.SlabBlock;
import net.minecraft.world.level.block.StairBlock;
import net.neoforged.api.distmarker.Dist;
import net.neoforged.api.distmarker.OnlyIn;
import net.neoforged.bus.api.IEventBus;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.fml.common.EventBusSubscriber.Bus;
import net.neoforged.fml.event.lifecycle.FMLCommonSetupEvent;
import net.neoforged.neoforge.client.event.RegisterParticleProvidersEvent;
import net.neoforged.neoforge.registries.DeferredHolder;
import org.apache.logging.log4j.LogManager;
import org.apache.logging.log4j.Logger;

@EventBusSubscriber(modid = ImmersivePetroleum.MODID, bus = Bus.MOD, value = Dist.CLIENT)
public class IPContent{
	public static final Logger log = LogManager.getLogger(ImmersivePetroleum.MODID + "/Content");
	
	public static class Multiblock{
		public static final MultiblockRegistration<DistillationTowerLogic.State> DISTILLATIONTOWER = IPRegisters.registerMetalMultiblock(
				"distillation_tower", new DistillationTowerLogic(), () -> DistillationTowerMultiblock.INSTANCE,
				builder -> builder.redstone(st -> st.rsState, DistillationTowerLogic.REDSTONE_IN).gui(IPMenuTypes.DISTILLATION_TOWER)
		);
		public static final MultiblockRegistration<PumpjackLogic.State> PUMPJACK = IPRegisters.registerMetalMultiblock(
				"pumpjack", new PumpjackLogic(), () -> PumpjackMultiblock.INSTANCE,
				builder -> builder.redstone(st -> st.rsState, PumpjackLogic.REDSTONE_IN)
		);
		public static final MultiblockRegistration<CokerUnitLogic.State> COKERUNIT = IPRegisters.registerMetalMultiblock(
				"coker_unit", new CokerUnitLogic(), () -> CokerUnitMultiblock.INSTANCE,
				builder -> builder.redstone(st -> st.rsState, CokerUnitLogic.Redstone_IN).gui(IPMenuTypes.COKER).withComparator()
		);
		public static final MultiblockRegistration<HydroTreaterLogic.State> HYDROTREATER = IPRegisters.registerMetalMultiblock(
				"hydrotreater", new HydroTreaterLogic(), () -> HydroTreaterMultiblock.INSTANCE,
				builder -> builder.redstone(st -> st.rsState, HydroTreaterLogic.Redstone_IN).gui(IPMenuTypes.HYDROTREATER)
		);
		public static final MultiblockRegistration<DerrickLogic.State> DERRICK = IPRegisters.registerMetalMultiblock(
				"derrick", new DerrickLogic(), () -> DerrickMultiblock.INSTANCE,
				builder -> builder.redstone(st -> st.rsState, DerrickLogic.REDSTONE_IN).gui(IPMenuTypes.DERRICK)
		);
		public static final MultiblockRegistration<OilTankLogic.State> OILTANK = IPRegisters.registerMetalMultiblock(
				"oiltank", new OilTankLogic(), () -> OilTankMultiblock.INSTANCE,
				builder -> builder.redstone(st -> st.rsState, OilTankLogic.Redstone_IN).withComparator()
		);
		
		//@formatter:off
		private static void forceClassLoad(){}
		//@formatter:on
	}
	
	public static class Fluids{
		public static final IPFluidEntry CRUDEOIL = IPFluid.makeFluid("crudeoil", 1000, 2250, 0.007, CrudeOilFluid::new, CrudeOilFluid.CrudeOilBlock::new);
		public static final IPFluidEntry DIESEL_SULFUR = IPFluid.makeFluid("diesel_sulfur", 789, 1750, DieselFluid::new);
		public static final IPFluidEntry DIESEL = IPFluid.makeFluid("diesel", 789, 1750, DieselFluid::new);
		public static final IPFluidEntry LUBRICANT = IPFluid.makeFluid("lubricant", 925, 1000);
		public static final IPFluidEntry GASOLINE = IPFluid.makeFluid("gasoline", 789, 1200);
		
		public static final IPFluidEntry NAPHTHA = IPFluid.makeFluid("naphtha", 750, 750);
		public static final IPFluidEntry BENZOL = IPFluid.makeFluid("benzol", 876, 700);
		public static final IPFluidEntry PETROLEUM_GAS = IPFluid.makeFluid("petroleum_gas", 2, 1);
		public static final IPFluidEntry KEROSENE = IPFluid.makeFluid("kerosene", 810, 900);
		
		public static final IPFluidEntry NAPALM = IPFluid.makeFluid("napalm", 1000, 4000, 0.0105, NapalmFluidBlock::new);
		
		//@formatter:off
		private static void forceClassLoad(){}
		//@formatter:on
	}
	
	public static class Blocks{
		public static final DeferredHolder<Block, SeismicSurveyBlock> SEISMIC_SURVEY = IPRegisters.registerIPBlock("seismic_survey", SeismicSurveyBlock::new);
		
		public static final DeferredHolder<Block, GasGeneratorBlock> GAS_GENERATOR = IPRegisters.registerIPBlock("gas_generator", GasGeneratorBlock::new);
		public static final DeferredHolder<Block, AutoLubricatorBlock> AUTO_LUBRICATOR = IPRegisters.registerIPBlock("auto_lubricator", AutoLubricatorBlock::new);
		public static final DeferredHolder<Block, FlarestackBlock> FLARESTACK = IPRegisters.registerIPBlock("flarestack", FlarestackBlock::new);
		
		public static final DeferredHolder<Block, AsphaltBlock> ASPHALT = IPRegisters.registerIPBlock("asphalt", AsphaltBlock::new);
		public static final DeferredHolder<Block, SlabBlock> ASPHALT_SLAB = IPRegisters.registerBlock("asphalt_slab", () -> new AsphaltSlab(ASPHALT.get()));
		public static final DeferredHolder<Block, StairBlock> ASPHALT_STAIR = IPRegisters.registerBlock("asphalt_stair", () -> new AsphaltStairs(ASPHALT.get()));
		public static final DeferredHolder<Block, PetcokeBlock> PETCOKE = IPRegisters.registerIPBlock("petcoke_block", PetcokeBlock::new);
		public static final DeferredHolder<Block, WellBlock> WELL = IPRegisters.registerBlock("well", WellBlock::new);
		public static final DeferredHolder<Block, WellPipeBlock> WELL_PIPE = IPRegisters.registerBlock("well_pipe", WellPipeBlock::new);
		public static final DeferredHolder<Block, ParaffinWaxBlock> PARAFFIN_WAX = IPRegisters.registerIPBlock("paraffin_wax_block", ParaffinWaxBlock::new);
		
		private static void forceClassLoad(){
			registerItemBlock(Blocks.ASPHALT_SLAB);
			registerItemBlock(Blocks.ASPHALT_STAIR);
		}
		
		private static void registerItemBlock(DeferredHolder<Block, ? extends Block> block){
			IPRegisters.registerItem(block.getId().getPath(), () -> new IPBlockItemBase(block.get(), new Item.Properties()));
		}
	}
	
	public static class Items{
		public static final DeferredHolder<Item, ProjectorItem> PROJECTOR = IPRegisters.registerItem("projector", ProjectorItem::new);
		public static final DeferredHolder<Item, MotorboatItem> SPEEDBOAT = IPRegisters.registerItem("speedboat", MotorboatItem::new);
		public static final DeferredHolder<Item, OilCanItem> OIL_CAN = IPRegisters.registerItem("oil_can", OilCanItem::new);
		public static final DeferredHolder<Item, Item> BITUMEN = IPRegisters.registerItem("bitumen", IPItemBase::new);
		public static final DeferredHolder<Item, Item> PETCOKE = IPRegisters.registerItem("petcoke", () -> new IPItemBase(){
			@Override
			public int getBurnTime(ItemStack itemStack, RecipeType<?> recipeType){
				return 3200;
			}
		});
		public static final DeferredHolder<Item, Item> PETCOKEDUST = IPRegisters.registerItem("petcoke_dust", IPItemBase::new);
		public static final DeferredHolder<Item, Item> SURVEYRESULT = IPRegisters.registerItem("survey_result", SurveyResultItem::new);
		
		public static final DeferredHolder<Item, Item> PARAFFIN_WAX = IPRegisters.registerItem("paraffin_wax", () -> new IPItemBase(){
			@Override
			public int getBurnTime(ItemStack itemStack, RecipeType<?> recipeType){
				return 800;
			}
		});
		
		public static final DeferredHolder<Item, Item> GASOLINE_BOTTLE = IPRegisters.registerItem("gasoline_bottle", GasolineBottleItem::new);
		public static final DeferredHolder<Item, Item> MOLOTOV = IPRegisters.registerItem("molotov", () -> new MolotovItem(false));
		public static final DeferredHolder<Item, Item> MOLOTOV_LIT = IPRegisters.registerItem("molotov_lit", () -> new MolotovItem(true));
		
		//@formatter:off
		private static void forceClassLoad(){}
		//@formatter:on
	}
	
	public static class BoatUpgrades{
		public static final DeferredHolder<Item, IPUpgradeItem> REINFORCED_HULL = createBoatUpgrade("reinforced_hull");
		public static final DeferredHolder<Item, IPUpgradeItem> ICE_BREAKER = createBoatUpgrade("icebreaker");
		public static final DeferredHolder<Item, IPUpgradeItem> TANK = createBoatUpgrade("tank");
		public static final DeferredHolder<Item, IPUpgradeItem> RUDDERS = createBoatUpgrade("rudders");
		public static final DeferredHolder<Item, IPUpgradeItem> PADDLES = createBoatUpgrade("paddles");
		
		//@formatter:off
		private static void forceClassLoad(){}
		//@formatter:on
		
		private static <T extends Item> DeferredHolder<Item, IPUpgradeItem> createBoatUpgrade(String name){
			return IPRegisters.registerItem("upgrade_" + name, () -> new IPUpgradeItem(MotorboatItem.UPGRADE_TYPE));
		}
	}
	
	public static final DeferredHolder<Item, Item> DEBUGITEM = IPRegisters.registerItem("debug", DebugItem::new);
	
	/** block/item/fluid population */
	public static void modConstruction(IEventBus eBus){
		Fluids.forceClassLoad();
		Blocks.forceClassLoad();
		Items.forceClassLoad();
		BoatUpgrades.forceClassLoad();
		Multiblock.forceClassLoad();
		IPTileTypes.forceClassLoad();
		IPMenuTypes.forceClassLoad();
		Serializers.forceClassLoad();
		IPEffects.forceClassLoad();
		IPEntityTypes.forceClassLoad();
		IPParticleTypes.forceClassLoad();
		IPSounds.forceClassLoad();
		IPDamageSources.forceClassLoad();
		WorldGenFeatures.forceClassLoad();
		IPCreativeTab.forceClassLoad();
		IPDataComponents.forceClassLoad();
	}
	
	public static void setup(FMLCommonSetupEvent event){
		//event.enqueueWork(IPWorldGen::registerReservoirGen);
		
		Fluids.CRUDEOIL.setEffect(IEPotions.FLAMMABLE, 100, 1);
		Fluids.DIESEL.setEffect(IEPotions.FLAMMABLE, 40, 1); // Real diesel can not be ignited with an open flame.
		Fluids.DIESEL_SULFUR.setEffect(IEPotions.FLAMMABLE, 40, 1);
		Fluids.GASOLINE.setEffect(IEPotions.FLAMMABLE, 120, 2);
		Fluids.KEROSENE.setEffect(IEPotions.FLAMMABLE, 120, 2);
		Fluids.NAPHTHA.setEffect(IEPotions.FLAMMABLE, 120, 2);
		Fluids.NAPALM.setEffect(IEPotions.FLAMMABLE, 140, 2);
		
		Fluids.LUBRICANT.setEffect(IEPotions.SLIPPERY, 100, 1);
		
		ChemthrowerHandler.registerEffect(IPTags.Fluids.lubricant, new LubricantEffect());
		ChemthrowerHandler.registerEffect(IPTags.Fluids.lubricant, new ChemthrowerEffect_Potion(null, 0, IEPotions.SLIPPERY, 60, 1));
		ChemthrowerHandler.registerEffect(IETags.fluidPlantoil, new LubricantEffect());
		
		ChemthrowerHandler.registerEffect(IPTags.Fluids.crudeOil, new ChemthrowerEffect_Potion(null, 0, IEPotions.FLAMMABLE, 60, 1));
		ChemthrowerHandler.registerEffect(IPTags.Fluids.gasoline, new ChemthrowerEffect_Potion(null, 0, IEPotions.FLAMMABLE, 60, 1));
		ChemthrowerHandler.registerEffect(IPTags.Fluids.naphtha, new ChemthrowerEffect_Potion(null, 0, IEPotions.FLAMMABLE, 60, 1));
		ChemthrowerHandler.registerEffect(IPTags.Fluids.benzol, new ChemthrowerEffect_Potion(null, 0, IEPotions.FLAMMABLE, 60, 1));
		ChemthrowerHandler.registerEffect(IPTags.Fluids.napalm, new ChemthrowerEffect_Potion(null, 0, IEPotions.FLAMMABLE, 60, 2));
		
		ChemthrowerHandler.registerFlammable(IPTags.Fluids.crudeOil);
		ChemthrowerHandler.registerFlammable(IPTags.Fluids.gasoline);
		ChemthrowerHandler.registerFlammable(IPTags.Fluids.naphtha);
		ChemthrowerHandler.registerFlammable(IPTags.Fluids.benzol);
		ChemthrowerHandler.registerFlammable(IPTags.Fluids.napalm);
		
		MultiblockHandler.registerMultiblock(DistillationTowerMultiblock.INSTANCE);
		MultiblockHandler.registerMultiblock(PumpjackMultiblock.INSTANCE);
		MultiblockHandler.registerMultiblock(CokerUnitMultiblock.INSTANCE);
		MultiblockHandler.registerMultiblock(HydroTreaterMultiblock.INSTANCE);
		MultiblockHandler.registerMultiblock(DerrickMultiblock.INSTANCE);
		MultiblockHandler.registerMultiblock(OilTankMultiblock.INSTANCE);
		
		LubricantHandler.register(IPTags.Fluids.lubricant, 3);
		LubricantHandler.register(IETags.fluidPlantoil, 12);
		
		FlarestackHandler.register(IPTags.Utility.burnableInFlarestack);
		
		LubricatedHandler.register(Multiblock.PUMPJACK, PumpjackLubricationHandler::new);
		LubricatedHandler.register(IEMultiblockLogic.EXCAVATOR, ExcavatorLubricationHandler::new);
		LubricatedHandler.register(IEMultiblockLogic.CRUSHER, CrusherLubricationHandler::new);
	}
	
	@OnlyIn(Dist.CLIENT)
	@SubscribeEvent
	public static void registerParticleFactories(RegisterParticleProvidersEvent event){
		event.registerSpriteSet(IPParticleTypes.FLARE_FIRE.value(), FlareFire.Factory::new);
		event.registerSpecial(IPParticleTypes.FLUID_SPILL.value(), new FluidSpill.Factory());
	}
}
