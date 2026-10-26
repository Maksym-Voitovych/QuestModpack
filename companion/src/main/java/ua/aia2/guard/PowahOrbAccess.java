package ua.aia2.guard;

import java.lang.reflect.Method;
import java.util.List;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.crafting.Recipe;
import net.minecraft.world.item.crafting.RecipeHolder;
import net.minecraft.world.item.crafting.RecipeInput;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.neoforged.neoforge.items.IItemHandler;

/** Authorize the receiving Orb, never the Rod/hopper currently calling it. */
public final class PowahOrbAccess {
    private record Access(Method inventory,Method buffer,Method contains) {}
    private static final ClassValue<Access> ACCESS=new ClassValue<>() {
        @Override protected Access computeValue(Class<?> type) {
            try { return new Access(type.getMethod("getInventory"),type.getMethod("getBuffer"),type.getMethod("containRecipe")); }
            catch (ReflectiveOperationException failure) { throw new IllegalStateException("Unsupported Powah6.2.10 Orb API",failure); }
        }
    };
    private static final ClassValue<Method> CAPACITY=new ClassValue<>() {
        @Override protected Method computeValue(Class<?> type) {
            try { return type.getMethod("getCapacity"); }
            catch (ReflectiveOperationException failure) { throw new IllegalStateException("Unsupported Powah energy API",failure); }
        }
    };
    public record Attempt(RecipeHolder<?> holder,String team,ItemStack output) {}
    private PowahOrbAccess() {}

    @SuppressWarnings("unchecked")
    public static Attempt begin(BlockEntity orb,RecipeHolder<?> cached) {
        if (!(orb.getLevel() instanceof ServerLevel level)) return null;
        var holder=EnderTaskAccess.resolve(cached,level);
        if (holder==null || !Aia2MachineGuard.mayProcessRecipe(orb,holder.value())) return null;
        try {
            var access=ACCESS.get(orb.getClass());
            if (!Boolean.TRUE.equals(access.contains().invoke(orb))) return null;
            Object buffer=access.buffer().invoke(orb);
            if (!(CAPACITY.get(buffer.getClass()).invoke(buffer) instanceof Number capacity) || capacity.longValue()<=0) return null;
            if (!(access.inventory().invoke(orb) instanceof IItemHandler inventory) || inventory.getSlots()!=7
                    || !inventory.getStackInSlot(0).isEmpty()) return null;
            boolean hasInput=false;
            for (int i=1;i<7;i++) hasInput|=!inventory.getStackInSlot(i).isEmpty();
            if (!hasInput) return null;
            RecipeInput input=new RecipeInput() {
                @Override public ItemStack getItem(int slot) { return inventory.getStackInSlot(slot).copy(); }
                @Override public int size() { return inventory.getSlots(); }
            };
            if (!((Recipe<RecipeInput>)holder.value()).matches(input,level)) return null;
            ItemStack output=holder.value().getResultItem(level.registryAccess()).copy();
            String team=Aia2MachineGuard.getOwner(orb);
            if (team.isBlank() || output.isEmpty() || !Aia2MachineGuard.mayProduce(orb,output)) return null;
            return new Attempt(holder,team,output);
        } catch (ReflectiveOperationException | RuntimeException unsupported) { return null; }
    }

    /** Inputs cleared and actual output inserted. Rod FE debit occurs after fillEnergy returns. */
    public static void finish(BlockEntity orb,Attempt attempt) {
        if (attempt==null || !attempt.team().equals(Aia2MachineGuard.getOwner(orb))) return;
        ItemStack observed;
        try {
            if (!(ACCESS.get(orb.getClass()).inventory().invoke(orb) instanceof IItemHandler inventory)) return;
            for (int i=1;i<inventory.getSlots();i++) if (!inventory.getStackInSlot(i).isEmpty()) return;
            ItemStack actual=inventory.getStackInSlot(0);
            if (actual.isEmpty() || actual.getCount()!=attempt.output().getCount()
                    || !ItemStack.isSameItemSameComponents(actual,attempt.output())) return;
            observed=actual.copy();
        } catch (ReflectiveOperationException | RuntimeException unsupported) { return; }
        // Storage/thread errors must remain visible; reflection failures alone fail closed.
        ProductionMilestoneBridge.finishedObservedMachine(orb,attempt.holder().value(),List.of(observed));
    }
}
