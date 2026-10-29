package ua.aia2.guard.mixin;

import java.lang.reflect.InvocationTargetException;
import java.lang.reflect.Method;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import java.util.Map;
import java.util.function.Consumer;
import com.google.gson.JsonParser;
import earth.terrarium.adastra.common.blockentities.machines.NasaWorkbenchBlockEntity;
import earth.terrarium.adastra.common.recipes.machines.NasaWorkbenchRecipe;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.tags.TagKey;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.item.ItemEntity;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.crafting.Ingredient;
import net.minecraft.world.item.crafting.RecipeHolder;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.saveddata.SavedData;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;
import ua.aia2.guard.AdAstraNasaAccess;
import ua.aia2.guard.Aia2MachineGuard;
import ua.aia2.guard.NasaProductionAccess;
import ua.aia2.guard.ProductionMilestoneBridge;

/** Actual helper, bridge and handlers with modeled receivers. This is not a weaving test. */
public final class NasaProductionHarness {
    private static final String PROOF = "nasa_workbench";
    private static int assertions;
    private static void check(boolean value, String message) {
        assertions++;
        if (!value) throw new AssertionError(message);
    }
    private static Object call(Class<?> type, String name, Object target, Object... arguments) {
        try {
            for (Method method : type.getDeclaredMethods()) {
                if (!method.getName().equals(name)) continue;
                method.setAccessible(true);
                return method.invoke(target, arguments);
            }
            throw new AssertionError("Missing actual handler " + name);
        } catch (InvocationTargetException failed) {
            if (failed.getCause() instanceof RuntimeException runtime) throw runtime;
            if (failed.getCause() instanceof Error error) throw error;
            throw new AssertionError(failed.getCause());
        } catch (ReflectiveOperationException failed) { throw new AssertionError(failed); }
    }
    public static boolean select(NasaWorkbenchBlockEntity owner, boolean nativeValue) {
        var callback = new CallbackInfoReturnable<Boolean>(nativeValue);
        call(AdAstraNasaMixin.class, "aia2$select", owner, callback);
        return callback.getReturnValue();
    }
    public static boolean finish(NasaWorkbenchBlockEntity owner) {
        var callback = new CallbackInfo();
        call(AdAstraNasaMixin.class, "aia2$finish", owner, callback);
        return !callback.cancelled;
    }
    public static void drop(NasaWorkbenchBlockEntity owner, Level level, double x, double y, double z, ItemStack stack) {
        call(AdAstraNasaMixin.class, "aia2$drop", owner, level, x, y, z, stack);
    }
    public static void shrink(NasaWorkbenchBlockEntity owner, ItemStack input, int amount) {
        call(AdAstraNasaMixin.class, "aia2$debit", owner, input, amount);
    }
    public static boolean spawn(Level level, Entity entity) {
        return (Boolean)call(NasaDropMixin.class, "aia2$acceptedDrop", null, level, entity);
    }
    private static void configureProof(String serializer, String recipeId) {
        ProductionMilestoneBridge.configureJson("[{\"id\":\"" + PROOF + "\",\"epoch\":37,"
                + "\"output\":\"ad_astra:tier_1_rocket\",\"serializer\":\"" + serializer
                + "\",\"recipeIds\":[\"" + recipeId + "\"]}]");
    }
    private static NasaWorkbenchRecipe install(NasaWorkbenchBlockEntity machine, String id) {
        var recipe = new NasaWorkbenchRecipe(new ItemStack("ad_astra:tier_1_rocket", 1));
        machine.recipe(recipe);
        Aia2MachineGuard.live.put(recipe, id);
        ((ServerLevel)machine.level).recipes.replace(List.of(new RecipeHolder<>(ResourceLocation.parse(id), recipe)));
        for (int slot = 0; slot < 14; slot++) machine.items[slot] = new ItemStack("minecraft:iron_ingot", 2);
        machine.items[14] = recipe.result().copy();
        return recipe;
    }
    private static NasaWorkbenchBlockEntity fixture() {
        Aia2MachineGuard.configure();
        ProductionMilestoneBridge.clearRuntime();
        configureProof("ad_astra:nasa_workbench", "ad_astra:t1");
        var machine = new NasaWorkbenchBlockEntity();
        machine.level = new ServerLevel(); machine.level.entity = machine;
        install(machine, "ad_astra:t1");
        return machine;
    }
    private static NasaWorkbenchRecipe recipe(NasaWorkbenchBlockEntity machine) {
        return (NasaWorkbenchRecipe)call(AdAstraNasaAccess.class, "currentRecipe", null, machine);
    }
    private static boolean proof(NasaWorkbenchBlockEntity machine, String team) {
        return ProductionMilestoneBridge.hasProof(((ServerLevel)machine.level).server, team, PROOF);
    }
    private static void noProof(NasaWorkbenchBlockEntity machine, String message) {
        check(!proof(machine, "team") && !proof(machine, "other_team"), message);
    }
    private static void before(String label, Consumer<NasaWorkbenchBlockEntity> change) {
        var machine = fixture(); change.accept(machine);
        ItemStack[] references = machine.items.clone();
        ItemStack[] contents = java.util.Arrays.stream(machine.items).map(ItemStack::copy).toArray(ItemStack[]::new);
        var cached = recipe(machine);
        machine.craft();
        noProof(machine, label + " no receipt");
        check(machine.nativeCalls == 0 && machine.nativeReturns == 0 && machine.particles == 0
                && machine.level.dropCalls == 0 && machine.level.spawnCalls == 0 && machine.level.drops == 0
                && machine.level.accepted.isEmpty() && machine.writes == 0,
                label + " rejects before native effects");
        boolean unchanged = recipe(machine) == cached;
        for (int slot = 0; slot < machine.items.length; slot++) {
            var actual = machine.items[slot]; var expected = contents[slot];
            unchanged &= actual == references[slot] && actual.getItem() == expected.getItem()
                    && actual.getCount() == expected.getCount() && actual.components.equals(expected.components);
        }
        check(unchanged, label + " leaves every input, preview and cached recipe unchanged");
    }
    private static void during(String label, Consumer<NasaWorkbenchBlockEntity> change) {
        var machine = fixture(); change.accept(machine); machine.craft();
        noProof(machine, label + " no receipt");
        check(machine.nativeCalls == 1 && machine.nativeReturns == 1,
                label + " preserves one native operation");
    }

