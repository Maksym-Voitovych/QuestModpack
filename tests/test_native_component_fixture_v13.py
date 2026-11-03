"""Actual debug fixture registration gates on a modeled host, not MC codecs.

The production class is compiled unchanged (and once with a deliberate missing
nativeSmoke guard). Files/temporary working directories are real. Registry and
annotation APIs below are bounded host models; Minecraft is not launched.
"""
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
PRODUCTION = ROOT/'companion/src/main/java/ua/aia2/guard/NativeComponentFixtures.java'

SOURCES = {
    'ua/aia2/guard/Aia2MachineGuard.java': '''package ua.aia2.guard;
public final class Aia2MachineGuard { public static final String MOD_ID="aia2_machine_guard"; }
''',
    'net/minecraft/SharedConstants.java': '''package net.minecraft;
public final class SharedConstants { public static boolean IS_RUNNING_IN_IDE; }
''',
    'net/minecraft/resources/ResourceLocation.java': '''package net.minecraft.resources;
public record ResourceLocation(String namespace,String path) {
 public static final Object CODEC=new Object(), STREAM_CODEC=new Object();
 public static ResourceLocation fromNamespaceAndPath(String namespace,String path) {return new ResourceLocation(namespace,path);}
 @Override public String toString(){return namespace+":"+path;}
}
''',
    'net/minecraft/core/registries/Registries.java': '''package net.minecraft.core.registries;
public final class Registries {public static final String DATA_COMPONENT_TYPE="minecraft:data_component_type";}
''',
    'net/minecraft/core/component/DataComponentType.java': '''package net.minecraft.core.component;
public final class DataComponentType<T> {
 public static int builds;
 public final Object persistentCodec,networkCodec;
 private DataComponentType(Object persistent,Object network){persistentCodec=persistent;networkCodec=network;}
 public static <T> Builder<T> builder(){return new Builder<>();}
 public static final class Builder<T>{
  private Object persistent,network;
  public Builder<T> persistent(Object codec){persistent=codec;return this;}
  public Builder<T> networkSynchronized(Object codec){network=codec;return this;}
  public DataComponentType<T> build(){builds++;return new DataComponentType<>(persistent,network);}
 }
}
''',
    'net/neoforged/bus/api/SubscribeEvent.java': '''package net.neoforged.bus.api;
import java.lang.annotation.*;
@Retention(RetentionPolicy.RUNTIME) @Target(ElementType.METHOD) public @interface SubscribeEvent {}
''',
    'net/neoforged/fml/common/EventBusSubscriber.java': '''package net.neoforged.fml.common;
import java.lang.annotation.*;
@Retention(RetentionPolicy.RUNTIME) @Target(ElementType.TYPE) public @interface EventBusSubscriber {
 String modid(); Bus bus(); enum Bus {MOD}
}
''',
    'net/neoforged/neoforge/registries/RegisterEvent.java': '''package net.neoforged.neoforge.registries;
import java.util.function.Supplier;import net.minecraft.resources.ResourceLocation;
public final class RegisterEvent {
 private final String key;
 public int calls;public String registeredRegistry;public ResourceLocation registeredId;public Object registeredValue;
 public RegisterEvent(String key){this.key=key;}
 public String getRegistryKey(){return key;}
 public <T> void register(String registry,ResourceLocation id,Supplier<T> supplier){
  calls++;registeredRegistry=registry;registeredId=id;registeredValue=supplier.get();
 }
}
''',
    'ua/aia2/guard/NativeComponentFixtureHarness.java': '''package ua.aia2.guard;
import java.nio.file.Files;import java.nio.file.Path;
import net.minecraft.SharedConstants;import net.minecraft.core.component.DataComponentType;
import net.minecraft.core.registries.Registries;import net.minecraft.resources.ResourceLocation;
import net.neoforged.neoforge.registries.RegisterEvent;
public final class NativeComponentFixtureHarness {
 private static int assertions,cases;
 private static final Path MARKER=Path.of(".aia2-native-smoke-allow");
 private static void check(boolean condition,String message){assertions++;if(!condition)throw new AssertionError(message);}
 private static void reset()throws Exception{
  var profile=NativeComponentFixtures.class.getDeclaredField("profile");profile.setAccessible(true);profile.set(null,null);
  DataComponentType.builds=0;
  Files.deleteIfExists(MARKER);
 }
 private static void expectUnregistered(){
  boolean threw=false;
  try{NativeComponentFixtures.profile();}catch(IllegalStateException expected){threw=true;}
  check(threw,"closed registration must leave fixture inaccessible");
 }
 private static void run(boolean flag,boolean ide,boolean marker,boolean correctRegistry,boolean directory)throws Exception{
  reset();cases++;
  System.setProperty("aia2.guard.nativeSmoke",String.valueOf(flag));SharedConstants.IS_RUNNING_IN_IDE=ide;
  if(marker){if(directory)Files.createDirectory(MARKER);else Files.writeString(MARKER,"owned fixture test\\n");}
  RegisterEvent event=new RegisterEvent(correctRegistry?Registries.DATA_COMPONENT_TYPE:"minecraft:item");
  NativeComponentFixtures.register(event);
  boolean expected=flag&&ide&&marker&&!directory&&correctRegistry;
  check(event.calls==(expected?1:0),"normal-play combination must not register: flag="+flag+",ide="+ide+",marker="+marker+",componentRegistry="+correctRegistry+",directory="+directory);
  check(DataComponentType.builds==(expected?1:0),"closed gates must not build a component");
  if(expected){
   check(Registries.DATA_COMPONENT_TYPE.equals(event.registeredRegistry),"only data-component registry target");
   check(event.registeredId.equals(ResourceLocation.fromNamespaceAndPath("aia2_machine_guard","native_mold_profile")),"fixture stays in owned test namespace, never CDG");
   var type=NativeComponentFixtures.profile();
   check(event.registeredValue==type,"public fixture accessor returns registered identity");
   check(type.persistentCodec==ResourceLocation.CODEC,"persistent codec remains ResourceLocation");
   check(type.networkCodec==ResourceLocation.STREAM_CODEC,"network codec remains ResourceLocation");
  }else{expectUnregistered();check(event.registeredValue==null,"closed gates never evaluate registration supplier");}
 }
 public static void main(String[] args)throws Exception{
  // Every flag/IDE/regular-marker combination is tested on each registry key.
  for(boolean flag:new boolean[]{false,true})for(boolean ide:new boolean[]{false,true})for(boolean marker:new boolean[]{false,true}){
   run(flag,ide,marker,true,false);
   run(flag,ide,marker,false,false);
  }
  // A directory at the exact marker path does not authorize a development fixture.
  run(true,true,true,true,true);run(true,true,true,false,true);
  // Default JVM state is closed even in an IDE with a regular marker present.
  reset();cases++;SharedConstants.IS_RUNNING_IN_IDE=true;System.clearProperty("aia2.guard.nativeSmoke");Files.writeString(MARKER,"owned");
  var absentFlag=new RegisterEvent(Registries.DATA_COMPONENT_TYPE);NativeComponentFixtures.register(absentFlag);
  check(absentFlag.calls==0,"absent flag cannot register a fixture");expectUnregistered();
  reset();System.clearProperty("aia2.guard.nativeSmoke");
  System.out.println(assertions+" actual debug-fixture gate assertions PASS across "+cases+" modeled-host cases; real marker files, no Minecraft codec claim");
 }
}
''',
}


