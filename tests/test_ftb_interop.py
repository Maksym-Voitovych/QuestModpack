"""Real Rhino regression for KubeJS UUID converters versus FTB QuestFile overloads.

Compiles the actual production FtbQuestBridge and pinned, unmodified public FTB
interface/KubeJS UUID converter. Minecraft entities, FTB TeamData storage and
error-reporting support are explicit fixtures. Full mod dispatch is not tested.
"""
import hashlib
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
TOOLS = Path('/workspace/aia2-toolchains')
SOURCES = Path('/workspace/aia2-dev-sources')


class FtbInteropTest(unittest.TestCase):
    def test_actual_rhino_ftb_team_overloads_and_production_bridge(self):
        jar = Path(os.environ.get('AIA2_RHINO_JAR', str(TOOLS/'rhino-2101.2.7-build.85-core-from-source.jar')))
        jdk = Path(os.environ.get('JAVA_HOME', str(TOOLS/'jdk-21.0.9')))
        ftb = Path(os.environ.get('AIA2_FTB_QUESTS_SOURCE', str(SOURCES/'FTB-Quests-1.21.1')))
        kube = Path(os.environ.get('AIA2_KUBEJS_SOURCE', str(SOURCES/'KubeJS-2101')))
        public_api = ftb/'common/src/main/java/dev/ftb/mods/ftbquests/api/QuestFile.java'
        uuid_converter = kube/'src/main/java/dev/latvian/mods/kubejs/plugin/builtin/wrapper/UUIDWrapper.java'
        if not jar.is_file() or not (jdk/'bin/javac').is_file() or not public_api.is_file() or not uuid_converter.is_file():
            self.skipTest('External exact Rhino85/JDK21/FTB1.21.1/KubeJS2101 sources unavailable')
        # Prevent a newer public API/converter from silently changing this regression.
        self.assertEqual(hashlib.sha256(public_api.read_bytes()).hexdigest(),
                         '2c665f0f939f8ea0009fd62856fb47b9ed483bc941ca41d32170d52d3e3b81b9')
        self.assertEqual(hashlib.sha256(uuid_converter.read_bytes()).hexdigest(),
                         '9a9a4f042b1e2a7275b7b5b4e1b02e8012a11069e33e506ec65b87799ebcab1e')
        jars = [jar]
        for pattern in ['com.google.guava/guava/32.1.2-jre/*/*.jar', 'com.google.code.gson/gson/2.10.1/*/*.jar']:
            found = list((TOOLS/'gradle-home/caches/modules-2/files-2.1').glob(pattern))
            if not found:
                self.skipTest('External Rhino dependencies missing')
            jars.extend(found)
        cp = os.pathsep.join(map(str,jars))
        fixtures = {
            'net/minecraft/world/entity/Entity.java': '''package net.minecraft.world.entity;
                import java.util.UUID; import dev.latvian.mods.rhino.util.RemapForJS;
                public class Entity { private final UUID id; public Entity(UUID id){this.id=id;}
                @RemapForJS("getUuid") public UUID getUUID(){return id;}
                public boolean isServerPlayer(){return true;} public boolean isFake(){return false;} }''',
            'net/minecraft/world/entity/player/Player.java': '''package net.minecraft.world.entity.player;
                public class Player extends net.minecraft.world.entity.Entity {public Player(java.util.UUID id){super(id);}}''',
            'net/minecraft/server/level/ServerPlayer.java': '''package net.minecraft.server.level;
                public class ServerPlayer extends net.minecraft.world.entity.player.Player {public ServerPlayer(java.util.UUID id){super(id);}}''',
            'net/neoforged/neoforge/common/util/FakePlayer.java': '''package net.neoforged.neoforge.common.util;
                public class FakePlayer extends net.minecraft.server.level.ServerPlayer {public FakePlayer(java.util.UUID id){super(id);} public boolean isFake(){return true;}}''',
            'dev/ftb/mods/ftbquests/quest/TeamData.java': '''package dev.ftb.mods.ftbquests.quest;
                public class TeamData {private final java.util.UUID id; public int completed;
                public TeamData(java.util.UUID id){this.id=id;} public java.util.UUID getTeamId(){return id;}}''',
            'dev/ftb/mods/ftbteams/api/Team.java': '''package dev.ftb.mods.ftbteams.api;
                public interface Team {java.util.UUID getId();}''',
            'dev/latvian/mods/kubejs/error/KubeRuntimeException.java': '''package dev.latvian.mods.kubejs.error;
                public class KubeRuntimeException extends RuntimeException {public KubeRuntimeException(String s){super(s);}
                public KubeRuntimeException(String s,Throwable e){super(s,e);}
                public KubeRuntimeException source(dev.latvian.mods.kubejs.script.SourceLine l){return this;}}''',
            'dev/latvian/mods/kubejs/script/SourceLine.java': '''package dev.latvian.mods.kubejs.script;
                public class SourceLine {public static SourceLine of(dev.latvian.mods.rhino.Context c){return new SourceLine();}}''',
            'org/jetbrains/annotations/Nullable.java': '''package org.jetbrains.annotations;
                public @interface Nullable {}''',
        }
        for name in ('Chapter','Quest','QuestLink'):
            fixtures['dev/ftb/mods/ftbquests/quest/'+name+'.java'] = 'package dev.ftb.mods.ftbquests.quest; public class '+name+' {}'
        with tempfile.TemporaryDirectory(prefix='aia2-ftb-interop-') as dest:
            source_files=[]
            for name, body in fixtures.items():
                file=Path(dest)/name
                file.parent.mkdir(parents=True,exist_ok=True)
                file.write_text(body)
                source_files.append(str(file))
            source_files.extend(map(str,[public_api,uuid_converter,
                ROOT/'companion/src/main/java/ua/aia2/guard/FtbQuestBridge.java',
                ROOT/'tests/rhino/FtbQuestInteropHarness.java']))
            compiled = subprocess.run([str(jdk/'bin/javac'),'-encoding','UTF-8','-cp',cp,'-d',dest,*source_files],capture_output=True,text=True)
            self.assertEqual(compiled.returncode,0,compiled.stdout+compiled.stderr)
            run=subprocess.run([str(jdk/'bin/java'),'-cp',dest+os.pathsep+cp,'FtbQuestInteropHarness',str(ROOT)],capture_output=True,text=True)
            self.assertEqual(run.returncode,0,run.stdout+run.stderr)
            self.assertIn('actual Rhino85/UUID-wrapper/production-helper assertions passed',run.stdout)
            print(run.stdout.strip())
