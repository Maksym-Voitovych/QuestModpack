package ua.aia2.guard;

import com.google.gson.GsonBuilder;
import com.mojang.authlib.GameProfile;
import net.minecraft.SharedConstants;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.entity.item.ItemEntity;
import net.minecraft.world.inventory.ContainerLevelAccess;
import net.minecraft.world.inventory.CraftingMenu;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.CrafterBlock;
import net.minecraft.world.level.block.HopperBlock;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.entity.CrafterBlockEntity;
import net.minecraft.world.level.block.entity.FurnaceBlockEntity;
import net.minecraft.world.level.block.entity.HopperBlockEntity;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.AABB;
import net.neoforged.bus.api.SubscribeEvent;
import net.neoforged.fml.common.EventBusSubscriber;
import net.neoforged.neoforge.common.util.FakePlayerFactory;
import net.neoforged.neoforge.event.server.ServerStartedEvent;
import net.neoforged.neoforge.event.entity.EntityJoinLevelEvent;
import net.neoforged.neoforge.event.tick.ServerTickEvent;

import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Instant;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.UUID;
import java.util.stream.Collectors;

/**
 * Opt-in integration tests using actual Minecraft server ticks and native inventories.
 * Disabled in ordinary installs. The runner must create an explicit marker in its
 * own development run directory; no player or modpack world is used.
 */
@EventBusSubscriber(modid = Aia2MachineGuard.MOD_ID)
public final class NativeSmokeTests {
    private static final String TEAM_A = "native-test-a-" + UUID.randomUUID();
    private static final String TEAM_B = "native-test-b-" + UUID.randomUUID();
    private static final BlockPos A = new BlockPos(8, 252, 8);
    private static final BlockPos B = new BlockPos(11, 252, 8);
    private static final BlockPos UNOWNED = new BlockPos(8, 252, 11);
    private static final BlockPos CRAFTER = new BlockPos(11, 252, 11);
    private static final BlockPos FEEDER = CRAFTER.above();
    private static final BlockPos POWER = CRAFTER.relative(Direction.NORTH);
    private static final BlockPos BENCH = new BlockPos(8, 252, 13);
    // Reserved only in this runner's explicitly owned development world.
    private static final BlockPos FIRE_PERSIST = new BlockPos(14, 252, 14);
    private static final List<BlockPos> POSITIONS = List.of(A, B, UNOWNED, CRAFTER, FEEDER, POWER, BENCH);
    private static final AABB AREA = new AABB(4, 250, 4, 16, 257, 16);
    private record Original(BlockState state, CompoundTag data) {}
    private static final Map<BlockPos, Original> ORIGINALS = new LinkedHashMap<>();
    private static final List<Map<String, Object>> CHECKS = new ArrayList<>();
    private static ServerLevel level;
    private static MinecraftServer server;
    private static Set<UUID> existingItemEntities;
    private static boolean wasForced;
    private static boolean running;
    private static int ticks;
    private static String startTime;
    private static final List<ItemEntity> emittedItems = new ArrayList<>();

    @SubscribeEvent
    public static void emitted(EntityJoinLevelEvent event) {
        if (running && event.getLevel() == level && !event.isCanceled()
                && event.getEntity() instanceof ItemEntity item && item.getItem().is(Items.IRON_INGOT)
                && AREA.contains(item.position()) && !existingItemEntities.contains(item.getUUID())
                && emittedItems.stream().noneMatch(old -> old.getUUID().equals(item.getUUID()))) emittedItems.add(item);
    }

    private NativeSmokeTests() {}

    @SubscribeEvent
    public static void started(ServerStartedEvent event) {
        if (!Boolean.getBoolean("aia2.guard.nativeSmoke")) return;
        server = event.getServer();
        if (!SharedConstants.IS_RUNNING_IN_IDE || !Files.isRegularFile(Path.of(".aia2-native-smoke-allow"))) {
            throw new IllegalStateException("AIA2 smoke tests require IDE development mode and explicit run-directory marker");
        }
        startTime = Instant.now().toString();
        try {
            if (Boolean.getBoolean("aia2.guard.nativeSmokeReceiptVerify")) {
                verifyStoredReceipt();
                return;
            }
            setup();
            running = true;
        } catch (Throwable failure) {
            finish(failure);
        }
    }

