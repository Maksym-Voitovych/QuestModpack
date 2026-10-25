package flaxbeard.immersivepetroleum.common.blocks.tileentities;

import blusunrize.immersiveengineering.api.Lib;
import blusunrize.immersiveengineering.api.multiblocks.blocks.env.IMultiblockBEHelperMaster;
import blusunrize.immersiveengineering.api.multiblocks.blocks.logic.IMultiblockBE;
import blusunrize.immersiveengineering.common.blocks.IEBlockInterfaces;
import flaxbeard.immersivepetroleum.api.crafting.LubricantHandler;
import flaxbeard.immersivepetroleum.api.crafting.LubricatedHandler;
import flaxbeard.immersivepetroleum.api.crafting.LubricatedHandler.ILubricationHandler;
import flaxbeard.immersivepetroleum.common.IPCapabilityRegistry;
import flaxbeard.immersivepetroleum.common.IPDataComponents;
import flaxbeard.immersivepetroleum.common.IPTileTypes;
import flaxbeard.immersivepetroleum.common.blocks.interfaces.IBlockEntityDrop;
import flaxbeard.immersivepetroleum.common.blocks.interfaces.IPlacementReader;
import flaxbeard.immersivepetroleum.common.blocks.interfaces.IPlayerInteraction;
import flaxbeard.immersivepetroleum.common.blocks.ticking.IPCommonTickableTile;
import flaxbeard.immersivepetroleum.common.blocks.wooden.AutoLubricatorBlock;
import flaxbeard.immersivepetroleum.common.util.Utils;
import net.minecraft.client.multiplayer.ClientLevel;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.HolderLookup;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.chat.Component;
import net.minecraft.network.chat.MutableComponent;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.storage.loot.LootContext;
import net.minecraft.world.level.storage.loot.parameters.LootContextParams;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.HitResult;
import net.neoforged.api.distmarker.Dist;
import net.neoforged.api.distmarker.OnlyIn;
import net.neoforged.neoforge.fluids.FluidStack;
import net.neoforged.neoforge.fluids.FluidUtil;
import net.neoforged.neoforge.fluids.capability.IFluidHandler;
import net.neoforged.neoforge.fluids.capability.templates.FluidTank;
import org.jetbrains.annotations.Nullable;

import javax.annotation.Nonnull;
import java.util.List;

public class AutoLubricatorTileEntity extends IPTileEntityBase implements IPCommonTickableTile, IPCapabilityRegistry.IHasCapability, IPlacementReader, IPlayerInteraction, IBlockEntityDrop, IEBlockInterfaces.IBlockOverlayText{
	public boolean isSlave;
	public Direction facing = Direction.NORTH;
	public FluidTank tank = new FluidTank(8000, fluid -> (fluid != null && LubricantHandler.isValidLube(fluid.getFluid())));
	
	public AutoLubricatorTileEntity(BlockPos pWorldPosition, BlockState pBlockState){
		super(IPTileTypes.AUTOLUBE.get(), pWorldPosition, pBlockState);
	}
	
	public AutoLubricatorTileEntity master(){
		if(!this.isSlave || this.level == null)
			return this;
		
		BlockEntity te = this.level.getBlockEntity(getBlockPos().below());
		return te instanceof AutoLubricatorTileEntity autolube ? autolube : null;
	}
	
	@Override
	protected void readCustom(CompoundTag compound, HolderLookup.Provider provider){
		this.isSlave = compound.getBoolean("slave");
		
		Direction facing = Direction.byName(compound.getString("facing"));
		this.facing = (facing == null || facing.get2DDataValue() == -1) ? Direction.NORTH : facing;
		
		this.tank.readFromNBT(provider, compound.getCompound("tank"));
	}
	
	@Override
	protected void writeCustom(CompoundTag compound, HolderLookup.Provider provider){
		compound.putBoolean("slave", this.isSlave);
		compound.putString("facing", this.facing.getName());
		compound.putInt("count", this.count);
		
		CompoundTag tank = this.tank.writeToNBT(provider, new CompoundTag());
		compound.put("tank", tank);
	}
	
	@Override
	public void readOnPlacement(LivingEntity placer, ItemStack stack){
		IPDataComponents.TankData tankData = stack.get(IPDataComponents.TANK_DATA);
		if(tankData != null && !tankData.fs().isEmpty())
			this.tank.fill(tankData.fs(), IFluidHandler.FluidAction.EXECUTE);
		
		if(placer instanceof Player player && this.level != null){
			BlockPos target = this.worldPosition.relative(this.facing);
			BlockEntity te = this.level.getBlockEntity(target);
			
			if(te instanceof IMultiblockBE<?> me){
				ILubricationHandler<?, ?> handler = LubricatedHandler.getHandlerForTile(me.getHelper());
				if(handler != null && handler.isPlacedCorrectly(this.level, this.getBlockPos(), this.facing)){
					Utils.unlockIPAdvancement(player, "main/auto_lubricator");
				}
			}
		}
	}
	
	@Override
	@Nonnull
	public List<ItemStack> getBlockEntityDrop(LootContext context){
		BlockState state = context.getParamOrNull(LootContextParams.BLOCK_STATE);
		if(state == null || state.getValue(AutoLubricatorBlock.SLAVE))
			return List.of(ItemStack.EMPTY);
		
		ItemStack stack = new ItemStack(state.getBlock());
		
		BlockEntity te = context.getParamOrNull(LootContextParams.BLOCK_ENTITY);
		if(te instanceof AutoLubricatorTileEntity autolube && !autolube.tank.getFluid().isEmpty()){
			FluidStack fs = autolube.tank.getFluid();
			stack.set(IPDataComponents.TANK_DATA, new IPDataComponents.TankData(fs));
		}
		
		return List.of(stack);
	}
	
