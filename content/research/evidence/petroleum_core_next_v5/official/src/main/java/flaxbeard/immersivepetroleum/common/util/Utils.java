package flaxbeard.immersivepetroleum.common.util;

import blusunrize.immersiveengineering.api.multiblocks.blocks.env.IMultiblockBEHelper;
import blusunrize.immersiveengineering.api.multiblocks.blocks.env.IMultiblockBEHelperMaster;
import blusunrize.immersiveengineering.api.multiblocks.blocks.logic.IMultiblockBE;
import blusunrize.immersiveengineering.api.multiblocks.blocks.registry.MultiblockBlockEntityMaster;
import net.minecraft.advancements.AdvancementHolder;
import net.minecraft.core.BlockPos;
import net.minecraft.server.PlayerAdvancements;
import net.minecraft.server.ServerAdvancementManager;
import net.minecraft.server.level.ColumnPos;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.item.ItemEntity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.neoforged.neoforge.capabilities.Capabilities;

import javax.annotation.Nullable;
import java.text.DecimalFormat;
import java.util.function.Consumer;

/**
 * General purpose Utilities
 *
 * @author TwistedGate
 */
public class Utils{
	static final DecimalFormat FORMATTER = new DecimalFormat("#,###.##");
	
	public static String fDecimal(byte number){
		return FORMATTER.format(number);
	}
	
	public static String fDecimal(short number){
		return FORMATTER.format(number);
	}
	
	public static String fDecimal(int number){
		return FORMATTER.format(number);
	}
	
	public static String fDecimal(long number){
		return FORMATTER.format(number);
	}
	
	public static String fDecimal(float number){
		return FORMATTER.format(number);
	}
	
	public static String fDecimal(double number){
		return FORMATTER.format(number);
	}
	
	/** Copy of {@link blusunrize.immersiveengineering.common.util.Utils#unlockIEAdvancement(Player, String)} */
	public static void unlockIPAdvancement(Player player, String name){
		if(player instanceof ServerPlayer serverPlayer && serverPlayer.getCommandSenderWorld() instanceof ServerLevel level){
			PlayerAdvancements advancements = serverPlayer.getAdvancements();
			ServerAdvancementManager manager = level.getServer().getAdvancements();
			AdvancementHolder advancement = manager.get(ResourceUtils.ip(name));
			if(advancement != null)
				advancements.award(advancement, "code_trigger");
		}
	}
	
	/** Copy of {@link blusunrize.immersiveengineering.common.util.Utils#isFluidRelatedItemStack(ItemStack)} */
	public static boolean isFluidRelatedItemStack(ItemStack stack){
		return !stack.isEmpty() && stack.getCapability(Capabilities.FluidHandler.ITEM) != null;
	}
	
	public static void dropItem(Level level, BlockPos pos, ItemStack stack){
		dropItem(level, pos, stack, ItemEntity::setDefaultPickUpDelay);
	}
	
	public static void dropItemNoDelay(Level level, BlockPos pos, ItemStack stack){
		dropItem(level, pos, stack, ItemEntity::setNoPickUpDelay);
	}
	
	public static void dropItem(Level level, BlockPos pos, ItemStack stack, Consumer<ItemEntity> func){
		if(!level.isClientSide && !stack.isEmpty() && !level.restoringBlockSnapshots){
			double f = EntityType.ITEM.getHeight() / 2.0D;
			double x = pos.getX() + 0.5D;
			double y = pos.getY() + 0.5D - f;
			double z = pos.getZ() + 0.5D;
			
			ItemEntity entity = new ItemEntity(level, x, y, z, stack);
			func.accept(entity);
			level.addFreshEntity(entity);
		}
	}
	
	public static ColumnPos toColumnPos(BlockPos pos){
		return new ColumnPos(pos.getX(), pos.getZ());
	}
	
	@Nullable
	public static MultiblockBlockEntityMaster<?> getMultiblockMasterBE(Level level, BlockPos pos){
		BlockEntity be = level.getBlockEntity(pos);
		if(!(be instanceof IMultiblockBE<?> mb))
			return null;
		
		if(be instanceof MultiblockBlockEntityMaster<?> master)
			return master;
		
		if(mb.getHelper().getContext() == null)
			return null;
		
		IMultiblockBEHelper<?> helper = mb.getHelper();
		BlockPos masterPos = helper.getContext().getLevel().toAbsolute(helper.getMultiblock().masterPosInMB());
		
		be = level.getBlockEntity(masterPos);
		
		return be instanceof MultiblockBlockEntityMaster<?> master ? master : null;
	}
	
	@Nullable
	public static IMultiblockBEHelperMaster<?> getMultiblockMasterHelper(Level level, IMultiblockBEHelper<?> helper){
		if(helper instanceof IMultiblockBEHelperMaster<?> masterHelper)
			return masterHelper;
		
		if(helper.getContext() == null)
			return null;
		
		BlockPos masterPos = helper.getContext().getLevel().toAbsolute(helper.getMultiblock().masterPosInMB());
		BlockEntity be = level.getBlockEntity(masterPos);
		
		return be instanceof MultiblockBlockEntityMaster<?> master ? master.getHelper() : null;
		
	}
	
	private Utils(){
	}
}
