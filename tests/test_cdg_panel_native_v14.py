"""Actual panel proof helper/bridge/policy and original CDG MoldType/HEAD on a modeled host.

CODEC adapters, Create apply body, Minecraft ownership/storage and Mixin dispatch
are modeled. This is not an installed CDG/Create binary or full-client test.
"""
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
FROZEN = ROOT/'content/research/evidence/cdg_molds_v13'
NATIVE_CREATE = (ROOT/'content/research/evidence/technology_v5/create/core_verified/official/'
                 'src/main/java/com/simibubi/create/content/processing/basin/BasinRecipe.java')
PRODUCTION = ROOT/'companion/src/main/java/ua/aia2/guard'

GUARD = '''package ua.aia2.guard;
import java.util.Map;import net.minecraft.world.item.crafting.Recipe;import net.minecraft.server.level.ServerLevel;import net.minecraft.world.level.block.entity.BlockEntity;
/** Actual stage policy; modeled machine ownership/current recipe manager adapters. */
public final class Aia2MachineGuard {
 public static final GuardPolicy BLOCKS=new GuardPolicy(),RECIPES=new GuardPolicy();public static boolean ready=true;
 public static boolean isReady(){return ready&&BLOCKS.isReady()&&RECIPES.isReady();}
 public static String getOwner(BlockEntity machine){return machine.owner;}
 public static boolean mayObserveStage(String team,int epoch){return isReady()&&team!=null&&!team.isBlank()&&RECIPES.mayUseStage(epoch,team);}
 public static boolean mayProcessRecipe(BlockEntity machine,Recipe<?> recipe){if(!(machine.getLevel() instanceof ServerLevel level))return true;if(!isReady()||!BLOCKS.mayTick("create:basin",machine.owner))return false;for(var holder:level.getRecipeManager().getRecipes())if(holder.value()==recipe)return RECIPES.mayTick(holder.id().toString(),machine.owner);return false;}
 public static void progress(String team,int completed){BLOCKS.setTeamProgress(team,completed);RECIPES.setTeamProgress(team,completed);}
 public static void configure(){BLOCKS.clear();RECIPES.clear();ready=true;BLOCKS.setRules(Map.of("create:basin",4));RECIPES.setRules(Map.of("createdieselgenerators:compression_molding/sheet_metal_panel",12));progress("team_a",11);progress("team_b",11);BLOCKS.setReady();RECIPES.setReady();}
}
'''


