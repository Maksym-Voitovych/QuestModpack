package ua.aia2.guard;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.Map;
import java.util.function.Consumer;
import earth.terrarium.adastra.api.planets.PlanetApi;
import earth.terrarium.adastra.common.network.packets.ServerboundConstructSpaceStationPacket;
import earth.terrarium.adastra.common.recipes.SpaceStationRecipe;
import earth.terrarium.adastra.common.recipes.base.IngredientHolder;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Holder;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.ResourceKey;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.tags.TagKey;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.crafting.Ingredient;
import net.minecraft.world.item.crafting.RecipeHolder;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Rotation;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.levelgen.structure.templatesystem.StructurePlaceSettings;
import net.minecraft.world.level.levelgen.structure.templatesystem.StructureTemplate;
import net.neoforged.neoforge.common.util.FakePlayer;

/** Actual station runtime helpers with modeled MC/Ad Astra receivers, not weaving. */
public final class StationConstructionHarness {
    private static int assertions;
    private static final ResourceLocation RECIPE = ResourceLocation.parse("ad_astra:station");
    private static final ResourceLocation STRUCTURE = ResourceLocation.parse("ad_astra:space_station");
    private static final ResourceKey<Level> EARTH = key("minecraft:overworld");
    private static final ResourceKey<Level> ORBIT = key("ad_astra:earth_orbit");
    private static final Component NAME = Component.literal("Оплачена станція");
    private static ResourceKey<Level> key(String id) { return ResourceKey.create(null, ResourceLocation.parse(id)); }
    private static void check(boolean value, String message) { assertions++; if (!value) throw new AssertionError(message); }
    private static ItemStack stack(String id, int amount) { return new ItemStack(id, amount); }
    private static IngredientHolder need(String id, int amount) { return new IngredientHolder(Ingredient.of(id), amount); }

    private static final class Fixture {
        final ServerLevel source = new ServerLevel(), target = new ServerLevel();
        ServerPlayer player = new ServerPlayer();
        final StructureTemplate template = new StructureTemplate();
        final StructurePlaceSettings settings = new StructurePlaceSettings();
        SpaceStationRecipe recipe;
        ServerboundConstructSpaceStationPacket packet = new ServerboundConstructSpaceStationPacket(EARTH, NAME);
        int registrations, teleports, claims, nativeCalls, nativeReturns, placementCalls;
        boolean placementResult = true, performWrites = true;
        java.util.function.UnaryOperator<BlockState> incomingState;
        Runnable afterSelection, afterPayment, afterNativePlacement, beforeRegistration, duringRegistration, afterRegistration;
        Fixture() {
            Aia2MachineGuard.configure();
            source.key = EARTH; target.key = ORBIT; target.server = source.server;
            source.server.levels.put(EARTH, source); source.server.levels.put(ORBIT, target);
            player.world = source;source.server.players.players.put(player.getUUID(),player);
            PlanetApi.API.planets.clear(); PlanetApi.API.planets.put(EARTH, new earth.terrarium.adastra.api.planets.Planet(ORBIT));
            template.blocks.put(new BlockPos(0, 0, 0), new BlockState("minecraft:iron_block"));
            template.blocks.put(new BlockPos(1, 0, 0), new BlockState("minecraft:glass"));
            target.structures.templates.put(STRUCTURE, template);
            install(List.of(need("minecraft:iron_ingot", 64)));
            player.inventory.items[0] = stack("minecraft:iron_ingot", 1);
            player.inventory.items[1] = stack("minecraft:iron_ingot", 63);
        }
        void install(List<IngredientHolder> inputs) {
            recipe = new SpaceStationRecipe(new ArrayList<>(inputs), ORBIT, STRUCTURE);
            target.recipes.replace(List.of(new RecipeHolder<>(RECIPE, recipe)));
            Aia2MachineGuard.live.clear(); Aia2MachineGuard.live.put(recipe, RECIPE.toString());
        }
        BlockPos origin() {
            return BlockPos.containing(player.chunk.getMiddleBlockX() - template.size.getX() / 2.0f,
                    100, player.chunk.getMiddleBlockZ() - template.size.getZ() / 2.0f);
        }
        void nativeAction(Player receiver) {
            nativeCalls++;
            if (!StationConstructionAccess.hasIngredients(receiver, target, recipe)) { nativeReturns++; return; }
            if (afterSelection != null) afterSelection.run();
            StationConstructionAccess.consume(receiver, target);
            if (afterPayment != null) afterPayment.run();
            BlockPos origin = origin();
            StationConstructionAccess.beforePlacement(template, target, origin, origin, settings, 2);
            placementCalls++;
            if (performWrites) for (var block : List.copyOf(template.blocks.entrySet())) {
                BlockState supplied = incomingState == null ? block.getValue() : incomingState.apply(block.getValue());
                StationConstructionAccess.writePrimary(target, origin.offset(block.getKey()), supplied, 2);
            }
            if (afterNativePlacement != null) afterNativePlacement.run();
            StationConstructionAccess.afterPlacement(template, placementResult);
            if (beforeRegistration != null) beforeRegistration.run();
            if (StationConstructionAccess.beforeRegister(player, target, NAME)) {
                registrations++;
                if (duringRegistration != null) duringRegistration.run();
                StationConstructionAccess.afterRegister(player, target, NAME);
            }
            if (afterRegistration != null) afterRegistration.run();
            teleports++; claims++; nativeReturns++;
        }
        void run() { StationConstructionAccess.wrap(packet, this::nativeAction).accept(player); }
    }

