package ua.aia2.guard;

import java.util.HashSet;
import java.util.Map;
import java.util.Set;
import java.util.function.Consumer;
import net.minecraft.core.BlockPos;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.ResourceKey;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.crafting.Recipe;
import net.minecraft.world.level.ChunkPos;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.ServerLevelAccessor;
import net.minecraft.world.level.block.Mirror;
import net.minecraft.world.level.block.Rotation;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.levelgen.structure.templatesystem.StructurePlaceSettings;
import net.minecraft.world.level.levelgen.structure.templatesystem.StructureTemplate;

/** One packet-scoped station operation. No new station data, proof, refund or rollback is fabricated. */
public final class StationConstructionAccess {
    private static final String PACKET = "earth.terrarium.adastra.common.network.packets.ServerboundConstructSpaceStationPacket";
    private static final String RECIPE = "earth.terrarium.adastra.common.recipes.SpaceStationRecipe";
    private static final ThreadLocal<Attempt> ACTIVE = new ThreadLocal<>();
    private static final class Denied extends RuntimeException {
        final Attempt attempt;
        Denied(Attempt attempt, String reason) { super(reason, null, false, false); this.attempt = attempt; }
    }
    private static final class Attempt {
        final ServerPlayer player; final ServerLevel source, target; final String team;
        final ChunkPos chunk; final Component name;
        Recipe<?> recipe; Object generation; ResourceLocation structureId;
        StationIngredients.Snapshot ingredients; StructureTemplate template; StationTemplateSnapshot snapshot;
        Map<BlockPos, BlockState> expected;
        ItemStack[] references, before; int[] plan; boolean[] removed;
        BlockPos origin; boolean paid, placing, placed, registering, registered, invalid;
        final Set<BlockPos> writes = new HashSet<>();
        Attempt(ServerPlayer player, ServerLevel target, String team, Component name) {
            this.player = player; source = player.serverLevel(); this.target = target;
            this.team = team; chunk = player.chunkPosition(); this.name = name.copy();
        }
    }
    private StationConstructionAccess() {}
    private static Object call(Object owner, String name) throws ReflectiveOperationException {
        return owner.getClass().getMethod(name).invoke(owner);
    }
    @SuppressWarnings("unchecked")
    private static ServerLevel target(ServerPlayer player, Object packet) throws ReflectiveOperationException {
        if (packet == null || !packet.getClass().getName().equals(PACKET)) return null;
        Object requested = call(packet, "dimension"); if (!(requested instanceof ResourceKey<?> key)) return null;
        Class<?> api = Class.forName("earth.terrarium.adastra.api.planets.PlanetApi");
        Object planet = api.getMethod("getPlanet", ResourceKey.class).invoke(api.getField("API").get(null), key);
        if (planet == null) return null;
        Object orbit = Class.forName("earth.terrarium.adastra.api.planets.Planet").getMethod("orbitIfPresent").invoke(planet);
        return orbit instanceof ResourceKey<?> destination ? player.serverLevel().getServer().getLevel((ResourceKey<Level>)destination) : null;
    }
    public static Consumer<Player> wrap(Object packet, Consumer<Player> original) {
        return player -> {
            Attempt active = ACTIVE.get();
            if (active != null) { active.invalid = true; return; }
            if (!(player instanceof ServerPlayer serverPlayer) || original == null
                    || !serverPlayer.serverLevel().getServer().isSameThread()) return;
            String team = Aia2MachineGuard.synchronizedPlayerTeam(serverPlayer);
            if (team.isBlank() || !serverPlayer.isAlive() || serverPlayer.isCreative() || serverPlayer.isSpectator()) {
                message(serverPlayer, "потрібна синхронізована Survival-команда"); return;
            }
            Attempt a;
            try {
                ServerLevel destination = target(serverPlayer, packet);
                if (destination == null || !Aia2MachineGuard.mayUseOwnedDimension(team, destination.dimension().location().toString())) {
                    message(serverPlayer, "орбіта ще не відкрита або відсутня"); return;
                }
                Object name = call(packet, "name"); if (!(name instanceof Component component)) return;
                a = new Attempt(serverPlayer, destination, team, component);
            } catch (ReflectiveOperationException | RuntimeException unsupported) {
                message(serverPlayer, "непідтримуваний API Ad Astra; перевірте версію JAR"); return;
            }
            ACTIVE.set(a);
            try { original.accept(player); }
            catch (Denied denied) { if (denied.attempt != a) throw denied; message(serverPlayer, denied.getMessage()); }
            finally { ACTIVE.remove(); }
        };
    }
    private static void message(ServerPlayer player, String reason) {
        player.sendSystemMessage(Component.literal("AIA2: будівництво станції зупинено: " + reason + "."));
    }
    public static boolean hasScope() { return ACTIVE.get() != null; }
    private static void require(Attempt a, boolean condition, String reason) {
        if (!condition) { if (a != null) a.invalid = true; throw new Denied(a, reason); }
    }
    private static boolean live(Attempt a) {
        if (a == null || a.invalid || a.player.isRemoved() || !a.player.isAlive() || a.player.isCreative() || a.player.isSpectator()
                || a.player.serverLevel() != a.source || !a.player.chunkPosition().equals(a.chunk)
                || a.source.getServer().getPlayerList().getPlayer(a.player.getUUID()) != a.player
                || a.source.getServer().getLevel(a.target.dimension()) != a.target
                || !a.team.equals(Aia2MachineGuard.synchronizedPlayerTeam(a.player))
                || !Aia2MachineGuard.mayUseOwnedDimension(a.team, a.target.dimension().location().toString())) return false;
        if (a.recipe == null) return true;
        try {
            if (a.generation != a.target.getRecipeManager().getRecipes()
                    || !Aia2MachineGuard.mayProcessOwnedRecipe(a.target, a.team, a.recipe)
                    || !a.target.dimension().equals(call(a.recipe, "dimension"))
                    || !a.structureId.equals(call(a.recipe, "structure"))
                    || a.target.getStructureManager().get(a.structureId).orElse(null) != a.template
                    || !a.ingredients.equals(StationIngredients.read(a.recipe))) return false;
            for (int slot = 0; slot < a.plan.length; slot++) if (a.plan[slot] > 0 && !Aia2MachineGuard.mayUseItemByTeam(
                    BuiltInRegistries.ITEM.getKey(a.before[slot].getItem()).toString(), a.team)) return false;
            return true;
        } catch (ReflectiveOperationException | RuntimeException unsupported) { return false; }
    }
    public static boolean hasIngredients(Player player, Level level, Object candidate) {
        Attempt a = ACTIVE.get();
        require(a, a != null && player == a.player && level == a.target && a.recipe == null && live(a), "недійсний контекст перевірки матеріалів");
        try {
            require(a, candidate != null && candidate.getClass().getName().equals(RECIPE) && candidate instanceof Recipe<?>, "непідтримуваний рецепт станції");
            Recipe<?> recipe = (Recipe<?>)candidate;
            require(a, a.target.dimension().equals(call(recipe, "dimension"))
                    && Aia2MachineGuard.mayProcessOwnedRecipe(a.target, a.team, recipe), "рецепт ще не відкрито або замінено");
            Object id = call(recipe, "structure"); require(a, id instanceof ResourceLocation, "недійсна структура станції");
            StructureTemplate template = a.target.getStructureManager().get((ResourceLocation)id).orElse(null);
            StationIngredients.Snapshot inputs = StationIngredients.read(recipe);
            require(a, inputs != null, "непідтримувані інгредієнти станції");
            int size = a.player.getInventory().getContainerSize(); require(a, size > 0 && size <= 64, "непідтримуваний інвентар");
            ItemStack[] references = new ItemStack[size], before = new ItemStack[size]; int[] capacities = new int[size];
            boolean[][] eligible = new boolean[inputs.counts().size()][size]; Set<ItemStack> aliases = java.util.Collections.newSetFromMap(new java.util.IdentityHashMap<>());
            for (int slot = 0; slot < size; slot++) {
                references[slot] = a.player.getInventory().getItem(slot); before[slot] = references[slot].copy();
                if (before[slot].isEmpty()) continue;
                require(a, aliases.add(references[slot]), "інвентар містить спільні посилання на матеріали");
                boolean standard = ItemStack.isSameItemSameComponents(before[slot], new ItemStack(before[slot].getItem()));
                boolean allowed = standard && Aia2MachineGuard.mayUseItemByTeam(BuiltInRegistries.ITEM.getKey(before[slot].getItem()).toString(), a.team);
                capacities[slot] = allowed ? before[slot].getCount() : 0;
                for (int row = 0; row < eligible.length; row++) eligible[row][slot] = allowed && inputs.accepted().get(row).contains(before[slot].getItem());
            }
            int[] plan = StationPaymentPlan.allocate(capacities, inputs.counts().stream().mapToInt(Integer::intValue).toArray(), eligible);
            if (plan == null) { message(a.player, "недостатньо дозволених стандартних матеріалів для всіх вимог"); return false; }
            StationTemplateSnapshot snapshot = StationTemplateSnapshot.read(template);
            require(a, snapshot != null, "відсутня або непідтримувана структура станції");
            a.recipe = recipe; a.generation = a.target.getRecipeManager().getRecipes(); a.structureId = (ResourceLocation)id;
            a.template = template; a.snapshot = snapshot; a.expected = snapshot.nonAir(); a.ingredients = inputs;
            a.references = references; a.before = before; a.plan = plan; a.removed = new boolean[size];
            a.origin = BlockPos.containing(a.chunk.getMiddleBlockX() - snapshot.size().getX() / 2.0f, 100, a.chunk.getMiddleBlockZ() - snapshot.size().getZ() / 2.0f);
            require(a, live(a) && inventory(a), "стан змінився під час планування"); return true;
        } catch (ReflectiveOperationException unsupported) { require(a, false, "непідтримуваний API рецепта станції"); return false; }
    }
    private static boolean inventory(Attempt a) {
        if (a.references == null || a.player.getInventory().getContainerSize() != a.references.length) return false;
        for (int slot = 0; slot < a.references.length; slot++) {
            ItemStack now = a.player.getInventory().getItem(slot);
            int expected = a.before[slot].getCount() - (a.removed[slot] ? a.plan[slot] : 0);
            if (now != a.references[slot] || now.getCount() != expected
                    || (expected == 0 ? !now.isEmpty() : !ItemStack.isSameItemSameComponents(now, a.before[slot]))) return false;
        }
        return true;
    }
    public static void consume(Player player, Level level) {
        Attempt a = ACTIVE.get(); require(a, a != null && player == a.player && level == a.target && !a.paid
                && a.recipe != null && live(a) && inventory(a), "оплата не відповідає поточному рецепту");
        for (int slot = 0; slot < a.plan.length; slot++) if (a.plan[slot] > 0) {
            require(a, live(a) && inventory(a), "матеріали або команда змінилися до списання");
            ItemStack removed = a.player.getInventory().removeItem(slot, a.plan[slot]); a.removed[slot] = true;
            require(a, removed.getCount() == a.plan[slot] && ItemStack.isSameItemSameComponents(removed, a.before[slot])
                    && inventory(a) && live(a), "нативне списання не підтверджено");
        }
        a.paid = true;
    }
    public static void beforePlacement(StructureTemplate template, ServerLevelAccessor world, BlockPos origin, BlockPos pivot, StructurePlaceSettings settings, int flags) {
        Attempt a = ACTIVE.get(); if (a == null) return;
        require(a, a.paid && !a.placing && !a.placed && world == a.target && template == a.template
                && a.origin.equals(origin) && origin.equals(pivot) && flags == 2
                && settings.getMirror() == Mirror.NONE && settings.getRotation() == Rotation.NONE
                && settings.getRotationPivot().equals(BlockPos.ZERO) && settings.getBoundingBox() == null
                && settings.getProcessors().isEmpty() && !settings.getKnownShape() && !settings.isIgnoreEntities()
                && settings.shouldApplyWaterlogging() && live(a) && inventory(a)
                && a.snapshot.equals(StationTemplateSnapshot.read(template)), "непідтримувані або змінені умови розміщення");
        a.placing = true;
    }
    public static boolean writePrimary(ServerLevelAccessor world, BlockPos position, BlockState state, int flags) {
        Attempt a = ACTIVE.get();
        if (a == null || !a.placing) return world.setBlock(position, state, flags);
        BlockPos local = position.subtract(a.origin); BlockState expected = a.snapshot.allBlocks().get(local);
        require(a, !a.invalid && world == a.target && flags == 2 && expected != null && expected.equals(state), "підміна блока структури");
        boolean accepted = world.setBlock(position, state, flags);
        if (!state.isAir()) require(a, accepted && world.getBlockState(position).getBlock() == state.getBlock() && a.writes.add(local.immutable()), "світ відхилив блок станції");
        return accepted;
    }
    private static boolean retained(Attempt a) {
        if (a.origin == null || a.expected == null) return false;
        for (var cell : a.expected.entrySet()) if (a.target.getBlockState(a.origin.offset(cell.getKey())).getBlock() != cell.getValue().getBlock()) return false;
        return true;
    }
    public static void afterPlacement(StructureTemplate template, boolean accepted) {
        Attempt a = ACTIVE.get(); if (a == null) return;
        require(a, a.placing && template == a.template && accepted && !a.writes.isEmpty()
                && a.writes.equals(a.expected.keySet()) && live(a) && inventory(a) && retained(a)
                && a.snapshot.equals(StationTemplateSnapshot.read(template)), "розміщення станції не підтверджено");
        a.placing = false; a.placed = true;
    }
    public static boolean beforeRegister(ServerPlayer player, ServerLevel level, Component name) {
        Attempt a = ACTIVE.get(); if (a == null) return false;
        require(a, player == a.player && level == a.target && a.name.equals(name) && a.paid && a.placed
                && !a.registering && !a.registered && live(a) && inventory(a) && retained(a)
                && a.snapshot.equals(StationTemplateSnapshot.read(a.template)), "реєстрація станції не підтверджена оплатою та розміщенням");
        a.registering = true; return true;
    }
    public static void afterRegister(ServerPlayer player, ServerLevel level, Component name) {
        Attempt a = ACTIVE.get(); if (a == null) return;
        require(a, a.registering && player == a.player && level == a.target && a.name.equals(name) && live(a) && inventory(a) && retained(a)
                && a.snapshot.equals(StationTemplateSnapshot.read(a.template)), "стан змінився під час реєстрації");
        a.registering = false; a.registered = true;
    }
}
