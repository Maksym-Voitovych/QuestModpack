package ua.aia2.guard;

import java.lang.reflect.InvocationTargetException;
import java.lang.reflect.Method;
import java.util.Collections;
import java.util.IdentityHashMap;
import java.util.Set;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.Container;
import net.minecraft.world.Containers;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.item.ItemEntity;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.crafting.Recipe;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.entity.BlockEntity;

/** Instant NASA operation witness. Never creates outputs, refunds or paid-history adoption. */
public final class NasaProductionAccess {
    private static final String MACHINE = "earth.terrarium.adastra.common.blockentities.machines.NasaWorkbenchBlockEntity";
    private static final ThreadLocal<Attempt> ACTIVE = new ThreadLocal<>();
    private static final ClassValue<Method> CRAFT = new ClassValue<>() {
        @Override protected Method computeValue(Class<?> type) {
            try { return type.getMethod("craft"); }
            catch (ReflectiveOperationException failure) { throw new IllegalStateException("Unsupported NASA craft entry", failure); }
        }
    };
    private static final class Attempt {
        final BlockEntity machine;
        final ServerLevel level;
        final Container inventory;
        final Recipe<?> recipe;
        final Object generation;
        final String team;
        final ItemStack output;
        final NasaIngredients.Snapshot ingredients;
        final ItemStack[] references = new ItemStack[14], before = new ItemStack[14];
        boolean permit = true, dropping, returned, committing, invalid;
        int drops, spawns, accepted, debits;
        ItemEntity entity;
        Attempt(BlockEntity machine) {
            this.machine = machine; this.level = (ServerLevel)machine.getLevel();
            this.inventory = (Container)machine;
            this.recipe = AdAstraNasaAccess.currentRecipe(machine);
            this.generation = level.getRecipeManager().getRecipes();
            this.team = Aia2MachineGuard.getOwner(machine);
            this.output = AdAstraNasaAccess.recipeOutput(recipe);
            this.ingredients = NasaIngredients.read(recipe);
            Set<ItemStack> unique = Collections.newSetFromMap(new IdentityHashMap<>());
            invalid = output.isEmpty() || output.getCount() != 1
                    || !ItemStack.isSameItemSameComponents(output, new ItemStack(output.getItem()));
            for (int slot = 0; slot < 14; slot++) {
                references[slot] = inventory.getItem(slot); before[slot] = references[slot].copy();
                invalid |= before[slot].isEmpty() || !unique.add(references[slot])
                        || !Aia2MachineGuard.mayProduce(machine, before[slot]);
            }
            invalid |= ingredients == null || !ingredients.matches(before);
        }
    }
    private NasaProductionAccess() {}

    /** A one-shot permit admits only the wrapper's reflected native call; nested callbacks do not borrow it. */
    public static boolean enterNative(BlockEntity machine) {
        if (machine == null || machine.getLevel() == null) return false;
        if (machine.getLevel().isClientSide() || !machine.getClass().getName().equals(MACHINE))
            return AdAstraNasaAccess.mayFinish(machine); // preserve guarded unknown subclasses, without proof
        Attempt attempt = ACTIVE.get();
        if (attempt == null || attempt.machine != machine || !attempt.permit) return false;
        attempt.permit = false; return true;
    }

    public static void craft(BlockEntity machine) {
        Attempt active = ACTIVE.get();
        if (active != null) { active.invalid = true; return; }
        if (!AdAstraNasaAccess.mayFinish(machine)
                || !machine.getClass().getName().equals(MACHINE)) return;
        Attempt attempt = new Attempt(machine);
        // Unsupported/corrupt inputs are rejected before native particles,
        // world output or payment. Existing reviewed four-rocket recipes fit this contract.
        if (attempt.invalid) return;
        ACTIVE.set(attempt);
        try {
            CRAFT.get(machine.getClass()).invoke(machine);
            attempt.returned = true;
            if (finished(attempt)) {
                attempt.committing = true;
                ProductionMilestoneBridge.finishedNasa(machine, attempt.recipe, attempt.team, attempt.output);
            }
        } catch (InvocationTargetException nativeFailure) {
            Throwable cause = nativeFailure.getCause();
            if (cause instanceof RuntimeException failure) throw failure;
            if (cause instanceof Error failure) throw failure;
            throw new IllegalStateException("Native NASA craft failed", cause);
        } catch (ReflectiveOperationException failure) {
            throw new IllegalStateException("Cannot invoke native NASA craft", failure);
        } finally { ACTIVE.remove(); }
    }

