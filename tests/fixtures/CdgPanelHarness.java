package ua.aia2.guard.mixin;

import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import com.jesz.createdieselgenerators.content.molds.CompressionMoldingRecipe;
import com.jesz.createdieselgenerators.content.molds.MoldType;
import com.simibubi.create.content.processing.basin.BasinBlockEntity;
import java.lang.reflect.InvocationTargetException;
import java.lang.reflect.Method;
import java.nio.file.Path;
import java.util.List;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.crafting.Recipe;
import net.minecraft.world.item.crafting.RecipeHolder;
import net.minecraft.world.level.saveddata.SavedData;
import net.neoforged.neoforge.items.IItemHandler;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;
import ua.aia2.guard.Aia2MachineGuard;
import ua.aia2.guard.CdgPanelAccess;
import ua.aia2.guard.KeyProductionBridge;
import ua.aia2.guard.ProductionMilestoneBridge;

/** Actual AIA2 bridge/helper/policy/handlers + original CDG MoldType/HEAD; remaining hosts modeled. */
public final class CdgPanelHarness {
    static final String ID = "cdg_panel_compression";
    static final String RECIPE = "createdieselgenerators:compression_molding/sheet_metal_panel";
    static final String OUTPUT = "createdieselgenerators:sheet_metal_panel";
    static final String DATA = "aia2_mechanics_v1";
    static final String EXPECTED = "{\"ingredients\":[{\"tag\":\"c:plates/iron\"}],\"mold\":\"createdieselgenerators:lines\",\"results\":[{\"id\":\"" + OUTPUT + "\",\"count\":4}]}";
    static final String RULES = "[{\"id\":\"" + ID + "\",\"epoch\":12,\"output\":\"" + OUTPUT
        + "\",\"serializer\":\"createdieselgenerators:compression_molding\",\"recipeIds\":[\"" + RECIPE + "\"]}]";
    static final List<String> HISTORICAL = List.of("andesite_mixing", "brass_mixing", "infused_alloy", "reinforced_alloy",
        "roots_living_pickaxe", "roots_charged_focus", "enderio_energetic_alloy", "powah_blazing_crystal", "clibano_arcane_dust",
        "clibano_rune", "clibano_obsidiansteel", "nasa_tier_1_rocket", "nasa_tier_2_rocket", "nasa_tier_3_rocket", "nasa_tier_4_rocket", "cca_electrum_mixing");
    static int checks, fixtures;
    static Path directory;
    static Method head, finish, moldHead;