    private static void deniedBefore(String label, Consumer<Fixture> change) {
        var f = new Fixture(); change.accept(f);
        ItemStack[] refs = f.player.inventory.items.clone();
        ItemStack[] contents = Arrays.stream(refs).map(ItemStack::copy).toArray(ItemStack[]::new);
        f.run();
        check(f.registrations == 0 && f.teleports == 0 && f.claims == 0, label + " prevents continuation");
        check(!StationConstructionAccess.hasScope(), label + " clears packet scope");
        check(f.target.writes == 0 && f.player.inventory.removals == 0, label + " rejects before payment and placement");
        for (int i=0;i<refs.length;i++) {
            ItemStack actual=f.player.inventory.items[i];
            check(actual==refs[i] && actual.getCount()==contents[i].getCount()
                    && actual.getItem()==contents[i].getItem() && actual.components.equals(contents[i].components),
                    label + " preserves input slot " + i);
        }
    }
    private static void deniedDuring(String label, Consumer<Fixture> change) {
        var f = new Fixture(); change.accept(f); f.run();
        check(f.registrations == 0 && f.teleports == 0 && f.claims == 0, label + " denies registration/teleport/claims");
        check(!StationConstructionAccess.hasScope(), label + " removes failed operation scope");
        var next = new Fixture(); next.run();
        check(next.registrations == 1 && next.teleports == 1, label + " clears scope for the next native call");
    }

