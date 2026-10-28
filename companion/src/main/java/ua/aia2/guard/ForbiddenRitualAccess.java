package ua.aia2.guard;

import com.google.gson.JsonArray;
import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import com.mojang.logging.LogUtils;
import com.mojang.serialization.Codec;
import com.mojang.serialization.JsonOps;
import java.lang.ref.WeakReference;
import java.lang.reflect.Field;
import java.lang.reflect.InvocationTargetException;
import java.lang.reflect.Method;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.HashMap;
import java.util.HashSet;
import java.util.HexFormat;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.UUID;
import java.util.WeakHashMap;
import java.util.function.Function;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Holder;
import net.minecraft.core.HolderLookup;
import net.minecraft.core.Registry;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.nbt.ListTag;
import net.minecraft.nbt.Tag;
import net.minecraft.resources.RegistryOps;
import net.minecraft.resources.ResourceKey;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.block.entity.BlockEntity;

/** Optional, source-pinned Forbidden Arcanus 2.6.1 adapter. No nearby-player attribution. */
public final class ForbiddenRitualAccess {
    private static final String BASE = "com.stal111.forbidden_arcanus.common.block.entity.forge.";
    private static final String FORGE = BASE + "HephaestusForgeBlockEntity";
    private static final String PEDESTAL = "com.stal111.forbidden_arcanus.common.block.entity.PedestalBlockEntity";
    private static final org.slf4j.Logger LOG = LogUtils.getLogger();
    private static final ThreadLocal<Attempt> START = new ThreadLocal<>();
    private static final ThreadLocal<Run> TICK = new ThreadLocal<>();
    // Cache values contain no manager, level, block entity, registry or strong ritual reference.
    private static final Map<Object, Cache> CACHES = new WeakHashMap<>();
    private static final Map<Object, String> REASONS = new WeakHashMap<>();
    private static final ClassValue<Map<String, Field>> FIELDS = new ClassValue<>() {
        protected Map<String, Field> computeValue(Class<?> type) { return new HashMap<>(); }
    };
    private static final ClassValue<Map<String, Method>> METHODS = new ClassValue<>() {
        protected Map<String, Method> computeValue(Class<?> type) { return new HashMap<>(); }
    };
    private static final class Cache {
        WeakReference<Object> ritual = new WeakReference<>(null);
        String definition;
        List<ItemStack> stacks = List.of();
        List<BlockPos> positions = List.of();
        String inputs;
    }
    private record View(BlockEntity forge, ServerLevel level, Object cache, String team,
                        List<ItemStack> stacks, List<BlockPos> positions) {}
    private record Checked(View view, Holder<?> holder, String id, String definition, String inputs,
                           ForbiddenDependencies.Snapshot dependencies) {}
    private record Attempt(Object manager, Object storage, UUID token, Checked checked, UUID starter) {}
    private static final class Run {
        final Object manager;
        boolean blocked, committed;
        Run(Object manager) { this.manager = manager; }
    }
    private ForbiddenRitualAccess() {}

