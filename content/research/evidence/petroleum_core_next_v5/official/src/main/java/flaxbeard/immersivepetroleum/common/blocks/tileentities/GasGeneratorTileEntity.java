package flaxbeard.immersivepetroleum.common.blocks.tileentities;

import blusunrize.immersiveengineering.api.Lib;
import blusunrize.immersiveengineering.api.TargetingInfo;
import blusunrize.immersiveengineering.api.energy.MutableEnergyStorage;
import blusunrize.immersiveengineering.api.wires.Connection;
import blusunrize.immersiveengineering.api.wires.ConnectionPoint;
import blusunrize.immersiveengineering.api.wires.IImmersiveConnectable;
import blusunrize.immersiveengineering.api.wires.WireType;
import blusunrize.immersiveengineering.api.wires.impl.ImmersiveConnectableBlockEntity;
import blusunrize.immersiveengineering.api.wires.localhandlers.EnergyTransferHandler;
import blusunrize.immersiveengineering.api.wires.utils.WireUtils;
import blusunrize.immersiveengineering.common.blocks.IEBlockInterfaces;
import blusunrize.immersiveengineering.common.blocks.PlacementLimitation;
import blusunrize.immersiveengineering.common.config.IEServerConfig;
import blusunrize.immersiveengineering.common.util.IESounds;
import com.google.common.collect.ImmutableList;
import flaxbeard.immersivepetroleum.ImmersivePetroleum;
import flaxbeard.immersivepetroleum.api.energy.FuelHandler;
import flaxbeard.immersivepetroleum.common.IPCapabilityRegistry;
import flaxbeard.immersivepetroleum.common.IPDataComponents;
import flaxbeard.immersivepetroleum.common.IPTileTypes;
import flaxbeard.immersivepetroleum.common.blocks.interfaces.IBlockEntityDrop;
import flaxbeard.immersivepetroleum.common.blocks.interfaces.IPlacementReader;
import flaxbeard.immersivepetroleum.common.blocks.interfaces.IPlayerInteraction;
import flaxbeard.immersivepetroleum.common.blocks.ticking.IPCommonTickableTile;
import flaxbeard.immersivepetroleum.common.sound.IPlaySound;
import flaxbeard.immersivepetroleum.common.util.Utils;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.HolderLookup;
import net.minecraft.core.Vec3i;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.chat.Component;
import net.minecraft.network.chat.MutableComponent;
import net.minecraft.network.protocol.game.ClientboundBlockEntityDataPacket;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.storage.loot.LootContext;
import net.minecraft.world.phys.HitResult;
import net.minecraft.world.phys.Vec3;
import net.neoforged.neoforge.capabilities.BlockCapability;
import net.neoforged.neoforge.capabilities.Capabilities;
import net.neoforged.neoforge.fluids.FluidStack;
import net.neoforged.neoforge.fluids.FluidUtil;
import net.neoforged.neoforge.fluids.capability.IFluidHandler;
import net.neoforged.neoforge.fluids.capability.IFluidHandler.FluidAction;
import net.neoforged.neoforge.fluids.capability.templates.FluidTank;

import javax.annotation.Nonnull;
import javax.annotation.Nullable;
import java.util.Collection;
import java.util.List;
import java.util.Objects;

public class GasGeneratorTileEntity extends ImmersiveConnectableBlockEntity implements IPCommonTickableTile, IPCapabilityRegistry.IHasMultiCapability, IPlacementReader, IPlayerInteraction, IBlockEntityDrop, IPlaySound, IEBlockInterfaces.IDirectionalBE, IEBlockInterfaces.IBlockOverlayText, EnergyTransferHandler.EnergyConnector{
	public static final int FUEL_CAPACITY = 8000;
	
	protected WireType wireType;
	protected boolean isActive = false;
	protected int fluidTick = 0;
	protected int currentFlux = 0;
	protected Direction facing = Direction.NORTH;
	protected final MutableEnergyStorage energyStorage = new MutableEnergyStorage(getMaxStorage(), Integer.MAX_VALUE, getMaxOutput());
	protected final FluidTank tank = new FluidTank(FUEL_CAPACITY, fluid -> (fluid != FluidStack.EMPTY && FuelHandler.isValidFuel(fluid.getFluid())));
	
	public GasGeneratorTileEntity(BlockPos pWorldPosition, BlockState pBlockState){
		super(IPTileTypes.GENERATOR.get(), pWorldPosition, pBlockState);
	}
	
	public int getMaxOutput(){
		return IEServerConfig.MACHINES.lvCapConfig.output.getAsInt();
	}
	
	private int getMaxStorage(){
		return IEServerConfig.MACHINES.lvCapConfig.storage.getAsInt();
	}
	
	@Override
	protected void loadAdditional(@Nonnull CompoundTag nbt, @Nonnull HolderLookup.Provider provider){
		super.loadAdditional(nbt, provider);
		
		this.isActive = nbt.getBoolean("isActive");
		this.fluidTick = nbt.getInt("fluidTick");
		this.currentFlux = nbt.getInt("currentFlux");
		this.tank.readFromNBT(provider, nbt.getCompound("tank"));
		this.wireType = nbt.contains("wiretype") ? WireUtils.getWireTypeFromNBT(nbt, "wiretype") : null;
		
		if(nbt.contains("buffer"))
			this.energyStorage.deserializeNBT(provider, nbt.get("buffer"));
	}
	
