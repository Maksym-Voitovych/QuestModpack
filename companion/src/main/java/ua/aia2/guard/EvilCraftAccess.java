package ua.aia2.guard;

import java.lang.reflect.InvocationTargetException;
import java.lang.reflect.Method;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.SpawnEggItem;
import net.minecraft.world.item.crafting.Recipe;
import net.minecraft.world.level.block.entity.BlockEntity;

/** Source-reviewed EvilCraft 1.2.99 infusion and direct spirit outputs. */
public final class EvilCraftAccess {
    private static final ClassValue<Method> ENTITY_TYPE = new ClassValue<>() {
        @Override protected Method computeValue(Class<?> type) {
            try { return type.getMethod("getEntityType"); }
            catch (ReflectiveOperationException failure) {
                throw new IllegalStateException("Unsupported EvilCraft Spirit Reanimator", failure);
            }
        }
    };
    private EvilCraftAccess() {}

    private static boolean canonical(BlockEntity owner) {
        return owner != null && owner.getLevel() instanceof ServerLevel level && !owner.isRemoved()
                && level.getServer().isSameThread() && level.hasChunkAt(owner.getBlockPos())
                && level.getBlockEntity(owner.getBlockPos()) == owner && Aia2MachineGuard.isReady();
    }

    /** Native raw SingleCache is untouched; a denied view cannot poison stage unlock. */
    public static boolean mayInfuse(BlockEntity owner, Recipe<?> recipe) {
        if (owner == null || recipe == null || owner.getLevel() == null) return false;
        if (owner.getLevel().isClientSide()) return true;
        if (!canonical(owner) || !Aia2MachineGuard.mayProcessRecipe(owner, recipe)) return false;
        return mayOutput(owner, recipe.getResultItem(((ServerLevel)owner.getLevel()).registryAccess()));
    }

    /** Loot and spawn-egg copying never substitutes for manufacturing a key. */
    public static boolean mayOutput(BlockEntity owner, ItemStack output) {
        if (owner == null || owner.getLevel() == null || output == null || output.isEmpty()) return false;
        if (owner.getLevel().isClientSide()) return true;
        if (!canonical(owner)) return false;
        String id = BuiltInRegistries.ITEM.getKey(output.getItem()).toString();
        if (id.matches("kubejs:aia2_(tech|arcane|epoch)_key_[0-9]{2}") || KeyProductionBridge.isKeyOutput(id)) return false;
        return Aia2MachineGuard.mayProduce(owner, output);
    }

    /** Called before native blood drain, egg consumption or destructive box clearing. */
    public static boolean mayReanimate(BlockEntity owner) {
        if (owner == null || owner.getLevel() == null) return false;
        if (owner.getLevel().isClientSide()) return true;
        if (!canonical(owner)) return false;
        try {
            Object nativeType = ENTITY_TYPE.get(owner.getClass()).invoke(owner);
            if (!(nativeType instanceof EntityType<?> type)) return false;
            SpawnEggItem egg = SpawnEggItem.byId(type);
            return egg != null && mayOutput(owner, new ItemStack(egg));
        } catch (InvocationTargetException nativeFailure) {
            Throwable cause = nativeFailure.getCause();
            if (cause instanceof RuntimeException failure) throw failure;
            if (cause instanceof Error failure) throw failure;
            throw new IllegalStateException("EvilCraft reanimation output lookup failed", cause);
        } catch (ReflectiveOperationException failure) {
            throw new IllegalStateException("Cannot read EvilCraft reanimation output", failure);
        }
    }
}
