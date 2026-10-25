package flaxbeard.immersivepetroleum.common.items;

import flaxbeard.immersivepetroleum.api.crafting.LubricantHandler;
import flaxbeard.immersivepetroleum.api.crafting.LubricatedHandler;
import flaxbeard.immersivepetroleum.common.util.Utils;
import net.minecraft.ChatFormatting;
import net.minecraft.core.BlockPos;
import net.minecraft.network.chat.Component;
import net.minecraft.network.chat.MutableComponent;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.animal.IronGolem;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.TooltipFlag;
import net.minecraft.world.item.context.UseOnContext;
import net.minecraft.world.level.Level;
import net.neoforged.neoforge.capabilities.Capabilities;
import net.neoforged.neoforge.fluids.FluidStack;
import net.neoforged.neoforge.fluids.FluidUtil;
import net.neoforged.neoforge.fluids.capability.IFluidHandler;
import net.neoforged.neoforge.fluids.capability.IFluidHandler.FluidAction;
import net.neoforged.neoforge.fluids.capability.IFluidHandlerItem;
import net.neoforged.neoforge.fluids.capability.templates.FluidHandlerItemStack;
import org.jetbrains.annotations.NotNull;

import javax.annotation.Nonnull;
import java.util.List;

public class OilCanItem extends IPItemBase{
	public OilCanItem(){
		super(new Item.Properties().stacksTo(1));
	}
	
	@Override
	public void appendHoverText(@Nonnull ItemStack stack, @Nonnull TooltipContext ctx, @Nonnull List<Component> tooltip, @Nonnull TooltipFlag flag){
		FluidUtil.getFluidContained(stack).ifPresent(fluid -> {
			if(!fluid.isEmpty() && fluid.getAmount() > 0){
				Component out = ((MutableComponent) fluid.getHoverName())
						.append(Component.literal(": " + fluid.getAmount() + "/8000mB")).withStyle(ChatFormatting.GRAY);
				tooltip.add(out);
			}else{
				tooltip.add(Component.translatable("gui.immersivepetroleum.empty"));
			}
		});
	}
	
	@Override
	@Nonnull
	public InteractionResult useOn(UseOnContext context){
		if(context.getPlayer() == null)
			return InteractionResult.PASS;
		
		Level level = context.getLevel();
		if(level.isClientSide)
			return InteractionResult.PASS;
		
		ItemStack stack = context.getItemInHand();
		Player player = context.getPlayer();
		InteractionHand hand = context.getHand();
		BlockPos pos = context.getClickedPos();
		
		IFluidHandler handler = level.getCapability(Capabilities.FluidHandler.BLOCK, pos, null);
		if(handler == null || !FluidUtil.interactWithFluidHandler(player, hand, handler)){
			return FluidUtil.getFluidHandler(stack)
				.map(h -> tryLubricateMachine(level, pos, player, h))
				.orElse(InteractionResult.PASS);
		}
		
		return InteractionResult.PASS;
	}
	
	private InteractionResult tryLubricateMachine(Level level, BlockPos pos, Player player, @NotNull IFluidHandlerItem handler){
		if(!(handler instanceof FluidHandlerItemStack can))
			return InteractionResult.PASS;
		
		FluidStack fs = can.getFluid();
		
		if(!fs.isEmpty() && LubricantHandler.isValidLube(fs.getFluid())){
			int amountNeeded = (LubricantHandler.getLubeAmount(fs.getFluid()) * 5 * 20);
			
			if(fs.getAmount() >= amountNeeded && LubricatedHandler.lubricateTile(level, pos, fs.getFluid(), 600)){ // 30 Seconds
				player.playSound(SoundEvents.BUCKET_EMPTY, 1F, 1F);
				
				if(!player.isCreative())
					can.drain(amountNeeded, FluidAction.EXECUTE);
				
				Utils.unlockIPAdvancement(player, "main/oil_can");
				return InteractionResult.SUCCESS;
			}
		}
		
		return InteractionResult.PASS;
	}
	
	@Override
	public boolean hurtEnemy(@Nonnull ItemStack stack, @Nonnull LivingEntity target, @Nonnull LivingEntity attacker){
		this.interactLivingEntity(stack, null, target, InteractionHand.MAIN_HAND);
		return true;
	}
	
	@Override
	@Nonnull
	public InteractionResult interactLivingEntity(@Nonnull ItemStack stack, @Nonnull Player player, @Nonnull LivingEntity target, @Nonnull InteractionHand hand){
		if(!(target instanceof IronGolem golem))
			return InteractionResult.FAIL;
		
		FluidUtil.getFluidHandler(stack).ifPresent(con -> {
			if(con instanceof FluidHandlerItemStack handler){
				
				if(!handler.getFluid().isEmpty() && LubricantHandler.isValidLube(handler.getFluid().getFluid())){
					int amountNeeded = (LubricantHandler.getLubeAmount(handler.getFluid().getFluid()) * 5 * 20);
					if(handler.getFluid().getAmount() >= amountNeeded){
						player.playSound(SoundEvents.BUCKET_EMPTY, 1F, 1F);
						golem.setHealth(Math.max(golem.getHealth() + 2F, golem.getMaxHealth()));
						golem.addEffect(new MobEffectInstance(MobEffects.MOVEMENT_SPEED, 1200, 1)); // 1 Minute
						golem.addEffect(new MobEffectInstance(MobEffects.DAMAGE_BOOST, 1200, 1)); // 1 Minute
						if(!player.isCreative()){
							handler.drain(amountNeeded, FluidAction.EXECUTE);
						}
					}
				}
			}
		});
		
		return InteractionResult.SUCCESS;
	}
}
