"""Actual read-only witness with modeled API receivers; no Ad Astra binary/client claim."""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]

SOURCES = {
    'net/minecraft/core/RegistryAccess.java': '''package net.minecraft.core;
public class RegistryAccess { public static final RegistryAccess EMPTY = new RegistryAccess(); }''',
    'net/minecraft/network/chat/Component.java': '''package net.minecraft.network.chat;
import net.minecraft.core.RegistryAccess;
public class Component {
 public String text; public Component child; public boolean malformed;
 public Component(String text){this.text=text;}
 public Component copy(){Component c=new Component(text);c.child=child;c.malformed=malformed;return c;}
 public static class Serializer {
  public static String toJson(Component c, RegistryAccess registry){
   if(c.malformed)throw new IllegalArgumentException("malformed component");
   return "["+c.text+(c.child==null?"":toJson(c.child,registry))+"]";
  }
 }
}''',
    'net/minecraft/world/level/ChunkPos.java': '''package net.minecraft.world.level;
public final class ChunkPos { public final int x,z;
 public ChunkPos(int x,int z){this.x=x;this.z=z;}
 public boolean equals(Object o){return o instanceof ChunkPos p&&p.x==x&&p.z==z;}
 public int hashCode(){return 31*x+z;}
}''',
    'net/minecraft/server/MinecraftServer.java': '''package net.minecraft.server;
public class MinecraftServer { public boolean sameThread=true; public boolean isSameThread(){return sameThread;} }''',
    'net/minecraft/server/level/ServerLevel.java': '''package net.minecraft.server.level;
import net.minecraft.server.MinecraftServer;
public class ServerLevel { private final MinecraftServer server=new MinecraftServer();
 public MinecraftServer getServer(){return server;}
}''',
    'net/minecraft/server/level/ServerPlayer.java': '''package net.minecraft.server.level;
import java.util.UUID;
public class ServerPlayer { public final UUID uuid=UUID.randomUUID(); public UUID getUUID(){return uuid;} }''',
    'earth/terrarium/adastra/common/handlers/base/SpaceStation.java': '''package earth.terrarium.adastra.common.handlers.base;
import net.minecraft.world.level.ChunkPos;import net.minecraft.network.chat.Component;
public record SpaceStation(ChunkPos position, Component name) {}''',
    'earth/terrarium/adastra/common/handlers/SpaceStationHandler.java': '''package earth.terrarium.adastra.common.handlers;
import java.util.*;import net.minecraft.server.level.*;import earth.terrarium.adastra.common.handlers.base.SpaceStation;
public class SpaceStationHandler {
 public static Set<SpaceStation> stations=new HashSet<>(); public static int calls;
 public static boolean fail;
 public static Set<SpaceStation> getOwnedSpaceStations(ServerPlayer player,ServerLevel level){
  calls++;if(fail)throw new IllegalStateException("native failure");return stations;
 }
 public static Set<SpaceStation> getOwnedSpaceStations(UUID id,ServerLevel level){throw new AssertionError("UUID overload chosen");}
}''',
    'ua/aia2/guard/StationRegistrationHarness.java': '''package ua.aia2.guard;
import java.util.*;import net.minecraft.server.level.*;import net.minecraft.network.chat.Component;
import net.minecraft.world.level.ChunkPos;import earth.terrarium.adastra.common.handlers.*;
import earth.terrarium.adastra.common.handlers.base.SpaceStation;
public class StationRegistrationHarness {
 static int checks; static void check(boolean ok,String reason){checks++;if(!ok)throw new AssertionError(reason);}
 static Component c(String text){return new Component(text);}
 static SpaceStation s(int x,String text){return new SpaceStation(new ChunkPos(x,x+1),c(text));}
 public static void main(String[] args){
  ServerPlayer player=new ServerPlayer();ServerLevel world=new ServerLevel();ChunkPos pos=new ChunkPos(2,3);
  Component name=c("new");
  var empty=StationRegistrationWitness.read(player,world);
  check(empty!=null,"empty live native owner map is valid");
  check(!empty.hasStation(pos,name),"no fabricated station");
  check(!StationRegistrationWitness.added(empty,empty,pos,name),"native no-op denied");
  SpaceStationHandler.stations.add(new SpaceStation(pos,name));
  var after=StationRegistrationWitness.read(player,world);
  check(StationRegistrationWitness.added(empty,after,pos,name),"exact one native addition");
  check(after.hasStation(new ChunkPos(2,3),c("new")),"frozen payload matching");
  check(!empty.hasStation(pos,name),"before snapshot independent of live Set");
  check(!StationRegistrationWitness.added(after,after,pos,name),"old station never adopted");
  check(!StationRegistrationWitness.added(empty,after,new ChunkPos(3,3),name),"wrong location denied");
  check(!StationRegistrationWitness.added(empty,after,pos,c("wrong")),"wrong name denied");
  var otherOwner=StationRegistrationWitness.read(new ServerPlayer(),world);
  check(!StationRegistrationWitness.added(empty,otherOwner,pos,name),"different owner denied");
  var otherWorld=StationRegistrationWitness.read(player,new ServerLevel());
  check(!StationRegistrationWitness.added(empty,otherWorld,pos,name),"different world identity denied");
  SpaceStationHandler.stations.add(s(8,"another"));
  check(!StationRegistrationWitness.added(empty,StationRegistrationWitness.read(player,world),pos,name),"multiple additions denied");
  var beforeRemoval=StationRegistrationWitness.read(player,world);
  SpaceStationHandler.stations.removeIf(station->station.position().x==8);
  SpaceStationHandler.stations.add(s(9,"replacement"));SpaceStationHandler.stations.add(s(10,"third"));
  check(!StationRegistrationWitness.added(beforeRemoval,StationRegistrationWitness.read(player,world),new ChunkPos(10,11),c("third")),"net +1 cannot hide old removal");
  SpaceStationHandler.stations.clear();Component mutable=c("parent");mutable.child=c("child");
  SpaceStationHandler.stations.add(new SpaceStation(new ChunkPos(4,5),mutable));
  var beforeMutation=StationRegistrationWitness.read(player,world);
  mutable.child.text="mutated";SpaceStationHandler.stations.add(new SpaceStation(pos,name));
  check(!StationRegistrationWitness.added(beforeMutation,StationRegistrationWitness.read(player,world),pos,name),"nested Component mutation invalidates old payload");
  Component original=c("parent");original.child=c("child");
  check(beforeMutation.hasStation(new ChunkPos(4,5),original),"nested name frozen rather than shallow copied");
  check(!beforeMutation.hasStation(new ChunkPos(4,5),mutable),"no retained nested alias");
  SpaceStationHandler.stations.clear();
  SpaceStationHandler.stations.add(new SpaceStation(pos,c("same")));SpaceStationHandler.stations.add(new SpaceStation(pos,c("same")));
  check(StationRegistrationWitness.read(player,world)==null,"duplicate frozen native payload rejected");
  SpaceStationHandler.stations.clear();SpaceStationHandler.stations.add(null);
  check(StationRegistrationWitness.read(player,world)==null,"null entry rejected");
  SpaceStationHandler.stations.clear();SpaceStationHandler.stations.add(new SpaceStation(pos,null));
  check(StationRegistrationWitness.read(player,world)==null,"null component rejected");
  Component malformed=c("broken");malformed.malformed=true;
  SpaceStationHandler.stations.clear();SpaceStationHandler.stations.add(new SpaceStation(pos,malformed));
  check(StationRegistrationWitness.read(player,world)==null,"serializer failure closed");
  check(!empty.hasStation(pos,malformed),"query serializer failure closed");
  check(!StationRegistrationWitness.added(empty,after,pos,malformed),"comparison serializer failure closed");
  SpaceStationHandler.stations.clear();SpaceStationHandler.fail=true;
  check(StationRegistrationWitness.read(player,world)==null,"native failure closed");SpaceStationHandler.fail=false;
  world.getServer().sameThread=false;
  check(StationRegistrationWitness.read(player,world)==null,"off-thread read closed");world.getServer().sameThread=true;
  check(StationRegistrationWitness.read(null,world)==null,"null player closed");
  check(StationRegistrationWitness.read(player,null)==null,"null world closed");
  check(!StationRegistrationWitness.added(null,after,pos,name),"null before closed");
  check(!StationRegistrationWitness.added(empty,null,pos,name),"null after closed");
  SpaceStationHandler.stations.add(new SpaceStation(pos,c("x".repeat(16384))));
  check(StationRegistrationWitness.read(player,world)==null,"oversized name rejected");
  SpaceStationHandler.stations.clear();
  for(int i=0;i<4096;i++)SpaceStationHandler.stations.add(s(i,"bounded"));
  check(StationRegistrationWitness.read(player,world)!=null,"4096 entry boundary accepted");
  SpaceStationHandler.stations.add(s(4097,"overflow"));
  check(StationRegistrationWitness.read(player,world)==null,"4097 entries rejected");
  SpaceStationHandler.stations.clear();
  for(int i=0;i<80;i++)SpaceStationHandler.stations.add(s(i,"x".repeat(14000)));
  check(StationRegistrationWitness.read(player,world)==null,"aggregate name bound rejected");
  check(SpaceStationHandler.calls>0,"exact ServerPlayer overload exercised");
  System.out.println(checks+" station native-registration witness modeled assertions PASS");
 }
}''',
}


