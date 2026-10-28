package ua.aia2.guard;

import java.lang.reflect.InvocationTargetException;
import java.lang.reflect.Method;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.BlockHitResult;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;
import com.stal111.forbidden_arcanus.common.block.entity.clibano.ClibanoFrameBlockEntity;
import com.stal111.forbidden_arcanus.common.block.entity.clibano.ClibanoMainBlockEntity;
import com.stal111.forbidden_arcanus.common.inventory.clibano.ClibanoMenu;

/** Executes the real owner helper/menu handler against a modeled optional host. */
public final class ClibanoOwnershipHarness {
    private static int checks;
    private static final BlockPos CENTER = new BlockPos(0, 64, 0);
    private static final BlockPos FRONT = new BlockPos(0, 64, 1);
    private static void check(boolean value, String message) {
        checks++;
        if (!value) throw new AssertionError(message);
    }
    private static final class Scene {
        final ServerLevel level = new ServerLevel();
        final ServerPlayer player = new ServerPlayer(level);
        final ClibanoMainBlockEntity main = new ClibanoMainBlockEntity(level, CENTER);
        final List<ClibanoFrameBlockEntity> frames = new ArrayList<>();
        final ClibanoFrameBlockEntity clicked;
        Scene() {
            resetPolicy();
            level.tiles.put(CENTER, main);
            ClibanoFrameBlockEntity front = null;
            for (BlockPos at : BlockPos.betweenClosed(CENTER.offset(-1, -1, -1), CENTER.offset(1, 1, 1))) {
                if (at.equals(CENTER)) continue;
                var frame = new ClibanoFrameBlockEntity(level, at);
                frame.data = new ClibanoFrameBlockEntity.FrameData(new BlockState("forbidden_arcanus:polished_darkstone"), CENTER);
                level.tiles.put(at, frame); frames.add(frame);
                if (at.equals(FRONT)) front = frame;
            }
            clicked = front;
        }
        int writes() { return main.ownerWrites + frames.stream().mapToInt(frame -> frame.ownerWrites).sum(); }
        Map<BlockPos, String> owners() {
            Map<BlockPos, String> result = new HashMap<>(); result.put(CENTER, main.owner);
            frames.forEach(frame -> result.put(frame.pos, frame.owner)); return result;
        }
        void denied(String why) {
            var before = owners(); int writes = writes();
            check(!ClibanoOwnership.claim(player, clicked), why + " denied");
            check(writes() == writes && owners().equals(before), why + " leaves every owner unchanged");
        }
    }
    private static Map<String, Integer> rules() {
        var result = new HashMap<String, Integer>();
        for (String block : List.of("clibano_main_part", "clibano_center", "clibano_corner", "clibano_side_horizontal", "clibano_side_vertical"))
            result.put("forbidden_arcanus:" + block, 15);
        return result;
    }
    private static void resetPolicy() {
        Aia2MachineGuard.POLICY.clear(); Aia2MachineGuard.POLICY.setRules(rules());
        Aia2MachineGuard.POLICY.setTeamProgress("a", 14); Aia2MachineGuard.POLICY.setTeamProgress("b", 14);
        Aia2MachineGuard.POLICY.setReady(); Aia2MachineGuard.ready = true;
        ClibanoAccess.payloadSafe = true;
    }
    private static Object invoke(Object receiver, Method method, Object... args) {
        try { method.setAccessible(true); return method.invoke(receiver, args); }
        catch (InvocationTargetException failure) {
            if (failure.getCause() instanceof RuntimeException runtime) throw runtime;
            throw new AssertionError(failure.getCause());
        } catch (ReflectiveOperationException failure) { throw new AssertionError(failure); }
    }
    private static CallbackInfoReturnable<InteractionResult> menuHandler(Level level, BlockPos pos, Player player) {
        try {
            Class<?> mixin = Class.forName("ua.aia2.guard.mixin.ClibanoFrameMenuMixin");
            Method handler = null;
            for (Method method : mixin.getDeclaredMethods()) {
                if (method.getParameterCount() == 6 && method.getParameterTypes()[5] == CallbackInfoReturnable.class) {
                    check(handler == null, "one unambiguous frame menu handler"); handler = method;
                }
            }
            check(handler != null, "frame menu handler found");
            Object receiver = new FrameMenuHost();
            var callback = new CallbackInfoReturnable<>(InteractionResult.PASS);
            invoke(receiver, handler, new BlockState("forbidden_arcanus:clibano_center"), level, pos, player, new BlockHitResult(), callback);
            return callback;
        } catch (ClassNotFoundException failure) { throw new AssertionError(failure); }
    }
    public static final class FrameMenuHost extends ua.aia2.guard.mixin.ClibanoFrameMenuMixin {}