    private static void accepted() {
        var machine = fixture();
        var recipe = Aia2MachineGuard.live.keySet().iterator().next();
        check(recipe.getResultItem(null).isEmpty(), "NASA record keeps the empty Minecraft result template");
        check(machine.canCraft(), "current allowed recipe selects");
        noProof(machine, "selection and slot14 preview are not production");
        ItemStack[] originals = machine.items.clone();
        machine.afterDrop = () -> noProof(machine, "accepted drop before debits has no receipt");
        machine.beforeShrink = slot -> noProof(machine, "receipt waits for native debit " + slot);
        machine.afterCraft = () -> noProof(machine, "receipt waits for the native return");
        machine.craft();
        check(machine.nativeCalls == 1 && machine.nativeReturns == 1, "wrapper admits the native body exactly once");
        check(machine.particles == 1 && machine.writes == 1 && machine.level.dropCalls == 1,
                "native particles, preview write and drop are preserved");
        check(machine.level.spawnCalls == 1 && machine.level.accepted.size() == 1,
                "one actual addFreshEntity call accepts one entity");
        var entity = (ItemEntity)machine.level.accepted.getFirst();
        check(entity.getItem().getCount() == 1 && entity.getItem().components.isEmpty()
                && entity.getItem().getItem().id().equals("ad_astra:tier_1_rocket"), "accepted default one-rocket output");
        for (int slot = 0; slot < 14; slot++) {
            check(machine.items[slot] == originals[slot] && machine.items[slot].getCount() == 1,
                    "one native debit on original input " + slot);
        }
        check(machine.items[14].isEmpty(), "native code clears preview");
        check(proof(machine, "team") && !proof(machine, "other_team"), "receipt belongs to the current owner only");
        int calls = machine.nativeCalls; machine.craft();
        check(machine.nativeCalls == calls, "cleared cached recipe cannot manufacture again");
        var storage = ((ServerLevel)machine.level).storage;
        SavedData saved = storage.data.get("aia2_mechanics_v1");
        check(saved != null && saved.dirty, "actual receipt marks its SavedData dirty");
        CompoundTag tag = saved.save(new CompoundTag(), null);
        check(tag.getInt("schema") == 1, "actual receipt serialization retains the schema");
        storage.data.put("aia2_mechanics_v1", (SavedData)call(saved.getClass(), "load", null, tag, null));
        ProductionMilestoneBridge.clearRuntime();
        configureProof("ad_astra:nasa_workbench", "ad_astra:t1");
        check(proof(machine, "team") && !proof(machine, "other_team"), "actual receipt survives SavedData reload and runtime reset");

        var alternate = fixture(); alternate.owner = "other_team"; alternate.craft();
        check(!proof(alternate, "team") && proof(alternate, "other_team"), "valid alternate owner gets its own receipt");
    }
    private static void outsideScope() {
        var machine = fixture();
        var recipe = (NasaWorkbenchRecipe)Aia2MachineGuard.live.keySet().iterator().next();
        check(!NasaProductionAccess.enterNative(machine), "no unscoped native-entry permit");
        check(spawn(machine.level, new ItemEntity(machine.level, 0, 65, 0, recipe.result().copy())),
                "outside-scope /give-like output keeps the native true return");
        var input = new ItemStack("minecraft:iron_ingot", 2);
        shrink(machine, input, 1);
        check(input.getCount() == 1, "outside-scope shrink keeps native behavior");
        drop(machine, machine.level, 0, 65, 0, recipe.result().copy());
        ProductionMilestoneBridge.finishedMachine(machine, recipe);
        ProductionMilestoneBridge.finishedObservedMachine(machine, recipe, List.of(recipe.result().copy()));
        call(ProductionMilestoneBridge.class, "finishedNasa", null, machine, recipe, machine.owner, recipe.result().copy());
        noProof(machine, "inventory output, unscoped hooks and generic production calls give no NASA receipt");
        machine.level.spawnAccepted = false;
        check(!spawn(machine.level, new Entity(machine.level)), "outside-scope spawn keeps native false return");
        noProof(machine, "native false spawn outside scope gives no receipt");
    }
    private static void rejectsInitialState() {
        before("unloaded", m -> ((ServerLevel)m.level).loaded = false);
        before("removed owner", m -> m.removed = true);
        before("replaced canonical machine", m -> m.level.entity = new NasaWorkbenchBlockEntity());
        before("off server thread", m -> ((ServerLevel)m.level).server.sameThread = false);
        before("unowned", m -> m.owner = "");
        before("unready", m -> Aia2MachineGuard.ready = false);
        before("locked stage", m -> Aia2MachineGuard.progress(35));
        before("stale recipe identity", m -> ((ServerLevel)m.level).recipes.replace(List.of()));
        before("wrong ingredient", m -> m.items[8] = new ItemStack("minecraft:diamond", 2));
        before("wrong preview count", m -> m.items[14].count = 2);
        before("wrong preview components", m -> m.items[14].components.put("forged", true));
        before("missing preview", m -> m.items[14] = ItemStack.EMPTY);
        var machine = fixture();
        check(!select(machine, false), "guard preserves a native false selection");
        noProof(machine, "native false selection produces no receipt");
    }
    private static void rejectsIncompleteWitness() {
        during("native addFreshEntity false", m -> m.level.spawnAccepted = false);
        during("accepted entity not retained by world", m -> m.level.retainAccepted = false);
        during("accepted unrelated entity", m -> m.level.unrelatedEntity = true);
        during("mutated accepted output components", m -> m.level.beforeSpawn = e -> ((ItemEntity)e).getItem().components.put("forged", true));
        during("mutated accepted output count", m -> m.level.beforeSpawn = e -> ((ItemEntity)e).getItem().count = 2);
        during("removed accepted entity", m -> m.level.beforeSpawn = e -> e.removed = true);
        during("accepted entity removed before finish", m -> m.afterDrop = () -> m.level.accepted.getFirst().removed = true);
        during("accepted output changes before finish", m -> m.afterDrop = () -> ((ItemEntity)m.level.accepted.getFirst()).getItem().components.put("late", true));
        during("world entity replaced before finish", m -> m.afterDrop = () -> m.level.entities.clear());
        during("wrong input reference", m -> m.substituteSlot = 7);
        during("wrong native shrink amount", m -> m.amount = 2);
        during("native no-op shrink", m -> m.amount = 0);
        during("reverse native debit order", m -> m.reverseDebits = true);
        before("aliased native input references", m -> m.items[1] = m.items[0]);
        during("input changed after acceptance", m -> m.afterDrop = () -> m.items[5].components.put("late", true));
        during("input replaced after acceptance", m -> m.afterDrop = () -> m.items[5] = m.items[5].copy());
        during("missing accepted drop", m -> m.skipDrop = true);
        during("duplicate native drop invocation", m -> m.afterDrop = () -> drop(m, m.level, 0, 65, 0, new ItemStack("ad_astra:tier_1_rocket", 1)));
        during("extra native debit", m -> m.afterCraft = () -> shrink(m, m.items[0], 1));
        during("native preview remains populated", m -> m.afterCraft = () -> m.items[14] = new ItemStack("ad_astra:tier_1_rocket", 1));
        during("native cached recipe remains populated", m -> m.afterCraft = () -> m.recipe(new NasaWorkbenchRecipe(new ItemStack("ad_astra:tier_1_rocket", 1))));
        during("changed recipe generation", m -> m.afterDrop = () -> ((ServerLevel)m.level).recipes.replace(new java.util.ArrayList<>(((ServerLevel)m.level).recipes.snapshot)));
        during("changed owner", m -> m.afterDrop = () -> m.owner = "other_team");
        during("chunk unloaded before finish", m -> m.afterDrop = () -> ((ServerLevel)m.level).loaded = false);
        during("server becomes unready", m -> m.afterDrop = () -> Aia2MachineGuard.ready = false);
        during("stage revoked", m -> m.afterDrop = () -> Aia2MachineGuard.progress(35));
        during("reentry", m -> m.reentry = true);
        during("wrong current recipe ID", m -> { install(m, "ad_astra:t3"); Aia2MachineGuard.progress(37); });
        during("wrong configured recipe ID", m -> configureProof("ad_astra:nasa_workbench", "ad_astra:other"));
        during("wrong configured serializer", m -> configureProof("create:mixing", "ad_astra:t1"));
        before("nondefault output components", m -> {
            var r = new NasaWorkbenchRecipe(new ItemStack("ad_astra:tier_1_rocket", 1)); r.result().components.put("custom", true);
            m.recipe(r); m.items[14] = r.result().copy(); Aia2MachineGuard.live.put(r, "ad_astra:t1");
            ((ServerLevel)m.level).recipes.replace(List.of(new RecipeHolder<>(ResourceLocation.parse("ad_astra:t1"), r)));
        });
        before("nondefault output count", m -> {
            var r = new NasaWorkbenchRecipe(new ItemStack("ad_astra:tier_1_rocket", 2));
            m.recipe(r); m.items[14] = r.result().copy(); Aia2MachineGuard.live.put(r, "ad_astra:t1");
            ((ServerLevel)m.level).recipes.replace(List.of(new RecipeHolder<>(ResourceLocation.parse("ad_astra:t1"), r)));
        });
    }
    private static void nativeExceptionAndCleanup() {
        var machine = fixture(); machine.throwAtSlot = 6;
        boolean thrown = false;
        try { machine.craft(); } catch (IllegalStateException failure) { thrown = failure.getMessage().equals("native NASA fault 6"); }
        check(thrown, "native exception propagates through the actual handler and wrapper");
        check(machine.nativeCalls == 1 && machine.nativeReturns == 0, "exception has no native normal return");
        for (int slot = 0; slot < 14; slot++) check(machine.items[slot].getCount() == (slot < 6 ? 1 : 2), "native partial exception payment " + slot);
        noProof(machine, "native exception never awards a partial operation");
        var stale = new ItemStack("minecraft:iron_ingot", 2);
        shrink(machine, stale, 1);
        check(stale.getCount() == 1, "exception cleanup leaves later unrelated shrink native");
        check(spawn(machine.level, new ItemEntity(machine.level, 0, 65, 0, new ItemStack("ad_astra:tier_1_rocket", 1))),
                "exception cleanup leaves later unrelated spawn native");
        noProof(machine, "no delayed receipt after exception cleanup");
        check(!NasaProductionAccess.enterNative(machine), "exception cleanup removes the native-entry permit");
        machine.throwAtSlot = -1; install(machine, "ad_astra:t1"); machine.craft();
        check(proof(machine, "team"), "a clean later operation succeeds after exception cleanup");
    }
    private static void nativePreviewClearAndDepletedInputs() {
        var machine = fixture();
        var recipe = (NasaWorkbenchRecipe)Aia2MachineGuard.live.keySet().iterator().next();
        machine.items[14] = recipe.result();
        for (int slot = 0; slot < 14; slot++) machine.items[slot].count = 1;
        machine.onPreviewClear = () -> machine.recipe(new NasaWorkbenchRecipe(new ItemStack("ad_astra:tier_1_rocket", 1)));
        machine.craft();
        check(proof(machine, "team"), "native clear update may rebind the cache before the final native null assignment");
        check(recipe.result().getCount() == 1, "native drop copies a preview alias of the recipe result");
        for (int slot = 0; slot < 14; slot++) check(machine.items[slot].isEmpty(), "native one-unit input depletes slot " + slot);
    }
    private static final TagKey<Item> IRON_TAG = new TagKey<>(ResourceLocation.parse("example:nasa_iron"));
    private static void bindIronTag(String item) {
        var value = BuiltInRegistries.item(item);
        BuiltInRegistries.ITEM.bind(IRON_TAG, List.of(BuiltInRegistries.ITEM.wrapAsHolder(value)));
    }
    private static void useIronTag(NasaWorkbenchBlockEntity machine) {
        bindIronTag("minecraft:iron_ingot");
        recipe(machine).ingredients().set(0, Ingredient.of(IRON_TAG));
    }
    private static void currentIngredientAndResultSemantics() {
        before("short native ingredient list", m -> recipe(m).ingredients().remove(13));
        before("empty native ingredient list", m -> recipe(m).ingredients().clear());
        before("unsupported custom ingredient", m -> recipe(m).ingredients().set(0,
                new Ingredient(true, new Ingredient.ItemValue(new ItemStack("minecraft:iron_ingot", 1)))));
        before("unsupported ingredient value", m -> recipe(m).ingredients().set(0,
                new Ingredient(() -> List.of(new ItemStack("minecraft:iron_ingot", 1)))));
        before("ingredient exceeds the bounded value count", m -> {
            var values = new Ingredient.Value[65];
            java.util.Arrays.fill(values, new Ingredient.ItemValue(new ItemStack("minecraft:iron_ingot", 1)));
            recipe(m).ingredients().set(0, new Ingredient(values));
        });
        before("empty individual ingredient", m -> recipe(m).ingredients().set(0, new Ingredient()));
        during("direct ingredient definition changes after drop", m -> {
            var ingredient = recipe(m).ingredients().get(0);
            m.afterDrop = () -> ingredient.getValues()[0] = new Ingredient.ItemValue(new ItemStack("minecraft:diamond", 1));
        });
        during("ingredient list changes after drop", m -> {
            var recipe = recipe(m);
            m.afterDrop = () -> recipe.ingredients().remove(13);
        });
        during("ingredient replacement after drop", m -> {
            var recipe = recipe(m);
            m.afterDrop = () -> recipe.ingredients().set(0, Ingredient.of("minecraft:diamond"));
        });
        before("current tag rejects stale native ingredient cache", m -> {
            useIronTag(m);
            check(m.canCraft(), "native match first caches the original tag membership");
            bindIronTag("minecraft:diamond");
            check(m.canCraft(), "native Ingredient cache still matches the removed tag item");
        });
        before("current tag disappears after native cache warmup", m -> {
            useIronTag(m); check(m.canCraft(), "native tag cache warmup before removal");
            BuiltInRegistries.ITEM.bind(IRON_TAG, List.of());
            check(m.canCraft(), "native cached tag match remains true after binding is emptied");
        });
        before("future gated item accepted by a current native tag", m -> {
            useIronTag(m); bindIronTag("example:future_iron");
            m.items[0] = new ItemStack("example:future_iron", 2);
            Aia2MachineGuard.ITEMS.setRules(Map.of("ad_astra:tier_1_rocket", 37, "example:future_iron", 44));
            check(m.canCraft(), "native recipe and current tag accept the imported future ingredient");
        });
        during("tag membership changes after acceptance", m -> {
            useIronTag(m); m.afterDrop = () -> bindIronTag("minecraft:diamond");
        });
        during("tag membership expands after acceptance", m -> {
            useIronTag(m); m.afterDrop = () -> BuiltInRegistries.ITEM.bind(IRON_TAG, List.of(
                    BuiltInRegistries.ITEM.wrapAsHolder(BuiltInRegistries.item("minecraft:iron_ingot")),
                    BuiltInRegistries.ITEM.wrapAsHolder(BuiltInRegistries.item("minecraft:diamond"))));
        });
        before("tag membership exceeds the bounded aggregate budget", m -> {
            useIronTag(m);
            var members = new java.util.ArrayList<net.minecraft.core.Holder<Item>>();
            members.add(BuiltInRegistries.ITEM.wrapAsHolder(BuiltInRegistries.item("minecraft:iron_ingot")));
            for (int i = 0; i < 16384; i++) members.add(BuiltInRegistries.ITEM.wrapAsHolder(BuiltInRegistries.item("example:tag_member_" + i)));
            BuiltInRegistries.ITEM.bind(IRON_TAG, members);
        });
        during("captured result components change after drop", m -> {
            var output = recipe(m).result(); m.afterDrop = () -> output.components.put("changed", true);
        });
        during("captured result count changes after drop", m -> {
            var output = recipe(m).result(); m.afterDrop = () -> output.count = 2;
        });
        var valid = fixture(); useIronTag(valid); valid.craft();
        check(proof(valid, "team"), "supported current vanilla tag ingredient awards the exact native payment");
        var bounded = fixture();
        var values = new Ingredient.Value[64];
        java.util.Arrays.fill(values, new Ingredient.ItemValue(new ItemStack("minecraft:iron_ingot", 1)));
        recipe(bounded).ingredients().set(0, new Ingredient(values)); bounded.craft();
        check(proof(bounded, "team"), "supported ingredient value count includes the exact 64-value boundary");
        var reordered = fixture(); useIronTag(reordered);
        var iron = BuiltInRegistries.ITEM.wrapAsHolder(BuiltInRegistries.item("minecraft:iron_ingot"));
        var diamond = BuiltInRegistries.ITEM.wrapAsHolder(BuiltInRegistries.item("minecraft:diamond"));
        BuiltInRegistries.ITEM.bind(IRON_TAG, List.of(iron, diamond));
        reordered.afterDrop = () -> BuiltInRegistries.ITEM.bind(IRON_TAG, List.of(diamond, iron));
        reordered.craft();
        check(proof(reordered, "team"), "equivalent tag membership order retains current ingredient semantics");
    }
    private static void allFourCuratedRules(String file) throws Exception {
        String json = Files.readString(Path.of(file));
        var rules = JsonParser.parseString(json).getAsJsonArray();
        check(rules.size() == 4, "exactly four authored NASA manufacture rules");
        for (var element : rules) {
            var rule = element.getAsJsonObject();
            String id = rule.get("id").getAsString(), output = rule.get("output").getAsString();
            String recipeId = rule.getAsJsonArray("recipeIds").get(0).getAsString();
            int epoch = rule.get("epoch").getAsInt();
            var machine = fixture();
            ProductionMilestoneBridge.configureJson(json);
            Aia2MachineGuard.ITEMS.setRules(Map.of(output, epoch));
            Aia2MachineGuard.RECIPES.setRules(Map.of(recipeId, epoch));
            Aia2MachineGuard.progress(epoch - 1);
            var recipe = new NasaWorkbenchRecipe(new ItemStack(output, 1));
            machine.recipe(recipe); machine.items[14] = recipe.result().copy();
            Aia2MachineGuard.live.put(recipe, recipeId);
            ((ServerLevel)machine.level).recipes.replace(List.of(new RecipeHolder<>(ResourceLocation.parse(recipeId), recipe)));
            machine.craft();
            var server = ((ServerLevel)machine.level).server;
            check(ProductionMilestoneBridge.hasProof(server, "team", id), "curated exact recipe awards " + id);
            check(!ProductionMilestoneBridge.hasProof(server, "other_team", id), "curated receipt stays with the current owner " + id);
            for (var other : rules) {
                String otherId = other.getAsJsonObject().get("id").getAsString();
                if (!id.equals(otherId)) check(!ProductionMilestoneBridge.hasProof(server, "team", otherId), "one manufacture does not award " + otherId);
            }
            check(machine.level.accepted.size() == 1 && ((ItemEntity)machine.level.accepted.getFirst()).getItem().getItem().id().equals(output), "curated native output " + output);
            for (int slot = 0; slot < 14; slot++) check(machine.items[slot].getCount() == 1, "curated one-unit native debit " + id + " slot " + slot);
        }
    }
    public static void main(String[] arguments) throws Exception {
        accepted(); outsideScope(); rejectsInitialState(); rejectsIncompleteWitness(); nativeExceptionAndCleanup();
        nativePreviewClearAndDepletedInputs(); currentIngredientAndResultSemantics(); allFourCuratedRules(arguments[0]);
        System.out.println(assertions + " NASA production actual-helper/handlers/bridge/real-policy modeled assertions PASS; no weaving claim");
    }
}