class CdgPanelNativeTests(unittest.TestCase):
    def test_original_sources_prove_mold_and_post_consumption_boundaries(self):
        manifest = json.loads((FROZEN/'manifest.json').read_text())
        files = {row['path']: row['sha256'] for row in manifest['files']}
        for relative in ('cdg/src/main/java/com/jesz/createdieselgenerators/content/molds/MoldType.java',
                         'cdg/src/main/java/com/jesz/createdieselgenerators/mixins/BasinRecipeMixin.java',
                         'cdg/src/main/java/com/jesz/createdieselgenerators/content/molds/CompressionMoldingRecipe.java'):
            path = FROZEN/relative
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), files[path.relative_to(ROOT).as_posix()])
        cdg = (FROZEN/'cdg/src/main/java/com/jesz/createdieselgenerators/mixins/BasinRecipeMixin.java').read_text()
        self.assertIn('moldStack = stack;', cdg)
        self.assertNotIn('break;', cdg)
        self.assertIn('if (moldingRecipe.moldType != type)', cdg)
        self.assertIn('at=@At("HEAD")', cdg)
        recipe = (FROZEN/'cdg/src/main/java/com/jesz/createdieselgenerators/content/molds/CompressionMoldingRecipe.java').read_text()
        self.assertIn('extends CompactingRecipe', recipe)
        self.assertIn('MoldType.findById(params.mold())', recipe)
        create = NATIVE_CREATE.read_text().split('private static boolean apply(', 1)[1].split('public static RecipeHolder', 1)[0]
        ordered = ['for (boolean simulate : Iterate.trueAndFalse)', 'if (!simulate && test)',
                   'availableItems.extractItem(slot, 1, false)',
                   'basin.acceptOutputs(recipeOutputItems, recipeOutputFluids, simulate)', 'return true;\n\t}']
        positions = [create.index(value) for value in ordered]
        self.assertEqual(positions, sorted(positions))

    def test_helper_embeds_the_exact_frozen_recipe_and_uses_error_rejecting_codec(self):
        source = (PRODUCTION/'CdgPanelAccess.java').read_text()
        expected = json.loads(re.search(r'JsonParser.parseString\("""(.*?)"""\)', source, re.S).group(1))
        recipe = json.loads((FROZEN/'recipes/createdieselgenerators/compression_molding/sheet_metal_panel.json').read_text())
        del recipe['type']
        self.assertEqual(expected, recipe)
        self.assertIn('codec.parse(ops, EXPECTED.deepCopy()).result().orElse(null)', source)
        self.assertNotIn('resultOrPartial(', source.replace('resultOrPartial(),', 'partial results,'))
        self.assertIn('!isCurrentMold(expected)', source)
        self.assertIn('before.equals(actual)', source)
        bridge = (PRODUCTION/'ProductionMilestoneBridge.java').read_text()
        self.assertIn('"createdieselgenerators:compression_molding"', bridge)
        self.assertIn('!CdgPanelAccess.matchesRecipe(holder.value(), level)', bridge)
        self.assertIn('!CdgPanelAccess.isCurrentMold(recipe)', bridge)

    def run_host(self, mutation=None):
        jdk = Path(os.environ.get('JAVA_HOME', '/workspace/aia2-toolchains/jdk-21.0.9'))
        cache = Path(os.environ.get('GRADLE_USER_HOME', '/workspace/aia2-toolchains/gradle-home'))
        jars = sorted((cache/'caches/modules-2/files-2.1/com.google.code.gson/gson').glob('**/gson-*.jar'))
        if not (jdk/'bin/javac').is_file() or not jars:
            self.skipTest('JDK21/Gson unavailable for actual-class modeled host')
        sources = json.loads((ROOT/'tests/fixtures/mechanics-ledger-host-v10.json').read_text())
        sources.pop('ua/aia2/guard/CdgPanelAccess.java', None)  # Only historical hosts may use the compatibility stub.
        annotations = json.loads((ROOT/'tests/fixtures/nasa-production-host-v7.json').read_text())
        sources.update({name: value for name, value in annotations.items() if name.startswith('org/spongepowered/')})
        sources.update(json.loads((ROOT/'tests/fixtures/cdg-panel-host-v14.json').read_text()))
        resource = sources['net/minecraft/resources/ResourceLocation.java']
        sources['net/minecraft/resources/ResourceLocation.java'] = resource.replace('public String toString()',
            'public static ResourceLocation fromNamespaceAndPath(String namespace,String path){return parse(namespace+":"+path);}'
            'public String getNamespace(){return value.split(":",2)[0];}public String getPath(){return value.split(":",2)[1];}public String toString()')
        sources['ua/aia2/guard/Aia2MachineGuard.java'] = GUARD
        sources['ua/aia2/guard/KeyProductionBridge.java'] = '''package ua.aia2.guard;import net.minecraft.world.level.block.entity.BlockEntity;import net.minecraft.world.item.crafting.Recipe;public final class KeyProductionBridge{public static int calls;public static void finishedMachine(BlockEntity block,Recipe<?> recipe){calls++;}}'''
        with tempfile.TemporaryDirectory(prefix='aia2-cdg-panel-native-v14-') as temporary:
            directory = Path(temporary); files = []
            for name, value in sources.items():
                path = directory/name; path.parent.mkdir(parents=True, exist_ok=True); path.write_text(value); files.append(str(path))
            for name in ['GuardPolicy', 'ProductionMilestoneBridge', 'CdgPanelAccess']:
                path = PRODUCTION/(name+'.java')
                text = path.read_text()
                if mutation == 'codec' and name == 'CdgPanelAccess':
                    self.assertEqual(text.count('before != null && before.equals(actual)'), 1)
                    text = text.replace('before != null && before.equals(actual)', 'before != null')
                if mutation == 'live_mold' and name == 'ProductionMilestoneBridge':
                    before = '&& !CdgPanelAccess.isCurrentMold(recipe) ? null : current'
                    self.assertEqual(text.count(before), 1)
                    text = text.replace(before, '&& false ? null : current')
                copy = directory/'ua/aia2/guard'/(name+'.java'); copy.parent.mkdir(parents=True, exist_ok=True); copy.write_text(text); files.append(str(copy))
            handler = PRODUCTION/'mixin/CreateBasinRecipeMixin.java'
            text = handler.read_text()
            if mutation == 'simulation':
                before = 'if (!test && Boolean.TRUE.equals(callback.getReturnValue()))'
                self.assertEqual(text.count(before), 1)
                text = text.replace(before, 'if (Boolean.TRUE.equals(callback.getReturnValue()))')
            copy = directory/'ua/aia2/guard/mixin/CreateBasinRecipeMixin.java'; copy.parent.mkdir(parents=True, exist_ok=True); copy.write_text(text); files.append(str(copy))
            for relative in ['content/molds/MoldType.java', 'mixins/BasinRecipeMixin.java']:
                files.append(str(FROZEN/('cdg/src/main/java/com/jesz/createdieselgenerators/'+relative)))
            files.append(str(ROOT/'tests/fixtures/CdgPanelHarness.java'))
            classpath = os.pathsep.join([temporary, str(jars[-1])])
            result = subprocess.run([str(jdk/'bin/javac'), '--release', '21', '-encoding', 'UTF-8',
                                     '-cp', classpath, '-d', temporary, *files], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stdout+result.stderr)
            return subprocess.run([str(jdk/'bin/java'), '-cp', classpath, 'ua.aia2.guard.mixin.CdgPanelHarness',
                                   str(directory/'worlds')], capture_output=True, text=True)

    def test_actual_helper_bridge_handlers_mold_policy_and_historical_proofs(self):
        result = self.run_host()
        self.assertEqual(result.returncode, 0, result.stdout+result.stderr)
        self.assertRegex(result.stdout, r'\d+ CDG panel actual-helper/actual-bridge/actual-handlers/real-policy assertions PASS')
        print(result.stdout.strip())

    def test_simulation_grant_negative_control_fails(self):
        result = self.run_host('simulation')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('Simulation cannot record a native CDG panel receipt', result.stderr)

    def test_changed_runtime_codec_negative_control_fails(self):
        result = self.run_host('codec')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('same-ID altered encoded semantics rejected', result.stderr)

    def test_cached_mold_mutation_negative_control_fails(self):
        result = self.run_host('live_mold')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('public moldType mutation is checked even after generation index was cached', result.stderr)


if __name__ == '__main__':
    unittest.main()