    private static void verifyStoredReceipt() {
        level = server.overworld();
        wasForced = level.getForcedChunks().contains(A.getX() >> 4 | (long) (A.getZ() >> 4) << 32);
        String team = System.getProperty("aia2.guard.nativeSmokeReceiptTeam", "");
        check(team.startsWith("native-test-a-"), "restart verification is restricted to this runner's generated test team");
        check(Aia2MachineGuard.hasProductionProof(server, team, 8, "tech"), "a fresh Minecraft server reloads the actual production receipt from the world SavedData file");
        check(!Aia2MachineGuard.hasProductionProof(server, team, 8, "arcane"), "restart does not fabricate the independent missing arcane proof");
        check(ProductionMilestoneBridge.hasProof(server, team, "native_crafter_fixture"),
                "a fresh server reloads the separate native process observation from SavedData");
        check(ProductionMilestoneBridge.hasProof(server,team,"native_observed_fixture"),
                "actual-output verified observation also reloads in a second JVM");
        check(FireWorksiteAccess.owner(level, FIRE_PERSIST).equals(team),
                "a fresh JVM reloads actual fire worksite ownership from SavedData");
        Aia2MachineGuard.clearRuntime();
        check(FireWorksiteAccess.owner(level, FIRE_PERSIST).equals(team),
                "runtime reset does not erase a persistent fire worksite");
        level.setBlockAndUpdate(FIRE_PERSIST, Blocks.AIR.defaultBlockState());
        check(FireWorksiteAccess.owner(level, FIRE_PERSIST).isBlank(),
                "actual base mutation hook revokes persistent ownership after restart");
        check(Aia2MachineGuard.hasProductionProof(server, team, 8, "tech"), "runtime bridge initialization never resets a receipt loaded after restart");
        check(ProductionMilestoneBridge.hasProof(server, team, "native_crafter_fixture"),
                "runtime reset never clears a reloaded generic process observation");
        finish(null);
    }

    private static void setup() {
        level = server.overworld();
        wasForced = level.getForcedChunks().contains(A.getX() >> 4 | (long) (A.getZ() >> 4) << 32);
        level.setChunkForced(A.getX() >> 4, A.getZ() >> 4, true);
        level.getChunkAt(A);
        existingItemEntities = level.getEntitiesOfClass(ItemEntity.class, AREA).stream()
                .map(ItemEntity::getUUID).collect(Collectors.toSet());
        for (BlockPos pos : POSITIONS) {
            BlockEntity old = level.getBlockEntity(pos);
            ORIGINALS.put(pos, new Original(level.getBlockState(pos),
                    old == null ? null : old.saveWithFullMetadata(level.registryAccess())));
        }
        Aia2MachineGuard.clearRuntime();
        Aia2MachineGuard.setRulesJson("{\"minecraft:furnace\":5,\"minecraft:crafter\":2,\"minecraft:hopper\":0,\"minecraft:diamond_block\":32}");
        Aia2MachineGuard.setItemRulesJson("{\"minecraft:iron_ingot\":8,\"minecraft:iron_nugget\":0,\"minecraft:coal\":0,\"minecraft:raw_iron\":0,\"minecraft:diamond\":99}");
        Aia2MachineGuard.setRecipeRulesJson("{\"minecraft:iron_ingot_from_smelting_raw_iron\":7,\"minecraft:iron_ingot_from_nuggets\":8}");
        Aia2MachineGuard.configureKeyRulesJson("[{\"recipeId\":\"minecraft:iron_ingot_from_nuggets\",\"output\":\"minecraft:iron_ingot\",\"epoch\":8,\"branch\":\"tech\",\"serializer\":\"minecraft:crafting_shaped\"}]");
        ProductionMilestoneBridge.configureJson("[{\"id\":\"native_crafter_fixture\",\"recipeIds\":[\"minecraft:iron_ingot_from_nuggets\"],\"output\":\"minecraft:iron_ingot\",\"epoch\":8,\"serializer\":\"minecraft:crafting_shaped\"}]");
        Aia2MachineGuard.setTeamProgress(TEAM_A, 3);
        Aia2MachineGuard.setTeamProgress(TEAM_B, 7);
        Aia2MachineGuard.setReady();
        check(Aia2MachineGuard.isReady(), "native bridge became ready with nonempty rules and teams");
        furnace(A, TEAM_A);
        furnace(B, TEAM_B);
        furnace(UNOWNED, null);
        level.setBlockAndUpdate(CRAFTER, Blocks.CRAFTER.defaultBlockState());
        CrafterBlockEntity crafter = crafter();
        Aia2MachineGuard.setOwner(crafter, TEAM_A);
        level.setBlockAndUpdate(FEEDER, Blocks.HOPPER.defaultBlockState().setValue(HopperBlock.FACING, Direction.DOWN));
        HopperBlockEntity feeder = (HopperBlockEntity) level.getBlockEntity(FEEDER);
        feeder.setItem(0, new ItemStack(Items.IRON_NUGGET, 9));
        level.setBlockAndUpdate(POWER, Blocks.AIR.defaultBlockState());
        level.setBlockAndUpdate(BENCH, Blocks.CRAFTING_TABLE.defaultBlockState());
        testPersistenceAndOwnership();
        testFakePlayerCrafting();
        testStrictMachineContext();
        testPassiveBoundaryFixtures();
        testFireWorksites();
        check(!Aia2MachineGuard.hasProductionProof(server, TEAM_A, 8, "tech"), "constructing or inserting a key item does not grant a production receipt");
        check(!ProductionMilestoneBridge.hasProof(server, TEAM_A, "native_crafter_fixture"),
                "constructing or inserting an observed output does not create a generic process observation");
    }

