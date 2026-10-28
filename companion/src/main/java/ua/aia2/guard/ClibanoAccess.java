package ua.aia2.guard;

import com.google.gson.JsonArray;
import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import com.mojang.logging.LogUtils;
import com.mojang.serialization.Codec;
import com.mojang.serialization.JsonOps;
import java.lang.reflect.Field;
import java.lang.reflect.InvocationTargetException;
import java.lang.reflect.Method;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.HexFormat;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.WeakHashMap;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Holder;
import net.minecraft.core.HolderLookup;
import net.minecraft.core.HolderSet;
import net.minecraft.core.Registry;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.nbt.ListTag;
import net.minecraft.nbt.Tag;
import net.minecraft.resources.RegistryOps;
import net.minecraft.resources.ResourceKey;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.crafting.Recipe;
import net.minecraft.world.item.crafting.RecipeHolder;
import net.minecraft.world.item.crafting.RecipeType;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.state.BlockState;

/** Source-reviewed Forbidden Arcanus 2.6.1 Clibano adapter. A lane binding is not a production proof. */
public final class ClibanoAccess {
    private static final String BASE = "com.stal111.forbidden_arcanus.common.block.entity.clibano.";
    private static final String RECIPE = "com.stal111.forbidden_arcanus.common.item.crafting.ClibanoRecipe";
    private static final ThreadLocal<Run> RUN = new ThreadLocal<>();
    private static final Map<BlockEntity, String> REASONS = new WeakHashMap<>();
    private static final Map<BlockEntity, Tag> UNREAD_RESIDUES = new WeakHashMap<>();
    private static final ClassValue<Map<String, Field>> FIELDS = new ClassValue<>() {
        protected Map<String, Field> computeValue(Class<?> type) { return new HashMap<>(); }
    };
    private static final ClassValue<Map<String, Method>> METHODS = new ClassValue<>() {
        protected Map<String, Method> computeValue(Class<?> type) { return new HashMap<>(); }
    };
    private record Plan(RecipeHolder<?> first, RecipeHolder<?> second, boolean alloy,
                        Holder<?> enhancer, ClibanoPaidState.Lane firstBinding, ClibanoPaidState.Lane secondBinding,
                        ClibanoDependencies.Snapshot firstDependencies, ClibanoDependencies.Snapshot secondDependencies) {
        RecipeHolder<?> holder(int lane) { return lane == 0 ? first : second; }
        ClibanoPaidState.Lane binding(int lane) { return lane == 0 ? firstBinding : secondBinding; }
        ClibanoDependencies.Snapshot dependencies(int lane) { return lane == 0 ? firstDependencies : secondDependencies; }
    }
    private record Finish(RecipeHolder<?> holder, int[] lanes, ItemStack[] inputs, ItemStack[] outputs,
                          ItemStack result, String team, ItemStack enhancerItem) {}
    private static final class Run {
        final BlockEntity machine;
        final Plan plan;
        final boolean[] commits = new boolean[2];
        final boolean[] blocked = new boolean[2];
        final ArrayDeque<Finish> finishes = new ArrayDeque<>();
        final java.util.Set<Finish> residueCredits = java.util.Collections.newSetFromMap(new java.util.IdentityHashMap<>());
        final int[] initialProgress;
        boolean rejected;
        Map<String, ClibanoDependencyState.Residue> conversionBefore;
        Addition addition;
        Run(BlockEntity machine, Plan plan) { this.machine = machine; this.plan = plan; initialProgress = progress(machine).clone(); }
    }
    private record Addition(Object storage, Holder<?> type, String id, String definition, int amount,
                            Map<String, ClibanoDependencyState.Residue> before) {}
    private ClibanoAccess() {}

