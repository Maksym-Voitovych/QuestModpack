"""Exact Clibano frame contracts and actual helper/handler in a modeled host.

The host deliberately has no POI API. This is not optional-mod weaving or a
Minecraft client/menu networking test; the real GuardPolicy is compiled here.
"""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class ClibanoOwnershipTests(unittest.TestCase):
    def test_exact_native_frame_controller_and_menu_contracts(self):
        manifest = json.loads((ROOT / 'content/research/evidence/forbidden_core_next_v5/manifest.json').read_text())
        self.assertEqual(manifest['installed_version'], '2.6.1')
        self.assertEqual(manifest['pin'], '34f83feb76204fd773e1d2e1d69ecc5b2f2bb933')
        names = {'ClibanoFrameBlockEntity.java', 'AbstractClibanoFrameBlock.java', 'CreateClibanoInteraction.java'}
        frozen = {}
        for row in manifest['sources']:
            name = Path(row.get('repository_path', row['path'])).name
            if name in names:
                raw = (ROOT / row['path']).read_bytes()
                self.assertEqual(hashlib.sha256(raw).hexdigest(), row['sha256'])
                frozen[name] = raw.decode()
        self.assertEqual(set(frozen), names)
        self.assertIn('public FrameData getFrameData()', frozen['ClibanoFrameBlockEntity.java'])
        self.assertIn('public record FrameData(BlockState replaceState, BlockPos mainPos)', frozen['ClibanoFrameBlockEntity.java'])
        self.assertIn('new FrameData(Blocks.AIR.defaultBlockState(), BlockPos.ZERO)', frozen['ClibanoFrameBlockEntity.java'])
        self.assertIn('blockEntity.setFrameData(new ClibanoFrameBlockEntity.FrameData(oldState, this.centerPos))', frozen['CreateClibanoInteraction.java'])
        frame = frozen['AbstractClibanoFrameBlock.java']
        self.assertIn('serverLevel.getPoiManager().find(', frame)
        self.assertIn('player.openMenu(clibanoMainBlockEntity, buffer ->', frame)
        self.assertIn('ResiduesStorage.STREAM_CODEC.encode(buffer, clibanoMainBlockEntity.getResiduesStorage())', frame)
        gates = json.loads((ROOT / 'kubejs/config/aia2_runtime.json').read_text())['blockGates']
        for block in ['clibano_main_part', 'clibano_center', 'clibano_corner', 'clibano_side_horizontal', 'clibano_side_vertical']:
            self.assertEqual(gates['forbidden_arcanus:' + block], 15)
        menu_names = {'ClibanoMenu.java', 'ClibanoMainBlockEntity.java', 'ClibanoSmeltLogic.java', 'ResiduesStorage.java'}
        menu_sources = {}
        expanded = json.loads((ROOT / 'content/research/evidence/clibano_core_v6/manifest.json').read_text())
        for row in expanded['sources']:
            name = Path(row.get('repository_path', row['path'])).name
            if name in menu_names:
                raw = (ROOT / row['path']).read_bytes()
                self.assertEqual(hashlib.sha256(raw).hexdigest(), row['sha256'])
                menu_sources[name] = raw.decode()
        self.assertEqual(set(menu_sources), menu_names)
        self.assertIn('private final MenuCreationContext<ClibanoMainBlockEntity, IItemHandler> context', menu_sources['ClibanoMenu.java'])
        self.assertIn('return stillValid(this.context.levelAccess(), player, ModBlocks.CLIBANO_MAIN_PART.get())', menu_sources['ClibanoMenu.java'])
        self.assertIn('private ClibanoSmeltLogic logic', menu_sources['ClibanoMainBlockEntity.java'])
        self.assertIn('blockEntity.logic.cookingProgress[0]', menu_sources['ClibanoMainBlockEntity.java'])
        self.assertIn('public int[] cookingProgress', menu_sources['ClibanoSmeltLogic.java'])
        self.assertIn('public int[] cookingDuration', menu_sources['ClibanoSmeltLogic.java'])
        self.assertIn('public static final StreamCodec<RegistryFriendlyByteBuf, ResiduesStorage> STREAM_CODEC', menu_sources['ResiduesStorage.java'])
        context = json.loads((ROOT / 'content/research/evidence/clibano_menu_context_v6/manifest.json').read_text())
        raw = (ROOT / context['evidence_path']).read_bytes()
        self.assertEqual(hashlib.sha256(raw).hexdigest(), context['evidence_sha256'])
        self.assertIn('ContainerLevelAccess.evaluate', raw.decode())
        hook = (ROOT / 'companion/src/main/java/ua/aia2/guard/mixin/ClibanoMenuValidityMixin.java').read_text()
        self.assertIn('<init>(ILnet/neoforged/neoforge/items/ItemStackHandler;Lnet/minecraft/world/inventory/ContainerData;Ljava/util/Map;Lnet/valhelsia/valhelsia_core/api/common/block/entity/MenuCreationContext;)V', hook)

    def test_actual_owner_helper_and_menu_handler_complete_physical_structure_and_policy(self):
        jdk = Path(os.environ.get('JAVA_HOME', '/workspace/aia2-toolchains/jdk-21.0.9'))
        if not (jdk / 'bin/javac').is_file():
            self.skipTest('External JDK21 unavailable')
        fixture = json.loads((ROOT / 'tests/fixtures/clibano-owner-host.json').read_text())
        with tempfile.TemporaryDirectory(prefix='aia2-clibano-owner-') as tmp:
            files = []
            for name, source in fixture.items():
                path = Path(tmp) / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(source)
                files.append(str(path))
            files += [str(ROOT / 'tests/fixtures/ClibanoOwnershipHarness.java')]
            files += [str(ROOT / f'companion/src/main/java/ua/aia2/guard/{name}.java')
                      for name in ['GuardPolicy', 'ClibanoOwnership']]
            files += [str(ROOT / f'companion/src/main/java/ua/aia2/guard/mixin/{name}.java')
                      for name in ['ClibanoFrameMenuMixin', 'ClibanoMenuValidityMixin']]
            result = subprocess.run([str(jdk / 'bin/javac'), '-encoding', 'UTF-8', '-d', tmp, *files], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            result = subprocess.run([str(jdk / 'bin/java'), '-cp', tmp, 'ua.aia2.guard.ClibanoOwnershipHarness'], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn('actual-helper/handler/real-policy modeled assertions PASS', result.stdout)
            print(result.stdout.strip())