class NativeComponentFixtureTests(unittest.TestCase):
    def run_class(self, remove_native_smoke_guard=False):
        candidate = Path(os.environ.get('JAVA_HOME', '/workspace/aia2-toolchains/jdk-21.0.9'))/'bin/javac'
        if not candidate.is_file():
            fallback = shutil.which('javac')
            if fallback is None:
                self.skipTest('JDK unavailable for actual debug-fixture host')
            candidate = Path(fallback)
        java = candidate.with_name('java')
        with tempfile.TemporaryDirectory(prefix='aia2-native-component-fixture-v13-') as temporary:
            directory=Path(temporary); files=[]
            for relative,source in SOURCES.items():
                path=directory/'src'/relative;path.parent.mkdir(parents=True,exist_ok=True);path.write_text(source);files.append(str(path))
            source=PRODUCTION.read_text()
            if remove_native_smoke_guard:
                guard='!Boolean.getBoolean("aia2.guard.nativeSmoke") || '
                self.assertEqual(source.count(guard),1,'Negative control must remove precisely one real gate')
                source=source.replace(guard,'')
            production=directory/'src/ua/aia2/guard/NativeComponentFixtures.java'
            production.write_text(source);files.append(str(production))
            compiled=subprocess.run([str(candidate),'--release','21','-encoding','UTF-8','-d',str(directory/'classes'),*files],capture_output=True,text=True)
            self.assertEqual(compiled.returncode,0,compiled.stdout+compiled.stderr)
            run=directory/'run';run.mkdir()
            return subprocess.run([str(java),'-cp',str(directory/'classes'),'ua.aia2.guard.NativeComponentFixtureHarness'],cwd=run,capture_output=True,text=True)

    def test_actual_registration_requires_all_three_opt_ins_and_correct_registry(self):
        result=self.run_class()
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)
        self.assertRegex(result.stdout,r'\d+ actual debug-fixture gate assertions PASS across 19 modeled-host cases')
        print(result.stdout.strip())

    def test_missing_native_smoke_guard_fails_behavioral_negative_control(self):
        result=self.run_class(remove_native_smoke_guard=True)
        self.assertNotEqual(result.returncode,0,'Missing opt-in gate must be caught')
        self.assertIn('normal-play combination must not register: flag=false,ide=true,marker=true,componentRegistry=true,directory=false',result.stderr)


if __name__ == '__main__':
    unittest.main()