    private static void successfulPayment() {
        var f = new Fixture();
        ItemStack first=f.player.inventory.items[0], second=f.player.inventory.items[1];
        f.run();
        check(f.nativeCalls==1 && f.nativeReturns==1, "one native consumer operation returns");
        check(first.getCount()==0 && second.getCount()==0, "64units from1+63 paid exactly");
        check(f.player.inventory.getItem(0)==first && f.player.inventory.getItem(1)==second,
                "native removeItem retains original stack references");
        check(f.player.inventory.removals==2 && f.target.writes==2, "split debits and two primary writes only");
        check(f.registrations==1 && f.teleports==1 && f.claims==1, "successful paid placement continues once");
        check(!StationConstructionAccess.beforeRegister(f.player,f.target,NAME), "unscoped direct constructor denied");

        var overlap = new Fixture();
        overlap.install(List.of(new IngredientHolder(new Ingredient(
                new Ingredient.ItemValue(stack("minecraft:iron_ingot",1)),
                new Ingredient.ItemValue(stack("minecraft:gold_ingot",1))),1), need("minecraft:iron_ingot",1)));
        Arrays.fill(overlap.player.inventory.items,ItemStack.EMPTY);
        overlap.player.inventory.items[0]=stack("minecraft:iron_ingot",1);
        overlap.player.inventory.items[1]=stack("minecraft:gold_ingot",1);
        overlap.run();
        check(overlap.registrations==1 && overlap.player.inventory.getItem(0).isEmpty()
                && overlap.player.inventory.getItem(1).isEmpty(), "global matching avoids greedy false negative");

        var armored = new Fixture();
        Arrays.fill(armored.player.inventory.items,ItemStack.EMPTY);
        armored.player.inventory.items[40]=stack("minecraft:iron_ingot",64);armored.run();
        check(armored.registrations==1 && armored.player.inventory.getItem(40).isEmpty(), "full native41slot inventory participates");

        var air = new Fixture();
        air.template.blocks.put(new BlockPos(2,0,0), new BlockState("minecraft:air"));
        air.target.beforeWrite=(position,state)->air.target.accepted=!state.isAir();
        air.run();
        check(air.registrations==1 && air.teleports==1,
                "unchanged native air writes may return false after every nonair write is accepted");

        var unrelated = new Fixture();
        unrelated.player.inventory.items[8]=stack("industrialupgrade:late_ingot",8);
        unrelated.player.inventory.items[9]=stack("minecraft:gold_ingot",8);
        unrelated.player.inventory.items[9].components.put("custom",true);
        unrelated.run();
        check(unrelated.registrations==1 && unrelated.player.inventory.getItem(8).getCount()==8
                && unrelated.player.inventory.getItem(9).getCount()==8,
                "unselected future and nondefault stacks remain intact without supplying capacity");

        var shape = new Fixture();
        shape.beforeRegistration=()->shape.target.blocks.replaceAll((position,state)->new BlockState(state.id(),"native-neighbor-update"));
        shape.run();
        check(shape.registrations==1 && shape.teleports==1,
                "retention permits native shape-property changes while retaining every required block identity");

        var immediateShape = new Fixture();
        immediateShape.target.afterWrite=(position,state)->immediateShape.target.blocks.put(position,
                new BlockState(state.id(),"synchronous-native-shape-update"));
        immediateShape.run();
        check(immediateShape.registrations==1 && immediateShape.teleports==1
                && immediateShape.target.writes==2,
                "setBlock may synchronously update properties before returning while preserving accepted block identity");
    }

    private static void initialDenials() {
        deniedBefore("insufficient63",f->f.player.inventory.items[1]=stack("minecraft:iron_ingot",62));
        deniedBefore("overlapping demand double-count",f->{f.install(List.of(need("minecraft:iron_ingot",64),need("minecraft:iron_ingot",1)));});
        deniedBefore("Creative",f->f.player.creative=true);
        deniedBefore("Spectator",f->f.player.spectator=true);
        deniedBefore("removed player",f->f.player.removed=true);
        deniedBefore("not alive player",f->f.player.alive=false);
        deniedBefore("player removed from live server list",f->f.source.server.players.players.clear());
        deniedBefore("off-thread packet",f->f.source.server.sameThread=false);
        deniedBefore("fake player",f->{var fake=new FakePlayer();fake.world=f.source;f.player=fake;});
        deniedBefore("not ready",f->Aia2MachineGuard.ready=false);
        deniedBefore("unsynchronized membership",f->f.player.synced="other");
        deniedBefore("early stage",f->Aia2MachineGuard.progress(35));
        deniedBefore("missing planet",f->PlanetApi.API.planets.clear());
        deniedBefore("missing orbit",f->f.source.server.levels.remove(ORBIT));
        deniedBefore("wrong destination recipe",f->{f.recipe=new SpaceStationRecipe(f.recipe.ingredients(),key("ad_astra:glacio_orbit"),STRUCTURE);f.target.recipes.replace(List.of(new RecipeHolder<>(RECIPE,f.recipe)));Aia2MachineGuard.live.put(f.recipe,RECIPE.toString());});
        deniedBefore("missing template",f->f.target.structures.templates.clear());
        deniedBefore("unsupported template",f->f.template.supported=false);
        deniedBefore("missing current recipe",f->f.target.recipes.replace(List.of()));
        deniedBefore("unregistered recipe identity",f->Aia2MachineGuard.live.clear());
        deniedBefore("nonpositive amount",f->f.install(List.of(need("minecraft:iron_ingot",0))));
        deniedBefore("oversize amount",f->f.install(List.of(need("minecraft:iron_ingot",4097))));
        deniedBefore("unknown custom ingredient",f->f.install(List.of(new IngredientHolder(new Ingredient(true,
                new Ingredient.ItemValue(stack("minecraft:iron_ingot",1))),1))));
        deniedBefore("future actual material",f->{f.install(List.of(need("industrialupgrade:late_ingot",1)));f.player.inventory.items[0]=stack("industrialupgrade:late_ingot",1);});
        deniedBefore("nondefault actual material",f->{f.player.inventory.items[1].components.put("custom",true);});
        deniedBefore("aliased nonempty inventory entries",f->f.player.inventory.items[1]=f.player.inventory.items[0]);
    }

