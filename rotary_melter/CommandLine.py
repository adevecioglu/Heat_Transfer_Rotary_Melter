"""Desktop startup and reproducible headless calculation commands."""
import argparse
import sys
from datetime import datetime
from pathlib import Path
from .Configuration import load_inputs, save_inputs
from .Paths import OUTPUTS_DIR


def main(argv=None):
    parser = argparse.ArgumentParser(description='Rotary Melter V11 / Desktop 2.2')
    parser.add_argument('--build', action='store_true', help='Rebuild the self-contained interface and exit')
    parser.add_argument('--run', action='store_true', help='Calculate with the production JavaScript model and export JSON/CSV/HTML')
    parser.add_argument('--config', type=Path, help='Scenario JSON; default: config/default_inputs.json')
    parser.add_argument('--output', type=Path, help='Headless output directory')
    parser.add_argument('--write-default', type=Path, help='Save the default scenario and exit')
    parser.add_argument('--self-test', type=Path, help='Run the desktop integration test with isolated scenario storage')
    args = parser.parse_args(argv)
    if args.write_default:
        save_inputs(load_inputs(args.config) if args.config else load_inputs(), args.write_default)
        return 0
    if args.run:
        from .JavaScriptEngine import simulate
        from .Reporting import export_result
        result = simulate(load_inputs(args.config) if args.config else load_inputs())
        output = args.output or OUTPUTS_DIR / datetime.now().strftime('run_%Y%m%d_%H%M%S_%f')
        folder = export_result(result, output)
        print(f"Target reached: {result.get('targetReached')} | Elapsed physical time: {result.get('seconds')} s")
        print(f'Output: {folder.resolve()}')
        return 0
    if getattr(sys, 'frozen', False):
        from .Paths import resource_path
        built = resource_path('Rotary_Melter.html')
    else:
        from tools.BuildInterface import build_interface
        built = build_interface()
    if args.build:
        print(built)
        return 0
    from .Interface import main as desktop_main
    return desktop_main(['--self-test', str(args.self_test)] if args.self_test else [])
