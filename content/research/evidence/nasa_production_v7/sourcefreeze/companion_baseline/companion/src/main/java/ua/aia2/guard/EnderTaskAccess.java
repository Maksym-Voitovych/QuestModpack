package ua.aia2.guard;

import com.mojang.serialization.JsonOps;
import com.mojang.serialization.MapCodec;
import java.lang.reflect.Method;
import java.util.ArrayList;
import java.util.IdentityHashMap;
import java.util.List;
import net.minecraft.resources.RegistryOps;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.crafting.CraftingInput;
import net.minecraft.world.item.crafting.Recipe;
import net.minecraft.world.item.crafting.RecipeHolder;
import net.minecraft.world.item.crafting.RecipeInput;
import net.minecraft.world.item.crafting.RecipeManager;
import net.minecraft.world.item.crafting.RecipeType;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.entity.BlockEntity;

/** Exact EnderIO task APIs; never rerolls saved SAG outputs or guesses a player. */
public final class EnderTaskAccess {
    private record Comparison(Recipe<?> current, boolean equal) {}
    private static Object generation;
    private static final IdentityHashMap<Recipe<?>, Comparison> REBINDS = new IdentityHashMap<>();
    private static final ClassValue<Method> ITEM = new ClassValue<>() {
        @Override protected Method computeValue(Class<?> type) {
            try { return type.getMethod("getItem"); }
            catch (ReflectiveOperationException failure) { throw new IllegalStateException("Unsupported EnderIO OutputStack",failure); }
        }
    };
    private record CrafterInput(Method input, Object slots) {}
    private static final ClassValue<CrafterInput> CRAFTER_INPUT = new ClassValue<>() {
        @Override protected CrafterInput computeValue(Class<?> type) {
            try {
                var field=type.getField("INPUT");
                for (Class<?> owner=type;owner!=null;owner=owner.getSuperclass()) {
                    try {
                        var method=owner.getDeclaredMethod("getCraftingInput",field.getType());
                        method.setAccessible(true);return new CrafterInput(method,field.get(null));
                    } catch (NoSuchMethodException next) { /* Find exact inherited owner. */ }
                }
                throw new NoSuchMethodException("getCraftingInput");
            } catch (ReflectiveOperationException failure) { throw new IllegalStateException("Unsupported EnderIO Crafter",failure); }
        }
    };
    public record CraftPlan(ItemStack output, List<ItemStack> remaining) {}
    private EnderTaskAccess() {}

    public static <I extends RecipeInput,T extends Recipe<I>> java.util.Optional<RecipeHolder<T>> lookup(
            BlockEntity owner,RecipeManager manager,RecipeType<T> type,I input,Level world) {
        // These three receivers have mandatory execution guards below. Selection
        // must remain pure: rejecting it during startup/stage unlock would leave
        // their one-shot callback caches empty forever. Neither a hopper's nor
        // an unready receiver's policy may poison the selected recipe cache.
        if (owner==null) throw new IllegalArgumentException("Missing protected recipe receiver");
        var parent=Aia2MachineGuard.enterTick(null);
        try { return manager.getRecipeFor(type,input,world); }
        finally { Aia2MachineGuard.exitTick(parent); }
    }

    /** Only source-reviewed static output accessors supplement Minecraft's empty template. */
    public static ItemStack template(Recipe<?> recipe,ServerLevel level) {
        ItemStack result=recipe.getResultItem(level.registryAccess());
        if (!result.isEmpty()) return result;
        String type=recipe.getClass().getName();
        if (!type.equals("com.enderio.enderio.content.machines.alloy.AlloySmeltingRecipe")
                && !type.equals("com.enderio.enderio.content.machines.tank.TankRecipe")) return ItemStack.EMPTY;
        try {
            Object output=recipe.getClass().getMethod("output").invoke(recipe);
            return output instanceof ItemStack stack?stack:ItemStack.EMPTY;
        } catch (ReflectiveOperationException | RuntimeException unsupported) { return ItemStack.EMPTY; }
    }

    /** Same-ID reload is accepted only when complete codec semantics are unchanged. */
    @SuppressWarnings("unchecked")
    public static synchronized RecipeHolder<?> resolve(RecipeHolder<?> old, ServerLevel level) {
        if (old==null || level==null) return null;
        var snapshot=level.getRecipeManager().getRecipes();
        if (generation!=snapshot) { REBINDS.clear();generation=snapshot; }
        var current=level.getRecipeManager().byKey(old.id()).orElse(null);
        if (current==null) return null;
        if (old.value()==current.value()) return current;
        var before=old.value();var after=current.value();
        if (before.getClass()!=after.getClass() || before.getType()!=after.getType() || before.getSerializer()!=after.getSerializer()) return null;
        var previous=REBINDS.get(before);
        if (previous!=null && previous.current()==after) return previous.equal()?current:null;
        boolean same=false;
        try {
            var ops=RegistryOps.create(JsonOps.INSTANCE,level.registryAccess());
            var codec=((MapCodec<Recipe<?>>)(MapCodec<?>)before.getSerializer().codec()).codec();
            var a=codec.encodeStart(ops,before).result().orElse(null);
            var b=codec.encodeStart(ops,after).result().orElse(null);
            same=a!=null && a.equals(b);
        } catch (RuntimeException unsupported) { /* Preserve paused progress. */ }
        REBINDS.put(before,new Comparison(after,same));
        return same?current:null;
    }

    public static synchronized void clearRuntime() { generation=null;REBINDS.clear(); }

    public static List<ItemStack> copyItems(List<?> nativeOutputs) {
        if (nativeOutputs==null) return null;
        var result=new ArrayList<ItemStack>();
        try {
            for (Object output:nativeOutputs) {
                if (output==null || !(ITEM.get(output.getClass()).invoke(output) instanceof ItemStack stack)) return null;
                if (!stack.isEmpty()) result.add(stack.copy());
            }
            return List.copyOf(result);
        } catch (ReflectiveOperationException | RuntimeException unsupported) { return null; }
    }

    public static boolean mayOutput(BlockEntity machine,List<ItemStack> items) {
        if (machine==null || items==null) return false;
        for (ItemStack item:items) if (!Aia2MachineGuard.mayProduce(machine,item)) return false;
        return true;
    }

    @SuppressWarnings("unchecked")
    public static CraftPlan prepareCrafter(BlockEntity machine,RecipeHolder<?> holder) {
        if (!(machine.getLevel() instanceof ServerLevel level) || holder==null || !Aia2MachineGuard.mayProcessRecipe(machine,holder.value())) return null;
        try {
            var access=CRAFTER_INPUT.get(machine.getClass());
            if (!(access.input().invoke(machine,access.slots()) instanceof CraftingInput input)) return null;
            var recipe=(Recipe<CraftingInput>)holder.value();
            if (!recipe.matches(input,level)) return null;
            ItemStack result=recipe.assemble(input,level.registryAccess()).copy();
            if (result.isEmpty() || !Aia2MachineGuard.mayProduce(machine,result)) return null;
            var remaining=new ArrayList<ItemStack>();
            for (ItemStack stack:recipe.getRemainingItems(input)) {
                if (!stack.isEmpty() && !Aia2MachineGuard.mayProduce(machine,stack)) return null;
                remaining.add(stack.copy());
            }
            return new CraftPlan(result,List.copyOf(remaining));
        } catch (ReflectiveOperationException | RuntimeException unsupported) { return null; }
    }
}