class StationRegistrationTests(unittest.TestCase):
    def test_actual_bounded_witness_and_native_delta_under_modeled_receivers(self):
        jdk = Path(os.environ.get('JAVA_HOME', '/workspace/aia2-toolchains/jdk-21.0.9'))
        if not (jdk / 'bin/javac').is_file():
            self.skipTest('JDK21 unavailable')
        with tempfile.TemporaryDirectory(prefix='aia2-station-registration-v9-') as temporary:
            directory = Path(temporary)
            files = []
            for relative, source in SOURCES.items():
                path = directory / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(source)
                files.append(str(path))
            files.append(str(ROOT / 'companion/src/main/java/ua/aia2/guard/StationRegistrationWitness.java'))
            compiled = subprocess.run([str(jdk / 'bin/javac'), '--release', '21', '-encoding', 'UTF-8',
                                       '-d', str(directory), *files], capture_output=True, text=True)
            self.assertEqual(compiled.returncode, 0, compiled.stdout + compiled.stderr)
            tested = subprocess.run([str(jdk / 'bin/java'), '-cp', str(directory),
                                     'ua.aia2.guard.StationRegistrationHarness'], capture_output=True, text=True)
            self.assertEqual(tested.returncode, 0, tested.stdout + tested.stderr)
            self.assertRegex(tested.stdout, r'\d+ station native-registration witness modeled assertions PASS')
            print(tested.stdout.strip())
