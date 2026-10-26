"""Build a standalone EXE from the organized sources without touching originals."""
import subprocess
import sys
from .BuildInterface import build_interface
from rotary_melter.Paths import PROJECT_ROOT, REFERENCE_DIR, OUTPUTS_DIR


def main():
    interface = build_interface()
    work = OUTPUTS_DIR / 'build'
    work.mkdir(parents=True, exist_ok=True)
    command = [sys.executable, '-m', 'PyInstaller', '--noconfirm', '--onefile', '--windowed',
               '--name', 'Rotary_Melter_V11', '--distpath', str(PROJECT_ROOT / 'releases' / 'current'),
               '--workpath', str(work / 'work'), '--specpath', str(work),
               '--add-data', str(interface)+';.',
               '--add-data', str(REFERENCE_DIR / 'motion_v18_record.npz')+';assets',
               '--add-data', str(PROJECT_ROOT / 'config')+';config', str(PROJECT_ROOT / 'app.py')]
    return subprocess.call(command, cwd=PROJECT_ROOT)


if __name__ == '__main__':
    raise SystemExit(main())