    private static void testPassiveBoundaryFixtures() {
        var receiver = level.getBlockEntity(B);
        check(ProjectEPassiveAccess.mayUseStored(receiver, new ItemStack(Items.RAW_IRON)),
                "passive boundary accepts canonical owned server receiver and available item");
        check(!ProjectEPassiveAccess.mayUseStored(receiver, new ItemStack(Items.DIAMOND)),
                "passive boundary checks actual stored item's future floor");
        check(!ProjectEPassiveAccess.mayUseStored(level.getBlockEntity(UNOWNED), new ItemStack(Items.RAW_IRON)),
                "passive boundary denies unowned actual receiver");
        var impostor = BlockEntity.loadStatic(B, receiver.getBlockState(), receiver.saveWithFullMetadata(level.registryAccess()), level.registryAccess());
        check(!ProjectEPassiveAccess.mayUseStored(impostor, new ItemStack(Items.RAW_IRON)),
                "same-position detached receiver cannot borrow real world's ownership");
        var fake = FakePlayerFactory.get(level, new GameProfile(UUID.randomUUID(), "AIA2PassiveTest"));
        check(!ProjectEPassiveAccess.mayUse(fake, new ItemStack(Items.RAW_IRON)),
                "passive personal callback rejects actual FakePlayer even for basic item");
        check(!ProjectEPassiveAccess.isProjectE(new ItemStack(Items.IRON_CHESTPLATE)),
                "generic equipment hook leaves vanilla namespace outside PE policy");
        try {
            // Execute the real native collectEquipmentChanges redirect and RETURN hook.
            var update = net.minecraft.world.entity.LivingEntity.class.getDeclaredMethod("detectEquipmentUpdates");
            update.setAccessible(true);
            var armor = fake.getAttribute(net.minecraft.world.entity.ai.attributes.Attributes.ARMOR);
            double before = armor.getValue();
            ItemStack chest = new ItemStack(Items.IRON_CHESTPLATE);
            fake.setItemSlot(net.minecraft.world.entity.EquipmentSlot.CHEST, chest);
            update.invoke(fake);
            check(armor.getValue() == before + 6, "real equipment application retains vanilla iron chestplate's armor");
            update.invoke(fake);
            check(armor.getValue() == before + 6 && fake.getItemBySlot(net.minecraft.world.entity.EquipmentSlot.CHEST) == chest,
                    "unchanged vanilla equipment neither accumulates attributes nor changes item identity");
            fake.setItemSlot(net.minecraft.world.entity.EquipmentSlot.CHEST, ItemStack.EMPTY);
            update.invoke(fake);
            check(armor.getValue() == before, "unfiltered native removal clears old vanilla equipment modifier");
        } catch (ReflectiveOperationException failure) {
            throw new IllegalStateException("Native equipment dispatch fixture failed", failure);
        }
    }