    public static void main(String[] args) {
        Scene scene = new Scene();
        check(ClibanoOwnership.isMain(scene.main) && !ClibanoOwnership.isFrame(scene.main), "exact native main classification");
        check(ClibanoOwnership.isFrame(scene.clicked) && !ClibanoOwnership.isMain(scene.clicked), "exact native frame classification");
        check(!ClibanoOwnership.isMain(null) && !ClibanoOwnership.isFrame(null), "null has no optional native identity");
        check(ClibanoOwnership.resolveMain(scene.clicked) == scene.main, "frame resolves its stored actual controller");
        check(ClibanoOwnership.resolveMain(scene.main) == scene.main, "canonical direct controller resolves itself");
        check(ClibanoOwnership.claim(scene.player, scene.clicked), "available team claims a complete physical machine");
        check(scene.writes() == 27 && scene.owners().values().stream().allMatch("a"::equals), "main and all26frames get same owner");
        check(ClibanoOwnership.claim(scene.player, scene.clicked), "same team can use already owned machine");
        check(scene.writes() == 27, "same-owner repeat claim creates no extra owner writes");
        check(ClibanoOwnership.open(scene.player, scene.clicked), "authorized frame opens bound menu");
        check(scene.player.opened == 1 && scene.player.lastMenu == scene.main, "menu uses actual associated main");
        check(scene.player.lastBuffer.encoded == scene.main.residues, "menu encodes exact controller residue storage");
        Scene neighbor = new Scene();
        var unrelated = new ClibanoMainBlockEntity(neighbor.level, CENTER.offset(0, 0, 2)); unrelated.owner = "b";
        neighbor.level.tiles.put(unrelated.pos, unrelated);
        check(ClibanoOwnership.open(neighbor.player, neighbor.clicked) && neighbor.player.lastMenu == neighbor.main,
                "unrelated neighboring controller never replaces bound GUI target");
        check(unrelated.owner.equals("b") && unrelated.ownerWrites == 0, "neighbor owner remains unchanged");
        check(!ClibanoOwnership.claim(neighbor.player, neighbor.main), "hidden main cannot substitute a clicked frame");

        for (int index = 0; index < 26; index++) {
            Scene missing = new Scene(); BlockPos at = missing.frames.get(index).pos;
            missing.level.tiles.remove(at); missing.denied("missing shell cell " + index);
            Scene stale = new Scene();
            stale.frames.get(index).data = new ClibanoFrameBlockEntity.FrameData(new BlockState("forbidden_arcanus:polished_darkstone"), CENTER.offset(9, 0, 0));
            stale.denied("shell association mismatch " + index);
            Scene foreign = new Scene(); foreign.frames.get(index).owner = "b";
            foreign.denied("existing foreign shell owner " + index);
        }
        Scene foreignMain = new Scene(); foreignMain.main.owner = "b"; foreignMain.denied("foreign main owner");
        Scene reserved = new Scene(); reserved.main.owner = "a"; reserved.frames.get(17).owner = "b";
        reserved.denied("same main owner cannot override a conflicting frame");
        Scene oldFrameOwner = new Scene(); oldFrameOwner.clicked.owner = "a";
        check(ClibanoOwnership.claim(oldFrameOwner.player, oldFrameOwner.clicked), "legacy frame owner can bind previously unowned main");
        check(oldFrameOwner.main.owner.equals("a") && oldFrameOwner.writes() == 26, "existing own frame not rewritten during migration");

        Scene fake = new Scene(); fake.player.fake = true; fake.denied("FakePlayer");
        Scene unsynced = new Scene(); unsynced.player.syncedTeam = "b"; unsynced.denied("outdated synchronized team");
        Scene blank = new Scene(); blank.player.liveTeam = ""; blank.player.syncedTeam = ""; blank.denied("blank live team");
        Scene tooEarly = new Scene(); Aia2MachineGuard.POLICY.setTeamProgress("a", 13); tooEarly.denied("future stage15 machine");
        Scene laterMain = new Scene(); var futureRules = rules(); futureRules.put("forbidden_arcanus:clibano_main_part", 21);
        Aia2MachineGuard.POLICY.setRules(futureRules); laterMain.denied("internal main floor checked independently");
        Scene futureFrame = new Scene(); futureFrame.frames.get(11).state = new BlockState("unreviewed:frame"); futureFrame.denied("unclassified shell block");
        Scene notReady = new Scene(); Aia2MachineGuard.ready = false; notReady.denied("guard not ready");
        Scene noBuild = new Scene(); noBuild.player.abilities.mayBuild = false; noBuild.denied("mayBuild false");
        Scene spectator = new Scene(); spectator.player.spectator = true; spectator.denied("spectator");
        Scene protectedClick = new Scene(); protectedClick.level.protectedPositions.add(FRONT); protectedClick.denied("protected clicked frame");
        Scene protectedMain = new Scene(); protectedMain.level.protectedPositions.add(CENTER); protectedMain.denied("protected internal main");
        for (int index = 0; index < 26; index++) {
            Scene protectedShell = new Scene(); protectedShell.level.protectedPositions.add(protectedShell.frames.get(index).pos);
            protectedShell.denied("protected shell cell " + index);
        }
        Scene useDenied = new Scene(); useDenied.player.cannotUse.add(FRONT); useDenied.denied("item interaction forbidden");
        Scene far = new Scene(); far.player.pos = new BlockPos(12, 64, 1); far.denied("far player");
        Scene otherLevel = new Scene(); otherLevel.player.level = new ServerLevel(); otherLevel.denied("different player dimension");
        Scene wrongThread = new Scene(); wrongThread.level.server.sameThread = false; wrongThread.denied("non-server thread");
        Scene nullPlayer = new Scene(); check(!ClibanoOwnership.claim(null, nullPlayer.clicked) && nullPlayer.writes() == 0, "missing player cannot claim");

        Scene empty = new Scene(); empty.clicked.data = ClibanoFrameBlockEntity.FrameData.EMPTY;
        check(ClibanoOwnership.resolveMain(empty.clicked) == null, "empty FrameData never resolves origin controller"); empty.denied("empty frame");
        Scene noData = new Scene(); noData.clicked.data = null; noData.denied("missing native frame association");
        Scene removed = new Scene(); removed.main.removed = true; removed.denied("removed main");
        Scene removedFrame = new Scene(); removedFrame.frames.get(4).removed = true; removedFrame.denied("removed shell cell");
        Scene staleReceiver = new Scene();
        var stale = new ClibanoFrameBlockEntity(staleReceiver.level, FRONT); stale.data = staleReceiver.clicked.data;
        check(ClibanoOwnership.resolveMain(stale) == null && !ClibanoOwnership.claim(staleReceiver.player, stale), "same-position stale frame object cannot substitute actual BE");
        Scene movedMain = new Scene(); movedMain.main.pos = CENTER.offset(1, 0, 0); movedMain.denied("main world map/position mismatch");
        Scene wrongFrameType = new Scene(); wrongFrameType.level.tiles.put(wrongFrameType.frames.get(5).pos,
                new BlockEntity(wrongFrameType.level, wrongFrameType.frames.get(5).pos, "forbidden_arcanus:clibano_center"));
        wrongFrameType.denied("matching block ID cannot replace native frame identity");
        Scene wrongMainType = new Scene(); wrongMainType.level.tiles.put(CENTER, new BlockEntity(wrongMainType.level, CENTER, "forbidden_arcanus:clibano_main_part"));
        wrongMainType.denied("matching main block ID cannot replace native controller");
        Scene unloaded = new Scene(); BlockPos absent = unloaded.frames.get(23).pos; unloaded.level.unloaded.add(absent); unloaded.level.reads.clear();
        unloaded.denied("unloaded shell chunk"); check(!unloaded.level.reads.contains(absent), "unloaded chunk is not read/forced by resolver");
        Scene unloadedMain = new Scene(); unloadedMain.level.unloaded.add(CENTER); unloadedMain.denied("unloaded main chunk");
        Scene outOfRange = new Scene(); outOfRange.clicked.data = new ClibanoFrameBlockEntity.FrameData(new BlockState("forbidden_arcanus:polished_darkstone"), CENTER.offset(12, 0, 0));
        outOfRange.denied("distant forged mainPos");

        Scene handler = new Scene();
        var allowed = menuHandler(handler.level, FRONT, handler.player);
        check(allowed.cancelled && allowed.getReturnValue() != InteractionResult.PASS && handler.player.lastMenu == handler.main,
                "actual frame handler cancels native POI route and opens bound controller");
        Scene menuDenied = new Scene(); menuDenied.main.owner = "b";
        var denied = menuHandler(menuDenied.level, FRONT, menuDenied.player);
        check(denied.cancelled && menuDenied.player.opened == 0 && menuDenied.writes() == 0,
                "denied frame handler suppresses all native POI fallback and owner writes");
        Level client = new Level(); client.client = true;
        var clientResult = menuHandler(client, FRONT, new Player());
        check(clientResult.cancelled && clientResult.getReturnValue() == InteractionResult.SUCCESS,
                "client predicts success without calling server owner bridge");

        Scene live = new Scene(); check(ClibanoOwnership.claim(live.player, live.clicked), "live menu fixture owns actual structure");
        ClibanoMenu menu = new ClibanoMenu(live.main);
        check(ClibanoOwnership.mayKeepMenu(menu, live.player) && menu.stillValid(live.player), "current authorized owner keeps native menu");
        check(menu.nativeChecks == 1, "allowed actual validity handler keeps native distance/block check");
        menu.nativeAllowed = false;
        check(!menu.stillValid(live.player) && menu.nativeChecks == 2, "helper cannot override native menu rejection");
        menu.nativeAllowed = true; live.main.owner = "b";
        check(!menu.stillValid(live.player) && menu.nativeChecks == 2, "owner changes close already open menu before native path");
        live.main.owner = "a"; live.player.liveTeam = "b";
        check(!menu.stillValid(live.player), "unsynchronized team changes revoke live menu");
        live.player.syncedTeam = "b";
        check(!menu.stillValid(live.player), "even synchronized foreign live team cannot keep prior owner menu");
        live.player.liveTeam = "a"; live.player.syncedTeam = "a";
        Aia2MachineGuard.POLICY.setTeamProgress("a", 13);
        check(!menu.stillValid(live.player), "stage removal revokes existing menu");
        Aia2MachineGuard.POLICY.setTeamProgress("a", 14);
        check(menu.stillValid(live.player), "current authorized policy can resume existing menu validation");
        live.player.fake = true; check(!menu.stillValid(live.player), "fake player cannot retain native menu"); live.player.fake = false;
        live.player.spectator = true; check(!menu.stillValid(live.player), "spectator cannot retain native menu"); live.player.spectator = false;
        live.level.protectedPositions.add(CENTER); check(!menu.stillValid(live.player), "new world protection revokes live menu"); live.level.protectedPositions.clear();
        live.main.removed = true; check(!menu.stillValid(live.player), "removed controller closes live menu"); live.main.removed = false;
        live.level.tiles.put(CENTER, new ClibanoMainBlockEntity(live.level, CENTER));
        check(!menu.stillValid(live.player), "same-position replacement cannot reuse an old menu's controller"); live.level.tiles.put(CENTER, live.main);
        live.player.level = new ServerLevel(); check(!menu.stillValid(live.player), "dimension change closes live menu"); live.player.level = live.level;
        live.level.unloaded.add(CENTER); check(!menu.stillValid(live.player), "unloaded main closes live menu"); live.level.unloaded.clear();
        Aia2MachineGuard.ready = false; check(!menu.stillValid(live.player), "guard reset revokes live menu"); Aia2MachineGuard.ready = true;
        check(!ClibanoOwnership.mayKeepMenu(null, live.player) && !ClibanoOwnership.mayKeepMenu(new Object(), live.player)
                && !ClibanoOwnership.mayKeepMenu(menu, null), "missing/wrong menu or player never proves server access");
        check(!new ClibanoMenu(null).stillValid(live.player), "null native context block is denied");
        Player clientPlayer = new Player(); clientPlayer.clientLevel = client;
        check(ClibanoOwnership.mayKeepMenu(null, clientPlayer), "client keeps its native prediction path without server holder lookup");

        for (int mode = 0; mode < 8; mode++) {
            Scene corrupt = new Scene();
            check(ClibanoOwnership.claim(corrupt.player, corrupt.clicked), "corrupt state fixture owner established");
            switch (mode) {
                case 0 -> corrupt.main.logic = null;
                case 1 -> corrupt.main.logic.cookingProgress = null;
                case 2 -> corrupt.main.logic.cookingDuration = null;
                case 3 -> corrupt.main.logic.cookingProgress = new int[] {0};
                case 4 -> corrupt.main.logic.cookingDuration = new int[] {0,0,0};
                case 5 -> corrupt.main.logic.cookingProgress = new int[] {-1,0};
                case 6 -> corrupt.main.logic.cookingDuration = new int[] {0,-1};
                case 7 -> corrupt.main.logic.cookingProgress = new int[] {0,0,0};
            }
            Object beforeLogic = corrupt.main.logic;
            int[] beforeProgress = corrupt.main.logic == null ? null : corrupt.main.logic.cookingProgress;
            int[] beforeDuration = corrupt.main.logic == null ? null : corrupt.main.logic.cookingDuration;
            check(!ClibanoOwnership.menuStateSafe(corrupt.main) && !ClibanoOwnership.open(corrupt.player, corrupt.clicked)
                    && corrupt.player.opened == 0, "corrupt native arrays denied before menu creation " + mode);
            check(!new ClibanoMenu(corrupt.main).stillValid(corrupt.player), "corrupt arrays also revoke live menu " + mode);
            check(corrupt.main.logic == beforeLogic && (corrupt.main.logic == null ||
                    corrupt.main.logic.cookingProgress == beforeProgress && corrupt.main.logic.cookingDuration == beforeDuration),
                    "GUI validation never repairs/replaces corrupt arrays " + mode);
        }
        Scene replaced = new Scene(); check(ClibanoOwnership.claim(replaced.player,replaced.clicked), "replacement fixture owns structure");
        ClibanoMenu oldMenu = new ClibanoMenu(replaced.main); check(oldMenu.stillValid(replaced.player), "original menu starts authorized");
        ClibanoMainBlockEntity successor = new ClibanoMainBlockEntity(replaced.level,CENTER); successor.owner="a"; replaced.level.tiles.put(CENTER,successor);
        check(!oldMenu.stillValid(replaced.player), "dynamic native context cannot rebind old inventory to a same-owner replacement controller");
        ClibanoOwnership.bindMenu(oldMenu);
        check(!oldMenu.stillValid(replaced.player), "a repeated binding call cannot replace the original menu inventory identity");
        check(new ClibanoMenu(successor).stillValid(replaced.player), "new replacement menu binds its actual new inventory");
        Scene stalePayload = new Scene();
        ClibanoAccess.payloadSafe = false;
        check(!ClibanoOwnership.open(stalePayload.player, stalePayload.clicked) && stalePayload.player.opened == 0,
                "stale/unread residue holders cannot reach native menu network encoder");
        check(!new ClibanoMenu(stalePayload.main).stillValid(stalePayload.player), "unsafe residue payload also revokes existing menu");
        ClibanoAccess.payloadSafe = true;
        System.out.println("ClibanoOwnershipHarness: " + checks + " actual-helper/handler/real-policy modeled assertions PASS");
    }
}