    private static void mutationsAndPlacement() {
        deniedDuring("recipe generation after selection",f->f.afterSelection=()->f.target.recipes.replace(List.of(new RecipeHolder<>(RECIPE,f.recipe))));
        deniedDuring("owner team after selection",f->f.afterSelection=()->f.player.team="other");
        deniedDuring("input replacement after selection",f->f.afterSelection=()->f.player.inventory.items[0]=stack("minecraft:iron_ingot",1));
        deniedDuring("input components after selection",f->f.afterSelection=()->f.player.inventory.items[0].components.put("changed",true));
        deniedDuring("input count after selection",f->f.afterSelection=()->f.player.inventory.items[1].count=64);
        deniedDuring("player changes chunk",f->f.afterSelection=()->f.player.chunk=new net.minecraft.world.level.ChunkPos(1,0));
        deniedDuring("live target replacement",f->f.afterSelection=()->f.source.server.levels.put(ORBIT,new ServerLevel()));
        deniedDuring("input callback replacement",f->f.player.inventory.beforeRemove=i->f.player.inventory.items[i]=stack("minecraft:iron_ingot",64));
        deniedDuring("definition mutation",f->f.afterPayment=()->f.recipe.ingredients().set(0,need("minecraft:gold_ingot",64)));
        deniedDuring("template edit after payment",f->f.afterPayment=()->f.template.blocks.put(new BlockPos(2,0,0),new BlockState("minecraft:diamond_block")));
        deniedDuring("template replacement",f->f.afterPayment=()->f.target.structures.templates.put(STRUCTURE,new StructureTemplate()));
        deniedDuring("nondefault rotation",f->f.settings.rotation=Rotation.CLOCKWISE_90);
        deniedDuring("native placement false",f->f.placementResult=false);
        deniedDuring("zero primary writes",f->f.performWrites=false);
        deniedDuring("world rejects primary write",f->f.target.accepted=false);
        deniedDuring("world discards accepted state",f->f.target.retain=false);
        deniedDuring("partial primary rejection",f->f.target.beforeWrite=(p,s)->{if(f.target.writes>1)f.target.accepted=false;});
        deniedDuring("incoming state property substitution",f->f.incomingState=s->new BlockState(s.id(),"wrong-before-native-call"));
        deniedDuring("block removed during native shape updates",f->f.afterNativePlacement=()->f.target.blocks.remove(f.origin()));
        deniedDuring("accepted block removed before register",f->f.beforeRegistration=()->f.target.blocks.remove(f.origin()));
        deniedDuring("accepted block replaced before register",f->f.beforeRegistration=()->f.target.blocks.put(f.origin(),new BlockState("minecraft:dirt")));
        deniedDuring("team changes during write",f->f.target.beforeWrite=(p,s)->f.player.team="other");
        deniedDuring("recipe reload during write",f->f.target.beforeWrite=(p,s)->f.target.recipes.replace(List.of(new RecipeHolder<>(RECIPE,f.recipe))));
        deniedDuring("team changes before register",f->f.beforeRegistration=()->f.player.team="other");
        deniedDuring("reentrant wrapped consumer",f->f.afterSelection=()->StationConstructionAccess.wrap(f.packet,p->{throw new AssertionError("nested native call ran");}).accept(f.player));
    }