    private static void testFireWorksites() {
        var recipe = level.getRecipeManager().byKey(net.minecraft.resources.ResourceLocation.parse(
                "minecraft:iron_ingot_from_smelting_raw_iron")).orElseThrow().value();
        var outputs = List.of(new ItemStack(Items.RAW_IRON));
        check(!FireWorksiteAccess.register(level, BENCH, TEAM_A), "early team cannot register a fire worksite");
        Aia2MachineGuard.setTeamProgress(TEAM_A, 18);
        check(FireWorksiteAccess.register(level, BENCH, TEAM_A), "trusted server operation registers an epoch19 team's exact base");
        check(FireWorksiteAccess.register(level, BENCH, TEAM_A), "same-owner claim is idempotent");
        Aia2MachineGuard.setTeamProgress(TEAM_B, 18);
        check(!FireWorksiteAccess.register(level, BENCH, TEAM_B), "another authorized team cannot take an existing worksite");
        check(FireWorksiteAccess.mayRunAtWorksite(level, BENCH.above(), recipe, outputs, null),
                "owned worksite permits current native recipe and available outputs without an online player");
        check(!FireWorksiteAccess.mayRunAtWorksite(level, BENCH.above().east(), recipe, outputs, null),
                "nearby ownership never authorizes an unclaimed position");
        check(!FireWorksiteAccess.mayRunAtWorksite(level, BENCH.above(), recipe, List.of(new ItemStack(Items.DIAMOND)), null),
                "all possible outputs are checked against current item policy");
        check(!FireWorksiteAccess.mayRunAtWorksite(level, BENCH.above(), recipe, List.of(new ItemStack(Items.IRON_INGOT)), null),
                "even an eligible manufactured key output is forbidden in fire crafting");
        check(!FireWorksiteAccess.mayRunAtWorksite(level, BENCH.above(), recipe, outputs, Blocks.DIAMOND_BLOCK),
                "post-burn base block requires its own stage");
        check(!FireWorksiteAccess.mayRunAtWorksite(level, BENCH.above(), recipe, List.of(), null),
                "empty possible output definitions cannot authorize fire production");
        check(!FireWorksiteAccess.maySpawn(level, BENCH.above(), recipe),
                "actual optional entry rejects non-EnderIO recipes even at a valid owned site");
        Aia2MachineGuard.setTeamProgress(TEAM_A, 17);
        check(!FireWorksiteAccess.mayRunAtWorksite(level, BENCH.above(), recipe, outputs, null),
                "team downgrade immediately stops fire worksite production");
        Aia2MachineGuard.setTeamProgress(TEAM_A, 18);
        level.setBlockAndUpdate(BENCH, Blocks.CRAFTING_TABLE.defaultBlockState());
        check(FireWorksiteAccess.owner(level, BENCH).equals(TEAM_A), "no-op native block update preserves a worksite");
        level.setBlockAndUpdate(BENCH, Blocks.AIR.defaultBlockState());
        level.setBlockAndUpdate(BENCH, Blocks.CRAFTING_TABLE.defaultBlockState());
        check(FireWorksiteAccess.owner(level, BENCH).isBlank(), "break and same-type replacement cannot inherit ownership");
        var fake = FakePlayerFactory.get(level, new GameProfile(UUID.randomUUID(), "AIA2FireTest"));
        check(Aia2MachineGuard.synchronizedPlayerTeam(fake).isBlank(), "real FakePlayer cannot claim through a synchronized team");
        var saved = level.getDataStorage().get(FireWorksiteAccess.SiteData.FACTORY, FireWorksiteAccess.DATA_NAME);
        CompoundTag invalid = saved.save(new CompoundTag(), level.registryAccess());
        invalid.putInt("schema", 99);
        var blocked = FireWorksiteAccess.SiteData.load(invalid, level.registryAccess());
        boolean rejected = false;
        try { blocked.save(new CompoundTag(), level.registryAccess()); }
        catch (IllegalStateException expected) { rejected = true; }
        check(blocked.blocked && rejected && !blocked.isDirty(), "unknown fire schema remains blocked/clean and cannot overwrite its old ledger");
        level.setBlockAndUpdate(FIRE_PERSIST, Blocks.AIR.defaultBlockState());
        level.setBlockAndUpdate(FIRE_PERSIST, Blocks.BEDROCK.defaultBlockState());
        check(FireWorksiteAccess.register(level, FIRE_PERSIST, TEAM_A), "actual bedrock worksite retained only for second-JVM persistence verification");
        Aia2MachineGuard.setTeamProgress(TEAM_A, 3);
        Aia2MachineGuard.setTeamProgress(TEAM_B, 7);
    }

