"""Actual curated electrum bridge and Create handlers in a bounded modeled host.

The optional Create binary, Mixin weaving, native heat/inventory effects and
Minecraft are not launched. Pinned source-order checks and behavior tests keep
those limits separate from the actual bridge/handler/policy code being compiled.
"""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
NATIVE = ('content/research/evidence/technology_v5/create/core_verified/official/'
          'src/main/java/com/simibubi/create/content/processing/basin/BasinRecipe.java')

GUARD = '''package ua.aia2.guard;
import java.util.Map;
import net.minecraft.world.item.crafting.Recipe;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.level.block.entity.BlockEntity;
/** Actual policy, modeled machine ownership and native recipe-manager adapter. */
public final class Aia2MachineGuard {
 public static final GuardPolicy BLOCKS=new GuardPolicy(), RECIPES=new GuardPolicy();
 public static boolean ready=true;
 public static boolean isReady(){return ready&&BLOCKS.isReady()&&RECIPES.isReady();}
 public static String getOwner(BlockEntity machine){return machine.owner;}
 public static boolean mayObserveStage(String team,int epoch){return isReady()&&team!=null&&!team.isBlank()&&RECIPES.mayUseStage(epoch,team);}
 public static boolean mayProcessRecipe(BlockEntity machine,Recipe<?> recipe){
  if(!(machine.getLevel() instanceof ServerLevel level))return true;
  if(!isReady()||!BLOCKS.mayTick("create:basin",machine.owner))return false;
  for(var holder:level.getRecipeManager().getRecipes())
   if(holder.value()==recipe)return RECIPES.mayTick(holder.id().toString(),machine.owner);
  return false;
 }
 public static void progress(String team,int completed){BLOCKS.setTeamProgress(team,completed);RECIPES.setTeamProgress(team,completed);}
 public static void configure(){
  BLOCKS.clear();RECIPES.clear();ready=true;
  BLOCKS.setRules(Map.of("create:basin",4));
  RECIPES.setRules(Map.of("createaddition:mixing/electrum",8));
  progress("team_a",14);progress("team_b",14);BLOCKS.setReady();RECIPES.setReady();
 }
}
'''


class CreateElectrumNativeTests(unittest.TestCase):
    def test_pinned_native_heat_consumption_acceptance_and_required_handler_edges(self):
        source = ROOT/NATIVE
        document = json.loads((ROOT/'content/research/technology_v5.json').read_text())
        create = next(mod for mod in document['mods'] if mod['mod_id'] == 'create')
        evidence = [row for row in create['sources'] if row['path'] == NATIVE]
        self.assertEqual(len(evidence), 1)
        self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(), evidence[0]['sha256'])
        native = source.read_text().split('private static boolean apply(', 1)[1].split('public static RecipeHolder', 1)[0]
        ordered = ['getRequiredHeat()', 'for (boolean simulate : Iterate.trueAndFalse)',
                   'if (!simulate && test)', 'availableItems.extractItem(slot, 1, false)',
                   'basin.acceptOutputs(recipeOutputItems, recipeOutputFluids, simulate)', 'return true;\n\t}']
        positions = [native.index(value) for value in ordered]
        self.assertEqual(positions, sorted(positions))
        handler = (ROOT/'companion/src/main/java/ua/aia2/guard/mixin/CreateBasinRecipeMixin.java').read_text()
        descriptor = 'apply(Lcom/simibubi/create/content/processing/basin/BasinBlockEntity;Lnet/minecraft/world/item/crafting/Recipe;Z)Z'
        self.assertEqual(handler.count(descriptor), 2)
        self.assertEqual(handler.count('require = 1'), 2)
        self.assertIn('at = @At("HEAD"), cancellable = true', handler)
        self.assertIn('at = @At("RETURN")', handler)
        self.assertIn('if (!test && Boolean.TRUE.equals(callback.getReturnValue()))', handler)

    def run_actual_handlers(self, allow_simulation=False):
        jdk = Path(os.environ.get('JAVA_HOME', '/workspace/aia2-toolchains/jdk-21.0.9'))
        cache = Path(os.environ.get('GRADLE_USER_HOME', '/workspace/aia2-toolchains/gradle-home'))
        jars = sorted((cache/'caches/modules-2/files-2.1/com.google.code.gson/gson').glob('**/gson-*.jar'))
        if not (jdk/'bin/javac').is_file() or not jars:
            self.skipTest('JDK21/Gson unavailable for actual-class modeled host')
        sources = json.loads((ROOT/'tests/fixtures/mechanics-ledger-host-v10.json').read_text())
        annotations = json.loads((ROOT/'tests/fixtures/nasa-production-host-v7.json').read_text())
        sources.update({name: value for name, value in annotations.items() if name.startswith('org/spongepowered/')})
        sources['ua/aia2/guard/Aia2MachineGuard.java'] = GUARD
        sources['ua/aia2/guard/KeyProductionBridge.java'] = '''package ua.aia2.guard;
import net.minecraft.world.level.block.entity.BlockEntity;import net.minecraft.world.item.crafting.Recipe;
public class KeyProductionBridge {public static int calls;public static void finishedMachine(BlockEntity machine,Recipe<?> recipe){calls++;}}'''
        with tempfile.TemporaryDirectory(prefix='aia2-electrum-native-v12-') as temporary:
            directory = Path(temporary); files = []
            for name, value in sources.items():
                path = directory/name; path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(value); files.append(str(path))
            production = ROOT/'companion/src/main/java/ua/aia2/guard'
            files.extend(str(production/(name+'.java')) for name in ['GuardPolicy', 'ProductionMilestoneBridge'])
            handler = production/'mixin/CreateBasinRecipeMixin.java'
            if allow_simulation:
                before = 'if (!test && Boolean.TRUE.equals(callback.getReturnValue()))'
                source = handler.read_text(); self.assertEqual(source.count(before), 1)
                bad = directory/'ua/aia2/guard/mixin/CreateBasinRecipeMixin.java'
                bad.parent.mkdir(parents=True, exist_ok=True)
                bad.write_text(source.replace(before, 'if (Boolean.TRUE.equals(callback.getReturnValue()))'))
                files.append(str(bad))
            else:
                files.append(str(handler))
            files.append(str(ROOT/'tests/fixtures/CreateElectrumHarness.java'))
            classpath = os.pathsep.join([temporary, str(jars[-1])])
            compiled = subprocess.run([str(jdk/'bin/javac'), '--release', '21', '-encoding', 'UTF-8',
                                       '-cp', classpath, '-d', temporary, *files], capture_output=True, text=True)
            self.assertEqual(compiled.returncode, 0, compiled.stdout+compiled.stderr)
            return subprocess.run([str(jdk/'bin/java'), '-cp', classpath,
                                   'ua.aia2.guard.mixin.CreateElectrumHarness', str(directory/'worlds')],
                                  capture_output=True, text=True)

    def test_actual_bridge_handlers_stage_policy_reload_and_old_history(self):
        result = self.run_actual_handlers()
        self.assertEqual(result.returncode, 0, result.stdout+result.stderr)
        self.assertRegex(result.stdout, r'\d+ electrum actual-bridge/actual-handlers/real-policy modeled assertions PASS')
        print(result.stdout.strip())

    def test_simulation_grant_negative_control_fails_real_behavior(self):
        result = self.run_actual_handlers(allow_simulation=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('Simulation cannot record a native electrum receipt', result.stderr)


if __name__ == '__main__':
    unittest.main()