    static void check(boolean value, String message) { checks++; if (!value) throw new AssertionError(message); }
    static void invoke(Method method, Object... arguments) {
        try { method.invoke(null, arguments); }
        catch (ReflectiveOperationException failure) {
            Throwable cause = failure instanceof InvocationTargetException ? failure.getCause() : failure;
            if (cause instanceof RuntimeException error) throw error;
            if (cause instanceof Error error) throw error;
            throw new AssertionError(cause);
        }
    }
    static ItemStack mold(String profile) {
        ItemStack stack = new ItemStack("createdieselgenerators:mold", 1);
        if (profile != null) stack.components.put("createdieselgenerators:mold_type", ResourceLocation.parse("createdieselgenerators:" + profile));
        return stack;
    }
    static CompressionMoldingRecipe recipe(String json) { return new CompressionMoldingRecipe(JsonParser.parseString(json).getAsJsonObject()); }
    static final class Items implements IItemHandler {
        final List<ItemStack> values;
        Items(ItemStack... stacks) { values = List.of(stacks); }
        public int getSlots() { return values.size(); }
        public ItemStack getStackInSlot(int slot) { return values.get(slot); }
    }
    static final class SubRecipe extends CompressionMoldingRecipe { SubRecipe(JsonObject json) { super(json); } }
    static final class Fixture {
        final MinecraftServer server = new MinecraftServer();
        final ServerLevel level = new ServerLevel();
        final BasinBlockEntity basin;
        CompressionMoldingRecipe recipe = recipe(EXPECTED);
        boolean simulatedOutputsAccepted = true, realOutputsAccepted = true;
        int inputs = 1, outputs;
        Fixture() {
            ProductionMilestoneBridge.clearRuntime(); Aia2MachineGuard.configure();
            BuiltInRegistries.item(OUTPUT);
            KeyProductionBridge.calls = 0; server.root = directory.resolve("fixture-" + fixtures++);
            server.main = level; level.server = server; level.items = new Items(mold("lines"));
            basin = new BasinBlockEntity(level, "team_a"); publish(RECIPE, recipe);
            ProductionMilestoneBridge.configureJson(RULES);
        }
        void publish(String id, Recipe<?> value) { level.recipes.replace(List.of(new RecipeHolder<>(ResourceLocation.parse(id), value))); }
        boolean proof(String team) { return ProductionMilestoneBridge.hasProof(server, team, ID); }
        void returned(boolean test, Boolean value) { invoke(finish, basin, recipe, test, new CallbackInfoReturnable<Boolean>(value)); }
        boolean guarded(boolean test) {
            CallbackInfoReturnable<Boolean> callback = new CallbackInfoReturnable<>(true);
            invoke(head, basin, recipe, test, callback); return !callback.cancelled;
        }
        boolean molded(boolean test) {
            CallbackInfoReturnable<Boolean> callback = new CallbackInfoReturnable<>(true);
            invoke(moldHead, basin, recipe, test, callback); return !callback.cancelled;
        }
        /** Source-shaped debit/output body; actual native Create apply and Mixin weaving are not executed. */
        boolean modelApply(boolean test) {
            boolean success = guarded(test) && molded(test) && inputs >= 1 && simulatedOutputsAccepted;
            if (success && !test) { inputs--; success = realOutputsAccepted; if (success) outputs += 4; }
            returned(test, success); return success;
        }
    }
    static void successfulBoundary() {
        Fixture f = new Fixture();
        check(ProductionMilestoneBridge.isConfigured(), "reviewed CDG serializer can configure");
        check(f.level.storage.writes == 0 && !f.proof("team_a"), "configuration/inventory alone gives no receipt or write");
        check(CdgPanelAccess.matchesRecipe(f.recipe, f.level), "reviewed recipe and exact Lines public field pass helper");
        check(f.modelApply(true), "correct source-shaped simulation may succeed");
        check(!f.proof("team_a"), "Simulation cannot record a native CDG panel receipt");
        check(f.inputs == 1 && f.outputs == 0 && KeyProductionBridge.calls == 0, "simulation performs no debit/output/key callback");
        f.returned(false, false); f.returned(false, null);
        check(!f.proof("team_a") && KeyProductionBridge.calls == 0, "false/null RETURN gives no proof");
        f.inputs = 0; check(!f.modelApply(false) && !f.proof("team_a"), "missing source-shaped iron plate gives no proof");
        f.inputs = 1; f.simulatedOutputsAccepted = false;
        check(!f.modelApply(false) && f.inputs == 1 && !f.proof("team_a"), "simulated output refusal gives no proof/debit");
        f.simulatedOutputsAccepted = true; f.realOutputsAccepted = false;
        check(!f.modelApply(false) && f.inputs == 0 && !f.proof("team_a"), "actual output refusal after modeled debit gives no receipt");
        f.inputs = 1; f.realOutputsAccepted = true;
        check(f.modelApply(false) && f.inputs == 0 && f.outputs == 4, "successful modeled native process debits one plate and accepts four panels");
        check(f.proof("team_a") && !f.proof("team_b"), "actual bridge records only current owner team");
        check(f.level.storage.writes == 1, "one successful completion creates one durable entry");
        int encoded = CompressionMoldingRecipe.encodes; f.returned(false, true);
        check(f.level.storage.writes == 1, "repeat completion is journal idempotent");
        check(encoded == CompressionMoldingRecipe.encodes, "codec check is cached for the RecipeManager generation");
    }
    static void actualMoldHeadCases() {
        for (String wrong : new String[]{null, "bowl", "chain", "bar", "unknown"}) {
            Fixture f = new Fixture(); f.level.items = new Items(mold(wrong));
            check(!f.molded(false), "actual original CDG HEAD refuses wrong/missing/unknown component: " + wrong);
            check(!f.modelApply(false) && !f.proof("team_a") && f.inputs == 1, "wrong mold cannot debit or receive panel proof");
        }
        Fixture f = new Fixture(); f.level.items = new Items();
        check(!f.molded(false) && !f.modelApply(false), "actual CDG HEAD rejects absent Mold item");
        f.level.items = null; check(!f.molded(false), "actual CDG HEAD rejects missing item capability");
        f.level.items = new Items(mold("lines"), mold("bowl"));
        check(!f.molded(false) && !f.molded(true), "actual CDG HEAD uses LAST Mold on both actual and simulated checks");
        f.level.items = new Items(mold("bowl"), mold("lines"));
        check(f.molded(false) && f.molded(true), "correct last Mold wins both actual and simulated checks");
        f.level.items = new Items(mold("lines")); check(f.molded(true), "initial simulated mold was valid");
        f.level.items = new Items(mold("bar"));
        check(!f.modelApply(false) && !f.proof("team_a"), "Mold swapped after simulation is rechecked before actual completion");
        f = new Fixture(); f.recipe = recipe(EXPECTED.replace("createdieselgenerators:lines", "createdieselgenerators:unknown"));
        f.publish(RECIPE, f.recipe); f.level.items = new Items(mold(null));
        check(f.molded(false), "original CDG null==null edge is genuinely reproduced on actual original HEAD");
        check(f.modelApply(false), "source-shaped body can finish altered unknown-mold recipe");
        check(!f.proof("team_a"), "actual AIA2 helper refuses null-mold recipe even when original CDG HEAD accepts null==null");
    }
    static void exactLiveSemantics() {
        String[] changes = {
            EXPECTED.replace("c:plates/iron", "c:ingots/iron"),
            EXPECTED.replace("createdieselgenerators:lines", "createdieselgenerators:bowl"),
            EXPECTED.replace("\"count\":4", "\"count\":1"),
            EXPECTED.replace("\"count\":4", "\"count\":4,\"chance\":0.5"),
            EXPECTED.replace("\"ingredients\":[", "\"ingredients\":[{\"item\":\"minecraft:dirt\"},"),
            EXPECTED.replace("\"results\":[", "\"results\":[{\"id\":\"minecraft:diamond\"},"),
            EXPECTED.replace("\"results\":[", "\"processing_time\":1,\"results\":["),
            EXPECTED.replace("\"results\":[", "\"heat_requirement\":\"heated\",\"results\":[")
        };
        for (String changed : changes) {
            Fixture f = new Fixture(); f.recipe = recipe(changed); f.publish(RECIPE, f.recipe);
            check(!CdgPanelAccess.matchesRecipe(f.recipe, f.level), "same-ID altered encoded semantics rejected: " + changed);
            f.returned(false, true); check(!f.proof("team_a"), "same-ID altered recipe cannot receive a completion receipt");
        }
        Fixture f = new Fixture(); f.recipe.json.addProperty("processing_time", 0); f.recipe.json.addProperty("heat_requirement", "none");
        f.recipe.json.getAsJsonArray("results").get(0).getAsJsonObject().addProperty("chance", 1);
        check(CdgPanelAccess.matchesRecipe(f.recipe, f.level), "same actual serializer normalizes explicit defaults before equality");
        f = new Fixture(); f.recipe.parseError = true;
        check(!CdgPanelAccess.matchesRecipe(f.recipe, f.level), "expected decode result with partial/error is rejected");
        f.returned(false, true); check(!f.proof("team_a"), "partial/error decode cannot grant proof");
        f = new Fixture(); f.recipe.encodeError = true;
        check(!CdgPanelAccess.matchesRecipe(f.recipe, f.level), "partial/error encoded result is rejected");
        f.returned(false, true); check(!f.proof("team_a"), "partial/error encode cannot grant proof");
        f = new Fixture(); f.recipe = new SubRecipe(JsonParser.parseString(EXPECTED).getAsJsonObject()); f.publish(RECIPE, f.recipe);
        check(!CdgPanelAccess.matchesRecipe(f.recipe, f.level), "unreviewed subclass rejected despite copied codec/mold/output");
        f.returned(false, true); check(!f.proof("team_a"), "unreviewed subclass gets no native proof");
        f = new Fixture(); Aia2MachineGuard.progress("team_a", 10); f.returned(false, true);
        check(!f.proof("team_a"), "index populated before later field mutation without granting early proof");
        f.recipe.moldType = MoldType.BOWL_MOLD; Aia2MachineGuard.progress("team_a", 11); f.returned(false, true);
        check(!f.proof("team_a"), "public moldType mutation is checked even after generation index was cached");
        f.recipe.moldType = null; f.returned(false, true); check(!f.proof("team_a"), "cached recipe with null public moldType gives no proof");
        f.recipe.moldType = MoldType.LINES_MOLD; f.returned(false, true); check(f.proof("team_a"), "restored verified Lines field can complete current recipe");
    }
    static void identityOwnershipAndHistory() {
        Fixture f = new Fixture(); f.publish("example:panel", f.recipe); f.returned(false, true);
        check(!f.proof("team_a"), "unlisted recipe producing same panel gets no proof");
        f = new Fixture(); f.recipe.serializer = "create:compacting"; f.returned(false, true);
        check(!f.proof("team_a"), "wrong serializer cannot substitute for exact CDG contract");
        f = new Fixture(); Aia2MachineGuard.progress("team_a", 10); f.returned(false, true);
        check(!f.proof("team_a"), "epoch11 does not grant epoch12 proof");
        CompressionMoldingRecipe old = f.recipe, replacement = recipe(EXPECTED); f.publish(RECIPE, replacement);
        Aia2MachineGuard.progress("team_a", 11); f.returned(false, true);
        check(!f.proof("team_a"), "stale same-ID object after reload cannot receive current generation proof");
        f.recipe = replacement; f.returned(false, true); check(old != replacement && f.proof("team_a"), "current verified replacement receives proof after reload");
        f = new Fixture(); Aia2MachineGuard.ready = false; check(!f.modelApply(false) && !f.proof("team_a"), "unready guard refuses process and proof");
        f.returned(false, true); check(!f.proof("team_a"), "successful-looking callback cannot bypass unready guard");
        f = new Fixture(); f.basin.owner = ""; f.returned(false, true); check(!f.proof("team_a"), "ownerless completion cannot be adopted");
        f.basin.owner = "unknown_team"; f.returned(false, true); check(!f.proof("unknown_team"), "unknown owner gets no stage proof");
        f.basin.owner = "team_b"; f.returned(false, true); check(f.proof("team_b") && !f.proof("team_a"), "second team receives only own receipt");
        f = new Fixture(); f.server.sameThread = false; boolean rejected = false;
        try { f.returned(false, true); } catch (IllegalStateException expected) { rejected = true; }
        check(rejected && f.level.storage.writes == 0, "off-thread completion fails before storage writes");
        f.server.sameThread = true;

        f = new Fixture(); CompoundTag root = new CompoundTag(); root.putInt("schema", 1);
        CompoundTag teams = new CompoundTag(), oldHistory = new CompoundTag();
        for (String id : HISTORICAL) oldHistory.putBoolean(id, true);
        teams.put("team_a", oldHistory); root.put("teams", teams); f.level.storage.raw.put(DATA, root);
        for (String id : HISTORICAL) check(ProductionMilestoneBridge.hasProof(f.server, "team_a", id), "published historical ID remains readable: " + id);
        check(!f.proof("team_a"), "16 historical proofs do not fabricate new panel proof");
        f.returned(false, true); SavedData saved = f.level.storage.data.get(DATA); CompoundTag encoded = saved.save(new CompoundTag(), null);
        check(encoded.getInt("schema") == 1 && encoded.getCompound("teams").getCompound("team_a").size() == 17, "new proof appends beside all16 old IDs in schema1");
        f.level.storage.raw.put(DATA, encoded); f.level.storage.data.clear(); ProductionMilestoneBridge.clearRuntime(); ProductionMilestoneBridge.configureJson(RULES);
        for (String id : HISTORICAL) check(ProductionMilestoneBridge.hasProof(f.server, "team_a", id), "modeled NBT reload preserves historical ID: " + id);
        check(f.proof("team_a"), "modeled NBT reload also preserves new native proof");
    }
    public static void main(String[] args) throws Exception {
        directory = Path.of(args[0]);
        head = CreateBasinRecipeMixin.class.getDeclaredMethod("aia2$guardBasin", Object.class, Recipe.class, boolean.class, CallbackInfoReturnable.class);
        finish = CreateBasinRecipeMixin.class.getDeclaredMethod("aia2$recordCompletedBasin", Object.class, Recipe.class, boolean.class, CallbackInfoReturnable.class);
        Class<?> cdg = Class.forName("com.jesz.createdieselgenerators.mixins.BasinRecipeMixin");
        moldHead = cdg.getDeclaredMethod("apply", BasinBlockEntity.class, Recipe.class, boolean.class, CallbackInfoReturnable.class);
        head.setAccessible(true); finish.setAccessible(true); moldHead.setAccessible(true);
        successfulBoundary(); actualMoldHeadCases(); exactLiveSemantics(); identityOwnershipAndHistory();
        System.out.println(checks + " CDG panel actual-helper/actual-bridge/actual-handlers/real-policy assertions PASS; original CDG MoldType/HEAD compiled; CODEC/Create body/host/NBT modeled, no optional binary weaving or full client");
    }
}
