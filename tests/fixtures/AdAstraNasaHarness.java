package ua.aia2.guard.mixin;

import java.lang.reflect.Method;
import java.util.function.Consumer;
import earth.terrarium.adastra.common.blockentities.machines.NasaWorkbenchBlockEntity;
import earth.terrarium.adastra.common.menus.machines.NasaWorkbenchMenu;
import earth.terrarium.adastra.common.recipes.machines.NasaWorkbenchRecipe;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.inventory.ClickType;
import net.minecraft.world.item.ItemStack;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;
import ua.aia2.guard.AdAstraNasaAccess;
import ua.aia2.guard.Aia2MachineGuard;

/** Actual helper and handlers; Minecraft/Ad Astra receivers are modeled, not woven. */
public final class AdAstraNasaHarness {
    private static int assertions;
    private static void check(boolean value, String text) {
        assertions++;
        if (!value) throw new AssertionError(text);
    }
    private static void call(Class<?> type, String name, Object target, Object... arguments) {
        try {
            for (Method method : type.getDeclaredMethods()) {
                if (!method.getName().equals(name)) continue;
                method.setAccessible(true); method.invoke(target, arguments); return;
            }
            throw new AssertionError("Missing actual handler " + name);
        } catch (ReflectiveOperationException failure) { throw new AssertionError(failure); }
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
    private static NasaWorkbenchBlockEntity fixture() {
        Aia2MachineGuard.configure();
        var level = new ServerLevel(); var machine = new NasaWorkbenchBlockEntity();
        machine.level = level; level.entity = machine;
        var recipe = new NasaWorkbenchRecipe(new ItemStack("ad_astra:tier_1_rocket", 1));
        machine.recipe(recipe); Aia2MachineGuard.live.put(recipe, "ad_astra:t1");
        for (int i = 0; i < 14; i++) machine.items[i] = new ItemStack("minecraft:iron_ingot", 2);
        machine.items[14] = recipe.result().copy();
        return machine;
    }
    private static String snapshot(NasaWorkbenchBlockEntity machine) {
        var result = new StringBuilder();
        for (var item : machine.items) result.append(item.item).append(':').append(item.count).append(item.components).append(';');
        return result + "/" + machine.particles + "/" + machine.writes + "/" + (machine.level == null ? -1 : machine.level.drops);
    }
    private static void denied(String label, Consumer<NasaWorkbenchBlockEntity> mutation, boolean previewMaySelect) {
        var machine = fixture(); mutation.accept(machine); String before = snapshot(machine);
        check(AdAstraNasaAccess.maySelect(machine) == previewMaySelect, label + " selection");
        check(!AdAstraNasaAccess.mayFinish(machine), label + " finish denied");
        machine.craft();
        check(before.equals(snapshot(machine)), label + " no particles/drop/writes/payment");
    }
    private static void machineCases() {
        var allowed = fixture();
        check(allowed.canCraft(), "current paid inputs can select in epoch37");
        check(AdAstraNasaAccess.mayFinish(allowed), "matching preview permits native finish");
        allowed.craft();
        check(allowed.level.drops == 1 && allowed.particles == 1 && allowed.writes == 1, "one native result with original effects");
        for (int i = 0; i < 14; i++) check(allowed.items[i].count == 1, "one native unit consumed slot" + i);
        check(allowed.items[14].isEmpty(), "preview cleared by original native code");
        String after = snapshot(allowed); allowed.craft();
        check(after.equals(snapshot(allowed)), "recipe reset prevents repeated manufacture");

        denied("before37", machine -> Aia2MachineGuard.progress(35), false);
        denied("future cached T3", machine -> {
            var recipe = new NasaWorkbenchRecipe(new ItemStack("ad_astra:tier_3_rocket", 1));
            machine.recipe(recipe); machine.items[14] = recipe.result().copy(); Aia2MachineGuard.live.put(recipe, "ad_astra:t3");
        }, false);
        denied("future output in allowed recipe", machine -> {
            var recipe = new NasaWorkbenchRecipe(new ItemStack("ad_astra:tier_3_rocket", 1));
            machine.recipe(recipe); machine.items[14] = recipe.result().copy(); Aia2MachineGuard.live.put(recipe, "ad_astra:t1");
        }, false);
        denied("stale future preview", machine -> machine.items[14] = new ItemStack("ad_astra:tier_3_rocket", 1), true);
        denied("wrong preview count", machine -> machine.items[14].count = 2, true);
        denied("wrong preview components", machine -> machine.items[14].components.put("custom", "stale"), true);
        denied("empty preview", machine -> machine.items[14] = ItemStack.EMPTY, true);
        denied("reloaded cached identity", machine -> Aia2MachineGuard.live.clear(), false);
        denied("wrong ingredient", machine -> machine.items[5] = new ItemStack("minecraft:diamond", 2), false);
        denied("missing ingredient", machine -> machine.items[2] = ItemStack.EMPTY, false);
        denied("removed owner", machine -> machine.removed = true, false);
        denied("unloaded chunk", machine -> ((ServerLevel)machine.level).loaded = false, false);
        denied("off thread", machine -> ((ServerLevel)machine.level).server.sameThread = false, false);
        denied("replaced block entity", machine -> machine.level.entity = new NasaWorkbenchBlockEntity(), false);
        denied("unowned", machine -> machine.owner = "", false);
        denied("unready", machine -> Aia2MachineGuard.ready = false, false);
        denied("wrong container shape", machine -> machine.size = 14, false);
        denied("null cached recipe", machine -> machine.recipe(null), false);
        for (String key : new String[]{"kubejs:aia2_tech_key_37", "example:registered_key"}) {
            denied("no NASA key receipt " + key, machine -> {
                var recipe = new NasaWorkbenchRecipe(new ItemStack(key, 1));
                machine.recipe(recipe); machine.items[14] = recipe.result().copy(); Aia2MachineGuard.live.put(recipe, "ad_astra:t1");
            }, false);
        }
        var rejected = fixture();
        check(!select(rejected, false), "guard never turns a native false match true");
        rejected.level.client = true; rejected.owner = ""; Aia2MachineGuard.ready = false;
        check(AdAstraNasaAccess.maySelect(rejected), "client selection preserves native presentation");
        check(AdAstraNasaAccess.mayFinish(rejected), "helper does not enforce server ownership on client");
        check(!AdAstraNasaAccess.mayFinish(null), "null receiver denies");
    }

    private static void menuCases(String mode) {
        var machine = fixture(); var menu = new NasaWorkbenchMenu(machine); var player = new ServerPlayer();
        player.world = machine.level; player.containerMenu = menu;
        check(AdAstraNasaAccess.mayUseMenu(menu, player), "original live owner can use menu");
        if (mode.equals("base")) {
            var valid = new CallbackInfoReturnable<Boolean>(true);
            call(AdAstraNasaBaseMenuMixin.class, "aia2$stillOwned", menu, player, valid);
            check(valid.getReturnValue(), "valid native menu remains open");
            String beforePreview = snapshot(machine);
            var preview = new CallbackInfoReturnable<ItemStack>(new ItemStack("ad_astra:tier_1_rocket", 1));
            call(AdAstraNasaBaseMenuMixin.class, "aia2$shiftMove", menu, player, 14, preview);
            check(preview.cancelled && preview.getReturnValue().isEmpty(), "direct shift caller cannot take unpaid preview");
            check(beforePreview.equals(snapshot(machine)), "preview quickmove rejection does not pay or drop");
            var input = new CallbackInfoReturnable<ItemStack>(new ItemStack("minecraft:iron_ingot", 1));
            call(AdAstraNasaBaseMenuMixin.class, "aia2$shiftMove", menu, player, 0, input);
            check(!input.cancelled, "valid owner ordinary input transfer remains native");
        }
        for (int scenario = 0; scenario < 10; scenario++) {
            machine = fixture(); menu = new NasaWorkbenchMenu(machine); player = new ServerPlayer();
            player.world = machine.level; player.containerMenu = menu;
            switch (scenario) {
                case 0 -> player.team = player.synced = "other_team";
                case 1 -> player.synced = "stale_team";
                case 2 -> player.near = false;
                case 3 -> ((ServerLevel)machine.level).interact = false;
                case 4 -> player.world = new ServerLevel();
                case 5 -> machine.level.entity = new NasaWorkbenchBlockEntity();
                case 6 -> machine.removed = true;
                case 7 -> player.containerMenu = null;
                case 8 -> Aia2MachineGuard.progress(35);
                case 9 -> {
                    var fake = new net.neoforged.neoforge.common.util.FakePlayer();
                    fake.world = machine.level; fake.containerMenu = menu; player = fake;
                }
            }
            check(!AdAstraNasaAccess.mayUseMenu(menu, player), "menu live check " + scenario);
            String before = snapshot(machine);
            if (mode.equals("base")) {
                var valid = new CallbackInfoReturnable<Boolean>(true);
                call(AdAstraNasaBaseMenuMixin.class, "aia2$stillOwned", menu, player, valid);
                check(!valid.getReturnValue(), "closed stale menu " + scenario);
                var shift = new CallbackInfoReturnable<ItemStack>(new ItemStack("minecraft:diamond", 1));
                call(AdAstraNasaBaseMenuMixin.class, "aia2$shiftMove", menu, player, 0, shift);
                check(shift.cancelled && shift.getReturnValue().isEmpty(), "no shift theft " + scenario);
            } else {
                var click = new CallbackInfo();
                call(AdAstraNasaMenuMixin.class, "aia2$ownerClick", menu, 14, 0, ClickType.PICKUP, player, click);
                check(click.cancelled, "NASA child click stopped before super/native craft " + scenario);
            }
            check(before.equals(snapshot(machine)), "denied menu handler remains read only " + scenario);
        }
        check(!AdAstraNasaAccess.isNasaMenu(new Object()), "base guard scope excludes other mod menus");
    }

    public static void main(String[] args) {
        machineCases(); menuCases(args[0]);
        System.out.println(assertions + " Ad Astra NASA modeled assertions PASS (" + args[0] + ")");
    }
}