    private static void tagsAndExceptions() {
        var key=TagKey.<Item>create(null,ResourceLocation.parse("test:station_metal"));
        var iron=BuiltInRegistries.ITEM.wrapAsHolder(BuiltInRegistries.item("minecraft:iron_ingot"));
        var gold=BuiltInRegistries.ITEM.wrapAsHolder(BuiltInRegistries.item("minecraft:gold_ingot"));
        BuiltInRegistries.ITEM.bind(key,List.of(iron));
        var f=new Fixture();var ingredient=Ingredient.of(key);ingredient.getItems();
        f.install(List.of(new IngredientHolder(ingredient,64)));
        BuiltInRegistries.ITEM.bind(key,List.of(gold));f.run();
        check(f.registrations==0 && f.player.inventory.removals==0, "stale native Ingredient cache cannot prove current tag membership");
        BuiltInRegistries.ITEM.bind(key,List.of(iron));
        var changed=new Fixture();changed.install(List.of(new IngredientHolder(Ingredient.of(key),64)));
        changed.afterSelection=()->BuiltInRegistries.ITEM.bind(key,List.of(gold));changed.run();
        check(changed.registrations==0 && changed.teleports==0, "current tag mutation after plan cannot continue");

        var future=BuiltInRegistries.ITEM.wrapAsHolder(BuiltInRegistries.item("industrialupgrade:late_ingot"));
        BuiltInRegistries.ITEM.bind(key,List.of(iron,future));
        var alternatives=new Fixture();alternatives.install(List.of(new IngredientHolder(Ingredient.of(key),64)));
        alternatives.player.inventory.items[4]=stack("industrialupgrade:late_ingot",64);alternatives.run();
        check(alternatives.registrations==1&&alternatives.player.inventory.getItem(4).getCount()==64,
                "future tag alternatives neither unlock early payment nor strand an available early alternative");

        var ex=new Fixture();var expected=new IllegalStateException("native exception");
        boolean propagated=false;
        try{StationConstructionAccess.wrap(ex.packet,p->{throw expected;}).accept(ex.player);}
        catch(IllegalStateException actual){propagated=actual==expected;}
        check(propagated,"unrelated native exception is propagated unchanged");
        var next=new Fixture();next.run();check(next.registrations==1,"exception finally removes active scope");
    }

