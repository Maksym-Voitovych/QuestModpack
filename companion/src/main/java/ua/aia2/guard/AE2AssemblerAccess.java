package ua.aia2.guard;

import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.block.entity.BlockEntity;
import java.lang.reflect.Field;
import java.lang.reflect.Method;

/** Exact AE2 19.2.18 bridge, outside the Mixin nest for JVM access safety. */
public final class AE2AssemblerAccess {
    private AE2AssemblerAccess() {}
    private static final ClassValue<Field> aia2$planFields = new ClassValue<>() {
        @Override protected Field computeValue(Class<?> type) {
            for (Class<?> current = type; current != null; current = current.getSuperclass()) {
                if (!current.getName().equals("appeng.blockentity.crafting.MolecularAssemblerBlockEntity")) continue;
                try {
                    Field field = current.getDeclaredField("myPlan");
                    field.setAccessible(true);
                    return field;
                } catch (NoSuchFieldException ignored) {
                    // Accommodate a subclass of the exact, source-verified target.
                }
            }
            throw new IllegalStateException("Unsupported AE2 MolecularAssembler myPlan field");
        }
    };

    private static final class Aia2AE2Api {
        private static final Class<?> ITEM_KEY;
        private static final Method OUTPUTS;
        private static final Method WHAT;
        private static final Method TO_STACK;
        private static final Object IDLE;
        static {
            try {
                ClassLoader loader = Aia2MachineGuard.class.getClassLoader();
                Class<?> pattern = Class.forName("appeng.api.crafting.IPatternDetails", false, loader);
                Class<?> stack = Class.forName("appeng.api.stacks.GenericStack", false, loader);
                ITEM_KEY = Class.forName("appeng.api.stacks.AEItemKey", false, loader);
                OUTPUTS = pattern.getMethod("getOutputs");
                WHAT = stack.getMethod("what");
                TO_STACK = ITEM_KEY.getMethod("toStack");
                Class<?> modulation = Class.forName("appeng.api.networking.ticking.TickRateModulation", false, loader);
                IDLE = modulation.getField("IDLE").get(null);
            } catch (ReflectiveOperationException error) {
                throw new IllegalStateException("Unsupported AE2 19.2.18 public pattern/tick API", error);
            }
        }
    }


    public static Object deniedModulation(BlockEntity owner) {
        boolean allowed = Aia2MachineGuard.mayTick(owner);
        if (allowed) {
            try {
                Object plan = aia2$planFields.get(owner.getClass()).get(owner);
                if (plan != null) {
                    for (Object output : (Iterable<?>) Aia2AE2Api.OUTPUTS.invoke(plan)) {
                        Object key = Aia2AE2Api.WHAT.invoke(output);
                        if (!Aia2AE2Api.ITEM_KEY.isInstance(key)
                                || !Aia2MachineGuard.mayProduce(owner, (ItemStack) Aia2AE2Api.TO_STACK.invoke(key))) {
                            allowed = false;
                            break;
                        }
                    }
                }
            } catch (ReflectiveOperationException | RuntimeException failure) {
                allowed = false;
            }
        }
        if (!allowed) {
            // IDLE keeps periodic retries, so gaining an epoch resumes the job.
            // SLEEP would leave a blocked plan asleep until another inventory change.
            return Aia2AE2Api.IDLE;
        }
        return null;
    }
}