    private static void testStrictMachineContext() {
        var recipe = level.getRecipeManager().byKey(net.minecraft.resources.ResourceLocation.parse(
                "minecraft:iron_ingot_from_smelting_raw_iron")).orElseThrow().value();
        check(!Aia2MachineGuard.mayProcessRecipeInCurrentTick(recipe), "strict component processing rejects absent ticker context");
        check(!Aia2MachineGuard.mayReplicateOutputInCurrentTick(new ItemStack(Items.RAW_IRON)), "replication rejects absent ticker context");
        var parent = Aia2MachineGuard.enterTick(level.getBlockEntity(B));
        try {
            check(Aia2MachineGuard.mayProcessRecipeInCurrentTick(recipe), "strict component accepts an authorized real owner and canonical recipe");
            var selected=EnderTaskAccess.lookup(level.getBlockEntity(A),level.getRecipeManager(),
                    net.minecraft.world.item.crafting.RecipeType.SMELTING,
                    new net.minecraft.world.item.crafting.SingleRecipeInput(new ItemStack(Items.RAW_IRON)),level);
            check(selected.isPresent() && !Aia2MachineGuard.mayProcessRecipe(level.getBlockEntity(A),selected.get().value()),
                    "pure protected callback selects a real recipe while locked receiver execution remains denied");
            check(Aia2MachineGuard.mayProcessRecipeInCurrentTick(recipe),"pure callback restores the actual caller ticker context");
            check(Aia2MachineGuard.mayReplicateOutputInCurrentTick(new ItemStack(Items.RAW_IRON)), "ordinary authorized copy output remains available");
            check(!Aia2MachineGuard.mayReplicateOutputInCurrentTick(new ItemStack(Items.DIAMOND)), "imported future output is denied independently of machine availability");
            check(!Aia2MachineGuard.mayReplicateOutputInCurrentTick(new ItemStack(Items.IRON_INGOT)), "configured manufacture-receipt outputs cannot be replicated");
            check(!Aia2MachineGuard.mayReplicateOutputInCurrentTick(ItemStack.EMPTY), "empty copy output is denied");
            Aia2MachineGuard.setTeamProgress(TEAM_B, 48);
            check(Aia2MachineGuard.mayReplicateOutputInCurrentTick(new ItemStack(Items.DIAMOND)), "postgame output becomes available only at completed48");
            check(!Aia2MachineGuard.mayReplicateOutputInCurrentTick(new ItemStack(Items.IRON_INGOT)), "postgame never manufactures a receipt by copying its output");
            Aia2MachineGuard.setTeamProgress(TEAM_B, 7);
            var nested = Aia2MachineGuard.enterTick(level.getBlockEntity(A));
            try {
                check(!Aia2MachineGuard.mayReplicateOutputInCurrentTick(new ItemStack(Items.RAW_IRON)), "locked owner cannot borrow parent ticker authorization");
            } finally { Aia2MachineGuard.exitTick(nested); }
            check(Aia2MachineGuard.mayProcessRecipeInCurrentTick(recipe), "nested ticker restores its authorized parent context");
        } finally { Aia2MachineGuard.exitTick(parent); }
        check(!Aia2MachineGuard.mayProcessRecipeInCurrentTick(recipe), "strict context is removed after ticker exit");
    }

    private static FurnaceBlockEntity furnace(BlockPos pos, String owner) {
        level.setBlockAndUpdate(pos, Blocks.FURNACE.defaultBlockState());
        FurnaceBlockEntity furnace = (FurnaceBlockEntity) level.getBlockEntity(pos);
        furnace.setItem(0, new ItemStack(Items.RAW_IRON));
        furnace.setItem(1, new ItemStack(Items.COAL));
        if (owner != null) Aia2MachineGuard.setOwner(furnace, owner);
        return furnace;
    }

    private static void testPersistenceAndOwnership() {
        FurnaceBlockEntity furnace = (FurnaceBlockEntity) level.getBlockEntity(A);
        CompoundTag saved = furnace.saveWithFullMetadata(level.registryAccess());
        BlockEntity reloaded = BlockEntity.loadStatic(A, furnace.getBlockState(), saved, level.registryAccess());
        check(reloaded != null && Aia2MachineGuard.getOwner(reloaded).equals(TEAM_A),
                "actual NeoForge block entity NBT roundtrip retains owning FTB team ID");
        boolean rejected = false;
        try { Aia2MachineGuard.setOwner(furnace, TEAM_B); }
        catch (IllegalStateException expected) { rejected = true; }
        check(rejected && Aia2MachineGuard.getOwner(furnace).equals(TEAM_A),
                "a visitor cannot replace an existing machine owner");
    }

