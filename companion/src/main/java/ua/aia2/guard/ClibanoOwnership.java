package ua.aia2.guard;

import java.lang.reflect.InvocationTargetException;
import java.lang.reflect.Field;
import java.lang.reflect.Method;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.WeakHashMap;
import java.lang.ref.WeakReference;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.network.RegistryFriendlyByteBuf;
import net.minecraft.network.chat.Component;
import net.minecraft.network.codec.StreamCodec;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.MenuProvider;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.block.entity.BlockEntity;

/** Exact frame association from Forbidden Arcanus 2.6.1, without a nearest-POI fallback. */
public final class ClibanoOwnership {
    private static final String BASE = "com.stal111.forbidden_arcanus.common.block.entity.clibano.";
    private static final String MAIN = BASE + "ClibanoMainBlockEntity";
    private static final String FRAME = BASE + "ClibanoFrameBlockEntity";
    // Neither a menu key nor its controller/world is retained strongly by this lookup.
    private static final Map<Object, WeakReference<BlockEntity>> MENU_OWNERS = new WeakHashMap<>();
    private record FrameApi(Method data, Method mainPos, Object empty) {}
    private record Shell(BlockEntity main, List<BlockEntity> frames, ServerLevel level) {}
    private static final ClassValue<FrameApi> FRAME_API = new ClassValue<>() {
        @Override protected FrameApi computeValue(Class<?> type) {
            try {
                Method data = type.getMethod("getFrameData");
                Class<?> frameData = data.getReturnType();
                return new FrameApi(data, frameData.getMethod("mainPos"), frameData.getField("EMPTY").get(null));
            } catch (ReflectiveOperationException unsupported) {
                throw new IllegalStateException("Unsupported Forbidden Arcanus frame association", unsupported);
            }
        }
    };
    private record MenuApi(Method storage, StreamCodec<RegistryFriendlyByteBuf, Object> codec) {}
    private record ProgressApi(Field logic, Field progress, Field duration) {}
    private static final ClassValue<ProgressApi> PROGRESS_API = new ClassValue<>() {
        @Override protected ProgressApi computeValue(Class<?> type) {
            try {
                Field logic = type.getDeclaredField("logic"); logic.setAccessible(true);
                return new ProgressApi(logic, logic.getType().getField("cookingProgress"),
                        logic.getType().getField("cookingDuration"));
            } catch (ReflectiveOperationException unsupported) {
                throw new IllegalStateException("Unsupported Clibano cooking arrays", unsupported);
            }
        }
    };
    private static final ClassValue<Field> MENU_CONTEXT = new ClassValue<>() {
        @Override protected Field computeValue(Class<?> type) {
            try { Field context = type.getDeclaredField("context"); context.setAccessible(true); return context; }
            catch (ReflectiveOperationException unsupported) { throw new IllegalStateException("Unsupported Clibano menu context", unsupported); }
        }
    };
    private static final ClassValue<MenuApi> MENU_API = new ClassValue<>() {
        @Override @SuppressWarnings("unchecked") protected MenuApi computeValue(Class<?> type) {
            try {
                Method storage = type.getMethod("getResiduesStorage");
                return new MenuApi(storage, (StreamCodec<RegistryFriendlyByteBuf, Object>)
                        storage.getReturnType().getField("STREAM_CODEC").get(null));
            } catch (ReflectiveOperationException unsupported) {
                throw new IllegalStateException("Unsupported Forbidden Arcanus residue menu payload", unsupported);
            }
        }
    };
    private ClibanoOwnership() {}

