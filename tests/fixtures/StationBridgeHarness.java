package ua.aia2.guard;

import com.google.gson.JsonArray;
import com.google.gson.JsonObject;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import java.util.Set;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.resources.ResourceKey;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.item.crafting.Recipe;
import net.minecraft.world.item.crafting.RecipeHolder;
import net.minecraft.world.item.crafting.RecipeInput;
import net.minecraft.world.item.crafting.RecipeSerializer;
import net.minecraft.world.level.Level;
import earth.terrarium.adastra.common.recipes.SpaceStationRecipe;

/** Real station bridge + real policy; Minecraft storage and packet permit modeled. */
public final class StationBridgeHarness {
    private static int checks, fixtures;
    private static Path directory;
    private static final String[] PLANETS = {"earth", "moon", "mars", "mercury", "venus", "glacio"};
    private static final String DATA = "aia2_stations_v1";
    private static void check(boolean value,String message){checks++;if(!value)throw new AssertionError(message);}
    private static void throwsRuntime(Runnable action,String message){boolean thrown=false;try{action.run();}catch(RuntimeException expected){thrown=true;}check(thrown,message);}
    private static ResourceKey<Level> key(String id){return ResourceKey.create(null,ResourceLocation.parse(id));}
    private static JsonArray rules(){
        JsonArray result=new JsonArray();
        for(String p:PLANETS){JsonObject r=new JsonObject();r.addProperty("id","station_"+p+"_orbit");
            r.addProperty("epoch",Set.of("earth","moon","mars").contains(p)?37:38);
            r.addProperty("dimension","ad_astra:"+p+"_orbit");
            r.addProperty("recipeId","ad_astra:space_station/"+p+"_orbit_space_station");
            r.addProperty("serializer","ad_astra:space_station_recipe");r.addProperty("advancement","aia2:stations/"+p+"_orbit");result.add(r);}
        return result;
    }
    private static final class Fixture {
        final MinecraftServer server=new MinecraftServer();
        final ServerLevel main=new ServerLevel(), orbit=new ServerLevel();
        final ServerPlayer player=new ServerPlayer();
        Recipe<?> recipe;
        final String planet;
        Fixture(String planet)throws Exception{
            this.planet=planet;StationProductionBridge.clearRuntime();Aia2MachineGuard.configure();
            StationConstructionAccess.committing=false;
            server.root=directory.resolve("fixture-"+(fixtures++));server.main=main;main.server=server;orbit.server=server;
            orbit.key=key("ad_astra:"+planet+"_orbit");player.world=orbit;
            install(new SpaceStationRecipe(List.of(),orbit.dimension(),ResourceLocation.parse("ad_astra:space_station")),
                    "ad_astra:space_station/"+planet+"_orbit_space_station");
            StationProductionBridge.configureJson(rules().toString());
        }
        void install(Recipe<?> candidate,String id){recipe=candidate;orbit.recipes.replace(List.of(new RecipeHolder<>(ResourceLocation.parse(id),candidate)));}
        boolean ready(){return StationProductionBridge.readyFor(orbit,"team",recipe);}
        void commit(String team){StationConstructionAccess.player=player;StationConstructionAccess.level=orbit;
            StationConstructionAccess.recipe=recipe;StationConstructionAccess.team=team;StationConstructionAccess.committing=true;
            try{StationProductionBridge.finishedStation(player,orbit,recipe,team);}finally{StationConstructionAccess.committing=false;}}
        boolean proof(String team){return StationProductionBridge.hasProof(server,team,"station_"+planet+"_orbit");}
    }
    private static void config()throws Exception{
        var f=new Fixture("earth");check(StationProductionBridge.isConfigured(),"six curated rules configure");
        for(String invalid:List.of("{}","[]","null","[1]","not json")){
            StationProductionBridge.configureJson(rules().toString());
            throwsRuntime(()->StationProductionBridge.configureJson(invalid),"invalid config rejected: "+invalid);
            check(!StationProductionBridge.isConfigured()&&!f.ready(),"invalid config closes previous rule map");}
        for(String property:List.of("id","epoch","dimension","recipeId","serializer","advancement")){
            StationProductionBridge.configureJson(rules().toString());var bad=rules();
            if(property.equals("epoch"))bad.get(0).getAsJsonObject().addProperty(property,37.5);
            else bad.get(0).getAsJsonObject().addProperty(property,"invalid:value");
            throwsRuntime(()->StationProductionBridge.configureJson(bad.toString()),"mismatched exact field rejected: "+property);
            check(!StationProductionBridge.isConfigured(),"bad field clears prior map: "+property);
            var missing=rules();missing.get(0).getAsJsonObject().remove(property);
            throwsRuntime(()->StationProductionBridge.configureJson(missing.toString()),"missing exact field rejected: "+property);
        }
        var duplicate=rules();duplicate.set(1,duplicate.get(0).deepCopy());
        throwsRuntime(()->StationProductionBridge.configureJson(duplicate.toString()),"duplicate planet rejected");
        var tooMany=rules();tooMany.add(tooMany.get(0).deepCopy());
        throwsRuntime(()->StationProductionBridge.configureJson(tooMany.toString()),"seventh rule rejected");
        var fewer=rules();fewer.remove(5);throwsRuntime(()->StationProductionBridge.configureJson(fewer.toString()),"five rules rejected");
        for(int i=0;i<PLANETS.length;i++){
            var stage=rules();stage.get(i).getAsJsonObject().addProperty("epoch",i<3?38:37);
            throwsRuntime(()->StationProductionBridge.configureJson(stage.toString()),"wrong reviewed stage rejected: "+PLANETS[i]);}
        check(f.main.storage.writes==0,"config and validation never write proof storage");
    }
    private static void policy()throws Exception{
        for(String p:PLANETS){
            var f=new Fixture(p);boolean early=Set.of("earth","moon","mars").contains(p);
            check(f.ready()==early,"exact station stage floor: "+p);
            Aia2MachineGuard.POLICY.setTeamProgress("team",37);check(f.ready(),"epoch38 opens late orbit: "+p);
            check(!StationProductionBridge.readyFor(f.orbit,"",f.recipe),"blank team rejected");
            check(!StationProductionBridge.readyFor(f.orbit,"x".repeat(129),f.recipe),"overlong team rejected");
            check(!StationProductionBridge.readyFor(f.orbit,"missing",f.recipe),"unknown team rejected");
            check(f.main.storage.writes==0,"readiness leaves empty journal uninstalled");
        }
        var f=new Fixture("earth");Recipe<?> original=f.recipe;
        var equal=new SpaceStationRecipe(List.of(),f.orbit.dimension(),ResourceLocation.parse("ad_astra:space_station"));
        check(!StationProductionBridge.readyFor(f.orbit,"team",equal),"equal but non-current recipe instance rejected");
        f.install(original,"ad_astra:station_not_reviewed");check(!f.ready(),"unreviewed recipe ID rejected");
        f.install(new Recipe<RecipeInput>(){public boolean matches(RecipeInput i,Level l){return true;}public RecipeSerializer<?> getSerializer(){return new RecipeSerializer<>("minecraft:crafting_shaped");}},
                "ad_astra:space_station/earth_orbit_space_station");check(!f.ready(),"wrong serializer under reviewed ID rejected");
        f.install(original,"ad_astra:space_station/earth_orbit_space_station");
        f.orbit.key=key("ad_astra:unknown_orbit");check(!f.ready(),"unreviewed destination rejected");
        f.orbit.key=key("ad_astra:earth_orbit");f.server.sameThread=false;
        throwsRuntime(f::ready,"off-thread readiness closed");
        f.server.sameThread=true;f.server.main=null;throwsRuntime(f::ready,"missing overworld closed");
    }
    private static void receipts()throws Exception{
        var f=new Fixture("earth");
        check(!f.proof("team")&&f.main.storage.writes==0,"lookup never adopts a native old station or creates a journal");
        StationProductionBridge.finishedStation(f.player,f.orbit,f.recipe,"team");check(!f.proof("team"),"unscoped bridge cannot record");
        f.commit("team");check(f.proof("team")&&!f.proof("other"),"valid scoped proof belongs only to its team");
        check(f.main.storage.writes==1&&f.main.storage.data.get(DATA).dirty,"first proof installs and dirties journal once");
        f.commit("team");check(f.main.storage.writes==1,"duplicate successful operation keeps historical proof idempotent");
        StationProductionBridge.clearRuntime();check(f.proof("team"),"clearing runtime does not erase historical proof");
        check(!StationProductionBridge.isConfigured()&&!f.ready(),"cleared rules close new construction despite historical proof");
        StationProductionBridge.configureJson(rules().toString());check(f.ready()&&f.proof("team"),"valid reload restores admission and preserves proof");
        var saved=f.main.storage.data.get(DATA).save(new CompoundTag(),null);f.main.storage.data.clear();f.main.storage.raw.put(DATA,saved);
        StationProductionBridge.clearRuntime();check(f.proof("team"),"strict reload restores durable team receipt from saved modeled NBT");
        check(!f.proof("other"),"historical proof is not transferred to a different team");
        throwsRuntime(()->StationProductionBridge.hasProof(f.server,"team","bad:id"),"invalid proof ID rejected");
        throwsRuntime(()->StationProductionBridge.hasProof(f.server,"team",null),"null proof ID rejected");
        check(!StationProductionBridge.hasProof(null,"team","station_earth_orbit"),"null server has no proof");
        check(!StationProductionBridge.hasProof(f.server,"","station_earth_orbit"),"blank team has no proof");
        var denied=new Fixture("earth");Aia2MachineGuard.POLICY.setTeamProgress("team",35);denied.commit("team");
        check(!denied.proof("team")&&denied.main.storage.writes==0,"late stage revocation prevents record even with modeled scoped permit");
        var wrong=new Fixture("earth");StationConstructionAccess.player=wrong.player;StationConstructionAccess.level=wrong.orbit;
        StationConstructionAccess.recipe=wrong.recipe;StationConstructionAccess.team="other";StationConstructionAccess.committing=true;
        StationProductionBridge.finishedStation(wrong.player,wrong.orbit,wrong.recipe,"team");StationConstructionAccess.committing=false;
        check(!wrong.proof("team"),"wrong team tuple cannot borrow modeled permit");
    }
    private static CompoundTag validTag(){var t=new CompoundTag();t.putInt("schema",1);t.put("teams",new CompoundTag());return t;}
    private static void invalid(CompoundTag tag,String reason){var loaded=StationProductionBridge.ReceiptData.load(tag,null);
        check(loaded.blocked,"invalid journal fails closed: "+reason);check(!loaded.dirty,"blocked load is not dirtied: "+reason);
        throwsRuntime(()->loaded.save(new CompoundTag(),null),"blocked journal refuses overwrite: "+reason);}
    private static void loader()throws Exception{
        var empty=StationProductionBridge.ReceiptData.load(validTag(),null);check(!empty.blocked&&empty.proofs.isEmpty(),"valid empty schema loads");
        invalid(new CompoundTag(),"missing schema");var wrongSchema=validTag();wrongSchema.putInt("schema",2);invalid(wrongSchema,"unsupported schema");
        var schemaType=validTag();schemaType.putByte("schema",(byte)1);invalid(schemaType,"byte schema is not int");
        var noTeams=validTag();noTeams.remove("teams");invalid(noTeams,"missing teams");
        var teamsType=validTag();teamsType.putInt("teams",0);invalid(teamsType,"wrong teams type");
        for(String name:List.of("", " ","x".repeat(129))){var t=validTag();t.getCompound("teams").put(name,new CompoundTag());invalid(t,"invalid team name length");}
        var teamType=validTag();teamType.getCompound("teams").putString("team","wrong");invalid(teamType,"wrong team entry type");
        for(String id:List.of("bad:id","BAD","x".repeat(65),"")){
            var t=validTag();var saved=new CompoundTag();saved.putBoolean(id,true);t.getCompound("teams").put("team",saved);invalid(t,"invalid proof identifier");}
        for(int value:new int[]{0,2,-1}){var t=validTag();var s=new CompoundTag();s.putByte("station_earth_orbit",(byte)value);t.getCompound("teams").put("team",s);invalid(t,"proof byte must be exactly1");}
        var proofType=validTag();var ints=new CompoundTag();ints.putInt("station_earth_orbit",1);proofType.getCompound("teams").put("team",ints);invalid(proofType,"int proof not byte");
        var lots=validTag();var entries=new CompoundTag();for(int i=0;i<65;i++)entries.putBoolean("proof_"+i,true);lots.getCompound("teams").put("team",entries);invalid(lots,"proof cap64");
        var teams=validTag();for(int i=0;i<16385;i++)teams.getCompound("teams").put("t"+i,new CompoundTag());invalid(teams,"team cap16384");
        var known=validTag();var history=new CompoundTag();history.putBoolean("historical_rule_not_in_current_config",true);known.getCompound("teams").put("team",history);
        var kept=StationProductionBridge.ReceiptData.load(known,null);check(!kept.blocked&&kept.proofs.get("team").contains("historical_rule_not_in_current_config"),"valid historical IDs preserved independently of current rules");
        var roundtrip=kept.save(new CompoundTag(),null);check(StationProductionBridge.ReceiptData.load(roundtrip,null).proofs.equals(kept.proofs),"modeled NBT save/load is lossless");
    }
    private static void corrupt()throws Exception{
        var f=new Fixture("earth");Path file=f.server.root.resolve("data").resolve(DATA+".dat");Files.createDirectories(file.getParent());byte[] original={1,3,3,7};Files.write(file,original);
        check(!f.ready()&&f.main.storage.writes==0,"existing unreadable file closes construction before payment without replacement");
        throwsRuntime(()->f.proof("team"),"unreadable journal makes projection fail closed");f.commit("team");
        check(java.util.Arrays.equals(Files.readAllBytes(file),original)&&f.main.storage.writes==0,"unreadable journal and opaque original bytes remain untouched");
        var malformed=new Fixture("earth");malformed.main.storage.raw.put(DATA,new CompoundTag());
        check(!malformed.ready()&&malformed.main.storage.writes==0,"loader-detected corrupt journal closes construction");
        throwsRuntime(()->malformed.proof("team"),"loader-detected corrupt journal closes projection");
        var fullProofs=new Fixture("earth");var fullTag=validTag();var fullSet=new CompoundTag();
        for(int i=0;i<64;i++)fullSet.putBoolean("historical_"+i,true);fullTag.getCompound("teams").put("team",fullSet);
        fullProofs.main.storage.raw.put(DATA,fullTag);
        check(!fullProofs.ready(),"new proof at exact64historical-proof cap is denied before creating unreadable65-entry ledger");
        fullSet.remove("historical_0");fullSet.putBoolean("station_earth_orbit",true);
        fullProofs.main.storage.data.clear();fullProofs.main.storage.raw.put(DATA,fullTag);StationProductionBridge.clearRuntime();StationProductionBridge.configureJson(rules().toString());
        check(fullProofs.ready()&&fullProofs.proof("team"),"existing historical proof remains eligible and idempotent at exact64-entry cap");
        fullProofs.commit("team");check(fullProofs.main.storage.writes==0,"idempotent proof at storagecap does not rewrite ledger");

        var capped=new Fixture("earth");var tag=validTag();for(int i=0;i<16384;i++)tag.getCompound("teams").put("t"+i,new CompoundTag());capped.main.storage.raw.put(DATA,tag);
        check(!capped.ready(),"new team denied at exact team storage cap");
        tag.getCompound("teams").remove("t0");tag.getCompound("teams").put("team",new CompoundTag());
        capped.main.storage.data.clear();capped.main.storage.raw.put(DATA,tag);StationProductionBridge.clearRuntime();StationProductionBridge.configureJson(rules().toString());
        check(capped.ready(),"existing team remains eligible at exact cap");
    }
    public static void main(String[] args)throws Exception{
        directory=Path.of(args[0]);config();policy();receipts();loader();corrupt();
        System.out.println(checks+" station actual-bridge/real-policy modeled assertions PASS; packet scope and NBT codecs modeled");
    }
}