    private static void testFakePlayerCrafting() {
        var fake = FakePlayerFactory.get(level, new GameProfile(
                UUID.fromString("9aa4224d-4123-4db4-afce-90d83205e638"), "AIA2NativeTest"));
        check(!Aia2MachineGuard.mayCraft(fake, new ItemStack(Items.IRON_INGOT)),
                "actual NeoForge FakePlayer cannot craft a staged output");
        fake.setPos(BENCH.getX() + .5, BENCH.getY(), BENCH.getZ() + .5);
        var menu = new CraftingMenu(1, fake.getInventory(), ContainerLevelAccess.create(level, BENCH));
        for (int slot = 1; slot <= 9; slot++) menu.getSlot(slot).set(new ItemStack(Items.IRON_NUGGET));
        check(menu.getSlot(0).getItem().is(Items.IRON_INGOT), "actual CraftingMenu resolves the vanilla nugget recipe");
        check(!menu.getSlot(0).mayPickup(fake), "native result-slot mixin denies FakePlayer output pickup");
        check(menu.quickMoveStack(fake, 0).isEmpty(), "native shift-click mixin rejects staged output");
        for (int slot = 1; slot <= 9; slot++) {
            check(menu.getSlot(slot).getItem().is(Items.IRON_NUGGET)
                    && menu.getSlot(slot).getItem().getCount() == 1,
                    "rejected shift-click preserves ingredient slot " + slot);
        }
    }

    @SubscribeEvent
    public static void tick(ServerTickEvent.Post event) {
        if (!running || event.getServer() != server) return;
        try {
            ticks++;
            if (ticks == 100) {
                check(crafterNuggets() == 9 && feederNuggets() == 0,
                        "real vanilla hopper automation inserts nine recipe ingredients into crafter");
                level.setBlockAndUpdate(POWER, Blocks.REDSTONE_BLOCK.defaultBlockState());
            }
            if (ticks == 250) {
                assertCold(A, "locked team's real furnace ticker leaves input and fuel intact");
                assertCold(UNOWNED, "unowned staged furnace remains stopped");
                check(output(B) == 1, "independent unlocked owner actually smelts raw iron in native furnace ticks");
                check(crafterNuggets() == 9, "redstone-triggered vanilla crafter rejects future output before consuming hopper-fed inputs");
                check(newIronDrops() == 0, "denied crafter produces no world item output");
                Aia2MachineGuard.setTeamProgress(TEAM_A, 4);
            }
            if (ticks == 360) {
                assertCold(A, "unlocking the furnace block alone cannot run a later recipe through the native cached lookup");
                check(crafterNuggets() == 9, "unlocked low-tier crafter cannot bypass output stage");
                Aia2MachineGuard.setTeamProgress(TEAM_A, 7);
                level.setBlockAndUpdate(POWER, Blocks.AIR.defaultBlockState());
                level.setBlockAndUpdate(POWER, Blocks.REDSTONE_BLOCK.defaultBlockState());
            }
            if (ticks == 410) {
                check(crafterNuggets() == 9, "unfinished key branch blocks a real crafter despite sufficient machine/output epochs");
                check(!Aia2MachineGuard.hasProductionProof(server, TEAM_A, 8, "tech"), "no successful recipe means no production receipt");
                check(!ProductionMilestoneBridge.hasProof(server, TEAM_A, "native_crafter_fixture"),
                        "a rejected native crafter never records a generic process observation");
                Aia2MachineGuard.setTeamKeyReady(TEAM_A, 8, "tech", true);
                level.setBlockAndUpdate(POWER, Blocks.AIR.defaultBlockState());
                level.setBlockAndUpdate(POWER, Blocks.REDSTONE_BLOCK.defaultBlockState());
            }
            if (ticks == 650) {
                check(output(A) == 1, "existing furnace resumes real processing after owning team reaches recipe stage");
                assertCold(UNOWNED, "global progress changes do not authorize an unowned machine");
                check(crafterNuggets() == 0, "authorized native crafter consumes exactly its previously blocked inputs");
                check(newIronDrops() == 1, "authorized redstone crafter creates one actual iron-ingot item entity");
                check(Aia2MachineGuard.hasProductionProof(server, TEAM_A, 8, "tech"), "real crafter records a production receipt only after ingredients were consumed");
                check(!Aia2MachineGuard.hasProductionProof(server, TEAM_A, 8, "arcane"), "technology production cannot substitute for the independent arcane branch");
                check(!Aia2MachineGuard.hasProductionProof(server, TEAM_B, 8, "tech"), "production receipt is bound to the actual machine owner team");
                check(ProductionMilestoneBridge.hasProof(server, TEAM_A, "native_crafter_fixture"),
                        "actual ingredient-consuming crafter completion records an independent generic process observation");
                check(!ProductionMilestoneBridge.hasProof(server, TEAM_B, "native_crafter_fixture"),
                        "generic process observation belongs only to the native machine owner team");
                testObservedCompletionBridge();
                var stored = server.overworld().getDataStorage().get(KeyProductionBridge.ReceiptData.FACTORY, "aia2_key_production_v1");
                var restored = KeyProductionBridge.ReceiptData.load(stored.save(new CompoundTag(), level.registryAccess()), level.registryAccess());
                check(restored.proofs.getOrDefault(TEAM_A, Set.of()).contains("8:tech"), "native SavedData NBT serialization retains the key receipt");
                var mechanicData = server.overworld().getDataStorage().get(ProductionMilestoneBridge.ReceiptData.FACTORY, "aia2_mechanics_v1");
                var mechanicReloaded = ProductionMilestoneBridge.ReceiptData.load(mechanicData.save(new CompoundTag(), level.registryAccess()), level.registryAccess());
                check(mechanicReloaded.proofs.getOrDefault(TEAM_A, Set.of()).contains("native_crafter_fixture"),
                        "generic process observation has its own persistent NBT data and survives serialization");
                check(Aia2MachineGuard.getDeniedTicks() > 0, "native tick/recipe guards recorded actual denied operations");
                Aia2MachineGuard.clearRuntime();
                check(!Aia2MachineGuard.isReady() && Aia2MachineGuard.hasProductionProof(server, TEAM_A, 8, "tech"), "server-script runtime reset closes guard but never clears durable production receipts");
                check(!ProductionMilestoneBridge.isConfigured() && ProductionMilestoneBridge.hasProof(server, TEAM_A, "native_crafter_fixture"),
                        "runtime reset closes generic observation rules but preserves durable process proofs");
                finish(null);
            }
        } catch (Throwable failure) {
            finish(failure);
        }
    }