	@Override
	public void saveAdditional(@Nonnull CompoundTag nbt, @Nonnull HolderLookup.Provider provider){
		nbt.putInt("fluidTick", this.fluidTick);
		nbt.putInt("currentFlux", this.currentFlux);
		nbt.putBoolean("isActive", this.isActive);
		nbt.put("tank", this.tank.writeToNBT(provider, new CompoundTag()));
		nbt.put("buffer", this.energyStorage.serializeNBT(provider));
		
		if(this.wireType != null){
			nbt.putString("wiretype", this.wireType.getUniqueName());
		}
	}
	
	@Override
	public ClientboundBlockEntityDataPacket getUpdatePacket(){
		return ClientboundBlockEntityDataPacket.create(this, (b, p) -> getUpdateTag(p));
	}
	
	@Nonnull
	public CompoundTag getUpdateTag(HolderLookup.Provider provider){
		CompoundTag nbt = new CompoundTag();
		saveAdditional(nbt, provider);
		return nbt;
	}
	
	@Nonnull
	public Level getNonnullLevel(){
		return Objects.requireNonNull(this.level);
	}
	
	@Override
	public void setChanged(){
		super.setChanged();
		
		BlockState state = getNonnullLevel().getBlockState(this.worldPosition);
		getNonnullLevel().sendBlockUpdated(this.worldPosition, state, state, 3);
		getNonnullLevel().updateNeighborsAt(this.worldPosition, state.getBlock());
	}
	
	@Override
	public int getAvailableEnergy(){
		return Math.min(getMaxOutput(), this.energyStorage.getEnergyStored());
	}
	
	@Override
	public void extractEnergy(int amount){
		this.energyStorage.extractEnergy(amount, false);
	}
	
	@Override
	public boolean isSource(ConnectionPoint cp){
		return true;
	}
	
	@Override
	public boolean isSink(ConnectionPoint cp){
		return false;
	}
	
	@Override
	public boolean stopSound(ResourceLocation soundLocation){
		return !this.isActive;
	}
	
	@Override
	public <C, T> T getCapability(BlockCapability<T, C> cap, Direction side){
		if(cap == Capabilities.FluidHandler.BLOCK && (side == null || side == Direction.UP)){
			return (T) this.tank;
			
		}else if(cap == Capabilities.EnergyStorage.BLOCK && (side == null || side == this.facing)){
			return (T) this.energyStorage;
		}
		
		return null;
	}
	
	@Nullable
	@Override
	public Component[] getOverlayText(@Nullable BlockState blockState, Player player, HitResult mop, boolean hammer){
		if(Utils.isFluidRelatedItemStack(player.getItemInHand(InteractionHand.MAIN_HAND))){
			Component s = switch(tank.getFluid().isEmpty() ? 0 : 1){
				case 0 -> Component.translatable(Lib.GUI + "empty");
				case 1 ->
					((MutableComponent) tank.getFluid().getHoverName()).append(": " + tank.getFluidAmount() + "mB");
				default -> null;
			};
			
			return new Component[]{s};
		}
		return null;
	}
	
	@Override
	public InteractionResult interact(Direction side, Player player, InteractionHand hand, ItemStack heldItem, float hitX, float hitY, float hitZ){
		if(FluidUtil.interactWithFluidHandler(player, hand, tank)){
			setChanged();
			Utils.unlockIPAdvancement(player, "main/gas_generator");
			return InteractionResult.SUCCESS;
		}else if(player.isShiftKeyDown()){
			boolean added;
			if(player.getInventory().getSelected().isEmpty()){
				added = true;
				player.getInventory().setItem(player.getInventory().selected, getFirstBlockEntityDrop());
			}else{
				added = player.getInventory().add(getFirstBlockEntityDrop());
			}
			
			if(added)
				getNonnullLevel().setBlockAndUpdate(this.worldPosition, Blocks.AIR.defaultBlockState());
			
			return InteractionResult.SUCCESS;
		}
		
		return InteractionResult.FAIL;
	}
	
	@Override
	public void readOnPlacement(LivingEntity placer, ItemStack stack){
		IPDataComponents.TankData tankData = stack.get(IPDataComponents.TANK_DATA);
		IPDataComponents.PowerData powerData = stack.get(IPDataComponents.POWER_DATA);
		
		if(tankData != null && !tankData.fs().isEmpty()){
			this.tank.fill(tankData.fs(), IFluidHandler.FluidAction.EXECUTE);
		}
		
		if(powerData != null){
			this.energyStorage.setStoredEnergy(powerData.energy());
		}
	}
	
