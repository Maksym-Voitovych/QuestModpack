#!/usr/bin/env python3
"""Create a portable runtime+source archive and verify its complete SHA256 manifest."""
import argparse
import hashlib
import json
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1]
VERSION = '0.4.8-alpha'
DEFAULT = Path('/workspace/shared/downloads') / ('AIA2-runtime-' + VERSION + '.zip')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=DEFAULT)
    args = parser.parse_args()
    config = json.loads((ROOT / 'kubejs/config/aia2_runtime.json').read_text())
    if config.get('machineGuard', {}).get('mode') == 'required':
        jars = list((ROOT / 'mods').glob('aia2-machine-guard-*.jar'))
        if len(jars) != 1:
            parser.error('Required mode needs exactly one compiled AIA2 Machine Guard JAR in mods/')
        with zipfile.ZipFile(jars[0]) as jar:
            assert 'ua/aia2/guard/Aia2MachineGuard.class' in jar.namelist()
            assert jar.testzip() is None, 'Compiled companion JAR CRC failed'
            if config.get('progressionVersion', 0) >= 4:
                for name in ['KeyProductionBridge', 'RhinoLongMapBridge', 'FtbQuestBridge', 'CreativeManaGuard', 'RootsAltarAccess', 'RootsRitualProof', 'ModernRecipeProxyAccess', 'EnderTaskAccess', 'EnderSmeltingProxyAccess', 'PowahOrbAccess']:
                    assert 'ua/aia2/guard/' + name + '.class' in jar.namelist()
                if (ROOT / 'kubejs/config/aia2_mechanics.json').is_file():
                    assert 'ua/aia2/guard/ProductionMilestoneBridge.class' in jar.namelist()
                for name in ['FireWorksiteAccess', 'FireWorksiteInteraction']:
                    assert 'ua/aia2/guard/' + name + '.class' in jar.namelist()
                for name in ['EnderFireCraftingMixin', 'FireWorksiteBaseMixin']:
                    assert 'ua/aia2/guard/mixin/' + name + '.class' in jar.namelist()
                assert 'ua/aia2/guard/mixin/KeyResultProductionMixin.class' in jar.namelist()
            for name in ['BoundTickingBlockEntityMixin', 'CrafterDispenseMixin',
                         'CraftingQuickMoveMixin', 'ResultPickupMixin', 'RecipeManagerContextMixin',
                         'MekanismCachedRecipeMixin', 'CreateBasinRecipeMixin',
                         'AE2MolecularAssemblerMixin', 'AE2CraftingTermSlotMixin', 'MekanismRobitRecipeMixin',
                         'DraconicFusionCoreMixin', 'BotaniaManaItemHandlerMixin', 'BotaniaManaTabletPoolMixin', 'RootsMortarMixin', 'RootsAltarMixin', 'ApothicSpawnerMixin',
                         'ModernCrafterMixin', 'ModernRecipeConversionsMixin', 'ModernReplicatorMixin',
                         'OritechMachineMixin', 'OritechFluidMachineMixin', 'OritechDustMixin', 'OritechRecipeLookupMixin', 'OritechBaseTickMixin',
                         'RootsMutationIngredientsMixin', 'RootsMutationRadiantMixin', 'EnderCraftingTaskMixin', 'EnderCrafterMixin', 'EnderTankMixin', 'PowahEnergizingOrbMixin']:
                assert 'ua/aia2/guard/mixin/' + name + '.class' in jar.namelist()
    selected = []
    for folder in ['kubejs', 'config', 'mods', 'implementation', 'tools', 'tests', 'design', 'docs', 'content', 'companion']:
        for file in (ROOT / folder).rglob('*'):
            rel = file.relative_to(ROOT)
            if not file.is_file() or any(p in {'.gradle', 'build', 'run', '__pycache__'} for p in rel.parts):
                continue
            if rel.as_posix() == 'implementation/package-report.json':
                continue  # Avoid recursively embedding an old archive checksum.
            selected.append(file)
    selected.extend([ROOT / name for name in ['install_runtime.py', 'README.uk.md', 'README.md', '.gitignore', '.gitattributes']])
    manifest = {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                for p in sorted(selected)}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(args.output, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for p in sorted(selected):
            z.write(p, p.relative_to(ROOT).as_posix())
        z.writestr('SHA256SUMS.json', json.dumps(manifest, indent=2)+'\n')
    with zipfile.ZipFile(args.output) as z:
        assert z.testzip() is None, 'CRC verification failed'
        assert set(z.namelist()) == {*manifest, 'SHA256SUMS.json'}
        for name, digest in manifest.items():
            assert hashlib.sha256(z.read(name)).hexdigest() == digest, name
        guard_jars = [p for p in z.namelist() if p.startswith('mods/') and p.endswith('.jar')]
    args.output.chmod(0o644)
    report = {'version': VERSION, 'archive': str(args.output.resolve()),
              'bytes': args.output.stat().st_size, 'files': len(manifest),
              'sha256': hashlib.sha256(args.output.read_bytes()).hexdigest(),
              'crc_and_manifest': 'passed', 'companion_jars': guard_jars,
              'download_in_client': 'not_verifiable_from_execution_tools'}
    (ROOT / 'implementation/package-report.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