    private static void testObservedCompletionBridge() {
        ProductionMilestoneBridge.configureJson("[{\"id\":\"native_observed_fixture\",\"recipeIds\":[\"minecraft:iron_ingot_from_nuggets\"],\"output\":\"minecraft:iron_ingot\",\"epoch\":8,\"serializer\":\"minecraft:crafting_shaped\"}]");
        var recipe=level.getRecipeManager().byKey(net.minecraft.resources.ResourceLocation.parse("minecraft:iron_ingot_from_nuggets")).orElseThrow().value();
        check(!ProductionMilestoneBridge.hasProof(server,TEAM_A,"native_observed_fixture"),"configuring actual-output observation never fabricates one");
        ProductionMilestoneBridge.finishedObservedMachine(crafter(),recipe,List.of(new ItemStack(Items.IRON_NUGGET)));
        check(!ProductionMilestoneBridge.hasProof(server,TEAM_A,"native_observed_fixture"),"wrong actual output is rejected by production helper");
        var wrongCount=new ItemStack(Items.IRON_INGOT,2);
        ProductionMilestoneBridge.finishedObservedMachine(crafter(),recipe,List.of(wrongCount));
        check(!ProductionMilestoneBridge.hasProof(server,TEAM_A,"native_observed_fixture"),"stale actual output count cannot be credited against a new template");
        var wrongVariant=new ItemStack(Items.IRON_INGOT);
        wrongVariant.set(net.minecraft.core.component.DataComponents.CUSTOM_NAME,net.minecraft.network.chat.Component.literal("synthetic different variant"));
        ProductionMilestoneBridge.finishedObservedMachine(crafter(),recipe,List.of(wrongVariant));
        check(!ProductionMilestoneBridge.hasProof(server,TEAM_A,"native_observed_fixture"),"different actual output components are rejected");
        ItemStack actual=emittedItems.getFirst().getItem().copy();
        ProductionMilestoneBridge.finishedObservedMachine(crafter(),recipe,List.of(actual));
        check(ProductionMilestoneBridge.hasProof(server,TEAM_A,"native_observed_fixture"),"trusted helper accepts the already verified native crafter's actual produced stack");
        check(ProductionMilestoneBridge.hasProof(server,TEAM_A,"native_crafter_fixture"),"reconfiguration never resets an older durable process proof");
    }

    private static void assertCold(BlockPos pos, String label) {
        FurnaceBlockEntity furnace = (FurnaceBlockEntity) level.getBlockEntity(pos);
        check(furnace.getItem(0).is(Items.RAW_IRON) && furnace.getItem(0).getCount() == 1
                && furnace.getItem(1).is(Items.COAL) && furnace.getItem(1).getCount() == 1
                && furnace.getItem(2).isEmpty(), label);
    }