    private static void ingredientBounds() {
        var f=new Fixture();
        check(StationIngredients.read(null)==null&&StationIngredients.read(new Object())==null,
                "unknown or missing recipe object cannot supply an ingredient definition");
        for(int amount:new int[]{-1,0,4097,Integer.MAX_VALUE}) {
            f.install(List.of(need("minecraft:iron_ingot",amount)));
            check(StationIngredients.read(f.recipe)==null,"reject native count outside reviewed bounds: "+amount);
        }
        f.install(List.of());check(StationIngredients.read(f.recipe)==null,"empty ingredient list rejected");
        f.install(java.util.Collections.nCopies(65,need("minecraft:iron_ingot",1)));
        check(StationIngredients.read(f.recipe)==null,"more than64requirements rejected");
        f.install(java.util.Collections.nCopies(5,need("minecraft:iron_ingot",4096)));
        check(StationIngredients.read(f.recipe)==null,"aggregate requirement budget enforced");
        f.install(java.util.Collections.nCopies(4,need("minecraft:iron_ingot",4096)));
        check(StationIngredients.read(f.recipe)!=null,"exact aggregate16384definition supported");
        f.install(List.of(new IngredientHolder(null,1)));
        check(StationIngredients.read(f.recipe)==null,"null ingredient rejected");
        f.install(List.of(new IngredientHolder(new Ingredient(),1)));
        check(StationIngredients.read(f.recipe)==null,"empty vanilla values rejected");
        Ingredient.Value[] values=new Ingredient.Value[65];Arrays.fill(values,new Ingredient.ItemValue(stack("minecraft:iron_ingot",1)));
        f.install(List.of(new IngredientHolder(new Ingredient(values),1)));
        check(StationIngredients.read(f.recipe)==null,"more than64values rejected before native matching");
        f.install(List.of(new IngredientHolder(new Ingredient(Arrays.copyOf(values,64)),1)));
        check(StationIngredients.read(f.recipe)!=null,"exact64vanilla values supported");
        f.install(List.of(new IngredientHolder(new Ingredient(new Ingredient.ItemValue(ItemStack.EMPTY)),1)));
        check(StationIngredients.read(f.recipe)==null,"empty direct item value rejected");
        Ingredient.Value unknown=()->List.of(stack("minecraft:iron_ingot",1));
        f.install(List.of(new IngredientHolder(new Ingredient(unknown),1)));
        check(StationIngredients.read(f.recipe)==null,"unknown value implementation is not adopted");
    }

    private static void unscopedAndDuplicateCalls() {
        var plain=new Fixture();var position=new BlockPos(8,101,8);var state=new BlockState("minecraft:stone");
        StationConstructionAccess.beforePlacement(plain.template,plain.target,position,position,plain.settings,2);
        check(StationConstructionAccess.writePrimary(plain.target,position,state,2)
                && plain.target.getBlockState(position).equals(state),"ordinary unscoped structure write preserves native result");
        StationConstructionAccess.afterPlacement(plain.template,false);
        check(!StationConstructionAccess.hasScope(),"ordinary common hook does not manufacture a station scope");
        boolean denied=false;
        try{StationConstructionAccess.consume(plain.player,plain.target);}catch(RuntimeException expected){denied=true;}
        check(denied&&plain.player.inventory.removals==0,"unscoped consume cannot spend native inventory");

        var repeated=new Fixture();
        repeated.afterRegistration=()->{
            if(StationConstructionAccess.beforeRegister(repeated.player,repeated.target,NAME))repeated.registrations++;
        };
        repeated.run();
        check(repeated.registrations==1&&repeated.teleports==0,
                "repeated constructor cannot register twice or continue after invalidation; existing first registration is not rolled back");
        check(repeated.player.inventory.removals==2,"duplicate callback does not charge inputs twice");
        check(!StationConstructionAccess.hasScope(),"duplicate callback clears scope");

        var wrong=new Fixture();boolean[] entered={false};
        StationConstructionAccess.wrap(new Object(),p->entered[0]=true).accept(wrong.player);
        check(!entered[0]&&!StationConstructionAccess.hasScope(),"unknown packet class does not invoke native consumer");
        StationConstructionAccess.wrap(wrong.packet,null).accept(wrong.player);
        check(!StationConstructionAccess.hasScope(),"missing consumer does not create a scope");

        var duringRegister=new Fixture();
        duringRegister.duringRegistration=()->duringRegister.target.blocks.remove(duringRegister.origin());
        duringRegister.run();
        check(duringRegister.registrations==1&&duringRegister.teleports==0&&duringRegister.claims==0,
                "post-register removal blocks continuation without fabricating rollback of the native registration already performed");
        check(!StationConstructionAccess.hasScope(),"post-register invalidation clears scope");
    }

    public static void main(String[] args) {
        successfulPayment();initialDenials();mutationsAndPlacement();tagsAndExceptions();ingredientBounds();unscopedAndDuplicateCalls();
        System.out.println(assertions+" station actual-helper/allocator/real-policy modeled assertions PASS; no optional Mixin or full-client claim");
    }
}
