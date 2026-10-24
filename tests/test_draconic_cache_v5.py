"""Exact DE source contract and executable production handler; no DE mod launch."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


def body(text, marker):
    start = text.index('{', text.index(marker))
    depth = 0
    for end in range(start, len(text)):
        depth += (text[end] == '{') - (text[end] == '}')
        if depth == 0:
            return text[start:end+1]
    raise AssertionError('Unclosed method: '+marker)


class DraconicCacheGuardTest(unittest.TestCase):
    def test_exact_source_confirms_packet_and_saved_recipe_cache_bypass(self):
        audit = json.loads((ROOT/'implementation/draconic-cache-v5-audit.json').read_text())
        sources = {}
        for source in audit['sources']:
            data = (ROOT/source['path']).read_bytes()
            self.assertEqual(hashlib.sha256(data).hexdigest(), source['sha256'])
            sources[Path(source['source_path']).name] = data.decode()
        core = sources['TileFusionCraftingCore.java']
        self.assertIn('startCraft();', body(core, 'public void receivePacketFromClient('))
        self.assertIn('setActiveRecipe(holder)', body(core, 'public void startCraft()'))
        self.assertIn('.byKey(', body(core, 'public RecipeHolder<IFusionRecipe> getActiveRecipe()'))
        self.assertIn('recipe.value().tickFusionState', body(core, 'public void tick()'))
        self.assertNotIn('getRecipeFor', body(core, 'public void tick()'))
        api = sources['IFusionRecipe.java']
        self.assertNotIn('.shrink(', body(api, 'default boolean canStartCraft('))
        self.assertIn('stack.shrink(1)', body(api, 'static void completeCraft('))
        self.assertIn('catalyst.shrink(catCount)', body(api, 'static void completeCraft('))
        cancel = body(core, 'public void cancelCraft()')
        self.assertIn('setEnergyRequirement(0, 0)', cancel)
        self.assertNotIn('.shrink(', cancel)
        self.assertIn('mod_version=3.1.4', sources['gradle.properties'].replace(' ', ''))

    def test_actual_mixin_handler_blocks_cached_stage99_before_consumption(self):
        jdk = Path(os.environ.get('JAVA_HOME', '/workspace/aia2-toolchains/jdk-21.0.9'))
        if not (jdk/'bin/javac').exists(): self.skipTest('External JDK21 unavailable')
        fixtures = {
            'net/minecraft/server/level/ServerLevel.java': 'package net.minecraft.server.level; public final class ServerLevel {}',
            # Interface host permits executing the real mixin handler directly;
            # Gradle separately compiles it against Minecraft's actual class.
            'net/minecraft/world/level/block/entity/BlockEntity.java': '''package net.minecraft.world.level.block.entity;
                public interface BlockEntity { Object getLevel(); String team(); }''',
            'net/minecraft/world/item/crafting/RecipeHolder.java': '''package net.minecraft.world.item.crafting;
                public record RecipeHolder<T>(T value) {}''',
            'org/spongepowered/asm/mixin/Mixin.java': '''package org.spongepowered.asm.mixin;
                public @interface Mixin {String[] targets(); boolean remap() default true;}''',
            'org/spongepowered/asm/mixin/Pseudo.java': 'package org.spongepowered.asm.mixin; public @interface Pseudo {}',
            'org/spongepowered/asm/mixin/Shadow.java': '''package org.spongepowered.asm.mixin;
                public @interface Shadow {boolean remap() default true;}''',
            'org/spongepowered/asm/mixin/injection/At.java': '''package org.spongepowered.asm.mixin.injection;
                public @interface At {String value();}''',
            'org/spongepowered/asm/mixin/injection/Inject.java': '''package org.spongepowered.asm.mixin.injection;
                public @interface Inject {String method(); At at(); boolean cancellable(); boolean remap(); int require();}''',
            'org/spongepowered/asm/mixin/injection/callback/CallbackInfo.java': '''package org.spongepowered.asm.mixin.injection.callback;
                public final class CallbackInfo {public boolean canceled; public void cancel(){canceled=true;}}''',
            'ua/aia2/guard/Aia2MachineGuard.java': '''package ua.aia2.guard;
                import net.minecraft.world.level.block.entity.BlockEntity;
                public final class Aia2MachineGuard {
                  public static final GuardPolicy policy = new GuardPolicy(); public static int calls;
                  public static boolean mayProcessRecipe(BlockEntity owner,Object recipe){calls++;return policy.mayUseStage((Integer)recipe,owner.team());}
                }''',
            'ua/aia2/guard/mixin/DraconicHandlerHarness.java': '''package ua.aia2.guard.mixin;
                import java.lang.reflect.Method;
                import net.minecraft.server.level.ServerLevel;
                import net.minecraft.world.level.block.entity.BlockEntity;
                import net.minecraft.world.item.crafting.RecipeHolder;
                import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;
                import ua.aia2.guard.Aia2MachineGuard;
                public final class DraconicHandlerHarness {
                  static int assertions;
                  static void check(boolean condition,String message){assertions++;if(!condition)throw new AssertionError(message);}
                  static final class Core extends DraconicFusionCoreMixin implements BlockEntity {
                    Object level=new ServerLevel(); String owner="team-a"; boolean crafting=true; int inputs=12,energyRequirement=100,cancelCalls,outputs;
                    RecipeHolder<?> cached = new RecipeHolder<>(99);
                    public Object getLevel(){return level;} public String team(){return owner;}
                    public boolean isCrafting(){return crafting;} public RecipeHolder<?> getActiveRecipe(){return cached;}
                    public void cancelCraft(){cancelCalls++;crafting=false;energyRequirement=0;}
                    boolean tick(Method hook)throws Exception {
                      CallbackInfo callback=new CallbackInfo();hook.invoke(this,callback);
                      if(!callback.canceled&&crafting){inputs--;outputs++;}
                      return callback.canceled;
                    }
                  }
                  public static void main(String[] args)throws Exception {
                    var policy=Aia2MachineGuard.policy;policy.setRules(java.util.Map.of("aia2:postgame",99));policy.setTeamProgress("team-a",47);policy.setReady();
                    Method hook=DraconicFusionCoreMixin.class.getDeclaredMethod("aia2$guardCachedFusion",CallbackInfo.class);hook.setAccessible(true);
                    Core denied=new Core();check(denied.tick(hook),"cached stage99 job canceled before completion");
                    check(denied.inputs==12&&denied.outputs==0,"no inputs consumed and no output minted");
                    check(denied.cancelCalls==1&&denied.energyRequirement==0,"native cancellation stops charging requirements");
                    check(Aia2MachineGuard.calls==1,"cached recipe actually reaches authoritative policy");
                    policy.setTeamProgress("team-a",48);Core allowed=new Core();check(!allowed.tick(hook),"all48 complete authorizes postgame");
                    check(allowed.inputs==11&&allowed.outputs==1,"allowed operation resumes ordinary execution");
                    policy.setTeamProgress("team-a",47);check(allowed.tick(hook),"existing cache is rechecked after progress change");
                    check(allowed.inputs==11&&allowed.outputs==1,"no second output after access loss");
                    Core unowned=new Core();unowned.owner=null;check(unowned.tick(hook),"unowned cached recipe denied");
                    Core unknown=new Core();unknown.cached=new RecipeHolder<>(100);check(unknown.tick(hook),"unknown recipe quarantined");
                    int calls=Aia2MachineGuard.calls;Core client=new Core();client.level=new Object();check(!client.tick(hook),"client rendering is not canceled");
                    check(Aia2MachineGuard.calls==calls,"client never reads server policy");
                    Core idle=new Core();idle.crafting=false;check(!idle.tick(hook),"idle comparator cache untouched");
                    check(Aia2MachineGuard.calls==calls,"idle recipe not queried");
                    Core missing=new Core();missing.cached=null;check(!missing.tick(hook),"native missing-recipe handling remains intact");
                    policy.clear();Core notReady=new Core();check(notReady.tick(hook),"unready policy stays closed");
                    System.out.println("DraconicHandlerHarness: "+assertions+" production-handler/real-policy assertions passed; modeled host, no optional DE dispatch");
                  }
                }''',
        }
        with tempfile.TemporaryDirectory(prefix='aia2-draconic-cache-') as destination:
            files = []
            for name, text in fixtures.items():
                path = Path(destination)/name; path.parent.mkdir(parents=True, exist_ok=True); path.write_text(text); files.append(str(path))
            files += [str(ROOT/'companion/src/main/java/ua/aia2/guard/GuardPolicy.java'),
                      str(ROOT/'companion/src/main/java/ua/aia2/guard/mixin/DraconicFusionCoreMixin.java')]
            result = subprocess.run([str(jdk/'bin/javac'), '-encoding', 'UTF-8', '-d', destination, *files], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stdout+result.stderr)
            result = subprocess.run([str(jdk/'bin/java'), '-cp', destination, 'ua.aia2.guard.mixin.DraconicHandlerHarness'], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stdout+result.stderr)
            self.assertIn('16 production-handler/real-policy assertions passed', result.stdout)
            print(result.stdout.strip())