    private static boolean live(Attempt a) {
        boolean valid = AdAstraNasaAccess.canonicalMachine(a.machine) && a.machine.getLevel() == a.level
                && a.generation == a.level.getRecipeManager().getRecipes()
                && a.team.equals(Aia2MachineGuard.getOwner(a.machine))
                && Aia2MachineGuard.mayProcessRecipe(a.machine, a.recipe)
                && Aia2MachineGuard.mayProduce(a.machine, a.output)
                && exact(a.output, AdAstraNasaAccess.recipeOutput(a.recipe))
                && a.ingredients != null && a.ingredients.equals(NasaIngredients.read(a.recipe));
        if (!valid) return false;
        for (ItemStack input : a.before) if (!Aia2MachineGuard.mayProduce(a.machine, input)) return false;
        return true;
    }
    private static boolean slot(Attempt a, int index, int count) {
        ItemStack current = a.inventory.getItem(index);
        return current == a.references[index] && current.getCount() == count
                && (count == 0 ? current.isEmpty() : ItemStack.isSameItemSameComponents(current, a.before[index]));
    }
    private static boolean unpaid(Attempt a) {
        for (int index = 0; index < 14; index++) if (!slot(a, index, a.before[index].getCount())) return false;
        return true;
    }
    private static boolean exact(ItemStack left, ItemStack right) {
        return !left.isEmpty() && !right.isEmpty() && left.getCount() == right.getCount()
                && ItemStack.isSameItemSameComponents(left, right);
    }

    /** Wrap only the exact native drop invocation; ordinary Containers calls remain native. */
    public static void drop(BlockEntity machine, Level level, double x, double y, double z, ItemStack stack) {
        Attempt a = ACTIVE.get();
        if (a == null || a.machine != machine) { Containers.dropItemStack(level, x, y, z, stack); return; }
        a.drops++;
        a.invalid |= a.drops != 1 || a.debits != 0 || a.dropping || !live(a) || !unpaid(a)
                || AdAstraNasaAccess.currentRecipe(machine) != a.recipe || level != a.level
                || x != machine.getBlockPos().getX() || y != machine.getBlockPos().getY() + 1
                || z != machine.getBlockPos().getZ() || !exact(stack, a.output);
        a.dropping = true;
        try { Containers.dropItemStack(level, x, y, z, stack); }
        finally { a.dropping = false; }
    }

    /** Observes the actual native addFreshEntity return and retained world identity. */
    public static boolean spawn(Level level, Entity entity) {
        Attempt a = ACTIVE.get();
        if (a == null || !a.dropping) return level.addFreshEntity(entity);
        a.spawns++;
        ItemStack before = entity instanceof ItemEntity item ? item.getItem().copy() : ItemStack.EMPTY;
        boolean candidate = !a.invalid && a.spawns == 1 && level == a.level
                && entity.level() == level && entity instanceof ItemEntity && exact(before, a.output)
                && live(a) && unpaid(a);
        boolean accepted = level.addFreshEntity(entity);
        if (candidate && accepted && entity instanceof ItemEntity item && !entity.isRemoved()
                && a.level.getEntity(entity.getUUID()) == entity && exact(item.getItem(), before)
                && live(a) && unpaid(a)) {
            a.entity = item; a.accepted++;
        } else a.invalid = true;
        return accepted;
    }

    /** Each native shrink must pay the next original slot, exactly once and exactly one unit. */
    public static void shrink(BlockEntity machine, ItemStack stack, int amount) {
        Attempt a = ACTIVE.get();
        if (a == null || a.machine != machine) { stack.shrink(amount); return; }
        int index = a.debits++;
        boolean before = !a.invalid && index < 14 && amount == 1 && a.accepted == 1
                && stack == a.references[index] && slot(a, index, a.before[index].getCount()) && live(a);
        stack.shrink(amount);
        if (!before || !slot(a, index, a.before[index].getCount() - 1)) a.invalid = true;
    }

    private static boolean finished(Attempt a) {
        if (a.invalid || !a.returned || a.permit || a.dropping || a.drops != 1 || a.spawns != 1
                || a.accepted != 1 || a.debits != 14 || !live(a) || !a.inventory.getItem(14).isEmpty()
                || AdAstraNasaAccess.currentRecipe(a.machine) != null || a.entity == null
                || a.entity.isRemoved() || a.level.getEntity(a.entity.getUUID()) != a.entity
                || !exact(a.entity.getItem(), a.output)) return false;
        for (int slot = 0; slot < 14; slot++) if (!slot(a, slot, a.before[slot].getCount() - 1)) return false;
        return true;
    }
    static boolean isCommitting(BlockEntity machine, Recipe<?> recipe, String team, ItemStack output) {
        Attempt a = ACTIVE.get();
        return a != null && a.committing && a.machine == machine && a.recipe == recipe
                && a.team.equals(team) && exact(output, a.output) && finished(a);
    }
}
