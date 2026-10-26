"""Run the same production thermal equations used by the desktop interface."""
import json
import subprocess
from .Paths import PROJECT_ROOT, WEB_DIR, node_executable


def simulate(configuration, no_history=False):
    command = [node_executable(), str(WEB_DIR / 'RunCalculation.cjs')]
    completed = subprocess.run(
        command, input=json.dumps({'configuration': configuration, 'noHistory': no_history}, allow_nan=False),
        capture_output=True, text=True, encoding='utf-8', cwd=PROJECT_ROOT, timeout=900)
    if completed.returncode:
        raise RuntimeError(completed.stderr.strip() or 'The calculation engine failed.')
    return json.loads(completed.stdout)