	@Nonnull
	public List<ItemStack> getBlockEntityDrop(LootContext context){
		ItemStack stack = new ItemStack(getBlockState().getBlock());
		
		if(this.tank.getFluidAmount() > 0){
			stack.set(IPDataComponents.TANK_DATA, new IPDataComponents.TankData(this.tank));
		}
		
		if(this.energyStorage.getEnergyStored() > 0){
			stack.set(IPDataComponents.POWER_DATA, new IPDataComponents.PowerData(this.energyStorage));
		}
		
		return ImmutableList.of(stack);
	}
	
	@Override
	@Nonnull
	public Direction getFacing(){
		return this.facing;
	}
	
	@Override
	public void setFacing(@Nonnull Direction facing){
		this.facing = facing;
	}
	
	@Override
	@Nonnull
	public PlacementLimitation getFacingLimitation(){
		return PlacementLimitation.HORIZONTAL;
	}
	
	@Override
	public boolean mirrorFacingOnPlacement(@Nonnull LivingEntity placer){
		return false;
	}
	
	@Override
	public boolean canHammerRotate(@Nonnull Direction side, @Nonnull Vec3 hit, @Nonnull LivingEntity entity){
		return true;
	}
	
	@Override
	public void tickClient(){
		ImmersivePetroleum.proxy.handleTileSound(IESounds.dieselGenerator, this, this.isActive, .3f, 1.25f);
		if(this.isActive && getNonnullLevel().getGameTime() % 4 == 0){
			Direction fl = this.facing;
			Direction fw = this.facing.getCounterClockWise();
			
			Vec3i vec = fw.getOpposite().getNormal();
			
			double x = this.worldPosition.getX() + .5 + (fl.getStepX() * -2 / 6F) + (-fw.getStepX() * .6125f);
			double y = this.worldPosition.getY() + .4;
			double z = this.worldPosition.getZ() + .5 + (fl.getStepZ() * -2 / 6F) + (-fw.getStepZ() * .6125f);
			
			getNonnullLevel().addParticle(getNonnullLevel().random.nextInt(10) == 0 ? ParticleTypes.LARGE_SMOKE : ParticleTypes.SMOKE, x, y, z, vec.getX() * 0.025, 0, vec.getZ() * 0.025);
		}
	}
	
	@Override
	public void tickServer(){
		boolean lastActive = this.isActive;
		this.isActive = false;
		
		if(!getNonnullLevel().hasNeighborSignal(this.worldPosition)){
			if(this.fluidTick == 0){
				FluidStack fStack = this.tank.getFluid();
				fStack = fStack.copyWithAmount(FuelHandler.getGeneratorFuelUse(fStack.getFluid()));
				
				if(fStack.getAmount() > 0 && this.tank.getFluidAmount() >= fStack.getAmount()){
					this.tank.drain(fStack, FluidAction.EXECUTE);
					this.currentFlux = FuelHandler.getFluxGeneratedPerTick(fStack.getFluid());
					this.fluidTick = 20;
				}
			}
			
			if(this.fluidTick > 0){
				if(this.energyStorage.receiveEnergy(this.currentFlux, true) >= this.currentFlux){
					this.energyStorage.receiveEnergy(this.currentFlux, false);
					this.isActive = true;
					this.fluidTick--;
				}
			}
		}
		
		if(lastActive != this.isActive || this.isActive || this.wireType != null)
			setChanged();
		
	}
	
	@Override
	public void connectCable(WireType cableType, ConnectionPoint target, IImmersiveConnectable other, ConnectionPoint otherTarget){
		this.wireType = cableType;
		setChanged();
	}
	
	@Override
	public void removeCable(@Nullable Connection connection, ConnectionPoint attachedPoint){
		this.wireType = null;
		setChanged();
	}
	
	@Override
	public boolean canConnect(){
		return true;
	}
	
	@Override
	public boolean canConnectCable(WireType cableType, ConnectionPoint target, Vec3i offset){
		if(getNonnullLevel().getBlockState(target.position()).getBlock() != getNonnullLevel().getBlockState(getBlockPos()).getBlock())
			return false;
		
		return this.wireType == null && (cableType.getCategory().equals(WireType.LV_CATEGORY) || cableType.getCategory().equals(WireType.MV_CATEGORY));
	}
	
	@Override
	public BlockPos getConnectionMaster(@Nullable WireType cableType, TargetingInfo target){
		return this.worldPosition;
	}
	
	@Override
	public ConnectionPoint getTargetedPoint(TargetingInfo info, Vec3i offset){
		return new ConnectionPoint(this.worldPosition, 0);
	}
	
	@Override
	public Collection<ConnectionPoint> getConnectionPoints(){
		return List.of(new ConnectionPoint(this.worldPosition, 0));
	}
	
	@Override
	public BlockPos getPosition(){
		return this.worldPosition;
	}
	
	@Override
	public Vec3 getConnectionOffset(ConnectionPoint here, ConnectionPoint other, WireType type){
		float xo = this.facing.getNormal().getX() * .5f + .5f;
		float zo = this.facing.getNormal().getZ() * .5f + .5f;
		return new Vec3(xo, .5f, zo);
	}
	
	@Override
	public Collection<ResourceLocation> getRequestedHandlers(){
		return ImmutableList.of(EnergyTransferHandler.ID);
	}
}
