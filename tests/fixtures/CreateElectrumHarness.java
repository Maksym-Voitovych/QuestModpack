package ua.aia2.guard.mixin;

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
import net.minecraft.world.item.crafting.RecipeInput;
import net.minecraft.world.item.crafting.RecipeSerializer;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.entity.CrafterBlockEntity;
import net.minecraft.world.level.saveddata.SavedData;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;
import ua.aia2.guard.Aia2MachineGuard;
import ua.aia2.guard.KeyProductionBridge;
import ua.aia2.guard.ProductionMilestoneBridge;

/** Actual bridge and actual private handlers; host native body/NBT/ownership modeled, no weaving. */
public final class CreateElectrumHarness {
    static final String ID = "cca_electrum_mixing";
    static final String RECIPE = "createaddition:mixing/electrum";
    static final String OUTPUT = "immersiveengineering:ingot_electrum";
    static final String DATA = "aia2_mechanics_v1";
    static final String RULES = "[{\"id\":\"" + ID + "\",\"epoch\":15,\"output\":\"" + OUTPUT
        + "\",\"serializer\":\"create:mixing\",\"recipeIds\":[\"" + RECIPE + "\"]}]";
    static int checks, fixtures;
    static Path directory;
    static Method head, finish;

    static void check(boolean value, String message) {
        checks++;
        if (!value) throw new AssertionError(message);
    }
    static void invoke(Method method, Object... arguments) {
        try { method.invoke(null, arguments); }
        catch (ReflectiveOperationException failure) {
            Throwable cause = failure instanceof InvocationTargetException ? failure.getCause() : failure;
            if (cause instanceof RuntimeException error) throw error;
            if (cause instanceof Error error) throw error;
            throw new AssertionError(cause);
        }
    }
    static final class MixingRecipe implements Recipe<RecipeInput> {
        final String output, serializer;
        MixingRecipe(String output, String serializer) { this.output = output; this.serializer = serializer; }
        public boolean matches(RecipeInput input, Level level) { return true; }
        public ItemStack getResultItem(Object registries) {
            return output.isEmpty() ? ItemStack.EMPTY : new ItemStack(output, 2);
        }
        public RecipeSerializer<?> getSerializer() { return new RecipeSerializer<>(serializer); }
    }
    static final class Fixture {
        final MinecraftServer server = new MinecraftServer();
        final ServerLevel level = new ServerLevel();
        final BlockEntity basin;
        MixingRecipe recipe = new MixingRecipe(OUTPUT, "create:mixing");
        boolean heated = true, outputAccepted = true;
        int inputs = 2, outputs;
        Fixture() {
            ProductionMilestoneBridge.clearRuntime();
            Aia2MachineGuard.configure();
            BuiltInRegistries.item(OUTPUT); // Explicit modeled installed registry entry.
            KeyProductionBridge.calls = 0;
            server.root = directory.resolve("fixture-" + fixtures++);
            server.main = level; level.server = server;
            basin = new BlockEntity(level, "team_a");
            publish(RECIPE, recipe);
            ProductionMilestoneBridge.configureJson(RULES);
        }
        void publish(String id, Recipe<?> value) {
            level.recipes.replace(List.of(new RecipeHolder<>(ResourceLocation.parse(id), value)));
        }
        boolean proof(String team) { return ProductionMilestoneBridge.hasProof(server, team, ID); }
        void returned(boolean test, Boolean result) {
            invoke(finish, basin, recipe, test, new CallbackInfoReturnable<Boolean>(result));
        }
        boolean admitted() {
            CallbackInfoReturnable<Boolean> callback = new CallbackInfoReturnable<>(true);
            invoke(head, basin, recipe, false, callback);
            return !callback.cancelled;
        }
        /** Source-shaped order only: native Create itself is not executed by this host. */
        boolean modelApply(boolean test) {
            CallbackInfoReturnable<Boolean> guard = new CallbackInfoReturnable<>(true);
            invoke(head, basin, recipe, test, guard);
            if (guard.cancelled) { returned(test, false); return false; }
            boolean success = heated && inputs >= 2 && outputAccepted;
            if (success && !test) { inputs -= 2; outputs += 2; }
            returned(test, success);
            return success;
        }
    }
    static void completionAndSimulation() {
        Fixture f = new Fixture();
        check(ProductionMilestoneBridge.isConfigured(), "new curated rule configures without Java API/schema change");
        check(f.level.storage.writes == 0, "configuration grants no proof and writes no journal");
        check(!f.proof("team_a"), "ready inventory is never production evidence");
        check(f.modelApply(true), "source-shaped simulated native match may succeed");
        check(!f.proof("team_a"), "Simulation cannot record a native electrum receipt");
        check(f.inputs == 2 && f.outputs == 0 && KeyProductionBridge.calls == 0,
            "simulation neither consumes, produces nor invokes key completion");
        f.returned(false, false); f.returned(false, null);
        check(!f.proof("team_a") && KeyProductionBridge.calls == 0, "false/null native result grants nothing");
        f.heated = false;
        check(!f.modelApply(false) && !f.proof("team_a"), "unheated modeled native failure cannot grant electrum proof");
        check(f.inputs == 2 && f.outputs == 0, "unheated modeled native process preserves inputs");
        f.heated = true; f.inputs = 1;
        check(!f.modelApply(false) && !f.proof("team_a"), "missing modeled inputs cannot prove completion");
        f.inputs = 2; f.outputAccepted = false;
        check(!f.modelApply(false) && !f.proof("team_a"), "rejected modeled outputs cannot prove completion");
        f.outputAccepted = true;
        check(f.modelApply(false), "successful modeled native completion returns true");
        check(f.inputs == 0 && f.outputs == 2, "modeled native completion consumes inputs and accepts two electrum");
        check(f.proof("team_a") && !f.proof("team_b"), "actual bridge records only current owner's team");
        check(f.level.storage.writes == 1 && KeyProductionBridge.calls == 1,
            "actual completion installs one journal entry and keeps key callback intact");
        f.returned(false, true);
        check(f.level.storage.writes == 1, "duplicate callback is journal-idempotent");
    }
    static void stageOwnershipAndReadiness() {
        Fixture f = new Fixture();
        Aia2MachineGuard.progress("team_a", 13);
        check(f.admitted(), "recipe floor8 alone permits a source-shaped process before independent proof floor15");
        f.returned(false, true);
        check(!f.proof("team_a"), "epoch14 cannot collect epoch15 process proof");
        Aia2MachineGuard.progress("team_a", 14); f.returned(false, true);
        check(f.proof("team_a"), "completion14 opens the exact epoch15 proof");

        f = new Fixture(); Aia2MachineGuard.ready = false;
        check(!f.admitted(), "unready guard denies the actual HEAD handler");
        f.returned(false, true);
        check(!f.proof("team_a"), "stale successful callback cannot bypass unready proof policy");
        Aia2MachineGuard.ready = true; f.basin.owner = ""; f.returned(false, true);
        check(!f.proof("team_a"), "ownerless output cannot be adopted by a nearby team");
        f.basin.owner = "unknown_team"; f.returned(false, true);
        check(!f.proof("unknown_team"), "unknown owner has no stage projection");
        f.basin.owner = "team_b"; Aia2MachineGuard.progress("team_b", 13); f.returned(false, true);
        check(!f.proof("team_b"), "second team requires its own epoch15 access");
        Aia2MachineGuard.progress("team_b", 14); f.returned(false, true);
        check(f.proof("team_b") && !f.proof("team_a"), "ready second team owns only its own receipt");

        f = new Fixture(); f.basin.level = new Level(); f.returned(false, true);
        check(!f.proof("team_a"), "client/non-server completion records nothing");
        f = new Fixture(); f.server.sameThread = false;
        boolean rejected = false;
        try { f.returned(false, true); } catch (IllegalStateException expected) { rejected = true; }
        check(rejected && f.level.storage.writes == 0, "off-thread completion fails before storage writes");
        f.server.sameThread = true;
        check(!f.proof("team_a"), "off-thread failure did not fabricate receipt");
    }
    static void nativeRecipeIdentityAndReload() {
        Fixture f = new Fixture();
        f.publish("example:other_electrum_route", f.recipe); f.returned(false, true);
        check(!f.proof("team_a"), "same output from an uncurated recipe ID gives no native proof");
        for (String serializer : List.of("minecraft:crafting_shaped", "create:compacting")) {
            f = new Fixture(); f.recipe = new MixingRecipe(OUTPUT, serializer); f.publish(RECIPE, f.recipe);
            f.returned(false, true);
            check(!f.proof("team_a"), "exact mixing serializer is required despite matching ID/output: " + serializer);
        }
        for (String output : List.of("minecraft:iron_ingot", "")) {
            f = new Fixture(); f.recipe = new MixingRecipe(output, "create:mixing"); f.publish(RECIPE, f.recipe);
            f.returned(false, true);
            check(!f.proof("team_a"), "changed/empty native recipe output gives no proof");
        }
        f = new Fixture();
        Aia2MachineGuard.progress("team_a", 13); f.returned(false, true);
        check(!f.proof("team_a"), "old recipe identity indexed before reload without granting");
        MixingRecipe old = f.recipe;
        MixingRecipe replacement = new MixingRecipe(OUTPUT, "create:mixing");
        f.publish(RECIPE, replacement); Aia2MachineGuard.progress("team_a", 14);
        f.returned(false, true);
        check(!f.proof("team_a"), "stale same-ID recipe object cannot receive a current-generation receipt");
        f.recipe = replacement; f.returned(false, true);
        check(f.proof("team_a"), "current same-ID exact output/type recipe works after reload");
        check(old != replacement, "reload case genuinely uses distinct recipe instances");

        f = new Fixture(); CrafterBlockEntity crafter = new CrafterBlockEntity(f.level, "team_a");
        crafter.slots[0] = new ItemStack("minecraft:gold_ingot", 1);
        ProductionMilestoneBridge.beginCrafter(crafter, f.recipe, new ItemStack(OUTPUT, 2));
        crafter.slots[0].shrink(1); ProductionMilestoneBridge.finishCrafter(crafter);
        check(!f.proof("team_a"), "a crafter cannot fabricate a mixing receipt through input shrink");
    }
    static void historicalProofsSurviveExtension() {
        Fixture f = new Fixture();
        CompoundTag root = new CompoundTag(); root.putInt("schema", 1);
        CompoundTag teams = new CompoundTag(), old = new CompoundTag();
        old.putBoolean("andesite_mixing", true); teams.put("team_a", old); root.put("teams", teams);
        f.level.storage.raw.put(DATA, root);
        check(ProductionMilestoneBridge.hasProof(f.server, "team_a", "andesite_mixing"),
            "existing schema1 history stays readable under the additional rule");
        check(!f.proof("team_a"), "old native proof cannot become the new electrum proof");
        f.returned(false, true);
        check(f.proof("team_a") && ProductionMilestoneBridge.hasProof(f.server, "team_a", "andesite_mixing"),
            "new receipt appends beside old proof without reset or adoption");
        SavedData saved = f.level.storage.data.get(DATA);
        CompoundTag encoded = saved.save(new CompoundTag(), null);
        check(encoded.getInt("schema") == 1 && encoded.getCompound("teams").getCompound("team_a").size() == 2,
            "existing durable schema and both literal IDs remain unchanged");
        f.level.storage.raw.put(DATA, encoded); f.level.storage.data.clear();
        ProductionMilestoneBridge.clearRuntime(); ProductionMilestoneBridge.configureJson(RULES);
        check(f.proof("team_a") && ProductionMilestoneBridge.hasProof(f.server, "team_a", "andesite_mixing"),
            "runtime reset and modeled NBT reload preserve both old and new proofs");
    }
    public static void main(String[] args) throws Exception {
        directory = Path.of(args[0]);
        head = CreateBasinRecipeMixin.class.getDeclaredMethod("aia2$guardBasin", Object.class, Recipe.class,
            boolean.class, CallbackInfoReturnable.class);
        finish = CreateBasinRecipeMixin.class.getDeclaredMethod("aia2$recordCompletedBasin", Object.class, Recipe.class,
            boolean.class, CallbackInfoReturnable.class);
        head.setAccessible(true); finish.setAccessible(true);
        completionAndSimulation(); stageOwnershipAndReadiness(); nativeRecipeIdentityAndReload(); historicalProofsSurviveExtension();
        System.out.println(checks + " electrum actual-bridge/actual-handlers/real-policy modeled assertions PASS; "
            + "native body, ownership and NBT/storage modeled; no weaving/client claim");
    }
}