    private static int output(BlockPos pos) {
        ItemStack item = ((FurnaceBlockEntity) level.getBlockEntity(pos)).getItem(2);
        return item.is(Items.IRON_INGOT) ? item.getCount() : 0;
    }
    private static CrafterBlockEntity crafter() { return (CrafterBlockEntity) level.getBlockEntity(CRAFTER); }
    private static int crafterNuggets() {
        int count = 0;
        for (int i = 0; i < crafter().getContainerSize(); i++) {
            var item = crafter().getItem(i);
            if (item.is(Items.IRON_NUGGET)) count += item.getCount();
        }
        return count;
    }
    private static int feederNuggets() {
        var feeder = (HopperBlockEntity) level.getBlockEntity(FEEDER);
        int count = 0;
        for (int i = 0; i < feeder.getContainerSize(); i++) {
            if (feeder.getItem(i).is(Items.IRON_NUGGET)) count += feeder.getItem(i).getCount();
        }
        return count;
    }
    private static long newIronDrops() {
        // Capture actual spawn events: items may fall out of the high-altitude
        // fixture's AABB long before the final assertion runs.
        return emittedItems.stream()
                .mapToLong(entity -> entity.getItem().getCount()).sum();
    }
    private static void check(boolean condition, String description) {
        CHECKS.add(Map.of("passed", condition, "description", description));
        if (!condition) throw new AssertionError(description);
    }

    private static void finish(Throwable failure) {
        running = false;
        Map<String, Object> report = new LinkedHashMap<>();
        report.put("status", failure == null ? "passed" : "failed");
        report.put("started_at_utc", startTime);
        report.put("finished_at_utc", Instant.now().toString());
        report.put("minecraft", "1.21.1");
        report.put("neoforge", "21.1.264");
        report.put("real_minecraft_server", true);
        report.put("actual_server_ticks", ticks);
        report.put("checks", CHECKS);
        report.put("assertions", CHECKS.size());
        boolean restart = Boolean.getBoolean("aia2.guard.nativeSmokeReceiptVerify");
        String receiptTeam = restart ? System.getProperty("aia2.guard.nativeSmokeReceiptTeam", "") : TEAM_A;
        report.put("receipt_team", receiptTeam);
        report.put("receipt_restart_verification", restart);
        report.put("modded_machines_tested", false);
        report.put("ftb_kubejs_runtime_present", false);
        report.put("tps_benchmark", "not performed; this is a small native correctness suite");
        if (failure != null) report.put("failure", failure.toString());
        try {
            if (level != null) {
                for (var entry : ORIGINALS.entrySet()) {
                    level.setBlockAndUpdate(entry.getKey(), entry.getValue().state());
                    if (entry.getValue().data() != null && level.getBlockEntity(entry.getKey()) != null) {
                        level.getBlockEntity(entry.getKey()).loadWithComponents(entry.getValue().data(), level.registryAccess());
                    }
                }
                if (existingItemEntities != null) {
                    for (ItemEntity item : level.getEntitiesOfClass(ItemEntity.class, AREA)) {
                        if (!existingItemEntities.contains(item.getUUID())) item.discard();
                    }
                }
                emittedItems.forEach(ItemEntity::discard);
                level.setChunkForced(A.getX() >> 4, A.getZ() >> 4, wasForced);
            }
            if (server != null && server.overworld() != null) {
                var data = server.overworld().getDataStorage().get(KeyProductionBridge.ReceiptData.FACTORY, "aia2_key_production_v1");
                // Leave only our generated receipt for the runner's second JVM.
                // The restart phase removes precisely that test record afterwards.
                if (data != null && (restart || failure != null)) {
                    data.proofs.remove(receiptTeam); data.proofs.remove(TEAM_B); data.setDirty();
                }
                var mechanics = server.overworld().getDataStorage().get(ProductionMilestoneBridge.ReceiptData.FACTORY, "aia2_mechanics_v1");
                if (mechanics != null && (restart || failure != null)) {
                    mechanics.proofs.remove(receiptTeam); mechanics.proofs.remove(TEAM_B); mechanics.setDirty();
                }
            }
            report.put("test_blocks_restored", true);
        } catch (Throwable cleanupFailure) {
            report.put("cleanup_failure", cleanupFailure.toString());
            report.put("status", "failed");
        }
        try {
            Files.writeString(Path.of("aia2-native-smoke.json"), new GsonBuilder().setPrettyPrinting().create().toJson(report) + "\n", StandardCharsets.UTF_8);
        } catch (Exception outputFailure) {
            throw new IllegalStateException("Cannot write native smoke evidence", outputFailure);
        } finally {
            System.out.println("AIA2_NATIVE_SMOKE_" + report.get("status").toString().toUpperCase() + " assertions=" + CHECKS.size());
            server.halt(false);
        }
    }
}
