"""Desktop startup and reproducible headless calculation commands."""
import argparse
import sys
from datetime import datetime
from pathlib import Path
from .Configuration import load_inputs, save_inputs
from .Paths import OUTPUTS_DIR


def main(argv=None):
    parser = argparse.ArgumentParser(description='Rotary Melter C++ engineering workstation')
    parser.add_argument('--build', action='store_true', help='Rebuild the self-contained interface and exit')
    parser.add_argument('--run', action='store_true', help='Calculate and export JSON/CSV/HTML/Markdown')
    parser.add_argument('--engine', choices=['cpp', 'javascript'], default='cpp', help='C++ production engine or retained V11 reference')
    parser.add_argument('--integrator', choices=['midpoint', 'rk4', 'dopri5'], default='midpoint')
    parser.add_argument('--threads', type=int, default=4)
    parser.add_argument('--water-model', choices=['constant', 'if97_reference'], default='constant')
    parser.add_argument('--analyse', choices=['convergence', 'sensitivity', 'rpm', 'sizing'], help='Run a C++ numerical analysis and export its report')
    parser.add_argument('--config', type=Path, help='Scenario JSON; default: config/default_inputs.json')
    parser.add_argument('--output', type=Path, help='Headless output directory')
    parser.add_argument('--write-default', type=Path, help='Save the default scenario and exit')
    parser.add_argument('--self-test', type=Path, help='Run the desktop integration test with isolated scenario storage')
    parser.add_argument('--require-gpu', action='store_true', help='Require a successful NVIDIA field audit in the desktop self-test')
    parser.add_argument('--gpu-info', type=Path, help='Write NVIDIA availability diagnostics as JSON and exit')
    args = parser.parse_args(argv)
    if args.gpu_info:
        import json
        from .GpuAnalysis import info
        report = info()
        args.gpu_info.parent.mkdir(parents=True, exist_ok=True)
        args.gpu_info.write_text(json.dumps(report, indent=2), encoding='utf-8')
        return 0 if report['available'] else 1
    if args.write_default:
        save_inputs(load_inputs(args.config) if args.config else load_inputs(), args.write_default)
        return 0
    if args.run or args.analyse:
        from .Reporting import export_result
        configuration = load_inputs(args.config) if args.config else load_inputs()
        output = args.output or OUTPUTS_DIR / datetime.now().strftime('run_%Y%m%d_%H%M%S_%f')
        if args.analyse:
            if args.engine != 'cpp':
                parser.error('--analyse requires --engine cpp')
            from .NativeEngine import execute
            from .AnalysisReporting import export_analysis
            result = execute({'action': 'analyse', 'analysis': args.analyse, 'configuration': configuration,
                              'options': {'integrator': args.integrator, 'threads': args.threads, 'waterModel': args.water_model}})
            folder = export_analysis(result, output)
            print(f'Analysis: {args.analyse} | Cases: {len(result.get("cases", []))}')
        else:
            if args.engine == 'cpp':
                from .NativeEngine import simulate
                result = simulate(configuration, options={'integrator': args.integrator, 'threads': args.threads,
                                  'parallelKernel': True, 'waterModel': args.water_model})
            else:
                from .JavaScriptEngine import simulate
                result = simulate(configuration)
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
    desktop_args=['--self-test', str(args.self_test)] if args.self_test else []
    if args.require_gpu:desktop_args.append('--require-gpu')
    return desktop_main(desktop_args)
