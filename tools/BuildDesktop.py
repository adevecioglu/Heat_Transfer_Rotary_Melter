"""Build a standalone EXE from the organized sources without touching originals."""
import subprocess
import json
import argparse
import importlib.util
from pathlib import Path
import sys
from .BuildInterface import build_interface
from rotary_melter.Paths import PROJECT_ROOT, REFERENCE_DIR, OUTPUTS_DIR
from rotary_melter.Reporting import REFERENCE_EQUATION_FILES


def main(with_gpu=False, *, dist_dir=None):
    from .BuildCpp import build
    native=build()
    interface = build_interface()
    work = OUTPUTS_DIR / 'build'
    work.mkdir(parents=True, exist_ok=True)
    name='Rotary_Melter_Cpp_GPU' if with_gpu else 'Rotary_Melter_Cpp'
    recording=OUTPUTS_DIR/'reference'/'motion_cpp_record.npz'
    if not recording.exists():recording=REFERENCE_DIR/'motion_v18_record.npz'
    dist_path = dist_dir.resolve() if dist_dir is not None else PROJECT_ROOT / 'releases' / 'current'
    command = [sys.executable, '-m', 'PyInstaller', '--noconfirm', '--onefile', '--windowed',
               '--name', name, '--distpath', str(dist_path),
               '--workpath', str(work / 'work'), '--specpath', str(work),
               '--add-data', str(interface)+';.',
               '--add-data', str(recording)+';assets',
               '--add-data', str(PROJECT_ROOT/'native/cuda/FieldAnalysis.cu')+';cuda',
               '--add-data', str(PROJECT_ROOT/'native')+';native_sources',
               '--add-data', str(PROJECT_ROOT / 'config')+';config',
               '--add-data', str(PROJECT_ROOT / 'docs' / 'CPP_CALCULATION_EQUATIONS.md')+';docs',
               '--add-data', str(PROJECT_ROOT / 'docs' / 'CALCULATION_EQUATIONS.md')+';docs',
               '--add-data', str(PROJECT_ROOT / 'native' / 'third_party_licenses')+';licenses']
    for relative in REFERENCE_EQUATION_FILES:
        destination = Path('reference_sources') / Path(relative).parent
        command += ['--add-data', f'{PROJECT_ROOT / relative};{destination.as_posix()}']
    manifest=json.loads((native.parent/'build_manifest.json').read_text(encoding='utf-8'))
    for name in manifest['runtimeFiles']:
        if name.lower().endswith('.dll'):
            command+=['--add-binary',str(native/name)+';native']
    if with_gpu:
        command+=['--collect-all','cupy','--collect-all','cupy_backends','--collect-all','fastrlock']
        site=Path(sys.prefix)/'Lib/site-packages'
        for package in ('cuda_runtime','cuda_nvrtc'):
            command+=['--add-data',str(site/'nvidia'/package)+';nvidia/'+package]
    else:
        command+=['--exclude-module','cupy','--exclude-module','cupy_backends','--exclude-module','nvidia']
    command.append(str(PROJECT_ROOT / 'app.py'))
    return subprocess.call(command, cwd=PROJECT_ROOT)


if __name__ == '__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--with-gpu',action='store_true')
    parser.add_argument('--dist-dir', type=Path, help='EXE output directory (default: releases/current)')
    args = parser.parse_args()
    raise SystemExit(main(args.with_gpu, dist_dir=args.dist_dir))
