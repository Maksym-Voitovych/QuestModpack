package flaxbeard.immersivepetroleum.common.data;

import blusunrize.immersiveengineering.api.multiblocks.MultiblockAdvancementTrigger;
import blusunrize.immersiveengineering.common.register.IEBlocks;
import blusunrize.immersiveengineering.common.register.IEItems.Tools;
import flaxbeard.immersivepetroleum.common.IPContent;
import flaxbeard.immersivepetroleum.common.util.ResourceUtils;
import net.minecraft.advancements.Advancement;
import net.minecraft.advancements.AdvancementHolder;
import net.minecraft.advancements.AdvancementRewards;
import net.minecraft.advancements.AdvancementType;
import net.minecraft.advancements.CriteriaTriggers;
import net.minecraft.advancements.Criterion;
import net.minecraft.advancements.critereon.ImpossibleTrigger;
import net.minecraft.advancements.critereon.InventoryChangeTrigger;
import net.minecraft.advancements.critereon.ItemPredicate;
import net.minecraft.core.HolderLookup;
import net.minecraft.core.registries.Registries;
import net.minecraft.data.PackOutput;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.ResourceKey;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.level.ItemLike;
import net.minecraft.world.level.storage.loot.LootTable;
import net.neoforged.neoforge.common.data.AdvancementProvider;
import net.neoforged.neoforge.common.data.ExistingFileHelper;

import javax.annotation.Nullable;
import java.util.List;
import java.util.concurrent.CompletableFuture;
import java.util.function.Consumer;

public class IPAdvancements extends AdvancementProvider{
	public IPAdvancements(PackOutput output, CompletableFuture<HolderLookup.Provider> registries, ExistingFileHelper helper){
		super(output, registries, helper, List.of(IPAdvancements::registerAdvancements));
	}
	