    private static Field field(Class<?> type, String name) {
        return FIELDS.get(type).computeIfAbsent(name, ignored -> {
            for (Class<?> c = type; c != null; c = c.getSuperclass()) {
                try { var result = c.getDeclaredField(name); result.setAccessible(true); return result; }
                catch (NoSuchFieldException next) { /* Native inventory/logic fields may be inherited. */ }
            }
            throw new IllegalStateException("Unsupported Clibano field " + name);
        });
    }
    private static Object get(Object target, String name) {
        try { return field(target.getClass(), name).get(target); }
        catch (IllegalAccessException failure) { throw new IllegalStateException(failure); }
    }
    private static void set(Object target, String name, Object value) {
        try { field(target.getClass(), name).set(target, value); }
        catch (IllegalAccessException failure) { throw new IllegalStateException(failure); }
    }
    private static Method method(Class<?> type, String name, int count) {
        return METHODS.get(type).computeIfAbsent(name + "/" + count, ignored -> {
            for (Class<?> c = type; c != null; c = c.getSuperclass()) {
                Method found = null;
                for (Method candidate : c.getDeclaredMethods()) {
                    if (candidate.getName().equals(name) && candidate.getParameterCount() == count
                            && !candidate.isBridge() && !candidate.isSynthetic()) {
                        if (found != null) throw new IllegalStateException("Ambiguous Clibano method " + name);
                        found = candidate;
                    }
                }
                if (found != null) { found.setAccessible(true); return found; }
            }
            throw new IllegalStateException("Unsupported Clibano method " + name);
        });
    }
    private static Object call(Object target, String name, Object... args) {
        try { return method(target.getClass(), name, args.length).invoke(target, args); }
        catch (InvocationTargetException failure) { throw nativeFailure(failure); }
        catch (ReflectiveOperationException failure) { throw new IllegalStateException(failure); }
    }
    private static RuntimeException nativeFailure(InvocationTargetException failure) {
        Throwable cause = failure.getCause();
        if (cause instanceof RuntimeException runtime) return runtime;
        if (cause instanceof Error error) throw error;
        return new IllegalStateException("Native Clibano callback failed", cause);
    }
    private static Class<?> type(BlockEntity machine, String name) {
        try { return Class.forName(name, false, machine.getClass().getClassLoader()); }
        catch (ClassNotFoundException failure) { throw new IllegalStateException(failure); }
    }
    private static void require(boolean valid, String reason) {
        if (!valid) throw new IllegalArgumentException(reason);
    }
    private static void pause(BlockEntity machine, String reason) {
        if (!reason.equals(REASONS.put(machine, reason))) LogUtils.getLogger().warn("[AIA2] Clibano призупинено: {}", reason);
    }
    private static boolean canonical(BlockEntity machine) {
        return ClibanoOwnership.isMain(machine) && machine.getLevel() instanceof ServerLevel level
                && !machine.isRemoved() && level.getServer().isSameThread() && level.hasChunkAt(machine.getBlockPos())
                && level.getBlockEntity(machine.getBlockPos()) == machine && Aia2MachineGuard.isReady()
                && !Aia2MachineGuard.getOwner(machine).isBlank() && Aia2MachineGuard.mayTick(machine)
                && (inTick(machine) || ClibanoOwnership.resolveMain(machine) == machine);
    }
    private static ItemStack stack(BlockEntity machine, int slot) { return (ItemStack)call(machine, "getStack", slot); }
    private static boolean item(BlockEntity machine, ItemStack stack) {
        if (stack.isEmpty()) return true;
        String id = BuiltInRegistries.ITEM.getKey(stack.getItem()).toString();
        return !id.matches("kubejs:aia2_(tech|arcane|epoch)_key_[0-9]{2}")
                && !KeyProductionBridge.isKeyOutput(id) && Aia2MachineGuard.mayProduce(machine, stack);
    }
    private static int[] progress(BlockEntity machine) { return (int[])get(get(machine, "logic"), "cookingProgress"); }
    private static int[] duration(BlockEntity machine) { return (int[])get(get(machine, "logic"), "cookingDuration"); }
    public static boolean canOpen(BlockEntity machine) {
        try {
            int[] progress = progress(machine), duration = duration(machine);
            return progress.length == 2 && duration.length == 2 && progress[0] >= 0 && progress[1] >= 0
                    && duration[0] >= 0 && duration[1] >= 0 && duration[0] <= 1200000 && duration[1] <= 1200000;
        } catch (RuntimeException unsupported) { return false; }
    }
    @SuppressWarnings("unchecked")
    private static Holder<?> physicalEnhancer(BlockEntity machine) {
        try {
            Method resolve = type(machine, "com.stal111.forbidden_arcanus.common.item.enhancer.EnhancerHelper")
                    .getMethod("getEnhancerHolder", HolderLookup.Provider.class, ItemStack.class);
            return ((java.util.Optional<Holder<?>>)resolve.invoke(null,
                    ((ServerLevel)machine.getLevel()).registryAccess(), stack(machine, 0))).orElse(null);
        } catch (InvocationTargetException failure) { throw nativeFailure(failure); }
        catch (ReflectiveOperationException failure) { throw new IllegalStateException(failure); }
    }
    private static Object input(BlockEntity machine, ItemStack first, ItemStack second) {
        try {
            return type(machine, "com.stal111.forbidden_arcanus.common.item.crafting.ClibanoRecipeInput")
                    .getConstructor(ItemStack.class, ItemStack.class).newInstance(first, second);
        } catch (InvocationTargetException failure) { throw nativeFailure(failure); }
        catch (ReflectiveOperationException failure) { throw new IllegalStateException(failure); }
    }
    @SuppressWarnings({"unchecked", "rawtypes"})
    private static boolean matches(BlockEntity machine, RecipeHolder<?> holder, Holder<?> enhancer, int[] lanes) {
        if (!ClibanoDependencies.inputsMatch(machine, holder.value(), lanes)) return false;
        Object input = input(machine, lanes.length == 2 || lanes[0] == 0 ? stack(machine, 3) : ItemStack.EMPTY,
                lanes.length == 2 || lanes[0] == 1 ? stack(machine, 4) : ItemStack.EMPTY);
        HolderSet<?> set = enhancer == null ? HolderSet.empty() : HolderSet.direct((Holder)enhancer);
        return Boolean.TRUE.equals(call(holder.value(), "matches", input, machine.getLevel(), set));
    }
    private static JsonElement ordered(JsonElement json) {
        if (json.isJsonObject()) {
            JsonObject result = new JsonObject(); json.getAsJsonObject().keySet().stream().sorted()
                    .forEach(key -> result.add(key, ordered(json.getAsJsonObject().get(key)))); return result;
        }
        if (json.isJsonArray()) {
            JsonArray result = new JsonArray(); json.getAsJsonArray().forEach(value -> result.add(ordered(value))); return result;
        }
        return json;
    }
    private static String hash(JsonElement json) {
        try { return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(ordered(json).toString().getBytes(StandardCharsets.UTF_8))); }
        catch (java.security.NoSuchAlgorithmException impossible) { throw new AssertionError(impossible); }
    }
    @SuppressWarnings("unchecked")
    private static String definition(BlockEntity machine, Recipe<?> recipe) {
        var codec = (Codec<Recipe<?>>)(Codec<?>)recipe.getSerializer().codec().codec();
        return hash(codec.encodeStart(RegistryOps.create(JsonOps.INSTANCE,
                ((ServerLevel)machine.getLevel()).registryAccess()), recipe).getOrThrow());
    }
    @SuppressWarnings("unchecked")
    private static String inputs(BlockEntity machine, Holder<?> enhancer, int[] lanes) {
        JsonObject result = new JsonObject(); result.addProperty("team", Aia2MachineGuard.getOwner(machine));
        JsonArray array = new JsonArray();
        var ops = RegistryOps.create(JsonOps.INSTANCE, ((ServerLevel)machine.getLevel()).registryAccess());
        for (int lane : lanes) {
            JsonObject entry = new JsonObject(); entry.addProperty("lane", lane);
            ItemStack unit = stack(machine, lane + 3).copyWithCount(1);
            entry.add("item", ItemStack.CODEC.encodeStart(ops, unit).getOrThrow()); array.add(entry);
        }
        result.add("inputs", array);
        ItemStack enhancerStack = stack(machine, 0);
        result.add("enhancer_item", enhancerStack.isEmpty() ? new JsonObject()
                : ItemStack.CODEC.encodeStart(ops, enhancerStack.copyWithCount(1)).getOrThrow());
        if (enhancer != null) {
            try {
                Codec<Object> codec = (Codec<Object>)enhancer.value().getClass().getField("CODEC").get(null);
                result.add("enhancer_definition", codec.encodeStart(ops, enhancer.value()).getOrThrow());
            } catch (ReflectiveOperationException failure) { throw new IllegalStateException(failure); }
        }
        return hash(result);
    }
    private static ClibanoPaidState.Lane binding(BlockEntity machine, RecipeHolder<?> holder, Holder<?> enhancer, int[] lanes) {
        return holder == null ? null : new ClibanoPaidState.Lane(holder.id().toString(),
                definition(machine, holder.value()), inputs(machine, enhancer, lanes));
    }
    /** Follow native first-same-item / second-same-item / empty-slot priority exactly. */
    private static boolean fits(BlockEntity machine, ItemStack result) {
        if (result == null || result.isEmpty() || result.getCount() > result.getMaxStackSize() || !item(machine, result)) return false;
        ItemStack first = stack(machine, 5), second = stack(machine, 6);
        if (!item(machine, first) || !item(machine, second)) return false;
        if (ItemStack.isSameItem(first, result) && first.getCount() + result.getCount() <= first.getMaxStackSize())
            return ItemStack.isSameItemSameComponents(first, result);
        if (ItemStack.isSameItem(second, result) && second.getCount() + result.getCount() <= second.getMaxStackSize())
            return ItemStack.isSameItemSameComponents(second, result);
        return first.isEmpty() || second.isEmpty();
    }
    private static RecipeHolder<?> current(BlockEntity machine, RecipeHolder<?> holder) {
        if (holder == null || !RECIPE.equals(holder.value().getClass().getName())) return null;
        var current = ((ServerLevel)machine.getLevel()).getRecipeManager().byKey(holder.id()).orElse(null);
        return current != null && current.value() == holder.value() ? current : null;
    }
    private static void recipeBounds(BlockEntity machine, Recipe<?> recipe) {
        Object times = call(recipe, "cookingTimes");
        Object fire = get(machine, "fireType");
        for (Object mode : fire.getClass().getEnumConstants()) {
            int duration = ((Number)call(times, "get", mode)).intValue();
            require(duration > 0 && duration <= 1200000, "непідтримувана тривалість випалу");
        }
        Object chance = ((java.util.Optional<?>)call(recipe, "residueChance")).orElse(null);
        if (chance != null) {
            double value = ((Number)call(chance, "chance")).doubleValue();
            require(Double.isFinite(value) && value >= 0 && value <= 1, "неправильний шанс залишків");
        }
    }
    @SuppressWarnings({"unchecked", "rawtypes"})
    private static Plan prepare(BlockEntity machine) {
        require(canonical(machine), "контролер/структура або власник не підтверджені");
        require(canOpen(machine), "пошкоджені масиви прогресу; потрібне явне відновлення");
        require(ClibanoPaidState.status(machine) != ClibanoPaidState.Status.CORRUPT, "пошкоджений запис операції");
        require(ClibanoDependencyState.status(machine) != ClibanoDependencyState.Status.CORRUPT, "пошкоджений журнал залежностей Clibano");
        require(!UNREAD_RESIDUES.containsKey(machine), "непрочитані залишки збережено; відновіть їх registry-визначення");
        for (int i = 0; i <= 6; i++) require(item(machine, stack(machine, i)), "заблокований предмет у слоті " + i);
        try { checkedResidues(call(machine, "getResiduesStorage"), machine); }
        catch (ReflectiveOperationException failure) { throw new IllegalArgumentException("не вдалося перевірити історію залишків", failure); }
        ServerLevel level = (ServerLevel)machine.getLevel();
        Holder<?> enhancer = physicalEnhancer(machine);
        RecipeType<?> recipeType;
        try { recipeType = (RecipeType<?>)machine.getClass().getField("RECIPE_TYPE").get(null); }
        catch (ReflectiveOperationException failure) { throw new IllegalStateException(failure); }
        List<RecipeHolder<?>> all = (List)level.getRecipeManager().getAllRecipesFor((RecipeType)recipeType);
        require(all.size() <= 1024, "завеликий список рецептів Clibano");
        RecipeHolder<?> alloy = null, first = null, second = null;
        for (RecipeHolder<?> holder : all) {
            require(current(machine, holder) != null, "невідоме або застаріле визначення рецепта");
            if (Boolean.TRUE.equals(call(holder.value(), "isDoubleRecipe"))) {
                if (alloy == null && matches(machine, holder, enhancer, new int[] {0, 1})) alloy = holder;
            } else {
                if (first == null && matches(machine, holder, enhancer, new int[] {0})) first = holder;
                if (second == null && matches(machine, holder, enhancer, new int[] {1})) second = holder;
            }
        }
        boolean doubleRecipe = alloy != null;
        if (doubleRecipe) { first = alloy; second = alloy; }
        ClibanoPaidState.Lane a = binding(machine, first, enhancer, doubleRecipe ? new int[] {0,1} : new int[] {0});
        ClibanoPaidState.Lane b = doubleRecipe ? a : binding(machine, second, enhancer, new int[] {1});
        var da = first == null ? null : ClibanoDependencies.capture(machine, first.value(), enhancer, doubleRecipe ? new int[]{0,1} : new int[]{0});
        var db = doubleRecipe ? da : second == null ? null : ClibanoDependencies.capture(machine, second.value(), enhancer, new int[]{1});
        Plan plan = new Plan(first, second, doubleRecipe, enhancer, a, b, da, db);
        int[] progress = progress(machine), duration = duration(machine);
        for (int lane = 0; lane < 2; lane++) {
            RecipeHolder<?> selected = plan.holder(lane);
            if (selected != null) {
                recipeBounds(machine, selected.value());
                require(Aia2MachineGuard.mayProcessRecipe(machine, selected.value())
                        && fits(machine, selected.value().getResultItem(level.registryAccess())), "рецепт/вихід заблоковано або слот заповнений");
            }
            if (progress[lane] > 0) {
                require(duration[lane] > 0 && progress[lane] < duration[lane], "лічильник незавершеної операції поза межами");
                require(selected != null && ClibanoPaidState.lane(machine, lane).orElse(null) != null
                        && ClibanoPaidState.lane(machine, lane).get().equals(plan.binding(lane)), "незавершена операція без тотожного запису рецепта/входів");
                var witness = ClibanoDependencyState.lane(machine, lane);
                require(witness.isPresent() ? witness.get().equals(plan.dependencies(lane).fingerprint())
                        : !plan.dependencies(lane).hasDependencies(), "залежності незавершеної операції змінено або відсутній історичний доказ");
            }
        }
        if (doubleRecipe) require(progress[0] == progress[1] && duration[0] == duration[1], "неузгоджені лічильники сплаву");
        return plan;
    }
    private static void apply(BlockEntity machine, Plan plan) {
        Object old = get(machine, "logic"), logic = old;
        int[] progress = progress(machine).clone(), duration = duration(machine).clone();
        String wanted = BASE + "logic." + (plan.alloy ? "DoubleSmeltLogic" : "DefaultSmeltLogic");
        if (!old.getClass().getName().equals(wanted)) {
            try {
                Class<?> accessor = type(machine, BASE + "logic.ClibanoAccessor");
                logic = plan.alloy ? type(machine, wanted).getConstructor(accessor, RecipeHolder.class).newInstance(machine, plan.first)
                        : type(machine, wanted).getConstructor(accessor, RecipeHolder.class, RecipeHolder.class).newInstance(machine, plan.first, plan.second);
                set(machine, "logic", logic);
            } catch (InvocationTargetException failure) { throw nativeFailure(failure); }
            catch (ReflectiveOperationException failure) { throw new IllegalStateException(failure); }
        }
        if (plan.alloy) set(logic, "recipe", plan.first);
        else { set(logic, "firstRecipe", plan.first); set(logic, "secondRecipe", plan.second); }
        set(logic, "cookingProgress", progress); set(logic, "cookingDuration", duration);
        set(machine, "enhancer", plan.enhancer);
        set(machine, "nextFireType", call(machine, "getFireTypeFromInput"));
        Object quick = get(machine, "quickCheck");
        set(quick, "lastAlloyRecipe", plan.alloy ? plan.first : null);
        // The raw selector queue never contains a rejected/stale holder after preflight.
        ((java.util.Queue<?>)get(quick, "lastRecipes")).clear();
    }
    public static boolean inTick(BlockEntity machine) { return RUN.get() != null && RUN.get().machine == machine; }
    public static void tick(Level level, BlockPos pos, BlockState state, BlockEntity machine) {
        Plan plan;
        try {
            require(machine != null && machine.getLevel() == level && machine.getBlockPos().equals(pos)
                    && machine.getBlockState() == state, "підмінений одержувач статичного тіку");
            plan = prepare(machine);
        }
        catch (RuntimeException denied) { pause(machine, message(denied)); return; }
        apply(machine, plan);
        Run previous = RUN.get(), run = new Run(machine, plan); RUN.set(run);
        try {
            try { machine.getClass().getMethod("serverTick", Level.class, BlockPos.class, BlockState.class, machine.getClass()).invoke(null, level, pos, state, machine); }
            catch (InvocationTargetException failure) { throw nativeFailure(failure); }
            catch (ReflectiveOperationException failure) { throw new IllegalStateException(failure); }
            if (!run.rejected && !run.blocked[0] && !run.blocked[1]) REASONS.remove(machine);
        } finally {
            try {
                int[] after = progress(machine);
                for (int lane = 0; lane < 2; lane++) {
                    if (run.commits[lane]) {
                        ClibanoPaidState.setLane(machine, lane, null); ClibanoDependencyState.setLane(machine, lane, null);
                    } else {
                        ClibanoPaidState.setLane(machine, lane, after[lane] > 0 ? plan.binding(lane) : null);
                        // Old dependency-free work remains old: never upgrade it from today's data.
                        if (after[lane] == 0) ClibanoDependencyState.setLane(machine, lane, null);
                        else if (run.initialProgress[lane] == 0 && plan.dependencies(lane) != null)
                            ClibanoDependencyState.setLane(machine, lane, plan.dependencies(lane).fingerprint());
                    }
                }
                machine.setChanged();
            } finally { if (previous == null) RUN.remove(); else RUN.set(previous); }
        }
    }
    /** Upstream logic advances even when unlit. Only actual burning ticks may advance production. */
    public static void updateRecipes(Object logic, List<?> ignored) {
        Run run = RUN.get();
        if (run == null || get(logic, "clibano") != run.machine) return;
        // Native quickCheck's polling queue may choose a different overlapping recipe for lane1.
        // Keep the exact already-validated current plan instead of resetting paid work to that cache.
        List<?> selected = run.plan.alloy ? List.of(run.plan.first)
                : java.util.Arrays.asList(run.plan.first, run.plan.second);
        call(logic, "updateRecipes", selected);
    }
    public static void cook(Object logic, boolean lit) {
        Run run = RUN.get();
        if (run == null || run.rejected || get(logic, "clibano") != run.machine || !lit) return;
        // A residue conversion can fill the destination earlier in this same native tick.
        for (int lane = 0; lane < 2; lane++) {
            var holder = run.plan.holder(lane);
            if (holder != null && (!actualFire(run.machine, holder)
                    || !maySmelt(run.machine, holder, nativeSlot(run.machine, run.plan.alloy ? "BOTH" : lane == 0 ? "FIRST" : "SECOND")))) return;
        }
        int[] before = progress(run.machine).clone(), duration = duration(run.machine).clone();
        try { call(logic, "tick", true); }
        finally {
            int[] after = progress(run.machine), afterDuration = duration(run.machine);
            for (int lane = 0; lane < 2; lane++) {
                // Lane0 may fill the last result slot before native lane1 performs its check.
                // Preserve uncommitted work instead of allowing native resetCookingProgress to erase it.
                if (!run.commits[lane] && (run.blocked[lane] || after[lane] < before[lane])) {
                    after[lane] = before[lane]; afterDuration[lane] = duration[lane];
                }
            }
        }
    }
    private static boolean actualFire(BlockEntity machine, RecipeHolder<?> holder) {
        Object actual = get(machine, "fireType");
        return ((Enum<?>)actual).ordinal() >= ((Enum<?>)call(holder.value(), "requiredFireType")).ordinal()
                && ((Number)call(call(holder.value(), "cookingTimes"), "get", actual)).intValue() > 0;
    }
    private static Object nativeSlot(BlockEntity machine, String name) {
        try { return type(machine, BASE + "ClibanoInputSlot").getField(name).get(null); }
        catch (ReflectiveOperationException failure) { throw new IllegalStateException(failure); }
    }
    private static int[] lanes(Object slot) {
        int[] indexes = (int[])call(slot, "getIndex");
        require(indexes.length == 1 || indexes.length == 2 && indexes[0] == 0 && indexes[1] == 1, "невідомі вхідні слоти");
        for (int index : indexes) require(index >= 0 && index <= 1, "невідомий вхідний слот");
        return indexes;
    }
    public static boolean maySmelt(BlockEntity machine, RecipeHolder<?> holder, Object slot) {
        if (holder == null) return true; // Let native null handling return false, without inventing a recipe.
        try {
            require(canonical(machine) && current(machine, holder) != null, "контролер або кеш рецепта не підтверджені");
            int[] lanes = lanes(slot);
            require(matches(machine, holder, physicalEnhancer(machine), lanes), "фізичні входи/підсилювач не відповідають рецепту");
            require(Aia2MachineGuard.mayProcessRecipe(machine, holder.value())
                    && fits(machine, holder.value().getResultItem(((ServerLevel)machine.getLevel()).registryAccess())), "вихід рецепта не дозволений");
            Object fire = ((Number)get(machine, "soulTime")).intValue() == 0 ? get(machine, "nextFireType") : get(machine, "fireType");
            require(((Enum<?>)fire).ordinal() >= ((Enum<?>)call(holder.value(), "requiredFireType")).ordinal(), "недостатній тип вогню");
            return true;
        } catch (RuntimeException denied) { pause(machine, message(denied)); return false; }
    }
    public static boolean mayFinish(BlockEntity machine, RecipeHolder<?> holder, Object slot) {
        Run run = RUN.get();
        if (run == null || run.machine != machine || ((Number)get(machine, "burnTime")).intValue() <= 0) return false;
        int[] lanes = lanes(slot);
        if (!maySmelt(machine, holder, slot) || !actualFire(machine, holder)) {
            for (int lane : lanes) run.blocked[lane] = true; return false;
        }
        try {
            var currentDependencies = ClibanoDependencies.capture(machine, holder.value(), physicalEnhancer(machine), lanes);
            for (int lane : lanes) require(currentDependencies.equals(run.plan.dependencies(lane)), "залежності Clibano змінилися перед завершенням");
        } catch (RuntimeException denied) {
            for (int lane : lanes) run.blocked[lane] = true;
            run.rejected = true;
            pause(machine, message(denied)); return false;
        }
        for (int lane : lanes) if (run.commits[lane] || run.plan.holder(lane) == null
                || run.plan.holder(lane).value() != holder.value() || progress(machine)[lane] != duration(machine)[lane]
                || duration(machine)[lane] <= 0 || duration(machine)[lane] != ((Number)call(machine, "getCookingTime", holder)).intValue()) {
            run.blocked[lane] = true; return false;
        }
        ItemStack[] inputs = {stack(machine, 3).copy(), stack(machine, 4).copy()};
        ItemStack[] outputs = {stack(machine, 5).copy(), stack(machine, 6).copy()};
        ItemStack result = holder.value().getResultItem(((ServerLevel)machine.getLevel()).registryAccess()).copy();
        run.finishes.push(new Finish(holder, lanes.clone(), inputs, outputs, result, Aia2MachineGuard.getOwner(machine), stack(machine, 0).copy()));
        for (int lane : lanes) { run.commits[lane] = true; ClibanoPaidState.setLane(machine, lane, null); ClibanoDependencyState.setLane(machine, lane, null); }
        return true;
    }
    private static boolean consumed(ItemStack before, ItemStack after) {
        return before.getCount() == 1 ? after.isEmpty() : after.getCount() == before.getCount() - 1
                && ItemStack.isSameItemSameComponents(before, after);
    }
    public static void finished(BlockEntity machine, RecipeHolder<?> holder, Object slot) {
        Run run = RUN.get();
        if (run == null || run.machine != machine || run.finishes.isEmpty()) return;
        Finish finish = run.finishes.pop();
        if (finish.holder.value() != holder.value() || !canonical(machine) || current(machine, holder) == null
                || !finish.team.equals(Aia2MachineGuard.getOwner(machine))) return;
        for (int lane = 0; lane < 2; lane++) {
            boolean used = false; for (int selected : finish.lanes) if (selected == lane) used = true;
            if (used ? !consumed(finish.inputs[lane], stack(machine, lane + 3))
                    : !ItemStack.matches(finish.inputs[lane], stack(machine, lane + 3))) return;
        }
        int delta = 0;
        for (int lane = 0; lane < 2; lane++) {
            ItemStack before = finish.outputs[lane], after = stack(machine, lane + 5);
            if (ItemStack.matches(before, after)) continue;
            if (!ItemStack.isSameItemSameComponents(after, finish.result)
                    || !before.isEmpty() && !ItemStack.isSameItemSameComponents(before, finish.result)) return;
            int added = after.getCount() - before.getCount(); if (added <= 0) return; delta += added;
        }
        if (delta == finish.result.getCount()) ProductionMilestoneBridge.finishedObservedMachine(machine, holder.value(), List.of(finish.result));
    }
    @SuppressWarnings("unchecked")
    private static Map<?, ?> checkedResidues(Object storage, BlockEntity machine) throws ReflectiveOperationException {
        require(canonical(machine) && call(machine, "getResiduesStorage") == storage && !UNREAD_RESIDUES.containsKey(machine), "сховище залишків не підтверджене");
        ServerLevel level = (ServerLevel)machine.getLevel();
        Object key = type(machine, "com.stal111.forbidden_arcanus.core.registry.FARegistries").getField("RESIDUE_TYPE").get(null);
        Registry<Object> registry = level.registryAccess().registryOrThrow((ResourceKey<Registry<Object>>)key);
        Map<?, ?> map = (Map<?, ?>)call(storage, "getResidueTypeAmountMap");
        require(map.size() <= 64, "пошкоджене сховище залишків");
        require(ClibanoDependencyState.status(machine) != ClibanoDependencyState.Status.CORRUPT, "пошкоджена історія залишків");
        Map<String, ClibanoDependencyState.Residue> history = ClibanoDependencyState.residues(machine);
        int witnessed = 0;
        int total = 0;
        for (var entry : map.entrySet()) {
            Holder<?> type = (Holder<?>)entry.getKey();
            require(entry.getValue() instanceof Integer, "неправильна кількість залишків");
            int amount = (Integer)entry.getValue(); total += amount;
            require(amount >= 0 && amount <= 64 && registry.get(type.unwrapKey().orElseThrow().location()) == type.value(), "застаріле визначення або кількість залишків");
            if (amount > 0) {
                var receipt = history.get(type.unwrapKey().orElseThrow().location().toString());
                require(receipt != null && receipt.amount() == amount
                        && receipt.definition().equals(ClibanoDependencies.residueDefinition(machine, type)),
                        "залишки не мають тотожного історичного визначення/кількості; див. /aia2clibano status");
                witnessed++;
            }
        }
        require(total <= 64 && total == ((Number)call(storage, "getTotalAmount")).intValue(), "неузгоджена сумарна кількість залишків");
        require(witnessed == history.size(), "історія залишків не відповідає фізичному сховищу");
        return map;
    }
    /** The native menu stream encodes holders; stale/removed holders cannot be sent safely. */
    public static boolean menuPayloadSafe(BlockEntity machine) {
        try { checkedResidues(call(machine, "getResiduesStorage"), machine); return true; }
        catch (ReflectiveOperationException | RuntimeException denied) { pause(machine, message(denied)); return false; }
    }
    public static boolean mayConvertResidues(Object storage, BlockEntity machine) {
        try {
            Run run = RUN.get(); require(run != null && run.machine == machine && run.conversionBefore == null, "об'єднання залишків поза перевіреним циклом");
            Map<?, ?> map = checkedResidues(storage, machine);
            for (var entry : map.entrySet()) {
                Holder<?> type = (Holder<?>)entry.getKey(); int amount = ((Number)entry.getValue()).intValue();
                Object combine = call(type.value(), "combineInfo");
                int required = ((Number)call(combine, "requiredAmount")).intValue();
                require(required > 0 && required <= 64, "неправильна ціна об'єднання залишків");
                if (amount >= required) require(fits(machine, (ItemStack)call(combine, "result")), "вихід залишків заблоковано");
            }
            run.conversionBefore = ClibanoDependencyState.residues(machine);
            return true;
        } catch (ReflectiveOperationException | RuntimeException denied) {
            Run run = RUN.get(); if (run != null && run.machine == machine) run.rejected = true;
            pause(machine, message(denied)); return false;
        }
    }
    /** Validate observed native count deltas. No current definition is adopted for an old balance. */
    public static void convertedResidues(Object storage, BlockEntity machine) {
        Run run = RUN.get();
        if (run == null || run.machine != machine || run.conversionBefore == null) return;
        Map<String, ClibanoDependencyState.Residue> before = run.conversionBefore; run.conversionBefore = null;
        try {
            require(call(machine, "getResiduesStorage") == storage && canonical(machine), "підмінене сховище залишків");
            Map<?, ?> map = (Map<?, ?>)call(storage, "getResidueTypeAmountMap");
            require(map.size() <= 64, "завелике сховище залишків");
            Map<String, ClibanoDependencyState.Residue> after = new HashMap<>(); int total = 0;
            for (var entry : map.entrySet()) {
                Holder<?> holder = (Holder<?>)entry.getKey(); int amount = (Integer)entry.getValue();
                require(amount >= 0 && amount <= 64, "неправильна кількість залишків після об'єднання");
                String id = holder.unwrapKey().orElseThrow().location().toString();
                var old = before.get(id);
                require(amount == 0 || old != null && amount <= old.amount()
                        && old.definition().equals(ClibanoDependencies.residueDefinition(machine, holder)), "непідтверджена зміна залишків під час об'єднання");
                if (amount > 0) after.put(id, new ClibanoDependencyState.Residue(old.definition(), amount));
                total += amount;
            }
            require(total <= 64 && total == ((Number)call(storage, "getTotalAmount")).intValue(), "неузгоджена кількість залишків після об'єднання");
            ClibanoDependencyState.setResidues(machine, after); machine.setChanged();
        } catch (RuntimeException denied) { run.rejected = true; run.blocked[0] = run.blocked[1] = true; pause(machine, message(denied)); }
    }
    /** Only the exact currently verified native finish may credit a newly produced residue. */
    public static boolean mayIncreaseResidue(Object storage, Holder<?> type, int amount) {
        Run run = RUN.get();
        if (run == null || run.finishes.isEmpty() || run.addition != null) return false;
        Finish finish = run.finishes.peek();
        if (run.residueCredits.contains(finish)) return false;
        try {
            BlockEntity machine = run.machine;
            require(amount == 1 && canonical(machine) && call(machine, "getResiduesStorage") == storage, "залишки поза перевіреним завершенням");
            Optional<?> chance = (Optional<?>)call(finish.holder.value(), "residueChance");
            require(chance.isPresent() && call(chance.get(), "type") == type, "тип залишків не відповідає рецепту");
            require(current(machine, finish.holder) != null && ItemStack.matches(finish.enhancerItem, stack(machine, 0)), "рецепт або фізичний підсилювач змінився під час завершення");
            var dependencies = ClibanoDependencies.definitionSnapshot(machine, finish.holder.value(), physicalEnhancer(machine));
            // Native finish has consumed inputs; retain the verified pre-consumption lane evidence.
            for (int lane : finish.lanes) require(dependencies.equals(run.plan.dependencies(lane)), "залежності залишків змінено");
            checkedResidues(storage, machine);
            String id = type.unwrapKey().orElseThrow().location().toString();
            run.addition = new Addition(storage, type, id, ClibanoDependencies.residueDefinition(machine, type), amount, ClibanoDependencyState.residues(machine));
            run.residueCredits.add(finish); // Native addResidue can attempt at most one unit per finish.
            return true;
        } catch (ReflectiveOperationException | RuntimeException denied) { run.rejected = true; pause(run.machine, message(denied)); return false; }
    }
    public static void increasedResidue(Object storage, Holder<?> type, int amount) {
        Run run = RUN.get();
        if (run == null || run.addition == null) return;
        Addition addition = run.addition; run.addition = null;
        if (addition.storage != storage || addition.type != type || addition.amount != amount) return;
        try {
            Map<?, ?> map = (Map<?, ?>)call(storage, "getResidueTypeAmountMap");
            require(map.size() <= 64, "завелике сховище залишків");
            Map<String, ClibanoDependencyState.Residue> updated = new HashMap<>(addition.before); int total = 0;
            int previous = addition.before.containsKey(addition.id) ? addition.before.get(addition.id).amount() : 0;
            int expected = previous + Math.min(amount, 64 - addition.before.values().stream().mapToInt(ClibanoDependencyState.Residue::amount).sum());
            require(addition.definition.equals(ClibanoDependencies.residueDefinition(run.machine, type)), "визначення залишків змінилося під час додавання");
            int seen = 0;
            for (var entry : map.entrySet()) {
                Holder<?> holder = (Holder<?>)entry.getKey(); String id = holder.unwrapKey().orElseThrow().location().toString();
                int actual = (Integer)entry.getValue(); require(actual >= 0 && actual <= 64, "неправильна кількість доданих залишків");
                var old = addition.before.get(id);
                require(actual == (id.equals(addition.id) ? expected : old == null ? 0 : old.amount()), "непідтверджена зміна балансу залишків");
                if (actual > 0) {
                    String definition = id.equals(addition.id) ? addition.definition : old.definition();
                    require(definition.equals(ClibanoDependencies.residueDefinition(run.machine, holder)), "змінилося визначення наявних залишків");
                    updated.put(id, new ClibanoDependencyState.Residue(definition, actual)); seen++;
                }
                total += actual;
            }
            require(seen == updated.size() && total <= 64 && total == ((Number)call(storage, "getTotalAmount")).intValue(), "неузгоджений баланс доданих залишків");
            require(expected == 0 || updated.containsKey(addition.id), "залишок не прийнятий сховищем");
            ClibanoDependencyState.setResidues(run.machine, updated); run.machine.setChanged();
        } catch (RuntimeException denied) { run.rejected = true; pause(run.machine, message(denied)); }
    }
    public static void load(BlockEntity machine, CompoundTag tag) {
        ClibanoPaidState.load(machine, tag);
        ClibanoDependencyState.load(machine, tag);
        Tag residues = tag.get("residues");
        if (residues == null) UNREAD_RESIDUES.remove(machine); else UNREAD_RESIDUES.put(machine, residues.copy());
    }
    /** Retain native residue data when decoding dropped unknown/removed registry holders. */
    public static void loaded(BlockEntity machine) {
        Tag raw = UNREAD_RESIDUES.get(machine);
        if (raw instanceof CompoundTag compound) {
            Map<?, ?> parsed = (Map<?, ?>)call(call(machine, "getResiduesStorage"), "getResidueTypeAmountMap");
            boolean same = compound.getAllKeys().size() == parsed.size();
            for (var entry : parsed.entrySet()) {
                String id = ((Holder<?>)entry.getKey()).unwrapKey().orElseThrow().location().toString();
                same &= compound.contains(id, Tag.TAG_INT) && compound.getInt(id) == ((Number)entry.getValue()).intValue();
            }
            if (same) UNREAD_RESIDUES.remove(machine);
        }
    }
    public static void save(BlockEntity machine, CompoundTag tag) {
        ClibanoPaidState.save(machine, tag);
        ClibanoDependencyState.save(machine, tag);
        Tag residues = UNREAD_RESIDUES.get(machine);
        if (residues != null) tag.put("residues", residues.copy());
        else if (!tag.contains("residues")) {
            // Native save skips residues when level==null and may omit a codec failure.
            // Retain actual ID/count data without certifying it against today's registry.
            Map<?, ?> map = (Map<?, ?>)call(call(machine, "getResiduesStorage"), "getResidueTypeAmountMap");
            if (map.size() <= 64 && map.values().stream().anyMatch(v -> v instanceof Integer amount && amount != 0)) {
                CompoundTag raw = new CompoundTag();
                for (var entry : map.entrySet()) {
                    require(entry.getKey() instanceof Holder<?> && entry.getValue() instanceof Integer, "непідтримуваний raw баланс залишків");
                    raw.putInt(((Holder<?>)entry.getKey()).unwrapKey().orElseThrow().location().toString(), (Integer)entry.getValue());
                }
                tag.put("residues", raw);
            }
        }
    }
    public static String status(BlockEntity machine) {
        return "Clibano: " + ClibanoPaidState.status(machine) + "; залежності: " + ClibanoDependencyState.status(machine)
                + "; " + REASONS.getOrDefault(machine, "причин призупинення не зареєстровано");
    }
    public static String cancelProgress(ServerPlayer player, BlockEntity machine) {
        try {
            require(player != null && player.hasPermissions(2) && !player.isSpectator(), "потрібні права оператора");
            require(canonical(machine) && player.serverLevel() == machine.getLevel()
                    && player.blockPosition().distSqr(machine.getBlockPos()) <= 64
                    && Aia2MachineGuard.getOwner(machine).equals(Aia2MachineGuard.synchronizedPlayerTeam(player)), "підійдіть до Clibano своєї команди");
            require(ClibanoDependencyState.status(machine) != ClibanoDependencyState.Status.CORRUPT,
                    "пошкоджений журнал залежностей: спочатку явно збережіть його через quarantine-residues");
            CompoundTag persistent = machine.getPersistentData(); String key = "aia2_clibano_cancel_backups_v1";
            require(!persistent.contains(key) || persistent.contains(key, Tag.TAG_LIST), "пошкоджений список резервних копій");
            ListTag backups = persistent.getList(key, Tag.TAG_COMPOUND);
            require(backups.size() < 8 && (!persistent.contains(key) || backups.size() == ((ListTag)persistent.get(key)).size()), "резервне сховище заповнене або пошкоджене");
            CompoundTag snapshot = new CompoundTag(); ClibanoPaidState.save(machine, snapshot);
            ClibanoDependencyState.save(machine, snapshot);
            snapshot.putIntArray("cooking_times", progress(machine).clone()); snapshot.putIntArray("cooking_durations", duration(machine).clone());
            snapshot.putLong("cancelled_at", player.serverLevel().getGameTime()); backups.add(snapshot); persistent.put(key, backups);
            set(get(machine, "logic"), "cookingProgress", new int[2]); set(get(machine, "logic"), "cookingDuration", new int[2]);
            ClibanoPaidState.clear(machine); ClibanoDependencyState.clearLanes(machine); REASONS.remove(machine); machine.setChanged();
            return "Прогрес Clibano скасовано; фізичні предмети й залишки збережено, паливо/душі не повертаються. Backup " + backups.size() + "/8.";
        } catch (RuntimeException denied) { return "Скасування не завершено: " + message(denied); }
    }
    /** Explicit operator quarantine only. Never convert unproven old residues into today's resources. */
    public static String quarantineResidues(ServerPlayer player, BlockEntity machine) {
        try {
            require(player != null && player.hasPermissions(2) && !player.isSpectator(), "потрібні права оператора");
            require(canonical(machine) && player.serverLevel() == machine.getLevel()
                    && player.blockPosition().distSqr(machine.getBlockPos()) <= 64
                    && Aia2MachineGuard.getOwner(machine).equals(Aia2MachineGuard.synchronizedPlayerTeam(player)), "підійдіть до Clibano своєї команди");
            CompoundTag persistent = machine.getPersistentData(); String key = "aia2_clibano_residue_backups_v1";
            require(!persistent.contains(key) || persistent.contains(key, Tag.TAG_LIST), "пошкоджений список карантинних копій");
            ListTag backups = persistent.getList(key, Tag.TAG_COMPOUND);
            require(backups.size() < 8 && (!persistent.contains(key) || backups.size() == ((ListTag)persistent.get(key)).size()), "карантинне сховище заповнене або пошкоджене");
            Object storage = call(machine, "getResiduesStorage");
            Map<?, ?> map = (Map<?, ?>)call(storage, "getResidueTypeAmountMap");
            require(map.size() <= 64, "завелике сховище залишків для карантину");
            // Resolve the exact setter before any backup or native mutation.
            method(storage.getClass(), "setTotalAmount", 1);
            CompoundTag snapshot = new CompoundTag(), rawMap = new CompoundTag();
            for (var entry : map.entrySet()) {
                require(entry.getKey() instanceof Holder<?> && entry.getValue() instanceof Integer, "непідтримуване сховище залишків");
                rawMap.putInt(((Holder<?>)entry.getKey()).unwrapKey().orElseThrow().location().toString(), (Integer)entry.getValue());
            }
            Tag unread = UNREAD_RESIDUES.get(machine);
            require(unread != null || !map.isEmpty() || ClibanoDependencyState.rawState(machine) != null, "немає залишків або журналу для карантину");
            snapshot.put("residues", unread == null ? rawMap : unread.copy());
            snapshot.putInt("native_total", ((Number)call(storage, "getTotalAmount")).intValue());
            ClibanoDependencyState.save(machine, snapshot); ClibanoPaidState.save(machine, snapshot);
            snapshot.putIntArray("cooking_times", progress(machine).clone()); snapshot.putIntArray("cooking_durations", duration(machine).clone());
            snapshot.putLong("quarantined_at", player.serverLevel().getGameTime()); backups.add(snapshot); persistent.put(key, backups);
            map.clear(); call(storage, "setTotalAmount", 0); UNREAD_RESIDUES.remove(machine);
            if (ClibanoDependencyState.status(machine) == ClibanoDependencyState.Status.CORRUPT) ClibanoDependencyState.clear(machine);
            else ClibanoDependencyState.setResidues(machine, Map.of());
            REASONS.remove(machine); machine.setChanged();
            return "Залишки переміщено до NBT-карантину " + backups.size() + "/8; результат не видається. Предмети, паливо й прогрес плавки збережено.";
        } catch (RuntimeException denied) { return "Карантин не завершено: " + message(denied); }
    }
    private static String message(Throwable error) { return error.getMessage() == null ? error.getClass().getSimpleName() : error.getMessage(); }
}
