"""Resolve project and packaged resources independently of the shell directory."""
from pathlib import Path
import os
import shutil
import sys

PACKAGE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = Path(sys.executable).resolve().parent if getattr(sys, 'frozen', False) else PACKAGE_DIR.parent
WEB_DIR = PACKAGE_DIR / 'web'
DEFAULT_CONFIG = (Path(sys._MEIPASS) if getattr(sys, 'frozen', False) else PROJECT_ROOT) / 'config' / 'default_inputs.json'
OUTPUTS_DIR = PROJECT_ROOT / 'outputs'
REFERENCE_DIR = PROJECT_ROOT / 'reference'
HTML_FILE = OUTPUTS_DIR / 'web' / 'Rotary_Melter.html'


def resource_path(name):
    if hasattr(sys, '_MEIPASS'):
        return Path(sys._MEIPASS) / name
    if name == 'Rotary_Melter.html':
        return HTML_FILE
    if name == 'assets/motion_cpp_record.npz':
        return OUTPUTS_DIR/'reference'/'motion_cpp_record.npz'
    if name.startswith('assets/'):
        return REFERENCE_DIR / Path(name).name
    return PROJECT_ROOT / name


def node_executable():
    override = os.environ.get('ROTARY_MELTER_NODE')
    if override:
        return str(Path(override).resolve())
    local = PROJECT_ROOT / '.tools' / 'node' / ('node.exe' if os.name == 'nt' else 'bin/node')
    if local.is_file():
        return str(local)
    found = shutil.which('node')
    if found:
        return found
    raise RuntimeError('Node.js is missing. Run .venv\\Scripts\\python.exe -m tools.SetupNode.')
