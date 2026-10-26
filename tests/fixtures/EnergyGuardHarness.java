package ua.aia2.guard.mixin;

import java.lang.reflect.*;
import java.util.*;
import com.google.gson.JsonObject;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.crafting.*;
import net.minecraft.resources.ResourceLocation;
import org.spongepowered.asm.mixin.injection.callback.*;
import ua.aia2.guard.*;
import net.neoforged.neoforge.items.IItemHandler;

/** Production helpers/handlers in a modeled host; no optional mod dispatch. */
public final class EnergyGuardHarness {
    static int checks;
    static ServerLevel world=new ServerLevel();
    static void check(boolean ok,String label){checks++;if(!ok)throw new AssertionError(label);}
    static Method hook(Class<?> owner,String name,Class<?>... args)throws Exception{var m=owner.getDeclaredMethod(name,args);m.setAccessible(true);return m;}
    static void field(Class<?> owner,Object host,String key,Object value)throws Exception{var f=owner.getDeclaredField(key);f.setAccessible(true);f.set(host,value);}
    static Object field(Class<?> owner,Object host,String key)throws Exception{var f=owner.getDeclaredField(key);f.setAccessible(true);return f.get(host);}
    static BaseRecipe recipe(String id){var r=new BaseRecipe(new JsonObject());r.output=new ItemStack(id);return r;}
    static RecipeHolder<?> install(String id,BaseRecipe r,int stage){var holder=new RecipeHolder<>(ResourceLocation.parse(id),r);world.recipes.rows.put(holder.id(),holder);world.recipes.generation=new Object();Aia2MachineGuard.index.put(r,stage);return holder;}
    public record NativeOutput(ItemStack stack){public ItemStack getItem(){return stack;}}
    static final Method TASK_HEAD,OUTPUTS,COMPLETE,CRAFT,QUEUE,CRAFT_RESULT,TANK,ORB_HEAD,ORB_OUTPUT,ORB_RETURN;
    static {try{
        TASK_HEAD=hook(EnderCraftingTaskMixin.class,"aia2$guardTask",CallbackInfo.class);
        OUTPUTS=hook(EnderCraftingTaskMixin.class,"aia2$guardDeterminedOutputs",CallbackInfo.class);
        COMPLETE=hook(EnderCraftingTaskMixin.class,"aia2$observeCompletion",CallbackInfo.class);
        CRAFT=hook(EnderCrafterMixin.class,"aia2$guardCraft",CallbackInfo.class);
        QUEUE=hook(EnderCrafterMixin.class,"aia2$guardQueue",CallbackInfo.class);
        CRAFT_RESULT=hook(EnderCrafterMixin.class,"aia2$useValidatedResult",CraftingRecipe.class,RecipeInput.class,net.minecraft.core.HolderLookup.Provider.class);
        TANK=hook(EnderTankMixin.class,"aia2$guardCachedTank",CallbackInfo.class);
        ORB_HEAD=hook(PowahEnergizingOrbMixin.class,"aia2$guardReceiver",long.class,CallbackInfoReturnable.class);
        ORB_OUTPUT=hook(PowahEnergizingOrbMixin.class,"aia2$observeBatch",long.class,CallbackInfoReturnable.class);
        ORB_RETURN=hook(PowahEnergizingOrbMixin.class,"aia2$releaseAttempt",long.class,CallbackInfoReturnable.class);
    }catch(Exception failure){throw new ExceptionInInitializerError(failure);}}