	@Override
	public <T> T getCapability(Direction side){
		if(this.isSlave && (side == null || side == Direction.UP)){
			AutoLubricatorTileEntity master = master();
			if(master == null)
				return null;
			
			return (T) master.tank;
		}
		
		return null;
	}
	
	@Override
	public void setChanged(){
		super.setChanged();
		
		BlockState state = this.level.getBlockState(this.worldPosition);
		this.level.sendBlockUpdated(this.worldPosition, state, state, 3);
		this.level.updateNeighborsAt(this.worldPosition, state.getBlock());
	}
	
	public Direction getFacing(){
		return this.facing;
	}
	
	public boolean isMaster(){
		return !this.isSlave;
	}
	
	@OnlyIn(Dist.CLIENT)
	public AABB getRenderBoundingBox(){
		BlockPos pos = getBlockPos();
		return AABB.encapsulatingFullBlocks(pos.offset(-3, -3, -3), pos.offset(3, 3, 3));
	}
	
	@Nullable
	@Override
	public Component[] getOverlayText(@Nullable BlockState blockState, Player player, @Nonnull HitResult mop, boolean hammer){
		if(Utils.isFluidRelatedItemStack(player.getItemInHand(InteractionHand.MAIN_HAND))){
			AutoLubricatorTileEntity master = master();
			if(master != null){
				Component s = switch(master.tank.isEmpty() ? 0 : 1){
					case 0 -> Component.translatable(Lib.GUI + "empty");
					case 1 ->
						((MutableComponent) master.tank.getFluid().getHoverName()).append(": " + master.tank.getFluidAmount() + "mB");
					default -> null;
				};
				
				return new Component[]{s};
			}
		}
		return null;
	}
	
	@Override
	public InteractionResult interact(@Nonnull Direction side, @Nonnull Player player, @Nonnull InteractionHand hand, @Nonnull ItemStack heldItem, float hitX, float hitY, float hitZ){
		AutoLubricatorTileEntity master = master();
		if(master != null && this.level != null){
			if(!this.level.isClientSide && FluidUtil.interactWithFluidHandler(player, hand, master.tank)){
				setChanged();
			}
			return InteractionResult.SUCCESS;
		}
		return InteractionResult.FAIL;
	}
	
	int count = 0;
	int countClient = 0;
	int lastTank = 0;
	
	@Override
	@SuppressWarnings("rawtypes, unchecked")
	public void tickClient(){
		if(this.isSlave || this.level == null){
			return;
		}
		
		if(!this.tank.isEmpty() && LubricantHandler.isValidLube(this.tank.getFluid()) && this.tank.getFluidAmount() >= LubricantHandler.getLubeAmount(this.tank.getFluid())){
			BlockPos target = this.worldPosition.relative(this.facing);
			BlockEntity te = this.level.getBlockEntity(target);
			
			if(te instanceof IMultiblockBE<?> mb){
				ILubricationHandler handler = LubricatedHandler.getHandlerForTile(mb.getHelper());
				if(handler != null && handler.isPlacedCorrectly(this.level, this.getBlockPos(), this.facing)){
					
					IMultiblockBEHelperMaster<?> masterHelper = Utils.getMultiblockMasterHelper(this.level, mb.getHelper());
					
					if(handler.isMachineEnabled(this.level, masterHelper)){
						handler.lubricateClient((ClientLevel) this.level, this.tank.getFluid().getFluid(), this.count, masterHelper);
						
						if(this.countClient++ % 50 == 0){
							this.countClient = this.level.random.nextInt(40);
							handler.spawnLubricantParticles((ClientLevel) this.level, this.getBlockPos(), this.facing, masterHelper);
						}
					}
				}
			}
		}
	}
	
	@Override
	@SuppressWarnings("rawtypes, unchecked")
	public void tickServer(){
		if(this.isSlave || this.level == null)
			return;
		
		
		if(!this.tank.isEmpty() && LubricantHandler.isValidLube(this.tank.getFluid()) && this.tank.getFluidAmount() >= LubricantHandler.getLubeAmount(this.tank.getFluid())){
			BlockPos target = this.worldPosition.relative(this.facing);
			BlockEntity te = this.level.getBlockEntity(target);
			
			if(te instanceof IMultiblockBE<?> mb){
				ILubricationHandler handler = LubricatedHandler.getHandlerForTile(mb.getHelper());
				
				if(handler != null && handler.isPlacedCorrectly(this.level, this.getBlockPos(), this.facing)){
					IMultiblockBEHelperMaster<?> masterHelper = Utils.getMultiblockMasterHelper(this.level, mb.getHelper());
					
					if(masterHelper != null && handler.isMachineEnabled(this.level, masterHelper)){
						handler.lubricateServer((ServerLevel) this.level, this.tank.getFluid().getFluid(), this.count, masterHelper);
						
						if(this.count++ % 4 == 0){
							this.tank.drain(LubricantHandler.getLubeAmount(this.tank.getFluid()), IFluidHandler.FluidAction.EXECUTE);
						}
						
						setChanged();
					}
				}
			}
		}
		
		if(!this.level.isClientSide && this.lastTank != this.tank.getFluidAmount()){
			this.lastTank = this.tank.getFluidAmount();
			setChanged();
		}
	}
}