    public static boolean isMain(BlockEntity entity) { return entity != null && MAIN.equals(entity.getClass().getName()); }
    public static boolean isFrame(BlockEntity entity) { return entity != null && FRAME.equals(entity.getClass().getName()); }
    private static boolean canonical(BlockEntity entity, ServerLevel level) {
        return entity != null && entity.getLevel() == level && !entity.isRemoved()
                && level.getServer().isSameThread() && level.hasChunkAt(entity.getBlockPos())
                && level.getBlockEntity(entity.getBlockPos()) == entity;
    }
    private static Object invoke(Method method, Object target) {
        try { return method.invoke(target); }
        catch (InvocationTargetException failure) {
            Throwable cause = failure.getCause();
            if (cause instanceof RuntimeException runtime) throw runtime;
            if (cause instanceof Error error) throw error;
            throw new IllegalStateException("Forbidden frame/menu callback failed", cause);
        } catch (ReflectiveOperationException unsupported) { throw new IllegalStateException(unsupported); }
    }
    private static BlockPos boundPos(BlockEntity frame) {
        FrameApi api = FRAME_API.get(frame.getClass());
        Object data = invoke(api.data, frame);
        return data == null || data == api.empty ? null : (BlockPos)invoke(api.mainPos, data);
    }
    private static boolean inShell(BlockPos frame, BlockPos main) {
        return !frame.equals(main) && Math.abs((long)frame.getX() - main.getX()) <= 1
                && Math.abs((long)frame.getY() - main.getY()) <= 1
                && Math.abs((long)frame.getZ() - main.getZ()) <= 1;
    }
    private static Shell shell(BlockEntity clicked) {
        if (clicked == null || !(clicked.getLevel() instanceof ServerLevel level) || !canonical(clicked, level)) return null;
        BlockEntity main;
        if (isMain(clicked)) main = clicked;
        else if (isFrame(clicked)) {
            BlockPos pos = boundPos(clicked);
            if (pos == null || !inShell(clicked.getBlockPos(), pos) || !level.hasChunkAt(pos)) return null;
            main = level.getBlockEntity(pos);
        } else return null;
        if (!isMain(main) || !canonical(main, level)) return null;
        List<BlockEntity> frames = new ArrayList<>(26);
        BlockPos center = main.getBlockPos();
        for (int x = -1; x <= 1; x++) for (int y = -1; y <= 1; y++) for (int z = -1; z <= 1; z++) {
            if (x == 0 && y == 0 && z == 0) continue;
            BlockPos pos = center.offset(x, y, z);
            if (!level.hasChunkAt(pos)) return null;
            BlockEntity frame = level.getBlockEntity(pos);
            if (!isFrame(frame) || !canonical(frame, level) || !center.equals(boundPos(frame))) return null;
            frames.add(frame);
        }
        return new Shell(main, List.copyOf(frames), level);
    }
    public static BlockEntity resolveMain(BlockEntity frame) {
        Shell shell = shell(frame); return shell == null ? null : shell.main;
    }
    /** Native ContainerData reads indexes0/1 before the first producer tick. Preserve invalid arrays, deny that GUI. */
    public static boolean menuStateSafe(BlockEntity main) {
        if (!isMain(main)) return false;
        try {
            ProgressApi api = PROGRESS_API.get(main.getClass()); Object logic = api.logic.get(main);
            if (logic == null || !(api.progress.get(logic) instanceof int[] progress)
                    || !(api.duration.get(logic) instanceof int[] duration) || progress.length != 2 || duration.length != 2) return false;
            return progress[0] >= 0 && progress[1] >= 0 && duration[0] >= 0 && duration[1] >= 0;
        } catch (IllegalAccessException unsupported) { throw new IllegalStateException(unsupported); }
    }
    /** Live authority is checked again on existing menus, not only when a frame was clicked. */
    public static void bindMenu(Object menu) {
        if (menu == null || !menu.getClass().getName().equals("com.stal111.forbidden_arcanus.common.inventory.clibano.ClibanoMenu")) return;
        try {
            Object context = MENU_CONTEXT.get(menu.getClass()).get(menu);
            if (context == null) return;
            Object candidate = invoke(context.getClass().getMethod("getBlockEntity"), context);
            if (candidate instanceof BlockEntity main && isMain(main) && main.getLevel() instanceof ServerLevel level && canonical(main, level))
                MENU_OWNERS.putIfAbsent(menu, new WeakReference<>(main));
        } catch (ReflectiveOperationException unsupported) { throw new IllegalStateException("Cannot bind Clibano menu controller", unsupported); }
    }
    public static boolean mayKeepMenu(Object menu, Player player) {
        if (player == null) return false;
        if (player.level().isClientSide()) return true;
        if (!(player instanceof ServerPlayer real) || player.isSpectator() || !Aia2MachineGuard.isReady()
                || menu == null || !menu.getClass().getName().equals("com.stal111.forbidden_arcanus.common.inventory.clibano.ClibanoMenu")) return false;
        try {
            Object context = MENU_CONTEXT.get(menu.getClass()).get(menu);
            if (context == null) return false;
            Object candidate = invoke(context.getClass().getMethod("getBlockEntity"), context);
            WeakReference<BlockEntity> original = MENU_OWNERS.get(menu);
            if (!(candidate instanceof BlockEntity main) || original == null || original.get() != main
                    || !isMain(main) || !canonical(main, real.serverLevel())
                    || !menuStateSafe(main) || !ClibanoAccess.menuPayloadSafe(main) || !Aia2MachineGuard.mayTick(main)) return false;
            String team = Aia2MachineGuard.synchronizedPlayerTeam(real);
            return !team.isBlank() && team.equals(Aia2MachineGuard.getOwner(main))
                    && real.serverLevel().mayInteract(real, main.getBlockPos());
        } catch (ReflectiveOperationException unsupported) { throw new IllegalStateException("Cannot verify Clibano live menu", unsupported); }
    }
    private static boolean mayOwn(BlockEntity entity, String team) {
        String owner = Aia2MachineGuard.getOwner(entity);
        String id = BuiltInRegistries.BLOCK.getKey(entity.getBlockState().getBlock()).toString();
        return (owner.isBlank() || owner.equals(team))
                && Aia2MachineGuard.mayObserveStage(team, Aia2MachineGuard.getRequiredStage(id));
    }
    /** All structure, permission and conflicting-owner checks finish before the first owner write. */
    public static boolean claim(ServerPlayer player, BlockEntity frame) {
        if (player == null || !isFrame(frame) || !Aia2MachineGuard.isReady()) return false;
        String team = Aia2MachineGuard.synchronizedPlayerTeam(player);
        if (team.isBlank() || player.isSpectator() || !player.getAbilities().mayBuild) return false;
        Shell shell = shell(frame);
        if (shell == null || player.serverLevel() != shell.level
                || player.blockPosition().distSqr(frame.getBlockPos()) > 64
                || !shell.level.mayInteract(player, frame.getBlockPos())
                || !player.mayUseItemAt(frame.getBlockPos(), Direction.UP, player.getMainHandItem())
                || !shell.level.mayInteract(player, shell.main.getBlockPos()) || !mayOwn(shell.main, team)) return false;
        for (BlockEntity part : shell.frames)
            if (!shell.level.mayInteract(player, part.getBlockPos()) || !mayOwn(part, team)) return false;
        if (Aia2MachineGuard.getOwner(shell.main).isBlank()) Aia2MachineGuard.setOwner(shell.main, team);
        for (BlockEntity part : shell.frames) if (Aia2MachineGuard.getOwner(part).isBlank()) Aia2MachineGuard.setOwner(part, team);
        return true;
    }
    /** Opens exactly the associated controller and encodes the same native residue payload as upstream. */
    public static boolean open(ServerPlayer player, BlockEntity frame) {
        if (!claim(player, frame)) {
            if (player != null) player.displayClientMessage(Component.literal(
                    "Clibano недоступна: перевірте епоху, цілісність печі та власника її частин."), false);
            return false;
        }
        BlockEntity main = resolveMain(frame);
        if (main == null || !menuStateSafe(main) || !ClibanoAccess.menuPayloadSafe(main)
                || !Aia2MachineGuard.mayTick(main) || !(main instanceof MenuProvider provider)) return false;
        MenuApi api = MENU_API.get(main.getClass());
        Object storage = invoke(api.storage, main);
        return player.openMenu(provider, buffer -> api.codec.encode(buffer, storage)).isPresent();
    }
}