	private static void registerAdvancements(HolderLookup.Provider lookup, Consumer<AdvancementHolder> consumer, ExistingFileHelper fileHelper){
		AdvancementHolder start = codeTriggered(Advancement.Builder.advancement()
			.display(IPContent.Blocks.SEISMIC_SURVEY.get(),
				Component.translatable("advancement.immersivepetroleum.root"),
				Component.translatable("advancement.immersivepetroleum.root.desc"),
				ResourceUtils.ip("textures/block/asphalt.png"),
				AdvancementType.TASK, true, true, false))
			.save(consumer, ResourceUtils.ip("main/root"), fileHelper);
		
		AdvancementHolder derrick = advancement(start, IPContent.Multiblock.DERRICK.block().get(), "mb_derrick", AdvancementType.GOAL, true, true, false)
			.addCriterion("derrick", createMultiblockTrigger("derrick"))
			.save(consumer, ResourceUtils.ip("main/mb_derrick"), fileHelper);
		
		AdvancementHolder pumpjack = advancement(derrick, IPContent.Multiblock.PUMPJACK.block().get(), "mb_pumpjack", AdvancementType.GOAL, true, true, false)
			.addCriterion("pumpjack", createMultiblockTrigger("pumpjack"))
			.save(consumer, ResourceUtils.ip("main/mb_pumpjack"), fileHelper);
		
		advancement(derrick, IPContent.Multiblock.OILTANK.block().get(), "mb_oiltank", AdvancementType.GOAL, true, true, false)
			.addCriterion("oiltank", createMultiblockTrigger("oiltank"))
			.save(consumer, ResourceUtils.ip("main/mb_oiltank"), fileHelper);
		
		AdvancementHolder tower = advancement(pumpjack, IPContent.Multiblock.DISTILLATIONTOWER.block().get(), "mb_distillationtower", AdvancementType.GOAL, true, true, false)
			.addCriterion("distillationtower", createMultiblockTrigger("distillationtower"))
			.save(consumer, ResourceUtils.ip("main/mb_distillationtower"), fileHelper);
		
		AdvancementHolder bitumen = advancement(tower, IPContent.Items.BITUMEN.get(), "bitumen", AdvancementType.TASK, true, true, false)
			.addCriterion("bitumen", InventoryChangeTrigger.TriggerInstance.hasItems(IPContent.Items.BITUMEN.get()))
			.save(consumer, ResourceUtils.ip("main/bitumen"), fileHelper);
		
		AdvancementHolder cokerunit = advancement(bitumen, IPContent.Multiblock.COKERUNIT.block().get(), "mb_cokerunit", AdvancementType.GOAL, true, true, false)
			.addCriterion("cokerunit", createMultiblockTrigger("cokerunit"))
			.rewards(reward(10, ResourceUtils.ip("advancements/forming_coker_reward")))
			.save(consumer, ResourceUtils.ip("main/mb_cokerunit"), fileHelper);
		
		advancement(cokerunit, IPContent.Items.PETCOKE.get(), "petcoke", AdvancementType.TASK, true, true, false)
			.addCriterion("petcoke", InventoryChangeTrigger.TriggerInstance.hasItems(IPContent.Items.PETCOKE.get()))
			.save(consumer, ResourceUtils.ip("main/petcoke"), fileHelper);
		
		AdvancementHolder hydrotreater = advancement(tower, IPContent.Multiblock.HYDROTREATER.block().get(), "mb_hydrotreater", AdvancementType.GOAL, true, true, false)
			.addCriterion("hydrotreater", createMultiblockTrigger("hydrotreater"))
			.save(consumer, ResourceUtils.ip("main/mb_hydrotreater"), fileHelper);
		
		motorboat(consumer, tower, fileHelper);
		
		codeTriggered(advancement(tower, IPContent.Blocks.GAS_GENERATOR.get(), "gas_generator", AdvancementType.TASK, true, true, false))
			.save(consumer, ResourceUtils.ip("main/gas_generator"), fileHelper);
		
		codeTriggered(advancement(tower, IPContent.Blocks.AUTO_LUBRICATOR.get(), "auto_lubricator", AdvancementType.TASK, true, true, false))
			.save(consumer, ResourceUtils.ip("main/auto_lubricator"), fileHelper);
		
		codeTriggered(advancement(tower, IPContent.Items.OIL_CAN.get(), "oil_can", AdvancementType.TASK, true, true, false))
			.save(consumer, ResourceUtils.ip("main/oil_can"), fileHelper);
		
		advancement(start, IPContent.Items.PROJECTOR.get(), "projector", AdvancementType.TASK, true, true, false)
			.addCriterion("projector", InventoryChangeTrigger.TriggerInstance.hasItems(IPContent.Items.PROJECTOR.get()))
			.save(consumer, ResourceUtils.ip("main/projector"), fileHelper);
		
		codeTriggered(advancement(start, IPContent.Blocks.FLARESTACK.get(), "flarestack", AdvancementType.TASK, true, true, false))
			.save(consumer, ResourceUtils.ip("main/flarestack"), fileHelper);
		
		AdvancementHolder cracking = advancement(hydrotreater, IPContent.Fluids.PETROLEUM_GAS.bucket().get(), "cracking", AdvancementType.TASK, true, true, false)
			.addCriterion("cracking", InventoryChangeTrigger.TriggerInstance.hasItems(IPContent.Fluids.PETROLEUM_GAS.bucket().get()))
			.save(consumer, ResourceUtils.ip("main/cracking"), fileHelper);
		
		advancement(cracking, IEBlocks.StoneDecoration.DUROPLAST.get().asItem(), "duroplast", AdvancementType.CHALLENGE, true, true, false)
			.addCriterion("benzol", InventoryChangeTrigger.TriggerInstance.hasItems(IPContent.Fluids.BENZOL.bucket().get()))
			.addCriterion("petroleum_gas", InventoryChangeTrigger.TriggerInstance.hasItems(IPContent.Fluids.PETROLEUM_GAS.bucket().get())) // These are here to make sure the player made their duroplast from naphtha
			.addCriterion("duroplast_block", InventoryChangeTrigger.TriggerInstance.hasItems(IEBlocks.StoneDecoration.DUROPLAST.get().asItem()))
			.save(consumer, ResourceUtils.ip("main/duroplast"), fileHelper);
		
		AdvancementHolder kerosene = advancement(tower, IPContent.Fluids.BENZOL.bucket().get(), "kerosene", AdvancementType.TASK, true, true, false)
			.addCriterion("kerosene", InventoryChangeTrigger.TriggerInstance.hasItems(IPContent.Fluids.BENZOL.bucket().get()))
			.save(consumer, ResourceUtils.ip("main/kerosene"), fileHelper);
		
		AdvancementHolder gasoline = advancement(kerosene, IPContent.Fluids.GASOLINE.bucket().get(), "gasoline", AdvancementType.GOAL, true, true, false)
			.addCriterion("gasoline", InventoryChangeTrigger.TriggerInstance.hasItems(IPContent.Fluids.GASOLINE.bucket().get()))
			.save(consumer, ResourceUtils.ip("main/gasoline"), fileHelper);
		
		advancement(gasoline, IPContent.Fluids.NAPALM.bucket().get(), "napalm", AdvancementType.TASK, true, true, false)
			.addCriterion("napalm", InventoryChangeTrigger.TriggerInstance.hasItems(IPContent.Fluids.NAPALM.bucket().get()))
			.save(consumer, ResourceUtils.ip("main/napalm"), fileHelper);
	}
	