    public static class Task extends EnderCraftingTaskMixin implements BlockEntity {
        String team="a";int inputs=1,energy=100,produced;
        public Object getLevel(){return world;}public String owner(){return team;}
        Task(RecipeHolder<?> holder,ItemStack output)throws Exception{field(EnderCraftingTaskMixin.class,this,"recipe",holder);field(EnderCraftingTaskMixin.class,this,"outputs",List.of(new NativeOutput(output)));}
        boolean tick()throws Exception{
            var parent=Aia2MachineGuard.enterTick(this);
            try{
                var cb=new CallbackInfo();TASK_HEAD.invoke(this,cb);if(cb.canceled)return false;
                if((boolean)field(EnderCraftingTaskMixin.class,this,"isComplete"))return false;
                OUTPUTS.invoke(this,cb);if(cb.canceled)return false;
                energy--;produced++;inputs--;COMPLETE.invoke(this,cb);field(EnderCraftingTaskMixin.class,this,"isComplete",true);return true;
            }finally{Aia2MachineGuard.exitTick(parent);}
        }
    }
    public static class Crafter extends EnderCrafterMixin implements BlockEntity {
        public static final Object INPUT=new Object();public final CraftingInput input=new CraftingInput();String team="a";Queue<ItemStack> queue=new ArrayDeque<>();
        public Object getLevel(){return world;}public String owner(){return team;}
        private CraftingInput getCraftingInput(Object slots){return input;}
        Crafter(RecipeHolder<?> holder)throws Exception{field(EnderCrafterMixin.class,this,"recipe",holder);field(EnderCrafterMixin.class,this,"outputBuffer",queue);}
        boolean permit()throws Exception{var cb=new CallbackInfo();CRAFT.invoke(this,cb);return !cb.canceled;}
    }
    public static class Tank extends EnderTankMixin implements BlockEntity {
        String team="a";public Object getLevel(){return world;}public String owner(){return team;}
        Tank(RecipeHolder<?> holder)throws Exception{field(EnderTankMixin.class,this,"currentRecipe",Optional.of(holder));}
    }
    public static class Inventory implements IItemHandler {
        final ItemStack[] slots=new ItemStack[7];Inventory(){Arrays.fill(slots,ItemStack.EMPTY);slots[1]=new ItemStack("minecraft:blaze_rod");}
        public int getSlots(){return 7;}public ItemStack getStackInSlot(int n){return slots[n];}
    }
    public static class Buffer {public long capacity=100,stored;public long getCapacity(){return capacity;}}
    public static class Orb extends PowahEnergizingOrbMixin implements BlockEntity {
        String team="b";boolean contains=true;final Inventory inventory=new Inventory();final Buffer buffer=new Buffer();
        public Object getLevel(){return world;}public String owner(){return team;}public Inventory getInventory(){return inventory;}public Buffer getBuffer(){return buffer;}public boolean containRecipe(){return contains;}
        Orb(RecipeHolder<?> holder)throws Exception{field(PowahEnergizingOrbMixin.class,this,"recipe",holder);}
        long fill(long amount)throws Exception{
            var cb=new CallbackInfoReturnable<Long>();ORB_HEAD.invoke(this,amount,cb);if(cb.canceled)return cb.getReturnValue();
            var holder=(RecipeHolder<?>)field(PowahEnergizingOrbMixin.class,this,"recipe");var output=holder.value().getResultItem(world.registryAccess()).copy();
            long received=Math.min(buffer.capacity-buffer.stored,amount);buffer.stored+=received;
            if(buffer.stored>=buffer.capacity){Arrays.fill(inventory.slots,ItemStack.EMPTY);contains=false;field(PowahEnergizingOrbMixin.class,this,"recipe",null);inventory.slots[0]=output;ORB_OUTPUT.invoke(this,amount,cb);buffer.capacity=0;buffer.stored=0;}
            ORB_RETURN.invoke(this,amount,cb);return received;
        }
    }
    public static void main(String[] args)throws Exception{
        var p=Aia2MachineGuard.policy;p.setRules(Map.of("enderio:alloy_smelter",19));p.setTeamProgress("a",18);p.setTeamProgress("b",28);p.setReady();
        Aia2MachineGuard.items.put("enderio:energetic_alloy_ingot",19);Aia2MachineGuard.items.put("future:crystal",36);Aia2MachineGuard.items.put("powah:crystal_blazing",29);
        var alloyTemplate=new com.enderio.enderio.content.machines.alloy.AlloySmeltingRecipe();check(EnderTaskAccess.template(alloyTemplate,world).item.id.equals("enderio:energetic_alloy_ingot"),"reviewed static alloy accessor supports empty Minecraft template");var original=new ItemStack("minecraft:iron_ingot");var copied=EnderTaskAccess.copyItems(List.of(new NativeOutput(original)));original.count=3;check(copied.getFirst().count==1,"actual output snapshot is copied before native mutation");
        var low=recipe("enderio:energetic_alloy_ingot");var lowHolder=install("enderio:alloy",low,19);var late=recipe("future:crystal");var lateHolder=install("future:recipe",late,36);
        var denied=new Task(lateHolder,late.output);check(!denied.tick(),"future cached task denied");check(denied.inputs==1&&denied.energy==100&&denied.produced==0,"no inputs FE or output touched");check(ProductionMilestoneBridge.observations==0,"denial no receipt");
        var task=new Task(lowHolder,low.output);check(task.tick(),"authorized cached task");check(task.inputs==0&&task.energy==99&&task.produced==1,"one native modeled completion");check(ProductionMilestoneBridge.observations==1&&"a".equals(ProductionMilestoneBridge.recipient),"completion owner receipt after consumption");check(!task.tick()&&ProductionMilestoneBridge.observations==1,"completed task never recredits");
        var staleOutput=new Task(lowHolder,new ItemStack("future:crystal"));check(!staleOutput.tick()&&staleOutput.energy==100,"saved actual outputs independently gated before FE");
        var creative=new ItemStack("enderio:energetic_alloy_ingot");creative.creative=true;check(!new Task(lowHolder,creative).tick(),"component variant is gated");
        var same=recipe("enderio:energetic_alloy_ingot");var sameHolder=install("enderio:alloy",same,19);Aia2MachineGuard.index.remove(low);var reload=new Task(lowHolder,low.output);check(reload.tick(),"unchanged complete codec rebind works");check(((RecipeHolder<?>)field(EnderCraftingTaskMixin.class,reload,"recipe")).value()==same,"current canonical object installed");
        var changed=recipe("enderio:energetic_alloy_ingot");changed.data.addProperty("new_cost",2);install("enderio:alloy",changed,19);var paused=new Task(sameHolder,same.output);paused.energy=41;check(!paused.tick()&&paused.energy==41&&paused.inputs==1,"changed paid task pauses without deleting progress");
        var craft=new Crafter(lateHolder);check(!craft.permit(),"Crafter cached future recipe denied before clearInput");check(craft.input.input.count==1,"crafter input preserved");
        var craftLow=install("example:craft",recipe("enderio:energetic_alloy_ingot"),19);craft=new Crafter(craftLow);check(craft.permit(),"authorized real-input craft plan");var result=(ItemStack)CRAFT_RESULT.invoke(craft,null,craft.input,world.registryAccess());check(result.item.id.equals("enderio:energetic_alloy_ingot"),"validated result replayed");
        var hiddenFuture=recipe("future:crystal");var hiddenHolder=install("example:dynamic",hiddenFuture,19);check(!new Crafter(hiddenHolder).permit(),"actual assembled future output denied despite early recipe gate");
        craft.queue.add(new ItemStack("future:crystal"));var cb=new CallbackInfo();QUEUE.invoke(craft,cb);check(cb.canceled&&craft.queue.size()==1,"queued future output paused without deletion");
        var tank=new Tank(lateHolder);cb=new CallbackInfo();TANK.invoke(tank,cb);check(cb.canceled,"tank callback cache future recipe denied");
        var crystal=recipe("powah:crystal_blazing");var crystalHolder=install("powah:crystal",crystal,29);var orb=new Orb(crystalHolder);orb.team="a";var rod=new Task(lowHolder,low.output);rod.team="b";Aia2MachineGuard.context=rod;
        check(orb.fill(100)==0,"advanced rod cannot authorize locked receiving orb");check(orb.inventory.slots[1].count==1&&orb.inventory.slots[0].isEmpty()&&orb.buffer.stored==0,"denied orb preserves materials buffer and output");
        rod.team="a";orb=new Orb(crystalHolder);int prior=ProductionMilestoneBridge.observations;check(orb.fill(100)==100,"authorized orb can receive from lower-stage caller");check(ProductionMilestoneBridge.observations==prior+1&&"b".equals(ProductionMilestoneBridge.recipient),"proof belongs to orb not rod");check(ProductionMilestoneBridge.completed==crystal,"original holder retained across clear callbacks");check(orb.inventory.slots[0].item.id.equals("powah:crystal_blazing")&&orb.inventory.slots[1].isEmpty(),"native modeled input clear/output insert");check(orb.fill(100)==0,"stale holder/empty buffer cannot clone output");
        var partial=new Orb(crystalHolder);int beforePartial=ProductionMilestoneBridge.observations;check(partial.fill(40)==40&&partial.inventory.slots[1].count==1,"partial charge retains materials");check(ProductionMilestoneBridge.observations==beforePartial,"partial energy charge never grants a receipt");check(partial.fill(60)==60&&ProductionMilestoneBridge.observations==beforePartial+1,"final charge completes one actual-output observation");crystal.matching=false;check(new Orb(crystalHolder).fill(100)==0,"cached recipe must still match actual inputs");crystal.matching=true;
        orb=new Orb(crystalHolder);orb.contains=false;check(orb.fill(100)==0,"false containRecipe rejected");orb.contains=true;orb.buffer.capacity=0;check(orb.fill(100)==0,"zero capacity rejected");orb=new Orb(crystalHolder);orb.inventory.slots[0]=new ItemStack("minecraft:stone");check(orb.fill(100)==0,"occupied output cannot be erased");orb=new Orb(crystalHolder);check(orb.fill(-1)==0,"negative transfer rejected");orb.team="";check(orb.fill(100)==0,"ownerless orb denied");
        world.recipes.rows.clear();world.recipes.rows.put(crystalHolder.id(),crystalHolder);var receiver=new Orb(crystalHolder);receiver.team="a";Aia2MachineGuard.context=rod;rod.team="b";var lookup=EnderTaskAccess.lookup(receiver,world.recipes,new RecipeType<>(),new RecipeInput(){},world);check(lookup.isPresent(),"pure selection is independent of caller or receiver stage");check(receiver.fill(100)==0,"selected future recipe cannot execute on a locked receiver");check(Aia2MachineGuard.context==rod,"outer ticker context restored");
        world.recipes.throwLookup=true;try{EnderTaskAccess.lookup(receiver,world.recipes,new RecipeType<>(),new RecipeInput(){},world);throw new AssertionError("expected lookup failure");}catch(IllegalStateException expected){}check(Aia2MachineGuard.context==rod,"exception restores caller context");world.recipes.throwLookup=false;
        p.clear();check(EnderTaskAccess.lookup(receiver,world.recipes,new RecipeType<>(),new RecipeInput(){},world).isPresent(),"startup can select without poisoning callback cache");check(new Orb(crystalHolder).fill(100)==0,"unready runtime still cannot execute");
        System.out.println("EnergyGuardHarness: "+checks+" actual-helper/handler/real-policy assertions; real DFU/Gson, modeled native host, no optional dispatch");
    }
}