    private static Field field(Class<?> type, String name) {
        return FIELDS.get(type).computeIfAbsent(name, ignored -> {
            for (Class<?> c = type; c != null; c = c.getSuperclass()) {
                try { Field f = c.getDeclaredField(name); f.setAccessible(true); return f; }
                catch (NoSuchFieldException absent) { /* Try the superclass. */ }
            }
            throw new IllegalStateException("Unsupported Forbidden field " + name);
        });
    }
    private static Object get(Object object, String name) {
        try { return field(object.getClass(), name).get(object); }
        catch (IllegalAccessException failure) { throw new IllegalStateException(failure); }
    }
    private static void set(Object object, String name, Object value) {
        try { field(object.getClass(), name).set(object, value); }
        catch (IllegalAccessException failure) { throw new IllegalStateException(failure); }
    }
    private static Method method(Class<?> type, String name, int count) {
        return METHODS.get(type).computeIfAbsent(name + "/" + count, ignored -> {
            for (Class<?> c = type; c != null; c = c.getSuperclass()) {
                Method found = null;
                for (Method m : c.getDeclaredMethods()) {
                    if (m.getName().equals(name) && m.getParameterCount() == count && !m.isBridge() && !m.isSynthetic()) {
                        if (found != null) throw new IllegalStateException("Ambiguous Forbidden method " + name);
                        found = m;
                    }
                }
                if (found != null) { found.setAccessible(true); return found; }
            }
            throw new IllegalStateException("Unsupported Forbidden method " + name);
        });
    }
    private static Object call(Object object, String name, Object... args) {
        try { return method(object.getClass(), name, args.length).invoke(object, args); }
        catch (InvocationTargetException failure) {
            Throwable cause = failure.getCause();
            if (cause instanceof RuntimeException runtime) throw runtime;
            if (cause instanceof Error error) throw error;
            throw new IllegalStateException("Forbidden native callback failed", cause);
        } catch (ReflectiveOperationException failure) { throw new IllegalStateException(failure); }
    }
    private static Class<?> type(Object manager, String name) {
        try { return Class.forName(name, false, manager.getClass().getClassLoader()); }
        catch (ClassNotFoundException failure) { throw new IllegalStateException(failure); }
    }
    @SuppressWarnings("unchecked")
    private static Registry<Object> registry(Object manager, ServerLevel level, String keyName) {
        try {
            Object key = type(manager, "com.stal111.forbidden_arcanus.core.registry.FARegistries").getField(keyName).get(null);
            return level.registryAccess().registryOrThrow((ResourceKey<Registry<Object>>) key);
        } catch (ReflectiveOperationException failure) { throw new IllegalStateException(failure); }
    }
    private static void require(boolean condition, String reason) {
        if (!condition) throw new IllegalArgumentException(reason);
    }
    private static void pause(Object manager, String reason) {
        if (!reason.equals(REASONS.put(manager, reason))) LOG.warn("[AIA2] Ритуал Forge призупинено: {}", reason);
    }
    private static boolean item(BlockEntity forge, ItemStack stack) {
        if (stack.isEmpty()) return true;
        String id = net.minecraft.core.registries.BuiltInRegistries.ITEM.getKey(stack.getItem()).toString();
        return !id.matches("kubejs:aia2_(tech|arcane|epoch)_key_[0-9]{2}")
                && !KeyProductionBridge.isKeyOutput(id) && Aia2MachineGuard.mayProduce(forge, stack);
    }
    private static View view(Object manager) {
        require(get(manager, "level") instanceof ServerLevel, "немає серверного рівня");
        ServerLevel level = (ServerLevel)get(manager, "level");
        require(level.getServer().isSameThread() && Aia2MachineGuard.isReady(), "захист ще не синхронізовано");
        BlockPos pos = (BlockPos)get(manager, "pos");
        require(pos != null && level.hasChunkAt(pos), "кузня не завантажена");
        BlockEntity forge = level.getBlockEntity(pos);
        require(forge != null && FORGE.equals(forge.getClass().getName()) && !forge.isRemoved()
                && call(forge, "getRitualManager") == manager, "невідповідний контролер кузні");
        String team = Aia2MachineGuard.getOwner(forge);
        require(!team.isBlank() && Aia2MachineGuard.mayTick(forge), "команда не має доступу до кузні");
        Object cache = get(manager, "dataCache");
        ItemStack main = (ItemStack)call(forge, "getStack", 4);
        require(ItemStack.matches(main, (ItemStack)call(cache, "mainIngredient")) && item(forge, main), "змінений або заблокований основний предмет");
        List<ItemStack> stacks = new ArrayList<>();
        List<BlockPos> positions = new ArrayList<>();
        stacks.add(main.copy()); positions.add(pos);
        List<?> entries = (List<?>)call(cache, "cachedIngredients");
        require(entries.size() <= 128, "завеликий список п'єдесталів");
        var unique = new HashSet<BlockPos>();
        // Native POI search radius is 4; reject stale/out-of-range physical cache entries.
        List<?> sorted = entries.stream().sorted(Comparator.comparingLong(e -> ((BlockPos)call(e, "pos")).asLong())).toList();
        for (Object entry : sorted) {
            BlockPos at = (BlockPos)call(entry, "pos");
            require(unique.add(at) && at.distSqr(pos) <= 16 && level.hasChunkAt(at), "невірна позиція п'єдесталу");
            BlockEntity pedestal = level.getBlockEntity(at);
            require(pedestal != null && PEDESTAL.equals(pedestal.getClass().getName()) && !pedestal.isRemoved(), "відсутній п'єдестал");
            ItemStack actual = (ItemStack)call(pedestal, "getStack");
            require(ItemStack.isSameItemSameComponents(actual, (ItemStack)call(entry, "stack")) && item(forge, actual), "змінений або заблокований предмет п'єдесталу");
            // Pedestals are passive shared inputs. Native POI association, not a guessed player, chooses their forge.
            stacks.add(actual.copy()); positions.add(at);
        }
        List<Holder<?>> physicalEnhancers = new ArrayList<>();
        for (int slot = 0; slot < 4; slot++) {
            ItemStack stack = (ItemStack)call(forge, "getStack", slot);
            require(item(forge, stack), "заблокований підсилювач");
            stacks.add(stack.copy()); positions.add(pos);
            try {
                Method resolve = type(manager, "com.stal111.forbidden_arcanus.common.item.enhancer.EnhancerHelper")
                        .getMethod("getEnhancerHolder", HolderLookup.Provider.class, ItemStack.class);
                Optional<?> resolved = (Optional<?>)resolve.invoke(null, level.registryAccess(), stack);
                resolved.ifPresent(value -> physicalEnhancers.add((Holder<?>)value));
            } catch (ReflectiveOperationException failure) { throw new IllegalStateException("Cannot resolve physical enhancer", failure); }
        }
        // Native requirements read cached enhancer holders: reject obsolete holder values after /reload.
        Registry<Object> enhancers = registry(manager, level, "ENHANCER_DEFINITION");
        List<?> cachedEnhancers = (List<?>)call(cache, "enhancers");
        require(physicalEnhancers.size() == cachedEnhancers.size(), "кеш підсилювачів не відповідає слотам");
        for (int i = 0; i < cachedEnhancers.size(); i++) {
            Object entry = cachedEnhancers.get(i);
            Holder<?> holder = (Holder<?>)entry;
            ResourceLocation id = holder.unwrapKey().orElseThrow().location();
            Holder<?> actual = physicalEnhancers.get(i);
            require(enhancers.get(id) == holder.value() && actual.unwrapKey().orElseThrow().location().equals(id)
                    && actual.value() == holder.value(), "кеш підсилювачів застарів; оновіть слот");
        }
        return new View(forge, level, cache, team, stacks, positions);
    }
    private static JsonElement ordered(JsonElement element) {
        if (element.isJsonObject()) {
            JsonObject sorted = new JsonObject();
            element.getAsJsonObject().keySet().stream().sorted().forEach(k -> sorted.add(k, ordered(element.getAsJsonObject().get(k))));
            return sorted;
        }
        if (element.isJsonArray()) {
            JsonArray array = new JsonArray(); element.getAsJsonArray().forEach(v -> array.add(ordered(v))); return array;
        }
        return element;
    }
    private static String sha(JsonElement data) {
        try { return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(ordered(data).toString().getBytes(StandardCharsets.UTF_8))); }
        catch (java.security.NoSuchAlgorithmException impossible) { throw new AssertionError(impossible); }
    }
    @SuppressWarnings("unchecked")
    private static String definition(Object manager, Object ritual, ServerLevel level) {
        Cache cache = CACHES.computeIfAbsent(manager, ignored -> new Cache());
        if (cache.ritual.get() != ritual || cache.definition == null) {
            try {
                Codec<Object> codec = (Codec<Object>)ritual.getClass().getField("DIRECT_CODEC").get(null);
                cache.definition = sha(codec.encodeStart(RegistryOps.create(JsonOps.INSTANCE, level.registryAccess()), ritual).getOrThrow());
                cache.ritual = new WeakReference<>(ritual);
            } catch (ReflectiveOperationException failure) { throw new IllegalStateException(failure); }
        }
        return cache.definition;
    }
    private static String inputs(Object manager, View view) {
        Cache cache = CACHES.computeIfAbsent(manager, ignored -> new Cache());
        boolean same = cache.positions.equals(view.positions) && cache.stacks.size() == view.stacks.size();
        for (int i = 0; same && i < cache.stacks.size(); i++) same = ItemStack.matches(cache.stacks.get(i), view.stacks.get(i));
        if (!same || cache.inputs == null) {
            JsonArray array = new JsonArray();
            for (int i = 0; i < view.stacks.size(); i++) {
                JsonObject entry = new JsonObject(); entry.addProperty("position", view.positions.get(i).asLong());
                ItemStack stack = view.stacks.get(i);
                entry.add("stack", stack.isEmpty() ? new JsonObject() : ItemStack.CODEC.encodeStart(
                        RegistryOps.create(JsonOps.INSTANCE, view.level.registryAccess()), stack).getOrThrow());
                array.add(entry);
            }
            cache.inputs = sha(array); cache.positions = List.copyOf(view.positions);
            cache.stacks = view.stacks.stream().map(ItemStack::copy).toList();
        }
        return cache.inputs;
    }
    private static Checked checked(Object manager, View view, ResourceLocation id, boolean starting) {
        Registry<Object> rituals = registry(manager, view.level, "RITUAL");
        Holder<?> holder = rituals.getHolder(id).orElseThrow(() -> new IllegalArgumentException("визначення ритуалу відсутнє"));
        Object ritual = holder.value();
        int duration = ((Number)call(ritual, "duration")).intValue();
        require(duration > 0 && duration <= 1200000, "непідтримувана тривалість ритуалу");
        List<ItemStack> pedestalStacks = view.stacks.subList(1, view.stacks.size() - 4);
        // Current tag bindings and enhancer definitions are checked before any native callbacks.
        var dependencies = ForbiddenDependencies.capture(ritual, registry(manager, view.level, "ENHANCER_DEFINITION"),
                (List<?>)call(view.cache, "enhancers"), view.level.registryAccess(), pedestalStacks, view.stacks.getFirst());
        require(Boolean.TRUE.equals(call(ritual, "checkIngredients", pedestalStacks, view.stacks.getFirst())), "склад ритуалу не відповідає визначенню");
        require(Boolean.TRUE.equals(call(ritual, "canStart", view.cache, get(manager, "forgeTier"))), "не виконано вимоги ритуалу");
        if (starting) {
            Object essenceManager = call(view.forge, "getEssenceManager");
            require(Boolean.TRUE.equals(call(manager, "canStartRitual", ritual, call(essenceManager, "getCurrentEssences"))), "недостатньо есенцій");
        }
        Object result = call(ritual, "result");
        String resultType = result.getClass().getName();
        String resultBase = BASE + "ritual.result.";
        if (resultType.equals(resultBase + "UpgradeTierResult")) {
            int tier = ((Number)call(result, "resultTier")).intValue();
            require(tier >= 1 && tier <= 5 && Aia2MachineGuard.mayObserveStage(view.team,
                    Aia2MachineGuard.getRequiredStage("forbidden_arcanus:hephaestus_forge_tier_" + tier)), "наступний рівень кузні заблоковано");
        } else {
            require(resultType.equals(resultBase + "CreateItemResult") || resultType.equals(resultBase + "TransmuteInputResult"), "невідомий тип результату ритуалу");
            ItemStack preview = (ItemStack)call(result, "getResultItem", view.stacks.getFirst().copy());
            require(!preview.isEmpty() && item(view.forge, preview), "результат ритуалу заблоковано");
        }
        return new Checked(view, holder, id.toString(), definition(manager, ritual, view.level), inputs(manager, view), dependencies);
    }

    /** Redirects only startRitual's Optional.map; native lambda and material costs remain native. */
    public static Optional<?> start(Object manager, ServerPlayer player, Object storage,
                                    Optional<?> selected, Function<Object, Object> mapper) {
        if (selected.isEmpty()) return Optional.empty();
        Checked checked;
        UUID token;
        try {
            require(get(manager, "activeRitualData") == null && !ForbiddenPaidState.hasRetainedActive(manager), "вже існує незавершений ритуал");
            View view = view(manager);
            require(player != null && player.serverLevel() == view.level
                    && view.team.equals(Aia2MachineGuard.synchronizedPlayerTeam(player)), "гравець не належить команді кузні");
            require(call(call(view.forge, "getEssenceManager"), "getStorage") == storage, "підмінене сховище есенцій");
            Holder<?> old = (Holder<?>)selected.get();
            ResourceLocation id = old.unwrapKey().orElseThrow().location();
            checked = checked(manager, view, id, true);
            token = ForbiddenPaidState.begin(manager);
        } catch (RuntimeException denied) { pause(manager, denied.getMessage() == null ? denied.getClass().getSimpleName() : denied.getMessage()); return Optional.empty(); }
        Attempt previous = START.get();
        START.set(new Attempt(manager, storage, token, checked, player.getUUID()));
        try { return Optional.ofNullable(mapper.apply(checked.holder)); }
        finally {
            try {
                Tag active = activeTag(manager);
                if (active != null) ForbiddenPaidState.captureActive(manager, active);
                ForbiddenPaidState.abortUnpaid(manager, token, get(manager, "activeRitualData") != null);
                checked.view.forge.setChanged();
            } finally { if (previous == null) START.remove(); else START.set(previous); }
        }
    }
    /** Exactly after native reduction returned, even if later pedestal callbacks throw. */
    public static void paid(Object storage, Object cost) {
        Attempt attempt = START.get();
        if (attempt == null || attempt.storage != storage) return;
        if (cost != call(call(attempt.checked.holder.value(), "requirements"), "essences")) return;
        try {
            Checked now = checked(attempt.manager, view(attempt.manager), ResourceLocation.parse(attempt.checked.id), false);
            require(now.definition.equals(attempt.checked.definition) && now.inputs.equals(attempt.checked.inputs)
                    && now.dependencies.equals(attempt.checked.dependencies) && now.view.team.equals(attempt.checked.view.team),
                    "залежності ритуалу змінилися під час оплати; операцію збережено без підтвердження");
            CompoundTag raw = activeTag(attempt.manager);
            ForbiddenDependencies.attach(raw, attempt.checked.dependencies);
            ForbiddenPaidState.markPaid(attempt.manager, attempt.token,
                    new ForbiddenPaidState.Receipt(attempt.checked.id, attempt.checked.definition,
                            attempt.checked.inputs, attempt.checked.view.team, attempt.starter), raw);
            REASONS.remove(attempt.manager);
        } catch (RuntimeException denied) {
            // The native cost has already been paid. Retain pending state instead of throwing
            // into the server event, inventing a refund or adopting a different definition.
            pause(attempt.manager, denied.getMessage() == null ? denied.getClass().getSimpleName() : denied.getMessage());
        }
        attempt.checked.view.forge.setChanged();
    }
    /** Encode only the verified native primitive fields; missing registry entries cannot erase them. */
    public static CompoundTag activeTag(Object manager) {
        Object active = get(manager, "activeRitualData");
        if (active == null) return null;
        Object id = call(active, "getRitualId");
        if (id == null) return null;
        CompoundTag tag = new CompoundTag(); tag.putString("ritual", id.toString());
        tag.putInt("counter", ((Number)call(active, "getCounter")).intValue());
        tag.putInt("lightning_counter", ((Number)call(active, "getLightningCounter")).intValue());
        tag.putUUID("started_by", (UUID)call(active, "getStartedBy")); return tag;
    }
    private static Object rebind(Object manager, Holder<?> holder, CompoundTag raw) {
        try {
            return type(manager, BASE + "ritual.ActiveRitualData").getConstructor(Holder.class, int.class, int.class, UUID.class)
                    .newInstance(holder, raw.getInt("counter"), raw.getInt("lightning_counter"), raw.getUUID("started_by"));
        } catch (ReflectiveOperationException failure) { throw new IllegalStateException(failure); }
    }
    private static Checked resume(Object manager, boolean committing) {
        var receipt = ForbiddenPaidState.receipt(manager).orElseThrow(() -> new IllegalArgumentException(
                "немає підтвердженої оплати (" + ForbiddenPaidState.status(manager) + "); див. /aia2forge status"));
        View view = view(manager);
        require(view.team.equals(receipt.ownerTeam()), "власник кузні змінився");
        Checked checked = checked(manager, view, ResourceLocation.parse(receipt.ritualId()), false);
        require(checked.definition.equals(receipt.definitionFingerprint()), "визначення оплаченого ритуалу змінено");
        require(checked.inputs.equals(receipt.inputFingerprint()), "входи оплаченого ритуалу змінено");
        require(ForbiddenDependencies.matches(ForbiddenPaidState.rawActive(manager), checked.dependencies),
                "залежності оплаченого ритуалу змінено або відсутній їхній історичний доказ; див. /aia2forge status");
        ServerPlayer starter = view.level.getServer().getPlayerList().getPlayer(receipt.starter());
        require(starter == null || view.team.equals(Aia2MachineGuard.synchronizedPlayerTeam(starter)), "команда ініціатора змінилася");
        CompoundTag raw = activeTag(manager);
        if (raw == null) raw = (CompoundTag)ForbiddenPaidState.rawActive(manager);
        require(raw != null && raw.getString("ritual").equals(checked.id) && raw.getUUID("started_by").equals(receipt.starter()), "активний ритуал не відповідає оплаті");
        int duration = ((Number)call(checked.holder.value(), "duration")).intValue();
        require(raw.getInt("counter") <= duration + (committing ? 1 : 0) && raw.getInt("counter") >= 0, "лічильник ритуалу поза межами");
        Object active = get(manager, "activeRitualData");
        if (active == null || call(active, "getRitual") != checked.holder.value()) set(manager, "activeRitualData", rebind(manager, checked.holder, raw));
        return checked;
    }
    public static boolean inTick(Object manager) { return TICK.get() != null && TICK.get().manager == manager; }
    @SuppressWarnings("unchecked")
    public static Optional<ItemStack> tick(Object manager) {
        if (get(manager, "activeRitualData") == null && !ForbiddenPaidState.hasRetainedActive(manager)) return Optional.empty();
        Checked checked;
        try { checked = resume(manager, false); }
        catch (RuntimeException denied) { pause(manager, denied.getMessage() == null ? denied.getClass().getSimpleName() : denied.getMessage()); return Optional.empty(); }
        CompoundTag before = activeTag(manager);
        Run previous = TICK.get(), run = new Run(manager); TICK.set(run);
        try {
            Optional<ItemStack> result = (Optional<ItemStack>)call(manager, "tick");
            if (run.blocked && !run.committed) {
                set(manager, "activeRitualData", rebind(manager, checked.holder, before));
                return Optional.empty(); // Optional.of(EMPTY) would otherwise clear the main slot.
            }
            REASONS.remove(manager); return result;
        } finally {
            try {
                if (!run.committed) {
                    Tag current = activeTag(manager);
                    if (current != null) ForbiddenPaidState.captureActive(manager, current);
                }
                checked.view.forge.setChanged();
            } finally { if (previous == null) TICK.remove(); else TICK.set(previous); }
        }
    }
    /** Native failure during load/onDataChanged is destructive and has no consuming caller. */
    public static boolean mayCommit(Object manager) {
        Run run = TICK.get();
        if (run == null || run.manager != manager || run.committed) return false;
        try {
            resume(manager, true); run.committed = true;
            // Before native reset/effects, so a later native exception cannot replay the receipt.
            ForbiddenPaidState.clear(manager); return true;
        } catch (RuntimeException denied) {
            run.blocked = true; pause(manager, denied.getMessage() == null ? denied.getClass().getSimpleName() : denied.getMessage()); return false;
        }
    }
    public static void beforeSave(Object manager) {
        Tag active = activeTag(manager); if (active != null) ForbiddenPaidState.captureActive(manager, active);
    }
    public static void afterSave(Object manager, CompoundTag tag) {
        ForbiddenPaidState.save(manager, tag, ForbiddenPaidState.hasRetainedActive(manager));
    }
    /** Native input slots are consumed before ritual.tick; pipes cannot launder future items into essence. */
    public static boolean mayConsumeEssence(BlockEntity forge, ItemStack input) {
        return forge != null && forge.getLevel() instanceof ServerLevel level && FORGE.equals(forge.getClass().getName())
                && !forge.isRemoved() && level.getServer().isSameThread() && level.hasChunkAt(forge.getBlockPos())
                && level.getBlockEntity(forge.getBlockPos()) == forge && Aia2MachineGuard.isReady()
                && !Aia2MachineGuard.getOwner(forge).isBlank() && !input.isEmpty()
                && Aia2MachineGuard.mayTick(forge) && item(forge, input);
    }
    private static Object nearForge(ServerPlayer player, int x, int y, int z) {
        require(player != null && !Aia2MachineGuard.synchronizedPlayerTeam(player).isBlank(), "гравця ще не синхронізовано");
        BlockPos pos = new BlockPos(x, y, z);
        require(player.blockPosition().distSqr(pos) <= 64 && player.serverLevel().hasChunkAt(pos), "підійдіть ближче до кузні");
        BlockEntity forge = player.serverLevel().getBlockEntity(pos);
        require(forge != null && FORGE.equals(forge.getClass().getName()), "за координатами немає кузні");
        require(Aia2MachineGuard.getOwner(forge).equals(Aia2MachineGuard.synchronizedPlayerTeam(player)), "кузня належить іншій команді");
        return call(forge, "getRitualManager");
    }
    public static String status(ServerPlayer player, int x, int y, int z) {
        try {
            Object manager = nearForge(player, x, y, z);
            return "Forge: " + ForbiddenPaidState.status(manager) + "; " + REASONS.getOrDefault(manager, "причин призупинення не зареєстровано");
        } catch (RuntimeException invalid) { return "Forge: " + invalid.getMessage(); }
    }
    /** Operator-requested recovery only. Keeps all physical items; no essence refund or result. */
    public static String cancel(ServerPlayer player, int x, int y, int z) {
        try {
            require(player != null && player.hasPermissions(2), "потрібні права оператора");
            Object manager = nearForge(player, x, y, z);
            BlockEntity forge = player.serverLevel().getBlockEntity(new BlockPos(x, y, z));
            CompoundTag persistent = forge.getPersistentData();
            String key = "aia2_fa_cancel_backups_v1";
            require(!persistent.contains(key) || persistent.contains(key, Tag.TAG_LIST), "пошкоджений список резервних копій");
            ListTag backups = persistent.getList(key, Tag.TAG_COMPOUND);
            require(backups.size() < 8 && (!persistent.contains(key) || backups.size() == ((ListTag)persistent.get(key)).size()), "сховище резервних копій заповнене або пошкоджене");
            CompoundTag saved = new CompoundTag(); beforeSave(manager); ForbiddenPaidState.save(manager, saved, true);
            Tag raw = activeTag(manager); if (!saved.contains(ForbiddenPaidState.ACTIVE_TAG) && raw != null) saved.put(ForbiddenPaidState.ACTIVE_TAG, raw);
            require(!saved.isEmpty(), "немає незавершеного ритуалу");
            saved.putLong("cancelled_at", player.serverLevel().getGameTime()); backups.add(saved); persistent.put(key, backups);
            forge.setChanged();
            // Do not call native reset/fail: both clear or eject physical inputs.
            call(manager, "setActiveRitual", null, null); set(manager, "validRitual", null);
            ForbiddenPaidState.clear(manager); REASONS.remove(manager);
            call(get(manager, "magicCircleController"), "removeMagicCircle", player.serverLevel(), forge.getBlockPos());
            call(manager, "updateRitualIndicator", false);
            for (Object entry : (List<?>)call(get(manager, "dataCache"), "cachedIngredients")) {
                BlockEntity pedestal = player.serverLevel().getBlockEntity((BlockPos)call(entry, "pos"));
                if (pedestal != null && PEDESTAL.equals(pedestal.getClass().getName())) call(pedestal, "setItemHeightTarget", 120);
            }
            return "Ритуал скасовано; предмети збережено, есенції не повертаються. Резервна копія: " + backups.size() + "/8.";
        } catch (RuntimeException invalid) { return "Скасування не завершено: " + invalid.getMessage(); }
    }
}