	private static void motorboat(Consumer<AdvancementHolder> consumer, AdvancementHolder start, ExistingFileHelper fileHelper){
		AdvancementHolder fill_motorboat = codeTriggered(advancement(start, IPContent.Items.SPEEDBOAT.get(), "motorboat", AdvancementType.TASK, true, true, false))
			.save(consumer, ResourceUtils.ip("main/motorboat"), fileHelper);
		
		codeTriggered(advancement(fill_motorboat, IPContent.BoatUpgrades.ICE_BREAKER.get(), "ice_breaker", AdvancementType.TASK, true, true, false))
			.save(consumer, ResourceUtils.ip("main/ice_breaker"), fileHelper);
		
		codeTriggered(advancement(fill_motorboat, IPContent.BoatUpgrades.PADDLES.get(), "paddles", AdvancementType.TASK, true, true, false))
			.save(consumer, ResourceUtils.ip("main/paddles"), fileHelper);
		
		codeTriggered(advancement(fill_motorboat, IPContent.BoatUpgrades.REINFORCED_HULL.get(), "reinforced_hull", AdvancementType.TASK, true, true, false))
			.save(consumer, ResourceUtils.ip("main/reinforced_hull"), fileHelper);
		
		codeTriggered(advancement(fill_motorboat, IPContent.BoatUpgrades.RUDDERS.get(), "rudders", AdvancementType.CHALLENGE, true, true, false))
			.rewards(reward(50, ResourceUtils.ie("advancements/shader_rare")))
			.save(consumer, ResourceUtils.ip("main/rudders"), fileHelper);
		
		codeTriggered(advancement(fill_motorboat, IPContent.BoatUpgrades.TANK.get(), "tank", AdvancementType.TASK, true, true, false))
			.save(consumer, ResourceUtils.ip("main/tank"), fileHelper);
	}
	
	static final ItemPredicate HAMMER = ItemPredicate.Builder.item().of(Tools.HAMMER).build();
	protected static Criterion<?> createMultiblockTrigger(String mbName){
		return MultiblockAdvancementTrigger.create(ResourceUtils.ip("multiblocks/" + mbName), HAMMER);
	}
	
	protected static Advancement.Builder advancement(AdvancementHolder parent, ItemLike display, String name, AdvancementType frame, boolean showToast, boolean announceToChat, boolean hidden){
		Advancement.Builder builder = Advancement.Builder.advancement()
			.parent(parent)
			.display(display,
				Component.translatable("advancement.immersivepetroleum." + name),
				Component.translatable("advancement.immersivepetroleum." + name + ".desc"),
			null, frame, showToast, announceToChat, hidden);
		return builder;
	}
	
	protected static Advancement.Builder codeTriggered(Advancement.Builder builder){
		return builder.addCriterion("code_trigger", CriteriaTriggers.IMPOSSIBLE.createCriterion(new ImpossibleTrigger.TriggerInstance()));
	}
	
	protected static AdvancementRewards reward(int exp, @Nullable ResourceLocation lootTable){
		return new AdvancementRewards.Builder()
			.addExperience(exp)
			.addLootTable(key(lootTable))
			.build();
	}
	
	private static ResourceKey<LootTable> key(ResourceLocation rl){
		return ResourceKey.create(Registries.LOOT_TABLE, rl);
	}
}
